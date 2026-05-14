// Autenticacion FINEX: login, registro y validaciones visuales.
let currentRegisterType = null;

function toggleForms(e) {
  e.preventDefault();
  document.getElementById("loginForm").classList.toggle("active");
  document.getElementById("registerTypeSelector").classList.toggle("active");
  document.getElementById("formLogin").reset();
  clearMessages();
  currentRegisterType = null;
}

function selectRegisterType(tipo) {
  currentRegisterType = tipo;
  document.getElementById("registerTypeSelector").classList.remove("active");
  document.getElementById("registerPersonaForm").classList.toggle("active", tipo === "persona");
  document.getElementById("registerEmpresaForm").classList.toggle("active", tipo === "empresa");
}

function backToTypeSelector(e) {
  e.preventDefault();
  document.getElementById("registerTypeSelector").classList.add("active");
  document.getElementById("registerPersonaForm").classList.remove("active");
  document.getElementById("registerEmpresaForm").classList.remove("active");
  clearMessages();
  currentRegisterType = null;
}

function showMessage(elementId, message, type) {
  const messageEl = document.getElementById(elementId);
  if (!messageEl) return;
  messageEl.textContent = message;
  messageEl.className = `message show ${type}`;
}

function clearMessages() {
  document.querySelectorAll(".message").forEach((msg) => {
    msg.classList.remove("show");
    msg.textContent = "";
  });
}

function validarEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function onlyDigits(value) {
  return String(value || "").replace(/\D/g, "");
}

function markInvalid(input, invalid = true) {
  if (!input) return;
  input.classList.toggle("input-invalid", invalid);
}

function validateRequired(form, messageId) {
  let ok = true;
  form.querySelectorAll("[required]").forEach((input) => {
    const empty = !String(input.value || "").trim();
    markInvalid(input, empty);
    if (empty) ok = false;
  });
  if (!ok) showMessage(messageId, "Completa todos los campos obligatorios.", "error");
  return ok;
}

function bindNumeric(input) {
  if (!input) return;
  input.addEventListener("input", () => {
    const clean = onlyDigits(input.value);
    if (input.value && input.value !== clean) alert("Solo es permitido numeros.");
    input.value = clean;
  });
}

["personaTelefono", "personaDocumento", "empresaTelefono", "empresaNIT"].forEach((id) => bindNumeric(document.getElementById(id)));

async function postJSON(url, data) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || "Error en la solicitud");
  return result;
}

// Inicio de sesion normal.
document.getElementById("formLogin").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value.trim();
  const contraseña = document.getElementById("loginPassword").value;
  if (!email || !contraseña) return showMessage("loginMessage", "Por favor completa todos los campos", "error");
  if (!validarEmail(email)) return showMessage("loginMessage", "Email inválido", "error");
  try {
    const data = await postJSON("/api/login", { email, contraseña });
    showMessage("loginMessage", data.message || "Inicio de sesión exitoso", "success");
    setTimeout(() => { window.location.href = data.redirect; }, 700);
  } catch (error) {
    showMessage("loginMessage", error.message, "error");
  }
});

// Registro de cuenta personal.
document.getElementById("formRegisterPersona").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  if (!validateRequired(form, "registerPersonaMessage")) return;
  const nombre = document.getElementById("personaNombre").value.trim();
  const apellido = document.getElementById("personaApellido").value.trim();
  const documento = document.getElementById("personaDocumento").value.trim();
  const telefono = document.getElementById("personaTelefono").value.trim();
  const email = document.getElementById("personaEmail").value.trim();
  const contraseña = document.getElementById("personaPassword").value;
  const confirmar = document.getElementById("personaPasswordConfirm").value;
  if (!validarEmail(email)) return showMessage("registerPersonaMessage", "Email inválido", "error");
  if (contraseña.length < 6) return showMessage("registerPersonaMessage", "La contraseña debe tener al menos 6 caracteres", "error");
  if (contraseña !== confirmar) return showMessage("registerPersonaMessage", "Las contraseñas no coinciden", "error");
  try {
    const data = await postJSON("/api/registro", { nombre, apellido, documento_identidad: documento, telefono, email, contraseña, tipo_cuenta: "persona" });
    showMessage("registerPersonaMessage", data.message || "Registro exitoso", "success");
    setTimeout(() => { window.location.href = data.redirect; }, 700);
  } catch (error) {
    showMessage("registerPersonaMessage", error.message, "error");
  }
});

// Registro de cuenta empresarial.
document.getElementById("formRegisterEmpresa").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  if (!validateRequired(form, "registerEmpresaMessage")) return;
  const razonSocial = document.getElementById("empresaRazonSocial").value.trim();
  const nit = document.getElementById("empresaNIT").value.trim();
  const telefono = document.getElementById("empresaTelefono").value.trim();
  const ciudad = document.getElementById("empresaCiudad").value.trim();
  const nombreContacto = document.getElementById("empresaContacto").value.trim();
  const email = document.getElementById("empresaEmail").value.trim();
  const contraseña = document.getElementById("empresaPassword").value;
  const confirmar = document.getElementById("empresaPasswordConfirm").value;
  if (!validarEmail(email)) return showMessage("registerEmpresaMessage", "Email inválido", "error");
  if (contraseña.length < 6) return showMessage("registerEmpresaMessage", "La contraseña debe tener al menos 6 caracteres", "error");
  if (contraseña !== confirmar) return showMessage("registerEmpresaMessage", "Las contraseñas no coinciden", "error");
  try {
    const data = await postJSON("/api/registro", { nombre: nombreContacto, razon_social: razonSocial, nit, telefono, ciudad, email, contraseña, tipo_cuenta: "empresa" });
    showMessage("registerEmpresaMessage", data.message || "Registro exitoso", "success");
    setTimeout(() => { window.location.href = data.redirect; }, 700);
  } catch (error) {
    showMessage("registerEmpresaMessage", error.message, "error");
  }
});

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("loginEmail")?.focus();
});
