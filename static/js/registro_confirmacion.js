const APP = window.APP_DATA || {};

let verificado = false;
let pagado = false;
let escaneoActivo = false;

// ==========================================================
// PAGO
// ==========================================================

function habilitarBotonPago() {
  const formPago = document.getElementById("formPago");

  if (formPago) {
    formPago.style.display = "block";
  }
}

// ==========================================================
// VALIDACIÓN DNS
// ==========================================================

async function validarDNS() {
  const { email, codigo, dominio } = APP;

  const btn = document.getElementById("btnValidar");

  const resultadoDiv = document.getElementById("resultado");

  btn.disabled = true;

  btn.innerHTML = '<span class="loading-spinner"></span> Verificando DNS...';

  resultadoDiv.style.display = "block";

  resultadoDiv.className = "resultado-box resultado-warning";

  resultadoDiv.innerHTML = `Verificando registro TXT en ${dominio}...`;

  try {
    const response = await fetch("/validar-dns", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        email,
        codigo,
        dominio,
      }),
    });

    const data = await response.json();

    if (data.exitoso) {
      verificado = true;

      resultadoDiv.className = "resultado-box resultado-success";

      resultadoDiv.innerHTML = data.mensaje;

      habilitarBotonPago();

      cambiarDisplayDns();
    } else {
      resultadoDiv.className = "resultado-box resultado-error";

      resultadoDiv.innerHTML = `
        ${data.mensaje}
        <br><br>
        Espera unos minutos a que se propague el DNS
        y vuelve a intentarlo.
        `;
    }
  } catch (error) {
    resultadoDiv.className = "resultado-box resultado-error";

    resultadoDiv.innerHTML = `
      Error de conexión:
      ${error}
      `;
  } finally {
    btn.disabled = false;

    btn.innerHTML = "Validar DNS";
  }
}

// ==========================================================
// MENSAJES
// ==========================================================

function mostrarMensaje(opcion) {
  const resultadoDiv = document.getElementById("resultado");

  if (!resultadoDiv) {
    return;
  }

  resultadoDiv.style.display = "block";

  if (opcion === "realizar-pago") {
    resultadoDiv.className = "resultado-box resultado-info";

    resultadoDiv.innerHTML = `
      <strong>Preparando pago...</strong>
      <br>
      Serás redirigido a Stripe.
      `;
  }
}

// ==========================================================
// AUDITORÍA
// ==========================================================

function habilitarAuditoria() {
  const seccion = document.getElementById("seccionAuditoria");

  if (!seccion) {
    return;
  }

  seccion.style.display = "block";

  seccion.scrollIntoView({
    behavior: "smooth",
    block: "center",
  });
}

async function iniciarAuditoria() {
  const { email, dominio } = APP;

  if (escaneoActivo) {
    alert("Ya hay un escaneo en curso.");

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

  estadoDiv.innerHTML = "Preparando análisis...";

  try {
    const response = await fetch("/lanzar-escaneo", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        email,
        dominio,
      }),
    });

    const data = await response.json();

    if (data.exitoso && data.cache) {
      mostrarResumen(data.resumen, data.url_completa);
    } else if (data.exitoso && data.escaneando) {
      await esperarEscaneo();
    } else {
      estadoDiv.innerHTML = "Error al iniciar el escaneo.";
    }
  } catch (error) {
    estadoDiv.innerHTML = `Error de conexión: ${error}`;
  } finally {
    escaneoActivo = false;

    btn.disabled = false;

    btn.innerHTML = "Re-escanear";
  }
}

async function esperarEscaneo() {
  const { email } = APP;

  const estadoDiv = document.getElementById("estadoEscaneo");

  let intentos = 0;

  const mensajes = [
    "Rastreando directorios...",

    "Analizando cabeceras...",

    "Verificando servidor...",

    "Cookies y seguridad...",

    "Generando informe...",
  ];

  while (intentos < 30) {
    await new Promise((r) => setTimeout(r, 10000));

    intentos++;

    estadoDiv.innerHTML = `
      ${mensajes[intentos % mensajes.length]}
      <small>
      ${intentos * 10}s
      </small>
      `;

    try {
      const response = await fetch("/estado-escaneo", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          email,
        }),
      });

      const data = await response.json();

      if (data.completado) {
        mostrarResumen(data.resumen, data.url_completa);

        return;
      }
    } catch (e) {
      console.error(e);
    }
  }

  estadoDiv.innerHTML = "El escaneo tarda más de lo esperado.";
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
        let icono = "ℹ️";

        if (d.riesgo === "3") icono = "🔴";
        else if (d.riesgo === "2") icono = "🟠";
        else if (d.riesgo === "1") icono = "🟢";

        return `
        <li>
          ${icono}
          <strong>${d.nombre}</strong>
        </li>
        `;
      })
      .join("");
  } else {
    lista.innerHTML = "<li>Sin vulnerabilidades</li>";
  }

  document.getElementById("linkDescarga").href = urlCompleta;
}

// ==========================================================
// UI
// ==========================================================

function cambiarDisplayDns() {
  const seccion = document.getElementById("seccionInstrucciones");

  const boton = document.getElementById("btnValidar");

  if (seccion) seccion.style.display = "none";

  if (boton) boton.style.display = "none";
}

function cambiarDisplayPago() {
  const seccion = document.getElementById("seccionPago");

  if (seccion) seccion.style.display = "none";
}

// ==========================================================
// INICIO
// ==========================================================

window.addEventListener("DOMContentLoaded", () => {
  if (APP.verificado) {
    cambiarDisplayDns();
    habilitarBotonPago();
  }

  if (APP.pagado) {
    cambiarDisplayDns();
    cambiarDisplayPago();
    habilitarAuditoria();
  }
});
