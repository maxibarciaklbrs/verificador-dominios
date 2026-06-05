const email = "{{ email }}";
const codigo = "{{ codigo }}";
const dominio = "{{ dominio }}";

let verificado = false;
let escaneoActivo = false;

function habilitarBotonPago() {
  const btnPago = document.getElementById("btnPago");
  btnPago.disabled = false;
  btnPago.style.opacity = "1";
}

async function validarDNS() {
  const btn = document.getElementById("btnValidar");
  const resultadoDiv = document.getElementById("resultado");

  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Verificando DNS...';

  resultadoDiv.style.display = "block";
  resultadoDiv.className = "resultado-box resultado-warning";
  resultadoDiv.innerHTML = `🔍 Verificando registro TXT en ${dominio}...`;

  try {
    const response = await fetch("/validar-dns", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, codigo, dominio }),
    });

    const data = await response.json();

    if (data.exitoso) {
      verificado = true;
      resultadoDiv.className = "resultado-box resultado-success";
      resultadoDiv.innerHTML = `✅ ${data.mensaje}`;
      habilitarBotonPago();
    } else {
      resultadoDiv.className = "resultado-box resultado-error";
      resultadoDiv.innerHTML = `❌ ${data.mensaje} 💡 Espera unos minutos a que se propague el DNS y vuelve a intentar.`;
    }
  } catch (error) {
    resultadoDiv.className = "resultado-box resultado-error";
    resultadoDiv.innerHTML = `❌ Error de conexión: ${error}`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🔍 Validar DNS";
  }
}

function mostrarMensaje(opcion) {
  const resultadoDiv = document.getElementById("resultado");
  resultadoDiv.style.display = "block";

  if (opcion === "realizar-pago") {
    resultadoDiv.className = "resultado-box resultado-info";
    resultadoDiv.innerHTML = `
            <strong>💰 EN DESARROLLO</strong><br>
            La pasarela de pago está en fase de integración.<br><br>
            <strong>Próximamente disponibles:</strong>
            <ul>
                <li>Stripe (Tarjetas de crédito/débito)</li>
                <li>PayPal</li>
                <li>Transferencia bancaria</li>
            </ul>
            <em>Por ahora, usa "Pago Completado" para simular el proceso.</em>
        `;
  } else if (opcion === "pago-completado") {
    resultadoDiv.className = "resultado-box resultado-warning";
    resultadoDiv.innerHTML =
      '<span class="loading-spinner"></span> Procesando pago...';

    fetch("/webhook-pago", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo, monto: 50.0 }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.exitoso) {
          resultadoDiv.className = "resultado-box resultado-success";
          resultadoDiv.innerHTML = `
                    <strong>✅ PAGO CONFIRMADO</strong><br>
                    ${data.mensaje}<br>
                    📧 Confirmación enviada al administrador<br>
                    📱 Notificación enviada por Telegram<br>
                    🛡️ Auditoría desbloqueada
                `;

          const opcionPago = document.querySelector(
            ".dropdown-content a:last-child",
          );
          if (opcionPago) {
            opcionPago.style.opacity = "0.5";
            opcionPago.style.pointerEvents = "none";
          }

          habilitarAuditoria();
        } else {
          resultadoDiv.className = "resultado-box resultado-error";
          resultadoDiv.innerHTML = `
                    <strong>❌ ERROR</strong><br>
                    ${data.mensaje}
                `;
        }
      })
      .catch((error) => {
        resultadoDiv.className = "resultado-box resultado-error";
        resultadoDiv.innerHTML = `
                <strong>❌ ERROR DE CONEXIÓN</strong><br>
                ${error}
            `;
      });
  }
}

function habilitarAuditoria() {
  const seccion = document.getElementById("seccionAuditoria");
  seccion.style.display = "block";
  seccion.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function iniciarAuditoria() {
  if (escaneoActivo) {
    alert("⚠️ Ya hay un escaneo en curso.");
    return;
  }

  const btn = document.getElementById("btnAuditoria");
  const estadoDiv = document.getElementById("estadoEscaneo");
  const resumenDiv = document.getElementById("resumenEscaneo");

  escaneoActivo = true;

  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Iniciando escaneo...';

  estadoDiv.style.display = "block";
  resumenDiv.style.display = "none";
  estadoDiv.innerHTML = "⏳ Preparando contenedor ZAP...";

  try {
    const response = await fetch("/lanzar-escaneo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, dominio }),
    });

    const data = await response.json();

    if (data.exitoso && data.cache) {
      mostrarResumen(data.resumen, data.url_completa);
      escaneoActivo = false;
      btn.disabled = false;
      btn.innerHTML = "🔄 Re-escanear";
    } else if (data.exitoso && data.escaneando) {
      await esperarEscaneo();
      escaneoActivo = false;
      btn.disabled = false;
      btn.innerHTML = "🔄 Re-escanear";
    } else {
      estadoDiv.innerHTML = "❌ Error al iniciar el escaneo.";
      escaneoActivo = false;
      btn.disabled = false;
      btn.innerHTML = "🔍 Iniciar Escaneo";
    }
  } catch (error) {
    estadoDiv.innerHTML = `❌ Error de conexión: ${error}`;
    escaneoActivo = false;
    btn.disabled = false;
    btn.innerHTML = "🔍 Iniciar Escaneo";
  }
}

async function esperarEscaneo() {
  const estadoDiv = document.getElementById("estadoEscaneo");

  const mensajes = [
    "🔍 Rastreando directorios...",
    "📡 Analizando cabeceras...",
    "🛡️ Verificando servidor...",
    "🔐 Cookies y seguridad...",
    "📊 Generando informe...",
  ];

  let intentos = 0;

  while (intentos < 30) {
    await new Promise((r) => setTimeout(r, 10000));
    intentos++;

    const msg = mensajes[Math.floor(intentos / 2) % mensajes.length];
    estadoDiv.innerHTML = `${msg} <small>⏱️ ${intentos * 10}s</small>`;

    try {
      const response = await fetch("/estado-escaneo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (data.completado) {
        mostrarResumen(data.resumen, data.url_completa);
        escaneoActivo = false;
        return;
      }
    } catch (e) {
      console.error(e);
    }
  }

  estadoDiv.innerHTML = "⚠️ El escaneo tarda más de lo esperado.";
  escaneoActivo = false;
}

function mostrarResumen(resumen, urlCompleta) {
  document.getElementById("estadoEscaneo").style.display = "none";

  const resumenDiv = document.getElementById("resumenEscaneo");
  resumenDiv.style.display = "block";

  document.getElementById("countCriticas").innerText = resumen.criticas;
  document.getElementById("countMedias").innerText = resumen.medias;
  document.getElementById("countBajas").innerText = resumen.bajas;
  document.getElementById("countTotal").innerText = resumen.total;

  const lista = document.getElementById("listaAlertas");

  if (resumen.detalles?.length) {
    lista.innerHTML = resumen.detalles
      .map((d) => {
        const icono =
          d.riesgo === "3"
            ? "🔴"
            : d.riesgo === "2"
              ? "🟠"
              : d.riesgo === "1"
                ? "🟢"
                : "ℹ️";

        return `<li>${icono} <strong>${d.nombre}</strong></li>`;
      })
      .join("");
  } else {
    lista.innerHTML = "<li>✅ Sin vulnerabilidades</li>";
  }

  document.getElementById("linkDescarga").href = urlCompleta;

  resumenDiv.scrollIntoView({ behavior: "smooth", block: "center" });
}
