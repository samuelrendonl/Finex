// Panel personal FINEX: navegación estable, movimientos, cuentas y exportaciones.
(function () {
  if (!document.body.matches("[data-personal-app]")) return;

  const money = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
  const currency = (value) => "$ " + money.format(Number(value || 0));
  const digits = (value) => String(value || "").replace(/\D/g, "");
  const numberValue = (value) => Number(digits(value) || 0);

  function showNotice(message, type = "success") {
    let wrap = document.getElementById("personalFlashWrap");
    if (!wrap) {
      const main = document.querySelector(".main") || document.body;
      wrap = document.createElement("div");
      wrap.id = "personalFlashWrap";
      wrap.className = "flash-wrap";
      main.prepend(wrap);
    }
    const msg = document.createElement("div");
    msg.className = `flash ${type === "error" ? "error" : "success"}`;
    msg.textContent = message;
    wrap.innerHTML = "";
    wrap.appendChild(msg);
    window.scrollTo({ top: 0, behavior: "smooth" });
    setTimeout(() => {
      msg.remove();
    }, 4500);
  }

  function escapeHtml(text) {
    return String(text || "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  }

  function localNow() {
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  }

  function formatInput(input) {
    const before = input.value;
    const clean = digits(before);
    if (before && before !== clean && before.replace(/\./g, "") !== clean)
      showNotice("Solo es permitido un dato numerico.", "error");
    input.value = clean ? money.format(Number(clean)) : "";
  }

  function bindFormat(input) {
    if (!input || input.dataset.bound === "1") return;
    input.dataset.bound = "1";
    input.addEventListener("input", () => formatInput(input));
    input.addEventListener("paste", () =>
      setTimeout(() => formatInput(input), 0),
    );
  }

  document.querySelectorAll("[data-format-int]").forEach(bindFormat);
  document.querySelectorAll('input[type="datetime-local"]').forEach((i) => {
    if (!i.value) i.value = localNow();
  });

  function showSection(id, updateUrl = true) {
    const fallback = document.getElementById("inicio");
    const section = document.getElementById(id) || fallback;
    if (!section) return;
    document
      .querySelectorAll(".personal-section")
      .forEach((s) => s.classList.remove("active-section"));
    section.classList.add("active-section");
    document
      .querySelectorAll("[data-personal-section]")
      .forEach((a) =>
        a.classList.toggle("active", a.dataset.personalSection === section.id),
      );
    if (updateUrl && history.replaceState) {
      const url = new URL(window.location.href);
      url.searchParams.set("section", section.id);
      url.hash = "";
      history.replaceState(null, "", url.pathname + url.search);
    }
  }

  function initialSection() {
    const params = new URLSearchParams(window.location.search);
    return (
      params.get("section") ||
      (window.location.hash ? window.location.hash.slice(1) : "") ||
      document.body.dataset.activeSection ||
      "inicio"
    );
  }

  document.querySelectorAll("[data-personal-section]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      showSection(a.dataset.personalSection);
      closeMenu();
    });
  });
  showSection(initialSection(), false);

  document.addEventListener("click", (e) => {
    if (e.target.matches("[data-close-dialog]"))
      e.target.closest("dialog")?.close();
    if (e.target.closest("[data-open-logout]"))
      document.getElementById("logoutDialog")?.showModal();
  });

  async function api(url, options = {}) {
    const res = await fetch(url, options);
    const data = await res.json().catch(() => ({}));
    if (!res.ok)
      throw new Error(data.error || "No se pudo procesar la solicitud.");
    return data;
  }

  async function loadCategories(tipo) {
    const categorias = await api(`/dashboard/api/categorias/${tipo}`);
    document
      .querySelectorAll(`[data-category-select="${tipo}"]`)
      .forEach((select) => {
        const current = select.value;
        select.innerHTML =
          '<option value="">Seleccione...</option>' +
          categorias
            .map(
              (c) =>
                `<option value="${escapeHtml(c.nombre)}">${escapeHtml(c.nombre)}</option>`,
            )
            .join("") +
          '<option value="__new__">+ Crear nueva categoria</option>';
        if (current) select.value = current;
      });
  }

  async function loadAccounts() {
    const cuentas = await api("/dashboard/api/cuentas");
    const options =
      '<option value="">Seleccione...</option>' +
      cuentas
        .map((c) => `<option value="${c.id}">${escapeHtml(c.nombre)}</option>`)
        .join("");
    document.querySelectorAll("[data-account-select]").forEach((select) => {
      const current = select.value;
      select.innerHTML = options;
      if (current) select.value = current;
    });
    const tabla = document.getElementById("tablaCuentas");
    if (tabla) {
      tabla.innerHTML =
        cuentas
          .map(
            (c) =>
              `<tr><td>${escapeHtml(c.nombre)}</td><td>${escapeHtml(c.tipo)}</td><td>${currency(c.saldo_inicial)}</td><td><strong>${currency(c.saldo_actual)}</strong></td><td><div class="actions"><button class="btn small" type="button" data-edit-account="${c.id}">Editar</button><button class="btn danger small" type="button" data-delete-account="${c.id}">Eliminar</button></div></td></tr>`,
          )
          .join("") ||
        '<tr><td colspan="5" class="empty">Sin cuentas registradas.</td></tr>';
    }
    renderResumenCuentas(cuentas);
    return cuentas;
  }

  function renderResumenCuentas(cuentas) {
    const body = document.getElementById("resumenCuentasBody");
    if (!body) return;
    body.innerHTML =
      (cuentas || [])
        .map(
          (c) =>
            `<tr><td><strong>${escapeHtml(c.nombre)}</strong></td><td>${escapeHtml(c.tipo)}</td><td>${currency(c.ingresos)}</td><td>${currency(c.egresos)}</td><td><strong>${currency(c.saldo_actual)}</strong></td><td>${currency(c.saldo_inicial)}</td></tr>`,
        )
        .join("") ||
      '<tr><td colspan="6" class="empty">Sin cuentas registradas.</td></tr>';
  }

  function statePill(estado) {
    return `<span class="pill state state-${escapeHtml(estado)}">${escapeHtml(estado)}</span>`;
  }
  function htmlDate(value) {
    const d = value ? new Date(value) : new Date();
    if (isNaN(d.getTime())) return value || "";
    return d.toLocaleString("es-CO", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  function toDatetimeLocal(value) {
    const d = value ? new Date(value) : new Date();
    if (isNaN(d.getTime())) return localNow();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  }

  async function loadDashboard() {
    const data = await api("/dashboard/api/dashboard");
    const saldo = document.getElementById("saldoActual");
    const ingresos = document.getElementById("ingresosMes");
    const egresos = document.getElementById("egresosMes");
    if (saldo) saldo.textContent = currency(data.saldo);
    if (ingresos) ingresos.textContent = currency(data.ingresos);
    if (egresos) egresos.textContent = currency(data.egresos);
    const script = document.getElementById("dashboard-data");
    if (script) script.textContent = JSON.stringify(data);
    if (window.FinexCharts) window.FinexCharts.renderCharts();
    renderResumenCuentas(data.cuentas || []);
  }

  function actionButtons(mov, report = false) {
    if (report) {
      return `<div class="actions"><a class="btn secondary small" href="/dashboard/api/movimientos/${mov.id}/pdf">PDF</a><button class="btn danger small" type="button" data-delete-movement="${mov.id}">Eliminar</button></div>`;
    }
    return `<div class="actions"><button class="btn small" type="button" data-edit-movement="${mov.id}">Editar</button><a class="btn secondary small" href="/dashboard/api/movimientos/${mov.id}/pdf">PDF</a><a class="btn secondary small" href="/dashboard/api/movimientos/${mov.id}/excel">Excel</a><button class="btn danger small" type="button" data-delete-movement="${mov.id}">Eliminar</button></div>`;
  }

  function buildReportQuery() {
    const params = new URLSearchParams();
    const desde = document.getElementById("desde")?.value || "";
    const hasta = document.getElementById("hasta")?.value || "";
    if (desde) params.set("desde", desde);
    if (hasta) params.set("hasta", hasta);
    return params.toString();
  }

  function updateReportExports() {
    const query = buildReportQuery();
    const suffix = query ? "?" + query : "";
    const pdf = document.getElementById("reportePdfGeneral");
    const excel = document.getElementById("reporteExcelGeneral");
    if (pdf) pdf.href = "/reportes/movimientos/pdf" + suffix;
    if (excel) excel.href = "/reportes/movimientos/excel" + suffix;
  }

  function renderRow(mov, report = false) {
    const rowClass = mov.estado === "anulado" ? ' class="row-anulada"' : "";
    if (report) {
      return `<tr${rowClass}><td><strong>${mov.numero_registro}</strong></td><td>${htmlDate(mov.fecha)}</td><td><span class="pill ${escapeHtml(mov.tipo)}">${escapeHtml(mov.tipo)}</span></td><td>${escapeHtml(mov.categoria)}</td><td>${escapeHtml(mov.cuenta || "")}</td><td>${escapeHtml(mov.descripcion)}</td><td>${currency(mov.valor)}</td><td>${statePill(mov.estado)}</td><td>${actionButtons(mov, true)}</td></tr>`;
    }
    return `<tr${rowClass}><td><strong>${mov.numero_registro}</strong></td><td>${htmlDate(mov.fecha)}</td><td>${escapeHtml(mov.categoria)}</td><td>${escapeHtml(mov.cuenta || "")}</td><td>${escapeHtml(mov.descripcion)}</td><td>${currency(mov.valor)}</td><td>${statePill(mov.estado)}</td><td>${actionButtons(mov)}</td></tr>`;
  }

  async function loadMovements() {
    updateReportExports();
    let url = "/dashboard/api/movimientos";
    const query = buildReportQuery();
    if (query) url += "?" + query;
    const movimientos = await api(url);
    const ingresos = document.getElementById("tablaIngresos");
    const egresos = document.getElementById("tablaEgresos");
    const report = document.getElementById("reporteBody");
    if (ingresos)
      ingresos.innerHTML =
        movimientos
          .filter((m) => m.tipo === "ingreso")
          .map((m) => renderRow(m))
          .join("") ||
        '<tr><td colspan="8" class="empty">Sin ingresos registrados.</td></tr>';
    if (egresos)
      egresos.innerHTML =
        movimientos
          .filter((m) => m.tipo === "egreso")
          .map((m) => renderRow(m))
          .join("") ||
        '<tr><td colspan="8" class="empty">Sin egresos registrados.</td></tr>';
    if (report)
      report.innerHTML =
        movimientos.map((m) => renderRow(m, true)).join("") ||
        '<tr><td colspan="9" class="empty">Sin movimientos.</td></tr>';
  }

  document.querySelectorAll("[data-category-select]").forEach((select) => {
    select.addEventListener("change", () => {
      const form = select.closest("form");
      let field = form.querySelector(".new-category-field");
      if (!field && select.value === "__new__") {
        field = document.createElement("label");
        field.className = "new-category-field";
        field.innerHTML =
          'Nueva categoría<input name="nueva_categoria" placeholder="Nombre de la categoría" />';
        select.closest("label").after(field);
      }
      if (field) field.hidden = select.value !== "__new__";
      const input = field?.querySelector("input");
      if (input) input.required = select.value === "__new__";
    });
  });

  document.querySelectorAll("[data-movement-form]").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const data = Object.fromEntries(new FormData(form).entries());
        data.tipo = form.dataset.type;
        if (data.categoria === "__new__") data.categoria = data.nueva_categoria;
        if (!data.categoria)
          throw new Error("Selecciona o crea una categoria.");
        if (numberValue(data.monto) <= 0)
          throw new Error("El monto debe ser mayor que cero.");
        data.monto = String(numberValue(data.monto));
        await api("/dashboard/api/movimientos", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        form.reset();
        form.querySelector('input[type="datetime-local"]').value = localNow();
        const field = form.querySelector(".new-category-field");
        if (field) field.hidden = true;
        await loadCategories(form.dataset.type);
        await loadAccounts();
        await loadMovements();
        await loadDashboard();
        showNotice("Registro guardado correctamente.", "success");
      } catch (err) {
        showNotice(err.message, "error");
      }
    });
  });

  document
    .querySelector("[data-account-form]")
    ?.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const form = e.target;
        const data = Object.fromEntries(new FormData(form).entries());
        data.saldo_inicial = String(numberValue(data.saldo_inicial));
        await api("/dashboard/api/cuentas", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        form.reset();
        await loadAccounts();
        await loadDashboard();
        showNotice("Cuenta guardada correctamente.", "success");
      } catch (err) {
        showNotice(err.message, "error");
      }
    });

  let deleteId = null;
  let deleteAccountId = null;
  document.addEventListener("click", async (e) => {
    const editBtn = e.target.closest("[data-edit-movement]");
    if (editBtn) {
      try {
        const mov = await api(
          `/dashboard/api/movimientos/${editBtn.dataset.editMovement}`,
        );
        const form = document.getElementById("editMovementForm");
        form.elements["id"].value = mov.id;
        form.elements["tipo"].value = mov.tipo;
        form.elements["categoria"].value = mov.categoria || "";
        form.elements["cuenta_id"].value = mov.cuenta_id || "";
        form.elements["monto"].value = money.format(Number(mov.valor || 0));
        form.elements["descripcion"].value = mov.descripcion || "";
        form.elements["fecha"].value = toDatetimeLocal(mov.fecha);
        form.elements["estado"].value = mov.estado || "completado";
        document.getElementById("editMovementDialog").showModal();
      } catch (err) {
        showNotice(err.message, "error");
      }
    }
    const delBtn = e.target.closest("[data-delete-movement]");
    if (delBtn) {
      deleteId = delBtn.dataset.deleteMovement;
      document.getElementById("deleteMovementDialog").showModal();
    }
    const editAccountBtn = e.target.closest("[data-edit-account]");
    if (editAccountBtn) {
      try {
        const cuenta = await api(
          `/dashboard/api/cuentas/${editAccountBtn.dataset.editAccount}`,
        );
        const form = document.getElementById("editAccountForm");
        form.elements["id"].value = cuenta.id;
        form.elements["nombre"].value = cuenta.nombre || "";
        form.elements["tipo"].value = cuenta.tipo || "efectivo";
        form.elements["saldo_inicial"].value = money.format(
          Number(cuenta.saldo_inicial || 0),
        );
        document.getElementById("editAccountDialog").showModal();
      } catch (err) {
        showNotice(err.message, "error");
      }
    }
    const deleteAccountBtn = e.target.closest("[data-delete-account]");
    if (deleteAccountBtn) {
      deleteAccountId = deleteAccountBtn.dataset.deleteAccount;
      document.getElementById("deleteAccountDialog").showModal();
    }
  });

  document
    .getElementById("editMovementForm")
    ?.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const form = e.target;
        const data = Object.fromEntries(new FormData(form).entries());
        data.monto = String(numberValue(data.monto));
        await api(`/dashboard/api/movimientos/${data.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        document.getElementById("editMovementDialog").close();
        await loadAccounts();
        await loadMovements();
        await loadDashboard();
      } catch (err) {
        showNotice(err.message, "error");
      }
    });

  document
    .getElementById("editAccountForm")
    ?.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const form = e.target;
        const data = Object.fromEntries(new FormData(form).entries());
        data.saldo_inicial = String(numberValue(data.saldo_inicial));
        await api(`/dashboard/api/cuentas/${data.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        document.getElementById("editAccountDialog").close();
        await loadAccounts();
        await loadDashboard();
      } catch (err) {
        showNotice(err.message, "error");
      }
    });

  document
    .getElementById("confirmDeleteMovement")
    ?.addEventListener("click", async () => {
      if (!deleteId) return;
      try {
        await api(`/dashboard/api/movimientos/${deleteId}`, {
          method: "DELETE",
        });
        document.getElementById("deleteMovementDialog").close();
        deleteId = null;
        await loadAccounts();
        await loadMovements();
        await loadDashboard();
      } catch (err) {
        showNotice(err.message, "error");
      }
    });

  document
    .getElementById("confirmDeleteAccount")
    ?.addEventListener("click", async () => {
      if (!deleteAccountId) return;
      try {
        await api(`/dashboard/api/cuentas/${deleteAccountId}`, {
          method: "DELETE",
        });
        document.getElementById("deleteAccountDialog").close();
        deleteAccountId = null;
        await loadAccounts();
        await loadDashboard();
      } catch (err) {
        showNotice(err.message, "error");
      }
    });

  document
    .querySelector("[data-filter-report]")
    ?.addEventListener("click", loadMovements);
  ["desde", "hasta"].forEach((id) =>
    document.getElementById(id)?.addEventListener("change", () => {
      updateReportExports();
      loadMovements();
    }),
  );

  async function init() {
    try {
      await Promise.all([
        loadCategories("ingreso"),
        loadCategories("egreso"),
        loadAccounts(),
      ]);
    } catch (err) {
      showNotice(err.message, "error");
    }
    try {
      await Promise.all([loadDashboard(), loadMovements()]);
    } catch (err) {
      showNotice(err.message, "error");
    }
  }
  init();

  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.getElementById("menuOverlay");
  function closeMenu() {
    sidebar?.classList.remove("active");
    overlay?.classList.remove("active");
  }
  menuToggle?.addEventListener("click", () => {
    const isOpening = !sidebar?.classList.contains("active");
    sidebar?.classList.toggle("active");
    if (isOpening) setTimeout(() => overlay?.classList.add("active"), 120);
    else overlay?.classList.remove("active");
  });
  overlay?.addEventListener("click", closeMenu);
})();
