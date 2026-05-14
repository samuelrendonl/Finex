// Panel personal FINEX: secciones, formularios, tablas y exportaciones.
(function(){
  if (!document.body.matches('[data-personal-app]')) return;
  const money = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
  const currency = (value) => '$ ' + money.format(Number(value || 0));
  const digits = (value) => String(value || '').replace(/\D/g, '');
  const numberValue = (value) => Number(digits(value) || 0);

  // Muestra avisos internos, sin alertas del navegador.
  function showNotice(message, type='success') {
    let wrap = document.getElementById('personalFlashWrap');
    if (!wrap) {
      const main = document.querySelector('.main') || document.body;
      wrap = document.createElement('div');
      wrap.id = 'personalFlashWrap';
      wrap.className = 'flash-wrap';
      main.prepend(wrap);
    }
    const msg = document.createElement('div');
    msg.className = `flash ${type === 'error' ? 'error' : 'success'}`;
    msg.textContent = message;
    wrap.innerHTML = '';
    wrap.appendChild(msg);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => { msg.remove(); }, 4500);
  }

  function formatInput(input){
    const before = input.value;
    const clean = digits(before);
    if (before && before !== clean && before.replace(/\./g,'') !== clean) showNotice('Solo es permitido un dato numerico.', 'error');
    input.value = clean ? money.format(Number(clean)) : '';
  }
  function bindFormat(input){
    if (!input || input.dataset.bound === '1') return;
    input.dataset.bound = '1';
    input.addEventListener('input', () => formatInput(input));
    input.addEventListener('paste', () => setTimeout(() => formatInput(input), 0));
  }
  document.querySelectorAll('[data-format-int]').forEach(bindFormat);

  function localNow(){
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0,16);
  }
  document.querySelectorAll('input[type="datetime-local"]').forEach(i => { if (!i.value) i.value = localNow(); });

  function showSection(id){
    document.querySelectorAll('.personal-section').forEach(s => s.classList.remove('active-section'));
    const section = document.getElementById(id) || document.getElementById('inicio');
    section.classList.add('active-section');
    document.querySelectorAll('[data-personal-section]').forEach(a => a.classList.toggle('active', a.dataset.personalSection === section.id));
    if (history.replaceState) history.replaceState(null, '', '#' + section.id);
  }
  document.querySelectorAll('[data-personal-section]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); showSection(a.dataset.personalSection); }));
  if (location.hash) showSection(location.hash.slice(1));

  document.addEventListener('click', e => {
    if (e.target.matches('[data-close-dialog]')) e.target.closest('dialog')?.close();
    if (e.target.matches('[data-open-logout]')) document.getElementById('logoutDialog')?.showModal();
  });

  async function api(url, options={}){
    const res = await fetch(url, options);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'No se pudo procesar la solicitud.');
    return data;
  }

  async function loadCategories(tipo){
    const categorias = await api(`/dashboard/api/categorias/${tipo}`);
    document.querySelectorAll(`[data-category-select="${tipo}"]`).forEach(select => {
      const current = select.value;
      select.innerHTML = '<option value="">Seleccione...</option>' + categorias.map(c => `<option value="${escapeHtml(c.nombre)}">${escapeHtml(c.nombre)}</option>`).join('') + '<option value="__new__">+ Crear nueva categoria</option>';
      if (current) select.value = current;
    });
  }

  function escapeHtml(text){ return String(text || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function statePill(estado){ return `<span class="pill state state-${estado}">${escapeHtml(estado)}</span>`; }
  function htmlDate(value){
    const d = value ? new Date(value) : new Date();
    if (isNaN(d.getTime())) return value || '';
    return d.toLocaleString('es-CO', { year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' });
  }
  function toDatetimeLocal(value){
    const d = value ? new Date(value) : new Date();
    if (isNaN(d.getTime())) return localNow();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0,16);
  }

  async function loadDashboard(){
    const data = await api('/dashboard/api/dashboard');
    document.getElementById('saldoActual').textContent = currency(data.saldo);
    document.getElementById('ingresosMes').textContent = currency(data.ingresos);
    document.getElementById('egresosMes').textContent = currency(data.egresos);
    const script = document.getElementById('dashboard-data');
    if (script) script.textContent = JSON.stringify(data);
    if (window.FinexCharts) window.FinexCharts.renderCharts();
  }

  function actionButtons(mov){
    return `<div class="actions">
      <button class="btn small" type="button" data-edit-movement="${mov.id}">Editar</button>
      <a class="btn secondary small" href="/dashboard/api/movimientos/${mov.id}/pdf">PDF</a>
      <a class="btn secondary small" href="/dashboard/api/movimientos/${mov.id}/excel">Excel</a>
      <button class="btn danger small" type="button" data-delete-movement="${mov.id}">Eliminar</button>
    </div>`;
  }

  function buildReportQuery(){
    const params = new URLSearchParams();
    const desde = document.getElementById('desde')?.value || '';
    const hasta = document.getElementById('hasta')?.value || '';
    if (desde) params.set('desde', desde);
    if (hasta) params.set('hasta', hasta);
    return params.toString();
  }

  function updateReportExports(){
    const query = buildReportQuery();
    const suffix = query ? '?' + query : '';
    const pdf = document.getElementById('reportePdfGeneral');
    const excel = document.getElementById('reporteExcelGeneral');
    if (pdf) pdf.href = '/reportes/movimientos/pdf' + suffix;
    if (excel) excel.href = '/reportes/movimientos/excel' + suffix;
  }


  function renderRow(mov, report=false){
    const rowClass = mov.estado === 'anulada' ? ' class="row-anulada"' : '';
    if (report) {
      return `<tr${rowClass}><td><strong>${mov.numero_registro}</strong></td><td>${htmlDate(mov.fecha)}</td><td><span class="pill ${mov.tipo}">${escapeHtml(mov.tipo)}</span></td><td>${escapeHtml(mov.categoria)}</td><td>${escapeHtml(mov.descripcion)}</td><td>${currency(mov.valor)}</td><td>${statePill(mov.estado)}</td><td>${actionButtons(mov)}</td></tr>`;
    }
    return `<tr${rowClass}><td><strong>${mov.numero_registro}</strong></td><td>${htmlDate(mov.fecha)}</td><td>${escapeHtml(mov.categoria)}</td><td>${escapeHtml(mov.descripcion)}</td><td>${currency(mov.valor)}</td><td>${statePill(mov.estado)}</td><td>${actionButtons(mov)}</td></tr>`;
  }

  async function loadMovements(){
    updateReportExports();
    let url = '/dashboard/api/movimientos';
    const query = buildReportQuery();
    if (query) url += '?' + query;
    const movimientos = await api(url);
    document.getElementById('tablaIngresos').innerHTML = movimientos.filter(m => m.tipo === 'ingreso').map(m => renderRow(m)).join('') || '<tr><td colspan="7" class="empty">Sin ingresos registrados.</td></tr>';
    document.getElementById('tablaEgresos').innerHTML = movimientos.filter(m => m.tipo === 'egreso').map(m => renderRow(m)).join('') || '<tr><td colspan="7" class="empty">Sin egresos registrados.</td></tr>';
    document.getElementById('reporteBody').innerHTML = movimientos.map(m => renderRow(m, true)).join('') || '<tr><td colspan="8" class="empty">Sin movimientos.</td></tr>';
  }

  document.querySelectorAll('[data-category-select]').forEach(select => {
    select.addEventListener('change', () => {
      const form = select.closest('form');
      const field = form.querySelector('.new-category-field');
      if (field) field.hidden = select.value !== '__new__';
      const input = field?.querySelector('input');
      if (input) input.required = select.value === '__new__';
    });
  });

  document.querySelectorAll('[data-movement-form]').forEach(form => {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      try {
        const data = Object.fromEntries(new FormData(form).entries());
        data.tipo = form.dataset.type;
        if (data.categoria === '__new__') data.categoria = data.nueva_categoria;
        if (!data.categoria) throw new Error('Selecciona o crea una categoria.');
        if (numberValue(data.monto) <= 0) throw new Error('El monto debe ser mayor que cero.');
        data.monto = String(numberValue(data.monto));
        await api('/dashboard/api/movimientos', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
        form.reset();
        form.querySelector('input[type="datetime-local"]').value = localNow();
        form.querySelector('.new-category-field').hidden = true;
        await loadCategories(form.dataset.type);
        await loadMovements();
        await loadDashboard();
        showNotice('Registro guardado correctamente.', 'success');
      } catch(err) { showNotice(err.message, 'error'); }
    });
  });

  let deleteId = null;
  document.addEventListener('click', async e => {
    const editBtn = e.target.closest('[data-edit-movement]');
    if (editBtn) {
      const mov = await api(`/dashboard/api/movimientos/${editBtn.dataset.editMovement}`);
      const form = document.getElementById('editMovementForm');
      form.elements['id'].value = mov.id;
      form.elements['tipo'].value = mov.tipo;
      form.elements['categoria'].value = mov.categoria || '';
      form.elements['monto'].value = money.format(Number(mov.valor || 0));
      form.elements['descripcion'].value = mov.descripcion || '';
      form.elements['fecha'].value = toDatetimeLocal(mov.fecha);
      form.elements['estado'].value = mov.estado || 'emitida';
      document.getElementById('editMovementDialog').showModal();
    }
    const delBtn = e.target.closest('[data-delete-movement]');
    if (delBtn) {
      deleteId = delBtn.dataset.deleteMovement;
      document.getElementById('deleteMovementDialog').showModal();
    }
  });

  document.getElementById('editMovementForm').addEventListener('submit', async e => {
    e.preventDefault();
    try {
      const form = e.target;
      const data = Object.fromEntries(new FormData(form).entries());
      data.monto = String(numberValue(data.monto));
      await api(`/dashboard/api/movimientos/${data.id}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
      document.getElementById('editMovementDialog').close();
      await loadMovements();
      await loadDashboard();
    } catch(err) { showNotice(err.message, 'error'); }
  });

  document.getElementById('confirmDeleteMovement').addEventListener('click', async () => {
    if (!deleteId) return;
    await api(`/dashboard/api/movimientos/${deleteId}`, { method:'DELETE' });
    document.getElementById('deleteMovementDialog').close();
    deleteId = null;
    await loadMovements();
    await loadDashboard();
  });

  document.querySelector('[data-filter-report]')?.addEventListener('click', loadMovements);
  ['desde','hasta'].forEach(id => document.getElementById(id)?.addEventListener('change', () => { updateReportExports(); loadMovements(); }));

  Promise.all([loadCategories('ingreso'), loadCategories('egreso')]).then(() => Promise.all([loadDashboard(), loadMovements()]));
})();

const menuToggle = document.getElementById("menuToggle");
const sidebar = document.querySelector(".sidebar");
const overlay = document.getElementById("menuOverlay");

menuToggle.addEventListener("click", () => {

  const isOpening = !sidebar.classList.contains("active");

  sidebar.classList.toggle("active");

  if(isOpening){
    setTimeout(() => {
      overlay.classList.add("active");
    }, 120);
  }else{
    overlay.classList.remove("active");
  }

});

overlay.addEventListener("click", () => {
  sidebar.classList.remove("active");
  overlay.classList.remove("active");
});

const menuLinks = document.querySelectorAll("[data-personal-section]");

menuLinks.forEach(link => {
  link.addEventListener("click", () => {
    sidebar.classList.remove("active");
    overlay.classList.remove("active");
  });
});