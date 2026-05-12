const API = "";
const empresaId = 1;
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

function today() {
  return new Date().toISOString().slice(0, 10);
}
function money(v) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(v || 0));
}
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2600);
}
async function request(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json", "X-Empresa-Id": empresaId },
    ...options,
  });
  if (path.includes("/pdf")) return res;
  const data = await res.json();
  if (!res.ok || data.ok === false)
    throw new Error(data.error || "Error de servidor");
  return data;
}
function formData(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  Object.keys(data).forEach((k) => {
    if (data[k] === "") data[k] = null;
  });
  return data;
}
function fillForm(form, data) {
  Object.entries(data).forEach(([k, v]) => {
    if (form.elements[k]) form.elements[k].value = v ?? "";
  });
}
function clearForm(id) {
  const f = document.getElementById(id);
  f.reset();
  if (f.elements.id) f.elements.id.value = "";
}

function drawLineChart(canvas, rows) {
  const ctx = canvas.getContext("2d"),
    w = (canvas.width = canvas.clientWidth),
    h = (canvas.height = 260);
  ctx.clearRect(0, 0, w, h);
  const pad = 34;
  const max = Math.max(
    1,
    ...rows.flatMap((r) => [r.ingresos, r.gastos, Math.abs(r.utilidad)]),
  );
  ctx.strokeStyle = "#e5e7eb";
  ctx.lineWidth = 1;
  ctx.font = "11px Arial";
  ctx.fillStyle = "#64748b";
  for (let i = 0; i < 5; i++) {
    const y = pad + ((h - pad * 2) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(w - pad, y);
    ctx.stroke();
    ctx.fillText(money((max * (4 - i)) / 4).replace(",00", ""), 4, y + 4);
  }
  function plot(key, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    rows.forEach((r, i) => {
      const x = pad + (w - pad * 2) * (i / Math.max(1, rows.length - 1));
      const y = h - pad - (h - pad * 2) * (Number(r[key]) / max);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.stroke();
  }
  plot("ingresos", "#16c784");
  plot("gastos", "#ff4d67");
  plot("utilidad", "#2563eb");
  ctx.fillStyle = "#64748b";
  if (rows[0]) ctx.fillText(rows[0].fecha.slice(5), pad, h - 10);
  if (rows.at(-1))
    ctx.fillText(rows.at(-1).fecha.slice(5), w - pad - 30, h - 10);
}
function drawDonut(canvas, rows) {
  const ctx = canvas.getContext("2d"),
    w = (canvas.width = canvas.clientWidth),
    h = (canvas.height = 240),
    cx = w / 2,
    cy = h / 2,
    r = 82;
  ctx.clearRect(0, 0, w, h);
  const colors = [
    "#2563eb",
    "#16c784",
    "#7057d3",
    "#f97316",
    "#94a3b8",
    "#ef4444",
  ];
  const total = rows.reduce((s, r) => s + Number(r.total), 0) || 1;
  let start = -Math.PI / 2;
  rows.forEach((row, i) => {
    const angle = (Number(row.total) / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + angle);
    ctx.fillStyle = colors[i % colors.length];
    ctx.fill();
    start += angle;
  });
  ctx.globalCompositeOperation = "destination-out";
  ctx.beginPath();
  ctx.arc(cx, cy, 45, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalCompositeOperation = "source-over";
  ctx.fillStyle = "#172033";
  ctx.font = "bold 14px Arial";
  ctx.textAlign = "center";
  ctx.fillText("Total", cx, cy - 4);
  ctx.font = "bold 13px Arial";
  ctx.fillText(money(total), cx, cy + 16);
  ctx.textAlign = "left";
  $("#donut-legend").innerHTML =
    rows
      .map(
        (r, i) =>
          `<div><span><b style="color:${colors[i % colors.length]}">●</b> ${r.categoria}</span><strong>${money(r.total)}</strong></div>`,
      )
      .join("") || "<p>No hay gastos registrados.</p>";
}

async function loadDashboard() {
  const period = $("#periodo-dashboard").value;
  let qs = "";
  if (period) {
    const [y, m] = period.split("-").map(Number);
    const last = new Date(y, m, 0).getDate();
    qs = `?desde=${period}-01&hasta=${period}-${String(last).padStart(2, "0")}`;
  }
  const data = await request("/api/dashboard/resumen" + qs);
  const c = data.cards;
  $("#card-ingresos").textContent = money(c.ingresos.valor);
  $("#var-ingresos").textContent = `${c.ingresos.variacion}% vs mes anterior`;
  $("#card-gastos").textContent = money(c.gastos.valor);
  $("#var-gastos").textContent = `${c.gastos.variacion}% vs mes anterior`;
  $("#card-utilidad").textContent = money(c.utilidad.valor);
  $("#var-utilidad").textContent = `${c.utilidad.variacion}% vs mes anterior`;
  $("#card-impuestos").textContent = money(c.impuestos.valor);
  $("#var-impuestos").textContent = `${c.impuestos.variacion}% vs mes anterior`;
  drawLineChart($("#cashflow-chart"), data.flujo);
  drawDonut($("#donut-chart"), data.gastos_por_categoria);
  $("#obligaciones-list").innerHTML =
    data.obligaciones
      .map(
        (o) =>
          `<div class="obligacion"><div><strong>${o.nombre}</strong><small>${o.periodo}<br>${money(o.valor_estimado)}</small></div><div class="date-badge">${new Date(o.fecha_vencimiento + "T00:00:00").getDate()}<br><small>${new Date(o.fecha_vencimiento + "T00:00:00").toLocaleString("es-CO", { month: "short" }).toUpperCase()}</small></div></div>`,
      )
      .join("") || "<p>No hay obligaciones pendientes.</p>";
}

async function loadCuenta() {
  const data = await request("/api/cuenta");
  fillForm($("#form-cuenta"), data.empresa);
  $("#side-company").textContent = data.empresa.nombre_empresa;
  $("#side-nit").textContent = "Nit. " + data.empresa.nit;
}

function table(headers, rows) {
  return `<thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody>`;
}
async function loadClientes() {
  const d = await request("/api/clientes");
  $("#tabla-clientes").innerHTML = table(
    ["Nombre", "Documento", "Email", "Acciones"],
    d.clientes.map(
      (r) =>
        `<tr><td><strong>${r.nombre}</strong><small>${r.telefono || ""}</small></td><td>${r.documento || ""}</td><td>${r.email || ""}</td><td class="action-row"><button onclick='editCliente(${JSON.stringify(r)})'>Editar</button><button class="danger" onclick="del('/api/clientes/${r.id}', loadClientes)">Eliminar</button></td></tr>`,
    ),
  );
  fillSelect("#venta-cliente", d.clientes, "nombre");
}
function editCliente(r) {
  fillForm($("#form-clientes"), r);
}
async function loadProveedores() {
  const d = await request("/api/proveedores");
  $("#tabla-proveedores").innerHTML = table(
    ["Nombre", "Documento", "Email", "Acciones"],
    d.proveedores.map(
      (r) =>
        `<tr><td><strong>${r.nombre}</strong><small>${r.telefono || ""}</small></td><td>${r.documento || ""}</td><td>${r.email || ""}</td><td class="action-row"><button onclick='editProveedor(${JSON.stringify(r)})'>Editar</button><button class="danger" onclick="del('/api/proveedores/${r.id}', loadProveedores)">Eliminar</button></td></tr>`,
    ),
  );
  fillSelect("#compra-proveedor", d.proveedores, "nombre");
}
function editProveedor(r) {
  fillForm($("#form-proveedores"), r);
}
async function loadItems() {
  const d = await request("/api/items");
  $("#tabla-items").innerHTML = table(
    ["Código", "Nombre", "Tipo", "Precio", "Acciones"],
    d.items.map(
      (r) =>
        `<tr><td>${r.codigo || ""}</td><td><strong>${r.nombre}</strong><small>${r.descripcion || ""}</small></td><td><span class="badge">${r.tipo}</span></td><td>${money(r.precio_unitario)}</td><td class="action-row"><button onclick='editItem(${JSON.stringify(r)})'>Editar</button><button class="danger" onclick="del('/api/items/${r.id}', loadItems)">Desactivar</button></td></tr>`,
    ),
  );
  fillSelect(
    "#venta-item",
    d.items.filter((i) => i.activo == 1),
    "nombre",
  );
}
function editItem(r) {
  fillForm($("#form-items"), r);
}
function fillSelect(selector, rows, label) {
  const el = $(selector);
  if (!el) return;
  el.innerHTML =
    '<option value="">Seleccione...</option>' +
    rows.map((r) => `<option value="${r.id}">${r[label]}</option>`).join("");
}

async function loadVentas() {
  const d = await request("/api/ventas");
  $("#tabla-ventas").innerHTML = table(
    ["ID", "Número", "Cliente", "Total", "Saldo", "Estado", "PDF"],
    d.ventas.map(
      (r) =>
        `<tr><td>${r.id}</td><td><strong>${r.numero}</strong><small>${r.fecha_emision}</small></td><td>${r.cliente_nombre || ""}</td><td>${money(r.total)}</td><td>${money(r.saldo)}</td><td><span class="badge">${r.estado}</span></td><td><button onclick="location.href='/api/ventas/${r.id}/pdf?empresa_id=${empresaId}'">PDF</button></td></tr>`,
    ),
  );
}
async function loadCompras() {
  const d = await request("/api/compras");
  $("#tabla-compras").innerHTML = table(
    ["ID", "Número", "Proveedor", "Total", "Saldo", "Estado"],
    d.compras.map(
      (r) =>
        `<tr><td>${r.id}</td><td><strong>${r.numero}</strong><small>${r.fecha_emision}</small></td><td>${r.proveedor_nombre || ""}</td><td>${money(r.total)}</td><td>${money(r.saldo)}</td><td><span class="badge">${r.estado}</span></td></tr>`,
    ),
  );
}
async function loadPagos() {
  const d = await request("/api/pagos");
  $("#tabla-pagos").innerHTML = table(
    ["Fecha", "Tipo", "Factura", "Monto", "Método", "Acciones"],
    d.pagos.map(
      (r) =>
        `<tr><td>${r.fecha_pago}</td><td>${r.tipo_factura}</td><td>${r.factura_venta_numero || r.factura_compra_numero || ""}</td><td>${money(r.monto)}</td><td>${r.metodo}</td><td><button class="danger" onclick="del('/api/pagos/${r.id}', loadAll)">Eliminar</button></td></tr>`,
    ),
  );
}
async function loadMovimientos() {
  const d = await request("/api/movimientos");
  $("#tabla-movimientos").innerHTML = table(
    ["Fecha", "Tipo", "Descripción", "Débito", "Crédito", "Categoría"],
    d.movimientos.map(
      (r) =>
        `<tr><td>${r.fecha}</td><td><span class="badge">${r.tipo}</span></td><td>${r.descripcion}</td><td>${money(r.debito)}</td><td>${money(r.credito)}</td><td>${r.categoria || ""}</td></tr>`,
    ),
  );
}
async function del(path, cb) {
  if (!confirm("¿Confirmas la eliminación?")) return;
  try {
    await request(path, { method: "DELETE" });
    toast("Eliminado correctamente");
    await cb();
    await loadDashboard();
  } catch (e) {
    toast(e.message);
  }
}

async function submitCrud(formId, base, reload) {
  const form = $("#" + formId);
  const data = formData(form);
  const id = data.id;
  delete data.id;
  const path = id ? `${base}/${id}` : base;
  const method = id ? "PUT" : "POST";
  await request(path, { method, body: JSON.stringify(data) });
  clearForm(formId);
  toast("Guardado correctamente");
  await reload();
  await loadDashboard();
}

async function loadAll() {
  await Promise.all([
    loadCuenta(),
    loadClientes(),
    loadProveedores(),
    loadItems(),
    loadVentas(),
    loadCompras(),
    loadPagos(),
    loadMovimientos(),
    loadDashboard(),
  ]);
}

function initForms() {
  ["form-clientes", "form-proveedores", "form-items", "form-cuenta"].forEach(
    (id) => {
      const f = $("#" + id);
      if (!f) return;
      f.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          if (id === "form-clientes")
            await submitCrud(id, "/api/clientes", loadClientes);
          if (id === "form-proveedores")
            await submitCrud(id, "/api/proveedores", loadProveedores);
          if (id === "form-items")
            await submitCrud(id, "/api/items", loadItems);
          if (id === "form-cuenta") {
            await request("/api/cuenta", {
              method: "PUT",
              body: JSON.stringify(formData(f)),
            });
            toast("Cuenta actualizada");
            await loadCuenta();
          }
        } catch (err) {
          toast(err.message);
        }
      });
    },
  );
  $("#form-ventas").addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      await request("/api/ventas", {
        method: "POST",
        body: JSON.stringify({
          cliente_id: d.cliente_id,
          fecha_emision: d.fecha_emision,
          fecha_vencimiento: d.fecha_vencimiento,
          observaciones: d.observaciones,
          items: [{ item_id: d.item_id, cantidad: d.cantidad }],
        }),
      });
      e.target.reset();
      setDefaultDates();
      toast("Factura creada");
      await loadVentas();
      await loadDashboard();
    } catch (err) {
      toast(err.message);
    }
  });
  $("#form-compras").addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      await request("/api/compras", {
        method: "POST",
        body: JSON.stringify({
          proveedor_id: d.proveedor_id,
          numero_proveedor: d.numero_proveedor,
          fecha_emision: d.fecha_emision,
          fecha_vencimiento: d.fecha_vencimiento,
          items: [
            {
              descripcion: d.descripcion,
              cantidad: d.cantidad,
              valor_unitario: d.valor_unitario,
              impuesto_porcentaje: d.impuesto_porcentaje,
              categoria: d.categoria,
            },
          ],
        }),
      });
      e.target.reset();
      setDefaultDates();
      toast("Compra registrada");
      await loadCompras();
      await loadDashboard();
    } catch (err) {
      toast(err.message);
    }
  });
  $("#form-pagos").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await request("/api/pagos", {
        method: "POST",
        body: JSON.stringify(formData(e.target)),
      });
      e.target.reset();
      setDefaultDates();
      toast("Pago registrado");
      await loadAll();
    } catch (err) {
      toast(err.message);
    }
  });
  $("#form-movimientos").addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    d.origen = "manual";
    d.origen_id = null;
    try {
      await request("/api/movimientos", {
        method: "POST",
        body: JSON.stringify(d),
      });
      e.target.reset();
      setDefaultDates();
      toast("Movimiento creado");
      await loadMovimientos();
      await loadDashboard();
    } catch (err) {
      toast(err.message);
    }
  });
  $$("[data-reset]").forEach((b) =>
    b.addEventListener("click", () => clearForm(b.dataset.reset)),
  );
}
function setDefaultDates() {
  $$('input[type="date"]').forEach((i) => {
    if (!i.value) i.value = today();
  });
  const now = new Date();
  $("#periodo-dashboard").value =
    `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}
function initNavigation() {
  $$("nav button").forEach((btn) =>
    btn.addEventListener("click", () => {
      $$("nav button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      $$(".page").forEach((p) => p.classList.remove("active-page"));
      $("#" + btn.dataset.section).classList.add("active-page");
      if (innerWidth < 1100) $(".sidebar").classList.remove("open");
    }),
  );
  $("#toggle-sidebar").addEventListener("click", () =>
    $(".sidebar").classList.toggle("open"),
  );
  $("#periodo-dashboard").addEventListener("change", loadDashboard);
}

document.addEventListener("DOMContentLoaded", async () => {
  setDefaultDates();
  initNavigation();
  initForms();
  await loadAll();
});

async function logout(e) {
  if (e) {
    e.preventDefault();
  }

  try {
    const response = await fetch("/api/logout", {
      method: "POST",
    });

    const data = await response.json();

    if (response.ok) {
      window.location.href = data.redirect;
    }
  } catch (error) {
    console.error("Error:", error);
    window.location.href = "/";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("btnLogout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
  }
});

const items = document.querySelectorAll(".nav-item");

items.forEach((item) => {
  item.addEventListener("click", () => {
    items.forEach((btn) => {
      btn.classList.remove("active");
    });

    item.classList.add("active");

    const section = item.dataset.section;

    console.log("Sección:", section);
  });
});
