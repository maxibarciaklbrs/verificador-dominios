/* 
 Turnstile
*/

const FORM = document.getElementById("registroForm");
const SUBMIT_BTN = document.getElementById("SUBMIT_BTN");
const TURNSTILE_TOKEN = document.getElementById("TURNSTILE_TOKEN");
const privacyAccept = document.getElementById("privacy_accept");

window.onTurnstileSuccess = function (token) {
  TURNSTILE_TOKEN.value = token;
};

window.onTurnstileExpired = function () {
  TURNSTILE_TOKEN.value = "";
};

window.onTurnstileError = function () {
  TURNSTILE_TOKEN.value = "";
};

FORM.addEventListener("submit", function (e) {
  if (!TURNSTILE_TOKEN.value) {
    e.preventDefault();
    alert("Completa el captcha antes de enviar.");
    return;
  }

  SUBMIT_BTN.disabled = true;
  SUBMIT_BTN.textContent = "Enviando...";
});

/* 
 Validaciones Form
*/

const nombre = document.getElementById("nombre");
const apellido = document.getElementById("apellido");
const email = document.getElementById("email");
const telefono = document.getElementById("telefono");
const submitBtn = document.getElementById("SUBMIT_BTN");

const NAME_REGEX = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$/;
const PHONE_REGEX = /^\+?[1-9]\d{7,14}$/;

const PERSONAL_DOMAINS = [
  "gmail.com",
  "hotmail.com",
  "outlook.com",
  "live.com",
  "yahoo.com",
  "icloud.com",
  "proton.me",
  "protonmail.com",
];

function setError(field, message) {
  document.getElementById(`${field.id}-error`).textContent = message;
  field.classList.add("input-error");
}

function clearError(field) {
  document.getElementById(`${field.id}-error`).textContent = "";
  field.classList.remove("input-error");
}

nombre.addEventListener("input", function () {
    this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]/g, "");
  });

nombre.addEventListener("blur", function () {
  this.value = this.value
    .trim()
    .replace(/\s+/g, " ");
});

function validateNombre() {
  const value = nombre.value.trim();
  
  if (!value) {
    setError(nombre, "El nombre es obligatorio.");
    return false;
  }

  if (value.length < 2) {
    setError(nombre, "Debe tener al menos 2 caracteres.");
    return false;
  }

  if (value.length > 80) {
  setError(nombre, "Longitud máxima excedida.");
  return false;
  }

  if (!NAME_REGEX.test(value)) {
    setError(nombre, "Solo se permiten letras y espacios.");
    return false;
  }

  clearError(nombre);
  return true;
}

apellido.addEventListener("input", function () {
    this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]/g, "");
  });

apellido.addEventListener("blur", function () {
  this.value = this.value
    .trim()
    .replace(/\s+/g, " ");
});

function validateApellido() {
  const value = apellido.value.trim();
  
  if (!value) {
    setError(apellido, "Los apellidos son obligatorios.");
    return false;
  }

  if (value.length < 2) {
    setError(apellido, "Debe tener al menos 2 caracteres.");
    return false;
  }

  if (value.length > 120) {
  setError(apellido, "Longitud máxima excedida.");
  return false;
  }

  if (!NAME_REGEX.test(value)) {
    setError(apellido, "Solo se permiten letras y espacios.");
    return false;
  }

  clearError(apellido);
  return true;
}

function validateEmail() {
  const value = email.value.trim().toLowerCase();

  if (!value) {
    setError(email, "El correo es obligatorio.");
    return false;
  }

  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  if (!emailRegex.test(value)) {
    setError(email, "Introduce un correo válido.");
    return false;
  }

  const domain = value.split("@")[1];

  if (PERSONAL_DOMAINS.includes(domain)) {
    setError(email, "Debe utilizar un correo corporativo.");
    return false;
  }

  clearError(email);
  return true;
}

telefono.addEventListener("input", function () {
  let value = this.value;

  // Elimina todo excepto números y +
  value = value.replace(/[^\d+]/g, "");

  // Elimina cualquier + que no esté al principio
  value = value.replace(/(?!^)\+/g, "");

  this.value = value;
});

function validateTelefono() {
  const value = telefono.value.trim();

  // Campo opcional
  if (!value) {
    clearError(telefono);
    return true;
  }

  if (!PHONE_REGEX.test(value)) {
    setError(
      telefono,
      "Introduce un teléfono válido (ej: +34612345678)."
    );
    return false;
  }

  clearError(telefono);
  return true;
}

function validateForm() {
  const valid =
    validateNombre() &&
    validateApellido() &&
    validateEmail() &&
    validateTelefono() &&
    privacyAccept.checked;

  submitBtn.disabled = !valid;

  return valid;
}

[nombre, apellido, email, telefono].forEach((field) => {
  field.addEventListener("input", validateForm);
});
privacyAccept.addEventListener("change", validateForm);
validateForm();

// ============================================
// FUNCIONES DE PAGO CON STRIPE (AGREGADAS)
// ============================================

let codigoVerificacion = '';
let emailUsuario = '';

// Función para establecer el código de verificación
function setCodigoPago(codigo) {
    codigoVerificacion = codigo;
    console.log('✅ Código de pago establecido:', codigo);
    // Mostrar la sección de pago
    mostrarSeccionPago();
}

// Función para establecer el email
function setEmailPago(email) {
    emailUsuario = email;
    console.log('✅ Email de pago establecido:', email);
}

// Función para mostrar la sección de pago
function mostrarSeccionPago() {
    const container = document.getElementById('seccionPagoContainer');
    if (container) {
        container.style.display = 'block';
        // Hacer scroll a la sección
        setTimeout(() => {
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
    }
    
    // Mostrar el botón de pago
    const btnPago = document.getElementById('btnPago');
    if (btnPago) {
        btnPago.style.display = 'block';
    }
}

// Función para realizar pago con Stripe
async function realizarPagoConStripe() {
    const email = emailUsuario || document.getElementById('email')?.value || '';
    const codigo = codigoVerificacion;
    
    if (!codigo || !email) {
        mostrarMensajePago('error', '❌ Faltan datos: código de verificación o email');
        return;
    }
    
    // Mostrar loading
    const btn = document.getElementById('btnRealizarPago');
    if (!btn) return;
    
    const textoOriginal = btn.textContent;
    btn.textContent = '⏳ Procesando...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/pago/crear-sesion-stripe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                codigo: codigo,
                email: email
            })
        });
        
        const data = await response.json();
        
        if (data.exitoso) {
            // Redirigir a Stripe
            window.location.href = data.checkout_url;
        } else {
            mostrarMensajePago('error', data.mensaje || '❌ Error al crear sesión de pago');
            btn.textContent = textoOriginal;
            btn.disabled = false;
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensajePago('error', '❌ Error de conexión. Intenta nuevamente.');
        btn.textContent = textoOriginal;
        btn.disabled = false;
    }
}

// Función para simular pago manual (legacy)
async function realizarPagoManual() {
    const email = emailUsuario || document.getElementById('email')?.value || '';
    const codigo = codigoVerificacion;
    
    if (!codigo || !email) {
        mostrarMensajePago('error', '❌ Faltan datos: código de verificación o email');
        return;
    }
    
    const btn = document.getElementById('btnPagoManual');
    if (!btn) return;
    
    const textoOriginal = btn.textContent;
    btn.textContent = '⏳ Procesando...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/pago/webhook-pago', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                codigo: codigo,
                monto: 50.00
            })
        });
        
        const data = await response.json();
        
        if (data.exitoso) {
            mostrarMensajePago('exito', '✅ ' + data.mensaje);
            // Recargar para actualizar estado
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            mostrarMensajePago('error', data.mensaje || '❌ Error al procesar pago manual');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensajePago('error', '❌ Error de conexión');
    }
    
    btn.textContent = textoOriginal;
    btn.disabled = false;
}

// Función para verificar estado del pago
async function verificarEstadoPago() {
    const codigo = codigoVerificacion;
    
    if (!codigo) {
        mostrarMensajePago('info', '⚠️ No hay código de verificación disponible');
        return;
    }
    
    try {
        const response = await fetch(`/api/pago/estado-pago/${codigo}`);
        const data = await response.json();
        
        if (data.exitoso) {
            if (data.pagado) {
                mostrarMensajePago('exito', '✅ ¡Pago confirmado! Ya puedes realizar el escaneo.');
                // Habilitar botón de escaneo si existe
                const btnEscaneo = document.getElementById('btnEscaneo');
                if (btnEscaneo) {
                    btnEscaneo.style.display = 'block';
                }
            } else {
                mostrarMensajePago('info', '⏳ Aún no se ha registrado tu pago.');
            }
        } else {
            mostrarMensajePago('error', data.mensaje || '❌ Error al verificar estado');
        }
    } catch (error) {
        console.error('Error verificando estado:', error);
        mostrarMensajePago('error', '❌ Error de conexión al verificar estado');
    }
}

// Función para toggle del menú de pago
function togglePago() {
    const menu = document.getElementById('menuPago');
    if (!menu) return;
    
    if (menu.style.display === 'none' || menu.style.display === '') {
        menu.style.display = 'block';
        // Verificar estado al abrir
        verificarEstadoPago();
    } else {
        menu.style.display = 'none';
    }
}

// Función para mostrar mensajes de pago
function mostrarMensajePago(tipo, mensaje) {
    // Buscar contenedor de mensajes
    let container = document.getElementById('mensajesPago');
    
    if (!container) {
        // Crear contenedor si no existe
        container = document.createElement('div');
        container.id = 'mensajesPago';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            width: 100%;
        `;
        document.body.appendChild(container);
    }
    
    const div = document.createElement('div');
    div.className = `mensaje-pago ${tipo}`;
    div.style.cssText = `
        padding: 15px 20px;
        margin-bottom: 10px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease;
        background: ${tipo === 'exito' ? '#d4edda' : tipo === 'error' ? '#f8d7da' : '#cce5ff'};
        color: ${tipo === 'exito' ? '#155724' : tipo === 'error' ? '#721c24' : '#004085'};
        border: 1px solid ${tipo === 'exito' ? '#c3e6cb' : tipo === 'error' ? '#f5c6cb' : '#b8daff'};
    `;
    div.textContent = mensaje;
    
    container.appendChild(div);
    
    // Auto-eliminar después de 6 segundos
    setTimeout(() => {
        if (div.parentNode) {
            div.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (div.parentNode) {
                    div.remove();
                }
            }, 300);
        }
    }, 6000);
}

// Agregar estilos para animaciones
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

console.log('✅ Funciones de pago cargadas correctamente');
