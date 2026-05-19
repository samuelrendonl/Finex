// Autenticacion FINEX: login, registro y validaciones visuales.
let currentRegisterType = null;

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const registerTypeSelector = document.getElementById("registerTypeSelector");
  const registerPersonaForm = document.getElementById("registerPersonaForm");
  const registerEmpresaForm = document.getElementById("registerEmpresaForm");
  const recoverPasswordForm = document.getElementById("recoverPasswordForm");

  const formLogin = document.getElementById("formLogin");
  const formRegisterPersona = document.getElementById("formRegisterPersona");
  const formRegisterEmpresa = document.getElementById("formRegisterEmpresa");
  const formRecoverPassword = document.getElementById("formRecoverPassword");
  const recoverSendCodeBtn = document.getElementById("recoverSendCodeBtn");
  const recoverCodeFields = document.getElementById("recoverCodeFields");
  const personaSendRegisterCodeBtn = document.getElementById(
    "personaSendRegisterCodeBtn",
  );
  const empresaSendRegisterCodeBtn = document.getElementById(
    "empresaSendRegisterCodeBtn",
  );

  const loginEmail = document.getElementById("loginEmail");

  function setActiveForm(formToShow) {
    [
      loginForm,
      registerTypeSelector,
      registerPersonaForm,
      registerEmpresaForm,
      recoverPasswordForm,
    ].forEach((form) => {
      if (form) form.classList.remove("active");
    });

    if (formToShow) {
      formToShow.classList.add("active");
    }

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  window.toggleForms = function toggleForms(e) {
    if (e) e.preventDefault();

    const goingToRegister = loginForm?.classList.contains("active");

    clearMessages();
    clearInvalidInputs();

    if (formLogin) formLogin.reset();
    if (formRegisterPersona) formRegisterPersona.reset();
    if (formRegisterEmpresa) formRegisterEmpresa.reset();
    if (formRecoverPassword) formRecoverPassword.reset();
    resetPasswordRecoveryStep();

    currentRegisterType = null;

    if (goingToRegister) {
      setActiveForm(registerTypeSelector);
    } else {
      setActiveForm(loginForm);
      setTimeout(() => loginEmail?.focus(), 100);
    }
  };

  window.selectRegisterType = function selectRegisterType(tipo) {
    currentRegisterType = tipo;

    clearMessages();
    clearInvalidInputs();

    if (tipo === "persona") {
      setActiveForm(registerPersonaForm);
      setTimeout(() => document.getElementById("personaNombre")?.focus(), 100);
    }

    if (tipo === "empresa") {
      setActiveForm(registerEmpresaForm);
      setTimeout(
        () => document.getElementById("empresaRazonSocial")?.focus(),
        100,
      );
    }
  };

  window.backToTypeSelector = function backToTypeSelector(e) {
    if (e) e.preventDefault();

    clearMessages();
    clearInvalidInputs();

    currentRegisterType = null;
    setActiveForm(registerTypeSelector);
  };

  window.showPasswordRecovery = function showPasswordRecovery(e) {
    if (e) e.preventDefault();

    clearMessages();
    clearInvalidInputs();

    if (formRecoverPassword) formRecoverPassword.reset();
    resetPasswordRecoveryStep();
    setActiveForm(recoverPasswordForm);
    setTimeout(() => document.getElementById("recoverEmail")?.focus(), 100);
  };

  window.backToLogin = function backToLogin(e) {
    if (e) e.preventDefault();

    clearMessages();
    clearInvalidInputs();

    resetPasswordRecoveryStep();
    setActiveForm(loginForm);
    setTimeout(() => loginEmail?.focus(), 100);
  };

  function showMessage(elementId, message, type) {
    const messageEl = document.getElementById(elementId);
    if (!messageEl) return;

    messageEl.textContent = message;
    messageEl.className = `message show ${type}`;
  }

  function clearMessages() {
    document.querySelectorAll(".message").forEach((msg) => {
      msg.classList.remove("show", "error", "success", "info");
      msg.textContent = "";
    });

    document.querySelectorAll(".field-error-message").forEach((msg) => {
      msg.remove();
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

  function clearFieldError(input) {
    function clearFieldError(input) {
      if (!input) return;
    }
  }

  function showFieldError(input, message) {
    function showFieldError(input, message) {
      if (!input) return;
      markInvalid(input, true);
    }
  }

  function clearInvalidInputs() {
    document.querySelectorAll(".input-invalid").forEach((input) => {
      input.classList.remove("input-invalid");
    });

    document.querySelectorAll(".field-error-message").forEach((msg) => {
      msg.remove();
    });
  }

  function validateRequired(form, messageId) {
    let ok = true;
    let firstInvalid = null;

    form.querySelectorAll("[required]").forEach((input) => {
      const empty = !String(input.value || "").trim();

      markInvalid(input, empty);
      clearFieldError(input);

      if (empty) {
        ok = false;
        if (!firstInvalid) firstInvalid = input;
        showFieldError(input, "Este campo es obligatorio.");
      }
    });

    if (!ok) {
      firstInvalid?.focus();
    }

    return ok;
  }

  function resetPasswordRecoveryStep() {
    if (recoverCodeFields) recoverCodeFields.hidden = true;
    if (recoverSendCodeBtn) {
      recoverSendCodeBtn.hidden = false;
      recoverSendCodeBtn.disabled = false;
      recoverSendCodeBtn.textContent =
        recoverSendCodeBtn.dataset.originalText || "Enviar código";
    }

    ["recoverCode", "recoverPassword", "recoverPasswordConfirm"].forEach(
      (id) => {
        const input = document.getElementById(id);
        if (input) {
          input.required = false;
          input.value = "";
        }
      },
    );
  }

  function enablePasswordRecoveryStep() {
    if (recoverCodeFields) recoverCodeFields.hidden = false;
    if (recoverSendCodeBtn) recoverSendCodeBtn.hidden = true;

    ["recoverCode", "recoverPassword", "recoverPasswordConfirm"].forEach(
      (id) => {
        const input = document.getElementById(id);
        if (input) input.required = true;
      },
    );

    setTimeout(() => document.getElementById("recoverCode")?.focus(), 100);
  }

  function showNumericMessage(input, message) {
    const form = input?.closest("form");
    const messageEl =
      form?.parentElement?.querySelector(".message") ||
      form?.querySelector(".message");

    if (messageEl?.id) {
      showMessage(messageEl.id, message, "error");
    }
  }

  function bindNumeric(input) {
    if (!input) return;

    input.addEventListener("input", () => {
      const clean = onlyDigits(input.value);

      if (input.value && input.value !== clean) {
        showNumericMessage(input, "Solo se permiten números.");
      }

      input.value = clean;
    });
  }

  function bindClearInvalid(input) {
    if (!input) return;

    input.addEventListener("input", () => {
      if (String(input.value || "").trim()) {
        markInvalid(input, false);
        clearFieldError(input);
      }
    });
  }

  async function postJSON(url, data) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(result.error || "Error en la solicitud");
    }

    return result;
  }

  function setButtonLoading(button, loading, textLoading = "Procesando...") {
    if (!button) return;

    if (loading) {
      button.dataset.originalText = button.textContent;
      button.textContent = textLoading;
      button.disabled = true;
    } else {
      button.textContent = button.dataset.originalText || button.textContent;
      button.disabled = false;
    }
  }

  function sendRegisteredUserToLogin(form, email) {
    if (form) form.reset();

    clearMessages();
    clearInvalidInputs();
    setActiveForm(loginForm);

    const passwordInput = document.getElementById("loginPassword");
    if (loginEmail) loginEmail.value = email || "";
    if (passwordInput) passwordInput.value = "";

    showMessage(
      "loginMessage",
      "Cuenta creada correctamente. Inicia sesión con tus credenciales.",
      "success",
    );
    setTimeout(() => loginEmail?.focus(), 100);
  }

  [
    "personaTelefono",
    "personaDocumento",
    "empresaTelefono",
    "empresaNIT",
    "recoverCode",
    "personaCodigoVerificacion",
    "empresaCodigoVerificacion",
  ].forEach((id) => {
    bindNumeric(document.getElementById(id));
  });

  document.querySelectorAll("input").forEach(bindClearInvalid);

  async function sendRegistrationCode(emailInput, messageId, button) {
    clearMessages();
    clearInvalidInputs();

    const email = emailInput?.value.trim();

    if (!email) {
      markInvalid(emailInput, true);
      showFieldError(emailInput, "Este campo es obligatorio.");
      return showMessage(
        messageId,
        "Ingresa el correo electronico para enviar el codigo.",
        "error",
      );
    }

    if (!validarEmail(email)) {
      markInvalid(emailInput, true);
      return showMessage(messageId, "Email invalido.", "error");
    }

    try {
      setButtonLoading(button, true, "Enviando codigo...");
      const data = await postJSON("/api/solicitar-codigo-registro", { email });
      showMessage(
        messageId,
        data.message || "Codigo enviado. Revisa tu correo.",
        "success",
      );
    } catch (error) {
      showMessage(messageId, error.message, "error");
    } finally {
      setButtonLoading(button, false);
    }
  }

  personaSendRegisterCodeBtn?.addEventListener("click", () => {
    sendRegistrationCode(
      document.getElementById("personaEmail"),
      "registerPersonaMessage",
      personaSendRegisterCodeBtn,
    );
  });

  empresaSendRegisterCodeBtn?.addEventListener("click", () => {
    sendRegistrationCode(
      document.getElementById("empresaEmail"),
      "registerEmpresaMessage",
      empresaSendRegisterCodeBtn,
    );
  });

  if (formLogin) {
    formLogin.addEventListener("submit", async (e) => {
      e.preventDefault();

      clearMessages();
      clearInvalidInputs();

      const button = formLogin.querySelector('button[type="submit"]');
      const emailInput = document.getElementById("loginEmail");
      const passwordInput = document.getElementById("loginPassword");

      const email = emailInput.value.trim();
      const contraseña = passwordInput.value;

      if (!email || !contraseña) {
        if (!email) {
          markInvalid(emailInput, true);
          showFieldError(emailInput, "Este campo es obligatorio.");
        }

        if (!contraseña) {
          markInvalid(passwordInput, true);
          showFieldError(passwordInput, "Este campo es obligatorio.");
        }

        return showMessage(
          "loginMessage",
          "Por favor completa todos los campos.",
          "error",
        );
      }

      if (!validarEmail(email)) {
        markInvalid(emailInput, true);
        return showMessage("loginMessage", "Email inválido.", "error");
      }

      try {
        setButtonLoading(button, true, "Entrando...");

        const data = await postJSON("/api/login", {
          email,
          contraseña,
        });

        showMessage(
          "loginMessage",
          data.message || "Inicio de sesión exitoso.",
          "success",
        );

        setTimeout(() => {
          window.location.href = data.redirect || "/";
        }, 700);
      } catch (error) {
        showMessage("loginMessage", error.message, "error");
      } finally {
        setButtonLoading(button, false);
      }
    });
  }

  if (recoverSendCodeBtn) {
    recoverSendCodeBtn.addEventListener("click", async () => {
      clearMessages();
      clearInvalidInputs();

      const emailInput = document.getElementById("recoverEmail");
      const email = emailInput.value.trim();

      if (!email) {
        markInvalid(emailInput, true);
        showFieldError(emailInput, "Este campo es obligatorio.");
        return showMessage(
          "recoverPasswordMessage",
          "Ingresa tu correo electrónico.",
          "error",
        );
      }

      if (!validarEmail(email)) {
        markInvalid(emailInput, true);
        return showMessage(
          "recoverPasswordMessage",
          "Email inválido.",
          "error",
        );
      }

      try {
        setButtonLoading(recoverSendCodeBtn, true, "Enviando código...");

        const data = await postJSON("/api/solicitar-codigo-recuperacion", {
          email,
        });

        showMessage(
          "recoverPasswordMessage",
          data.message || "Código enviado. Revisa tu correo.",
          "success",
        );
        enablePasswordRecoveryStep();
      } catch (error) {
        showMessage("recoverPasswordMessage", error.message, "error");
      } finally {
        setButtonLoading(recoverSendCodeBtn, false);
      }
    });
  }

  if (formRecoverPassword) {
    formRecoverPassword.addEventListener("submit", async (e) => {
      e.preventDefault();

      clearMessages();
      clearInvalidInputs();

      const form = e.currentTarget;
      const button = form.querySelector('button[type="submit"]');

      if (!validateRequired(form, "recoverPasswordMessage")) return;

      const emailInput = document.getElementById("recoverEmail");
      const codeInput = document.getElementById("recoverCode");
      const passwordInput = document.getElementById("recoverPassword");
      const confirmInput = document.getElementById("recoverPasswordConfirm");

      const email = emailInput.value.trim();
      const codigo = codeInput.value.trim();
      const contraseña = passwordInput.value;
      const confirmar = confirmInput.value;

      if (!validarEmail(email)) {
        markInvalid(emailInput, true);
        return showMessage(
          "recoverPasswordMessage",
          "Email inválido.",
          "error",
        );
      }

      if (!/^\d{6}$/.test(codigo)) {
        markInvalid(codeInput, true);
        return showMessage(
          "recoverPasswordMessage",
          "Ingresa el código de 6 dígitos enviado a tu correo.",
          "error",
        );
      }

      if (contraseña.length < 6) {
        markInvalid(passwordInput, true);
        return showMessage(
          "recoverPasswordMessage",
          "La contraseña debe tener al menos 6 caracteres.",
          "error",
        );
      }

      if (contraseña !== confirmar) {
        markInvalid(passwordInput, true);
        markInvalid(confirmInput, true);
        return showMessage(
          "recoverPasswordMessage",
          "Las contraseñas no coinciden.",
          "error",
        );
      }

      try {
        setButtonLoading(button, true, "Actualizando...");

        await postJSON("/api/recuperar-contrasena", {
          email,
          codigo,
          nueva_contraseña: contraseña,
        });

        form.reset();
        resetPasswordRecoveryStep();
        clearMessages();
        setActiveForm(loginForm);

        const passwordLoginInput = document.getElementById("loginPassword");
        if (loginEmail) loginEmail.value = email;
        if (passwordLoginInput) passwordLoginInput.value = "";

        showMessage(
          "loginMessage",
          "Contraseña actualizada. Inicia sesión con tu nueva contraseña.",
          "success",
        );
      } catch (error) {
        showMessage("recoverPasswordMessage", error.message, "error");
      } finally {
        setButtonLoading(button, false);
      }
    });
  }

  if (formRegisterPersona) {
    formRegisterPersona.addEventListener("submit", async (e) => {
      e.preventDefault();

      clearMessages();
      clearInvalidInputs();

      const form = e.currentTarget;
      const button = form.querySelector('button[type="submit"]');

      if (!validateRequired(form, "registerPersonaMessage")) return;

      const nombre = document.getElementById("personaNombre").value.trim();
      const apellido = document.getElementById("personaApellido").value.trim();
      const documento = document
        .getElementById("personaDocumento")
        .value.trim();
      const telefono = document.getElementById("personaTelefono").value.trim();
      const emailInput = document.getElementById("personaEmail");
      const codeInput = document.getElementById("personaCodigoVerificacion");
      const passwordInput = document.getElementById("personaPassword");
      const confirmInput = document.getElementById("personaPasswordConfirm");

      const email = emailInput.value.trim();
      const codigoVerificacion = codeInput.value.trim();
      const contraseña = passwordInput.value;
      const confirmar = confirmInput.value;

      if (!validarEmail(email)) {
        markInvalid(emailInput, true);
        return showMessage(
          "registerPersonaMessage",
          "Email inválido.",
          "error",
        );
      }

      if (!/^\d{6}$/.test(codigoVerificacion)) {
        markInvalid(codeInput, true);
        return showMessage(
          "registerPersonaMessage",
          "Ingresa el codigo de 6 digitos enviado a tu correo.",
          "error",
        );
      }

      if (contraseña.length < 6) {
        markInvalid(passwordInput, true);
        return showMessage(
          "registerPersonaMessage",
          "La contraseña debe tener al menos 6 caracteres.",
          "error",
        );
      }

      if (contraseña !== confirmar) {
        markInvalid(passwordInput, true);
        markInvalid(confirmInput, true);
        return showMessage(
          "registerPersonaMessage",
          "Las contraseñas no coinciden.",
          "error",
        );
      }

      try {
        setButtonLoading(button, true, "Creando cuenta...");

        const data = await postJSON("/api/registro", {
          nombre,
          apellido,
          documento_identidad: documento,
          telefono,
          email,
          codigo_verificacion: codigoVerificacion,
          contraseña,
          tipo_cuenta: "persona",
        });

        showMessage(
          "registerPersonaMessage",
          data.message || "Registro exitoso.",
          "success",
        );

        setTimeout(() => {
          sendRegisteredUserToLogin(form, email);
        }, 700);
      } catch (error) {
        showMessage("registerPersonaMessage", error.message, "error");
      } finally {
        setButtonLoading(button, false);
      }
    });
  }

  if (formRegisterEmpresa) {
    formRegisterEmpresa.addEventListener("submit", async (e) => {
      e.preventDefault();

      clearMessages();
      clearInvalidInputs();

      const form = e.currentTarget;
      const button = form.querySelector('button[type="submit"]');

      if (!validateRequired(form, "registerEmpresaMessage")) return;

      const razonSocial = document
        .getElementById("empresaRazonSocial")
        .value.trim();
      const nit = document.getElementById("empresaNIT").value.trim();
      const telefono = document.getElementById("empresaTelefono").value.trim();
      const ciudad = document.getElementById("empresaCiudad").value.trim();
      const nombreContacto = document
        .getElementById("empresaContacto")
        .value.trim();
      const emailInput = document.getElementById("empresaEmail");
      const codeInput = document.getElementById("empresaCodigoVerificacion");
      const passwordInput = document.getElementById("empresaPassword");
      const confirmInput = document.getElementById("empresaPasswordConfirm");

      const email = emailInput.value.trim();
      const codigoVerificacion = codeInput.value.trim();
      const contraseña = passwordInput.value;
      const confirmar = confirmInput.value;

      if (!validarEmail(email)) {
        markInvalid(emailInput, true);
        return showMessage(
          "registerEmpresaMessage",
          "Email inválido.",
          "error",
        );
      }

      if (!/^\d{6}$/.test(codigoVerificacion)) {
        markInvalid(codeInput, true);
        return showMessage(
          "registerEmpresaMessage",
          "Ingresa el codigo de 6 digitos enviado a tu correo.",
          "error",
        );
      }

      if (contraseña.length < 6) {
        markInvalid(passwordInput, true);
        return showMessage(
          "registerEmpresaMessage",
          "La contraseña debe tener al menos 6 caracteres.",
          "error",
        );
      }

      if (contraseña !== confirmar) {
        markInvalid(passwordInput, true);
        markInvalid(confirmInput, true);
        return showMessage(
          "registerEmpresaMessage",
          "Las contraseñas no coinciden.",
          "error",
        );
      }

      try {
        setButtonLoading(button, true, "Creando empresa...");

        const data = await postJSON("/api/registro", {
          nombre: nombreContacto,
          razon_social: razonSocial,
          nit,
          telefono,
          ciudad,
          email,
          codigo_verificacion: codigoVerificacion,
          contraseña,
          tipo_cuenta: "empresa",
        });

        showMessage(
          "registerEmpresaMessage",
          data.message || "Registro exitoso.",
          "success",
        );

        setTimeout(() => {
          sendRegisteredUserToLogin(form, email);
        }, 700);
      } catch (error) {
        showMessage("registerEmpresaMessage", error.message, "error");
      } finally {
        setButtonLoading(button, false);
      }
    });
  }

  loginEmail?.focus();
});
