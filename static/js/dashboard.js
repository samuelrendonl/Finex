// ======================================
// VARIABLES
// ======================================

let financeChart;
let pieChart;
let movimientoEditando = null;

// ======================================
// INIT
// ======================================

document.addEventListener("DOMContentLoaded", () => {
  showSection("inicio");

  cargarDashboard();
  cargarMovimientos();

  cargarCategorias("ingreso");
  cargarCategorias("egreso");

  crearGraficas();
});

// ======================================
// SECCIONES
// ======================================

function showSection(id) {
  document.querySelectorAll(".section").forEach((section) => {
    section.style.display = "none";
  });

  document.getElementById(id).style.display = "block";
}

// ======================================
// FORMULARIOS
// ======================================

function toggleIngresoForm() {
  const form = document.getElementById("ingresoForm");

  form.style.display = form.style.display === "block" ? "none" : "block";
}

function toggleEgresoForm() {
  const form = document.getElementById("egresoForm");

  form.style.display = form.style.display === "block" ? "none" : "block";
}

// ======================================
// CARGAR CATEGORIAS
// ======================================

async function cargarCategorias(tipo) {
  try {
    const response = await fetch(`/dashboard/api/categorias/${tipo}`);

    const categorias = await response.json();

    let select;

    if (tipo === "ingreso") {
      select = document.getElementById("ingresoCategoria");
    } else {
      select = document.getElementById("egresoCategoria");
    }

    select.innerHTML = `
      <option value="">
        Seleccionar categoría
      </option>
    `;

    categorias.forEach((cat) => {
      select.innerHTML += `
        <option value="${cat.nombre}">
          ${cat.nombre}
        </option>
      `;
    });

    select.innerHTML += `
      <option value="nueva">
        + Crear nueva categoría
      </option>
    `;
  } catch (error) {
    console.error("Error cargando categorías:", error);
  }
}

// ======================================
// GUARDAR INGRESO
// ======================================

async function guardarIngreso() {
  try {
    let categoria = document.getElementById("ingresoCategoria").value;

    if (categoria === "nueva") {
      categoria = prompt("Nombre de la nueva categoría");

      if (!categoria) return;

      await fetch("/dashboard/api/categorias", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          nombre: categoria,
          tipo: "ingreso",
        }),
      });

      await cargarCategorias("ingreso");
    }

    const data = {
      tipo: "ingreso",

      categoria: categoria,

      monto: document.getElementById("ingresoMonto").value,

      descripcion: document.getElementById("ingresoDescripcion").value,

      fecha: document.getElementById("ingresoFecha").value,

      estado: document.getElementById("ingresoEstado").value,
    };

    await fetch("/dashboard/api/movimientos", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(data),
    });

    await cargarMovimientos();

    await cargarDashboard();

    toggleIngresoForm();
  } catch (error) {
    console.error("Error guardando ingreso:", error);
  }
}

// ======================================
// GUARDAR EGRESO
// ======================================

async function guardarEgreso() {
  try {
    let categoria = document.getElementById("egresoCategoria").value;

    if (categoria === "nueva") {
      categoria = prompt("Nombre de la nueva categoría");

      if (!categoria) return;

      await fetch("/dashboard/api/categorias", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          nombre: categoria,
          tipo: "egreso",
        }),
      });

      await cargarCategorias("egreso");
    }

    const data = {
      tipo: "egreso",

      categoria: categoria,

      monto: document.getElementById("egresoMonto").value,

      descripcion: document.getElementById("egresoDescripcion").value,

      fecha: document.getElementById("egresoFecha").value,

      estado: document.getElementById("egresoEstado").value,
    };

    await fetch("/dashboard/api/movimientos", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(data),
    });

    await cargarMovimientos();

    await cargarDashboard();

    toggleEgresoForm();
  } catch (error) {
    console.error("Error guardando egreso:", error);
  }
}

// ======================================
// CARGAR MOVIMIENTOS
// ======================================

async function cargarMovimientos(desde, hasta) {
  let url = "/dashboard/api/movimientos";

  if (desde === undefined || hasta === undefined) {
    desde = document.getElementById("desde")?.value || "";

    hasta = document.getElementById("hasta")?.value || "";
  }

  if (desde || hasta) {
    url += `?desde=${desde}&hasta=${hasta}`;
  }

  const response = await fetch(url);

  const movimientos = await response.json();

  const tablaIngresos = document.getElementById("tablaIngresos");

  const tablaEgresos = document.getElementById("tablaEgresos");

  const reporte = document.getElementById("reporteBody");

  tablaIngresos.innerHTML = "";
  tablaEgresos.innerHTML = "";
  reporte.innerHTML = "";

  movimientos.forEach((mov) => {
    const fecha = new Date(mov.fecha).toLocaleDateString("es-CO");

    const monto = Number(mov.valor).toLocaleString("es-CO");

    // =========================
    // REPORTE
    // =========================

    const reporteRow = `
      <tr>

        <td>${mov.tipo}</td>

        <td>${mov.categoria}</td>

        <td>${mov.descripcion}</td>

        <td>$${monto}</td>

        <td>${fecha}</td>

        <td>${mov.estado}</td>

      </tr>
    `;

    reporte.innerHTML += reporteRow;

    // =========================
    // TABLAS
    // =========================

    const row = `
      <tr>

        <td>${mov.categoria}</td>

        <td>${mov.descripcion}</td>

        <td>$${monto}</td>

        <td>${fecha}</td>

        <td>${mov.estado}</td>

        <td class="acciones">

          <button
            class="btn-editar"
            onclick="editarMovimiento(${mov.id})">
            ✏️
          </button>

          <button
            class="btn-eliminar"
            onclick="eliminarMovimiento(${mov.id})">
            🗑️
          </button>

        </td>

      </tr>
    `;

    if (mov.tipo === "ingreso") {
      tablaIngresos.innerHTML += row;
    } else {
      tablaEgresos.innerHTML += row;
    }
  });
}

// ======================================
// ELIMINAR MOVIMIENTO
// ======================================

async function eliminarMovimiento(id) {
  mostrarConfirmacion(
    "¿Deseas eliminar este movimiento?",

    async () => {
      try {
        await fetch(
          `/dashboard/api/movimientos/${id}`,

          {
            method: "DELETE",
          },
        );

        await cargarMovimientos();

        await cargarDashboard();

        mostrarToast("Movimiento eliminado correctamente");
      } catch (error) {
        console.error(error);

        mostrarToast("Error eliminando movimiento");
      }
    },
  );
}

// ======================================
// EDITAR MOVIMIENTO
// ======================================

async function editarMovimiento(id) {
  try {
    const response = await fetch(`/dashboard/api/movimientos/${id}`);

    const mov = await response.json();

    movimientoEditando = id;

    document.getElementById("editCategoria").value = mov.categoria;

    document.getElementById("editMonto").value = mov.valor;

    document.getElementById("editDescripcion").value = mov.descripcion;

    document.getElementById("editFecha").value = mov.fecha;

    document.getElementById("editEstado").value = mov.estado;

    document.getElementById("modalEditar").style.display = "flex";
  } catch (error) {
    console.error("Error cargando movimiento:", error);
  }
}

// ======================================
// CERRAR MODAL
// ======================================

function cerrarModal() {
  document.getElementById("modalEditar").style.display = "none";
}

// ======================================
// GUARDAR EDICION
// ======================================

async function guardarEdicion() {
  try {
    const data = {
      valor: document.getElementById("editMonto").value,

      descripcion: document.getElementById("editDescripcion").value,

      fecha: document.getElementById("editFecha").value,

      estado: document.getElementById("editEstado").value,
    };

    await fetch(
      `/dashboard/api/movimientos/${movimientoEditando}`,

      {
        method: "PUT",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify(data),
      },
    );

    cerrarModal();

    await cargarMovimientos();

    await cargarDashboard();
  } catch (error) {
    console.error("Error actualizando:", error);
  }
}

// ======================================
// DASHBOARD
// ======================================

async function cargarDashboard() {
  try {
    const response = await fetch("/dashboard/api/dashboard");

    const data = await response.json();

    const cards = document.querySelectorAll(".card h2");

    cards[0].textContent = `$${Number(data.saldo).toLocaleString("es-CO")}`;

    cards[1].textContent = `$${Number(data.ingresos).toLocaleString("es-CO")}`;

    cards[2].textContent = `$${Number(data.egresos).toLocaleString("es-CO")}`;

    cards[3].textContent = `$${Number(data.ahorros).toLocaleString("es-CO")}`;

    actualizarGraficas(data.ingresos, data.egresos);
  } catch (error) {
    console.error("Error cargando dashboard:", error);
  }
}

// ======================================
// GRAFICAS
// ======================================

function crearGraficas() {
  financeChart = new Chart(document.getElementById("financeChart"), {
    type: "bar",

    data: {
      labels: ["Ingresos", "Egresos"],

      datasets: [
        {
          label: "Monto",
          data: [0, 0],
          borderRadius: 10,
        },
      ],
    },
  });

  pieChart = new Chart(document.getElementById("pieChart"), {
    type: "doughnut",

    data: {
      labels: ["Ingresos", "Egresos"],

      datasets: [
        {
          data: [0, 0],
        },
      ],
    },
  });
}

function actualizarGraficas(ingresos, egresos) {
  financeChart.data.datasets[0].data = [ingresos, egresos];

  financeChart.update();

  pieChart.data.datasets[0].data = [ingresos, egresos];

  pieChart.update();
}

// ======================================
// MOBILE MENU
// ======================================

const menuToggle = document.querySelector(".menu-toggle");

const sidebar = document.querySelector(".sidebar");

const overlay = document.getElementById("overlay");

const menuItems = document.querySelectorAll(".menu li");

function openMenu() {
  sidebar.classList.add("active");

  overlay.classList.add("active");
}

function closeMenu() {
  sidebar.classList.remove("active");

  overlay.classList.remove("active");
}

menuToggle.addEventListener("click", () => {
  sidebar.classList.contains("active") ? closeMenu() : openMenu();
});

overlay.addEventListener("click", closeMenu);

menuItems.forEach((item) => {
  item.addEventListener("click", closeMenu);
});

// ======================================
// FILTRAR
// ======================================

async function filtrarMovimientos() {
  const desde = document.getElementById("desde").value;

  const hasta = document.getElementById("hasta").value;

  await cargarMovimientos(desde, hasta);
}

// ======================================
// EXPORTAR PDF
// ======================================

function exportarPDF() {
  const desde = document.getElementById("desde").value;

  const hasta = document.getElementById("hasta").value;

  let url = "/reportes/movimientos/pdf";

  if (desde || hasta) {
    url += `?desde=${desde}&hasta=${hasta}`;
  }

  window.open(url, "_blank");
}

// ======================================
// TOAST
// ======================================

function mostrarToast(texto) {
  const toast = document.getElementById("toast");

  toast.textContent = texto;

  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

// ======================================
// CONFIRMACION
// ======================================

function mostrarConfirmacion(mensaje, callback) {
  const modal = document.getElementById("confirmModal");

  const texto = document.getElementById("confirmText");

  const aceptar = document.getElementById("confirmAccept");

  texto.textContent = mensaje;

  modal.style.display = "flex";

  aceptar.onclick = () => {
    callback();

    cerrarConfirmacion();
  };
}

function cerrarConfirmacion() {
  document.getElementById("confirmModal").style.display = "none";
}
