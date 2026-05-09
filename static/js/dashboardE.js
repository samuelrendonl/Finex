// ===============================
// DASHBOARD EMPRESA - dashboard_empresa.js
// ===============================

document.addEventListener("DOMContentLoaded", () => {
  loadCompanyInfo();
  setupMenuNavigation();
  setupUserMenu();
  setupProfileForm();
  setupPasswordForm();
  setupLogout();
  setupModal();
  setupSessionTimeout();
  loadDashboardStats();
});

// ===============================
// CARGAR INFORMACIÓN EMPRESA
// ===============================

async function loadCompanyInfo() {
  try {
    const response = await fetch("/api/usuario-info");

    if (!response.ok) {
      if (response.status === 401) {
        window.location.href = "/";
        return;
      }

      throw new Error("No se pudo cargar la información");
    }

    const data = await response.json();

    // Header
    const userName = document.getElementById("userName");
    if (userName) {
      userName.textContent = data.nombre || "Empresa";
    }

    // Empresa
    const companyName = document.getElementById("companyName");
    if (companyName) {
      companyName.textContent = data.empresa || "Mi Empresa";
    }

    // Perfil
    const profileName = document.getElementById("profileName");
    if (profileName) {
      profileName.value = data.nombre || "";
    }

    const profileCompany = document.getElementById("profileCompany");
    if (profileCompany) {
      profileCompany.value = data.empresa || "";
    }

    const profileEmail = document.getElementById("profileEmail");
    if (profileEmail) {
      profileEmail.value = data.email || "";
    }
  } catch (error) {
    console.error(error);
    showModal("Error al cargar la información de la empresa", "error");
  }
}

// ===============================
// ESTADÍSTICAS DASHBOARD
// ===============================

async function loadDashboardStats() {
  try {
    const response = await fetch("/api/dashboard-empresa");

    if (!response.ok) {
      return;
    }

    const data = await response.json();

    setText("ventasTotal", formatCurrency(data.ventas || 0));
    setText("gastosTotal", formatCurrency(data.gastos || 0));
    setText("clientesTotal", data.clientes || 0);
    setText("productosTotal", data.productos || 0);
    setText("facturasPendientes", data.facturas_pendientes || 0);
    setText("balanceTotal", formatCurrency(data.balance || 0));
  } catch (error) {
    console.error("Error cargando estadísticas:", error);
  }
}

function setText(id, value) {
  const el = document.getElementById(id);

  if (el) {
    el.textContent = value;
  }
}

function formatCurrency(value) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
  }).format(value);
}

// ===============================
// NAVEGACIÓN SIDEBAR
// ===============================

function setupMenuNavigation() {
  const menuItems = document.querySelectorAll(".menu-item");

  menuItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();

      menuItems.forEach((i) => {
        i.classList.remove("active");
      });

      item.classList.add("active");

      const section = item.dataset.section;

      openSection(section);

      closeDropdown();
    });
  });
}

function openSection(sectionId) {
  const sections = document.querySelectorAll(".content-section");

  sections.forEach((section) => {
    section.classList.remove("active");
  });

  const selectedSection = document.getElementById(sectionId);

  if (selectedSection) {
    selectedSection.classList.add("active");

    const title = selectedSection.querySelector(".section-title h2");

    if (title) {
      const headerTitle = document.querySelector(".header-title");

      if (headerTitle) {
        headerTitle.textContent = title.textContent;
      }
    }
  }
}

// ===============================
// USER MENU
// ===============================

function setupUserMenu() {
  const btn = document.getElementById("userMenuBtn");
  const dropdown = document.getElementById("userDropdown");

  if (!btn || !dropdown) return;

  btn.addEventListener("click", (e) => {
    e.preventDefault();

    dropdown.classList.toggle("show");
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".user-menu")) {
      dropdown.classList.remove("show");
    }
  });
}

function closeDropdown() {
  const dropdown = document.getElementById("userDropdown");

  if (dropdown) {
    dropdown.classList.remove("show");
  }
}

// ===============================
// PERFIL EMPRESA
// ===============================

function setupProfileForm() {
  const form = document.getElementById("formProfile");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nombre = document.getElementById("profileName").value.trim();
    const empresa = document.getElementById("profileCompany").value.trim();

    if (!nombre || !empresa) {
      showModal("Completa todos los campos", "error");
      return;
    }

    try {
      const response = await fetch("/api/actualizar-perfil", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nombre,
          empresa,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        showModal(data.error || "Error actualizando perfil", "error");
        return;
      }

      showModal(data.message || "Perfil actualizado", "success");

      setText("userName", nombre);
      setText("companyName", empresa);
    } catch (error) {
      console.error(error);
      showModal("Error de conexión", "error");
    }
  });
}

// ===============================
// CONTRASEÑA
// ===============================

function setupPasswordForm() {
  const form = document.getElementById("formPassword");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const actual = document.getElementById("currentPassword").value;
    const nueva = document.getElementById("newPassword").value;
    const confirmar = document.getElementById("confirmPassword").value;

    if (!actual || !nueva || !confirmar) {
      showModal("Completa todos los campos", "error");
      return;
    }

    if (nueva.length < 6) {
      showModal("La contraseña debe tener mínimo 6 caracteres", "error");
      return;
    }

    if (nueva !== confirmar) {
      showModal("Las contraseñas no coinciden", "error");
      return;
    }

    try {
      const response = await fetch("/api/cambiar-contraseña", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contraseña_actual: actual,
          contraseña_nueva: nueva,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        showModal(data.error || "Error cambiando contraseña", "error");
        return;
      }

      showModal(data.message || "Contraseña actualizada", "success");

      form.reset();
    } catch (error) {
      console.error(error);
      showModal("Error de conexión", "error");
    }
  });
}

// ===============================
// LOGOUT
// ===============================

function setupLogout() {
  const logoutBtn = document.getElementById("btnLogout");

  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
  }
}

async function logout(e) {
  if (e) {
    e.preventDefault();
  }

  try {
    const response = await fetch("/api/logout", {
      method: "POST",
    });

    const data = await response.json();

    window.location.href = data.redirect || "/";
  } catch (error) {
    console.error(error);
    window.location.href = "/";
  }
}

// ===============================
// MODAL
// ===============================

function setupModal() {
  const closeBtn = document.querySelector(".close");

  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
  }

  const modal = document.getElementById("messageModal");

  if (modal) {
    window.addEventListener("click", (e) => {
      if (e.target === modal) {
        closeModal();
      }
    });
  }
}

function showModal(message, type = "info") {
  const modal = document.getElementById("messageModal");
  const modalMessage = document.getElementById("modalMessage");

  if (!modal || !modalMessage) return;

  modalMessage.innerHTML = message;

  modalMessage.style.color = "#1f2937";

  if (type === "success") {
    modalMessage.style.color = "#10b981";
  }

  if (type === "error") {
    modalMessage.style.color = "#ef4444";
  }

  modal.classList.add("show");
}

function closeModal() {
  const modal = document.getElementById("messageModal");

  if (modal) {
    modal.classList.remove("show");
  }
}

// ===============================
// SESSION TIMEOUT
// ===============================

let sessionTimeout;

function resetSessionTimeout() {
  clearTimeout(sessionTimeout);

  sessionTimeout = setTimeout(
    () => {
      logout();
    },
    30 * 60 * 1000,
  );
}

function setupSessionTimeout() {
  document.addEventListener("mousemove", resetSessionTimeout);
  document.addEventListener("keypress", resetSessionTimeout);
  document.addEventListener("click", resetSessionTimeout);

  resetSessionTimeout();

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      resetSessionTimeout();
    }
  });
}

// ===============================
// FUNCIONES EXTRA EMPRESA
// ===============================

function createInvoice() {
  showModal("Módulo de facturación próximamente", "info");
}

function createProduct() {
  showModal("Módulo de inventario próximamente", "info");
}

function createClient() {
  showModal("Módulo de clientes próximamente", "info");
}

function generateReport() {
  showModal("Generando reporte empresarial...", "success");
}
