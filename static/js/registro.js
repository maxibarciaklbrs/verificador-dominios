/* 
 Turnstile
*/

const FORM = document.getElementById("registroForm");
const SUBMIT_BTN = document.getElementById("SUBMIT_BTN");
const TURNSTILE_TOKEN = document.getElementById("TURNSTILE_TOKEN");

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
  setError(nombre, "Longitud máxima excedida.");
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
    validateTelefono();

  submitBtn.disabled = !valid;

  return valid;
}

[nombre, apellido, email, telefono].forEach((field) => {
  field.addEventListener("input", validateForm);
});

validateForm();
