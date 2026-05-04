// ===== VARIABLE GLOBAL =====
let currentRegisterType = null;

// ===== TOGGLE ENTRE LOGIN Y REGISTRO =====
function toggleForms(e) {
  e.preventDefault();

  const loginForm = document.getElementById("loginForm");
  const registerTypeSelector = document.getElementById("registerTypeSelector");

  console.log(
    "Toggle Forms - Login visible:",
    loginForm.classList.contains("active"),
  );

  loginForm.classList.toggle("active");
  registerTypeSelector.classList.toggle("active");

  // Limpiar formularios y mensajes
  document.getElementById("formLogin").reset();
  clearMessages();

  // Resetear tipo de registro
  currentRegisterType = null;

  console.log(
    "Toggle Forms - Registro visible:",
    registerTypeSelector.classList.contains("active"),
  );
}

// ===== SELECTOR DE TIPO DE CUENTA =====
function selectRegisterType(tipo) {
  currentRegisterType = tipo;

  const typeSelector = document.getElementById("registerTypeSelector");
  const personaForm = document.getElementById("registerPersonaForm");
  const empresaForm = document.getElementById("registerEmpresaForm");

  console.log("Seleccionar tipo:", tipo);

  typeSelector.classList.remove("active");

  if (tipo === "persona") {
    personaForm.classList.add("active");
    empresaForm.classList.remove("active");
    if (document.getElementById("formRegisterPersona")) {
      document.getElementById("formRegisterPersona").reset();
    }
    console.log("Mostrar formulario PERSONA");
  } else if (tipo === "empresa") {
    empresaForm.classList.add("active");
    personaForm.classList.remove("active");
    if (document.getElementById("formRegisterEmpresa")) {
      document.getElementById("formRegisterEmpresa").reset();
    }
    console.log("Mostrar formulario EMPRESA");
  }
}

// ===== VOLVER AL SELECTOR DE TIPO =====
function backToTypeSelector(e) {
  e.preventDefault();

  const typeSelector = document.getElementById("registerTypeSelector");
  const personaForm = document.getElementById("registerPersonaForm");
  const empresaForm = document.getElementById("registerEmpresaForm");

  typeSelector.classList.add("active");
  personaForm.classList.remove("active");
  empresaForm.classList.remove("active");

  clearMessages();
  currentRegisterType = null;
}

// ===== MOSTRAR MENSAJE =====
function showMessage(elementId, message, type) {
  const messageEl = document.getElementById(elementId);
  messageEl.textContent = message;
  messageEl.className = `message show ${type}`;

  // Auto-desaparecer si es éxito
  if (type === "success") {
    setTimeout(() => {
      messageEl.classList.remove("show");
    }, 3500);
  }
}

// ===== LIMPIAR MENSAJES =====
function clearMessages() {
  const messages = document.querySelectorAll(".message");
  messages.forEach((msg) => {
    msg.classList.remove("show");
    msg.textContent = "";
  });
}

// ===== VALIDAR EMAIL =====
function validarEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// ===== HANDLE LOGIN =====
document.getElementById("formLogin").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("loginEmail").value.trim();
  const contraseña = document.getElementById("loginPassword").value;

  if (!email || !contraseña) {
    showMessage("loginMessage", "Por favor completa todos los campos", "error");
    return;
  }

  if (!validarEmail(email)) {
    showMessage("loginMessage", "Email inválido", "error");
    return;
  }

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        contraseña: contraseña,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      showMessage(
        "loginMessage",
        data.error || "Error al iniciar sesión",
        "error",
      );
      return;
    }

    showMessage("loginMessage", data.message, "success");

    // Redirigir al dashboard
    setTimeout(() => {
      window.location.href = data.redirect;
    }, 1500);
  } catch (error) {
    showMessage("loginMessage", "Error de conexión: " + error.message, "error");
  }
});

// ===== HANDLE REGISTRO PERSONA =====
document
  .getElementById("formRegisterPersona")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const nombre = document.getElementById("personaNombre").value.trim();
    const apellido = document.getElementById("personaApellido").value.trim();
    const documento = document.getElementById("personaDocumento").value.trim();
    const email = document.getElementById("personaEmail").value.trim();
    const contraseña = document.getElementById("personaPassword").value;
    const confirmar = document.getElementById("personaPasswordConfirm").value;

    // Validaciones
    if (!nombre || !apellido || !email || !contraseña || !confirmar) {
      showMessage(
        "registerPersonaMessage",
        "Por favor completa todos los campos requeridos",
        "error",
      );
      return;
    }

    if (contraseña.length < 6) {
      showMessage(
        "registerPersonaMessage",
        "La contraseña debe tener al menos 6 caracteres",
        "error",
      );
      return;
    }

    if (contraseña !== confirmar) {
      showMessage(
        "registerPersonaMessage",
        "Las contraseñas no coinciden",
        "error",
      );
      return;
    }

    if (!validarEmail(email)) {
      showMessage("registerPersonaMessage", "Email inválido", "error");
      return;
    }

    try {
      const response = await fetch("/api/registro", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nombre: nombre,
          apellido: apellido,
          documento_identidad: documento,
          email: email,
          contraseña: contraseña,
          tipo_cuenta: "persona",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        showMessage(
          "registerPersonaMessage",
          data.error || "Error al registrarse",
          "error",
        );
        return;
      }

      showMessage("registerPersonaMessage", data.message, "success");

      // Redirigir al dashboard
      setTimeout(() => {
        window.location.href = data.redirect;
      }, 1500);
    } catch (error) {
      showMessage(
        "registerPersonaMessage",
        "Error de conexión: " + error.message,
        "error",
      );
    }
  });

// ===== HANDLE REGISTRO EMPRESA =====
document
  .getElementById("formRegisterEmpresa")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const razonSocial = document
      .getElementById("empresaRazonSocial")
      .value.trim();
    const nit = document.getElementById("empresaNIT").value.trim();
    const telefono = document.getElementById("empresaTelefono").value.trim();
    const ciudad = document.getElementById("empresaCiudad").value.trim();
    const nombreContacto = document
      .getElementById("empresaContacto")
      .value.trim();
    const email = document.getElementById("empresaEmail").value.trim();
    const contraseña = document.getElementById("empresaPassword").value;
    const confirmar = document.getElementById("empresaPasswordConfirm").value;

    // Validaciones
    if (!razonSocial || !nit || !email || !contraseña || !confirmar) {
      showMessage(
        "registerEmpresaMessage",
        "Por favor completa todos los campos requeridos",
        "error",
      );
      return;
    }

    if (contraseña.length < 6) {
      showMessage(
        "registerEmpresaMessage",
        "La contraseña debe tener al menos 6 caracteres",
        "error",
      );
      return;
    }

    if (contraseña !== confirmar) {
      showMessage(
        "registerEmpresaMessage",
        "Las contraseñas no coinciden",
        "error",
      );
      return;
    }

    if (!validarEmail(email)) {
      showMessage("registerEmpresaMessage", "Email inválido", "error");
      return;
    }

    // Validar NIT (mínimo 8 caracteres)
    if (nit.length < 8) {
      showMessage(
        "registerEmpresaMessage",
        "NIT debe tener al menos 8 caracteres",
        "error",
      );
      return;
    }

    try {
      const response = await fetch("/api/registro", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nombre: nombreContacto,
          razon_social: razonSocial,
          nit: nit,
          telefono: telefono,
          ciudad: ciudad,
          email: email,
          contraseña: contraseña,
          tipo_cuenta: "empresa",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        showMessage(
          "registerEmpresaMessage",
          data.error || "Error al registrarse",
          "error",
        );
        return;
      }

      showMessage("registerEmpresaMessage", data.message, "success");

      // Redirigir al dashboard
      setTimeout(() => {
        window.location.href = data.redirect;
      }, 1500);
    } catch (error) {
      showMessage(
        "registerEmpresaMessage",
        "Error de conexión: " + error.message,
        "error",
      );
    }
  });

// ===== INICIALIZACIÓN =====
document.addEventListener("DOMContentLoaded", () => {
  // Enfoque automático en el primer campo
  const loginEmail = document.getElementById("loginEmail");
  if (loginEmail) {
    loginEmail.focus();
  }

  // Guardar texto original de botones
  document.querySelectorAll('button[type="submit"]').forEach((btn) => {
    btn.setAttribute("data-original-text", btn.textContent);
  });
});

// ===== PREVENIR DOBLE ENVÍO =====
document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Procesando...";

        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.textContent =
            submitBtn.getAttribute("data-original-text") || "Enviar";
        }, 2000);
      }
    });
  });
});
