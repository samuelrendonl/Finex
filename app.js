const USERS_KEY = "login_funcional_users";
const SESSION_KEY = "login_funcional_session";

const goToRegisterBtn = document.getElementById("goToRegister");
const goToLoginBtn = document.getElementById("goToLogin");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const dashboard = document.getElementById("dashboard");

const alertBox = document.getElementById("alert");
const accountTypeInput = document.getElementById("accountType");
const personalFields = document.getElementById("personalFields");
const companyFields = document.getElementById("companyFields");
const typeCards = document.querySelectorAll(".type-card");

const welcomeTitle = document.getElementById("welcomeTitle");
const welcomeDescription = document.getElementById("welcomeDescription");
const accountData = document.getElementById("accountData");
const logoutBtn = document.getElementById("logoutBtn");

function getUsers() {
  return JSON.parse(localStorage.getItem(USERS_KEY)) || [];
}

function saveUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function setSession(email) {
  localStorage.setItem(SESSION_KEY, email);
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function showAlert(message, type = "success") {
  alertBox.textContent = message;
  alertBox.className = `alert ${type}`;

  setTimeout(() => {
    alertBox.className = "alert hidden";
    alertBox.textContent = "";
  }, 4200);
}

function setRequiredFields(container, required) {
  const fields = container.querySelectorAll("input, select");

  fields.forEach((field) => {
    const isOptionalWebsite = field.id === "companyWebsite";
    field.required = required && !isOptionalWebsite;
  });
}

function switchView(view) {
  const isLogin = view === "login";
  const isRegister = view === "register";
  const isDashboard = view === "dashboard";

  loginForm.classList.toggle("hidden", !isLogin);
  registerForm.classList.toggle("hidden", !isRegister);
  dashboard.classList.toggle("hidden", !isDashboard);
}

function switchAccountType(type) {
  accountTypeInput.value = type;

  typeCards.forEach((card) => {
    card.classList.toggle("active", card.dataset.type === type);
  });

  const isPersonal = type === "personal";

  personalFields.classList.toggle("hidden", !isPersonal);
  companyFields.classList.toggle("hidden", isPersonal);

  setRequiredFields(personalFields, isPersonal);
  setRequiredFields(companyFields, !isPersonal);
}

function normalizeEmail(email) {
  return email.trim().toLowerCase();
}

function validatePassword(password, confirmPassword) {
  if (password.length < 6) {
    return "La contraseña debe tener mínimo 6 caracteres.";
  }

  if (password !== confirmPassword) {
    return "Las contraseñas no coinciden.";
  }

  return null;
}

function buildPersonalUser() {
  const password = document.getElementById("personalPassword").value;
  const confirmPassword = document.getElementById("personalConfirmPassword").value;
  const passwordError = validatePassword(password, confirmPassword);

  if (passwordError) {
    throw new Error(passwordError);
  }

  return {
    accountType: "personal",
    names: document.getElementById("personalNames").value.trim(),
    lastNames: document.getElementById("personalLastNames").value.trim(),
    documentType: document.getElementById("personalDocumentType").value,
    documentNumber: document.getElementById("personalDocumentNumber").value.trim(),
    phone: document.getElementById("personalPhone").value.trim(),
    email: normalizeEmail(document.getElementById("personalEmail").value),
    password,
    createdAt: new Date().toISOString(),
  };
}

function buildCompanyUser() {
  const password = document.getElementById("companyPassword").value;
  const confirmPassword = document.getElementById("companyConfirmPassword").value;
  const passwordError = validatePassword(password, confirmPassword);

  if (passwordError) {
    throw new Error(passwordError);
  }

  return {
    accountType: "empresa",
    companyName: document.getElementById("companyName").value.trim(),
    nit: document.getElementById("companyNit").value.trim(),
    companyType: document.getElementById("companyType").value,
    legalRepresentative: document.getElementById("legalRepresentative").value.trim(),
    legalRepresentativeDocument: document.getElementById("legalRepresentativeDocument").value.trim(),
    email: normalizeEmail(document.getElementById("companyEmail").value),
    phone: document.getElementById("companyPhone").value.trim(),
    address: document.getElementById("companyAddress").value.trim(),
    city: document.getElementById("companyCity").value.trim(),
    state: document.getElementById("companyState").value.trim(),
    economicActivity: document.getElementById("economicActivity")?.value.trim() || "",
    website: document.getElementById("companyWebsite")?.value.trim() || "",
    password,
    createdAt: new Date().toISOString(),
  };
}

function publicUserData(user) {
  const { password, ...safeData } = user;
  return safeData;
}

function renderDashboard(user) {
  const isCompany = user.accountType === "empresa";

  welcomeTitle.textContent = isCompany
    ? `Hola, ${user.companyName}`
    : `Hola, ${user.names}`;

  welcomeDescription.textContent = isCompany
    ? "Ingresaste con una cuenta empresarial."
    : "Ingresaste con una cuenta personal.";

  accountData.textContent = JSON.stringify(publicUserData(user), null, 2);
  switchView("dashboard");
}

function loadActiveSession() {
  const sessionEmail = localStorage.getItem(SESSION_KEY);

  if (!sessionEmail) {
    switchView("login");
    return;
  }

  const users = getUsers();
  const user = users.find((item) => item.email === sessionEmail);

  if (user) {
    renderDashboard(user);
  } else {
    clearSession();
    switchView("login");
  }
}

goToRegisterBtn.addEventListener("click", () => switchView("register"));
goToLoginBtn.addEventListener("click", () => switchView("login"));

typeCards.forEach((card) => {
  card.addEventListener("click", () => switchAccountType(card.dataset.type));
});

registerForm.addEventListener("submit", (event) => {
  event.preventDefault();

  try {
    if (!document.getElementById("terms").checked) {
      throw new Error("Debes aceptar los términos y condiciones.");
    }

    const accountType = accountTypeInput.value;
    const newUser = accountType === "personal" ? buildPersonalUser() : buildCompanyUser();

    if (!newUser.email) {
      throw new Error("El correo electrónico es obligatorio.");
    }

    const users = getUsers();
    const emailAlreadyExists = users.some((user) => user.email === newUser.email);

    if (emailAlreadyExists) {
      throw new Error("Ya existe una cuenta registrada con este correo.");
    }

    users.push(newUser);
    saveUsers(users);
    setSession(newUser.email);
    registerForm.reset();
    switchAccountType("personal");
    showAlert("Cuenta creada correctamente.", "success");
    renderDashboard(newUser);
  } catch (error) {
    showAlert(error.message, "error");
  }
});

loginForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const email = normalizeEmail(document.getElementById("loginEmail").value);
  const password = document.getElementById("loginPassword").value;

  const users = getUsers();
  const user = users.find((item) => item.email === email && item.password === password);

  if (!user) {
    showAlert("Correo o contraseña incorrectos.", "error");
    return;
  }

  setSession(user.email);
  loginForm.reset();
  showAlert("Inicio de sesión correcto.", "success");
  renderDashboard(user);
});

logoutBtn.addEventListener("click", () => {
  clearSession();
  switchView("login");
  showAlert("Sesión cerrada correctamente.", "success");
});

switchAccountType("personal");
loadActiveSession();
