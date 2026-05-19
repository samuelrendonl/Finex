(function(){
  const money = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
  const currency = (value) => '$ ' + money.format(Math.max(0, Number(value || 0)));
  const digits = (value) => String(value || '').replace(/\D/g, '');
  const numberValue = (value) => Number(digits(value) || 0);

  function getAppAlertDialog(){
    let dialog = document.getElementById('appAlertDialog');
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.className = 'modal';
    dialog.id = 'appAlertDialog';
    dialog.innerHTML = '<div class="modal-content confirm-modal"><h2 data-app-alert-title>Aviso</h2><p data-app-alert-message></p><div class="form-actions"><button class="btn secondary" type="button" data-app-alert-cancel>Cancelar</button><button class="btn" type="button" data-app-alert-accept>Aceptar</button></div></div>';
    document.body.appendChild(dialog);
    return dialog;
  }

  function showAppAlert(message, options = {}){
    const dialog = getAppAlertDialog();
    const title = dialog.querySelector('[data-app-alert-title]');
    const text = dialog.querySelector('[data-app-alert-message]');
    const cancel = dialog.querySelector('[data-app-alert-cancel]');
    const accept = dialog.querySelector('[data-app-alert-accept]');
    const isConfirm = options.confirm === true;
    title.textContent = options.title || (isConfirm ? 'Confirmar acción' : 'Aviso');
    text.textContent = message || '';
    cancel.hidden = !isConfirm;
    accept.textContent = options.acceptText || 'Aceptar';
    cancel.textContent = options.cancelText || 'Cancelar';

    return new Promise((resolve) => {
      const finish = (result) => {
        accept.removeEventListener('click', onAccept);
        cancel.removeEventListener('click', onCancel);
        dialog.removeEventListener('cancel', onCancel);
        if (dialog.open) dialog.close();
        resolve(result);
      };
      const onAccept = () => finish(true);
      const onCancel = (event) => { if (event) event.preventDefault(); finish(false); };
      accept.addEventListener('click', onAccept);
      cancel.addEventListener('click', onCancel);
      dialog.addEventListener('cancel', onCancel);
      if (dialog.showModal) dialog.showModal();
      else dialog.setAttribute('open', '');
      accept.focus();
    });
  }

  const showAppConfirm = (message) => showAppAlert(message, { confirm: true, acceptText: 'Aceptar', cancelText: 'Cancelar' });

  function showNumericAlert(input){
    if (input.dataset.warned === '1') return;
    input.dataset.warned = '1';
    showAppAlert('Solo es permitido un dato numerico.');
    setTimeout(() => { input.dataset.warned = '0'; }, 700);
  }

  function formatIntInput(input){
    const before = input.value;
    const clean = digits(before);
    if (before && before !== clean && before.replace(/\./g,'') !== clean) showNumericAlert(input);
    input.value = clean ? money.format(Number(clean)) : '';
  }

  function bindFormattedInput(input){
    if (!input || input.dataset.boundFormat === '1') return;
    input.dataset.boundFormat = '1';
    formatIntInput(input);
    input.addEventListener('input', () => formatIntInput(input));
    input.addEventListener('paste', () => setTimeout(() => formatIntInput(input), 0));
  }
  document.querySelectorAll('[data-format-int]').forEach(bindFormattedInput);

  function fillFromSelect(select, map){
    const option = select.selectedOptions[0];
    if (!option) return;
    Object.entries(map).forEach(([dataName, targetSelector]) => {
      const target = document.querySelector(targetSelector);
      if (target) target.value = option.dataset[dataName] || '';
    });
  }

  document.querySelectorAll('[data-client-select]').forEach((select) => {
    const map = { email: select.dataset.targetEmail, telefono: select.dataset.targetPhone, direccion: select.dataset.targetAddress };
    select.addEventListener('change', () => {
      if (select.value === '__new_client__') {
        select.value = '';
        document.getElementById('quick-client-dialog')?.showModal();
        return;
      }
      fillFromSelect(select, map);
    });
    fillFromSelect(select, map);
  });

  document.querySelectorAll('[data-provider-select]').forEach((select) => {
    const map = { numero: select.dataset.targetNumber, email: select.dataset.targetEmail, telefono: select.dataset.targetPhone, direccion: select.dataset.targetAddress };
    select.addEventListener('change', () => {
      if (select.value === '__new_provider__') {
        select.value = '';
        document.getElementById('quick-provider-dialog')?.showModal();
        return;
      }
      fillFromSelect(select, map);
    });
    fillFromSelect(select, map);
  });


  document.addEventListener('submit', async (event) => {
    const form = event.target;
    const message = form?.dataset?.confirmMessage;
    if (!message) return;
    if (form.dataset.confirmedSubmit === '1') {
      form.dataset.confirmedSubmit = '';
      return;
    }
    event.preventDefault();
    const confirmed = await showAppConfirm(message);
    if (confirmed) {
      form.dataset.confirmedSubmit = '1';
      if (form.requestSubmit) form.requestSubmit();
      else form.submit();
    }
  });

  document.querySelectorAll('[data-open-dialog]').forEach((button) => {
    button.addEventListener('click', () => {
      const dialog = document.getElementById(button.dataset.openDialog);
      if (dialog && dialog.showModal) dialog.showModal();
    });
  });

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-open-logout]')) {
      const dialog = document.getElementById('logoutDialog');
      if (dialog && dialog.showModal) dialog.showModal();
    }
    if (event.target.matches('[data-close-dialog]')) {
      const dialog = event.target.closest('dialog');
      if (dialog) dialog.close();
    }
    if (!event.target.closest('[data-product-search-wrap]')) {
      document.querySelectorAll('[data-product-results]').forEach(box => { box.hidden = true; box.closest('.invoice-lines-card')?.classList.remove('search-open'); });
    }
  });

  let saleItems = [];
  let pendingItemRow = null;
  const itemsScript = document.getElementById('sale-items-data');
  if (itemsScript) {
    try { saleItems = JSON.parse(itemsScript.textContent || '[]'); } catch(e) { saleItems = []; }
  }

  function escapeHtml(text){
    return String(text || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c] || c));
  }
  function normalize(text){ return String(text || '').trim().toLowerCase(); }
  function findItem(text) {
    const t = normalize(text);
    if (!t) return null;
    return saleItems.find(item => normalize(item.label) === t || normalize(item.nombre) === t || normalize(item.codigo) === t) || null;
  }
  function matchingItems(text) {
    const t = normalize(text);
    if (!t) return saleItems.slice(0, 8);
    return saleItems.filter(item => {
      const hay = `${item.codigo || ''} ${item.nombre || ''} ${item.descripcion || ''}`.toLowerCase();
      return hay.includes(t);
    }).slice(0, 8);
  }

  function positionProductResults(row){
    const box = row?.querySelector('[data-product-results]');
    if (!box) return;
    // El listado queda exactamente debajo del campo Producto/Servicio.
    // No se calcula con coordenadas de pantalla para evitar que aparezca arriba o en medio del formulario.
    box.style.position = 'static';
    box.style.left = '';
    box.style.top = '';
    box.style.width = '100%';
    box.style.maxHeight = 'none';
  }

  function recalcLine(row){
    const price = numberValue(row.querySelector('[data-price]')?.value);
    const tax = numberValue(row.querySelector('[data-tax]')?.value);
    const qty = numberValue(row.querySelector('[data-quantity]')?.value);
    const subtotal = price * qty;
    const total = Math.round(subtotal + (subtotal * tax / 100));
    const totalCell = row.querySelector('[data-line-total]');
    if (totalCell) totalCell.textContent = currency(total);
    return total;
  }

  function recalcInvoice(form){
    if (!form) return;
    let total = 0;
    let subtotal = 0;
    let taxTotal = 0;
    form.querySelectorAll('[data-line-row]').forEach(row => {
      const price = numberValue(row.querySelector('[data-price]')?.value);
      const tax = numberValue(row.querySelector('[data-tax]')?.value);
      const qty = numberValue(row.querySelector('[data-quantity]')?.value);
      const sub = price * qty;
      const imp = Math.round(sub * tax / 100);
      subtotal += sub;
      taxTotal += imp;
      total += recalcLine(row);
    });
    const target = form.querySelector('[data-invoice-total]');
    const subTarget = form.querySelector('[data-invoice-subtotal]');
    const taxTarget = form.querySelector('[data-invoice-tax]');
    if (target) target.textContent = currency(total);
    if (subTarget) subTarget.textContent = currency(subtotal);
    if (taxTarget) taxTarget.textContent = currency(taxTotal);
  }

  function fillRowWithItem(row, item){
    if (!row || !item) return;
    const search = row.querySelector('.item-search');
    const hidden = row.querySelector('[data-item-id]');
    const price = row.querySelector('[data-price]');
    const tax = row.querySelector('[data-tax]');
    const desc = row.querySelector('[data-description]');
    if (search) { search.value = item.label || item.nombre || ''; search.dataset.selectedValue = search.value; }
    if (hidden) hidden.value = item.id;
    if (price) price.value = money.format(item.precio_unitario || 0);
    if (tax) tax.value = money.format(item.impuesto_porcentaje || 0);
    if (desc) desc.value = item.descripcion || item.nombre || '';
    recalcInvoice(row.closest('[data-invoice-form]'));
  }

  function showProductResults(row){
    const wrap = row.querySelector('[data-product-search-wrap]');
    const input = row.querySelector('.item-search');
    const box = row.querySelector('[data-product-results]');
    if (!wrap || !input || !box) return;
    const query = input.value;
    const matches = matchingItems(query);
    let html = '';
    const exact = findItem(query);
    if (!exact) {
      html += `<button type="button" class="product-option add-product" data-add-product><strong>+ Agregar producto/servicio</strong><small>${query ? 'Crear: ' + escapeHtml(query) : 'Crear un item nuevo'}</small></button>`;
    }
    matches.forEach(item => {
      html += `<button type="button" class="product-option" data-item-id="${item.id}"><strong>${escapeHtml(item.label || item.nombre)}</strong><small>${currency(item.precio_unitario)} · Imp. ${item.impuesto_porcentaje || 0}%</small></button>`;
    });
    box.innerHTML = html;
    box.hidden = false;
    box.closest('.invoice-lines-card')?.classList.add('search-open');
    positionProductResults(row);
  }

  function clearSelectedItemIfNeeded(row){
    const search = row.querySelector('.item-search');
    const hidden = row.querySelector('[data-item-id]');
    const exact = findItem(search?.value);
    if (exact) fillRowWithItem(row, exact);
    else {
      if (hidden) hidden.value = '';
      if (!String(search?.value || '').trim()) {
        const price = row.querySelector('[data-price]');
        const tax = row.querySelector('[data-tax]');
        const desc = row.querySelector('[data-description]');
        const note = row.querySelector('[data-note]');
        if (price) price.value = '0';
        if (tax) tax.value = '0';
        if (desc) desc.value = '';
        if (note) note.value = '';
        recalcInvoice(row.closest('[data-invoice-form]'));
      }
    }
  }

  function openQuickItemDialog(row){
    pendingItemRow = row;
    const dialog = document.getElementById('quick-item-dialog');
    if (!dialog || !dialog.showModal) return;
    const name = dialog.querySelector('input[name="nombre"]');
    const query = row?.querySelector('.item-search')?.value || '';
    if (name && query && !findItem(query)) name.value = query;
    dialog.showModal();
  }

  function handleProductOption(event){
    const productOption = event.target.closest('.product-option');
    if (!productOption) return;
    const row = productOption.closest('[data-line-row]');
    if (!row) return;
    event.preventDefault();
    if (productOption.matches('[data-add-product]')) {
      const box = row.querySelector('[data-product-results]');
      if (box) { box.hidden = true; box.closest('.invoice-lines-card')?.classList.remove('search-open'); }
      openQuickItemDialog(row);
      return;
    }
    if (productOption.dataset.itemId) {
      const item = saleItems.find(x => String(x.id) === String(productOption.dataset.itemId));
      fillRowWithItem(row, item);
      const box = row.querySelector('[data-product-results]');
      if (box) { box.hidden = true; box.closest('.invoice-lines-card')?.classList.remove('search-open'); }
    }
  }

  document.addEventListener('pointerdown', handleProductOption);

  document.addEventListener('click', (event) => {
    const option = event.target.closest('[data-item-id].product-option');
    if (option) {
      const row = option.closest('[data-line-row]');
      const item = saleItems.find(x => String(x.id) === String(option.dataset.itemId));
      fillRowWithItem(row, item);
      const box = row.querySelector('[data-product-results]');
      if (box) { box.hidden = true; box.closest('.invoice-lines-card')?.classList.remove('search-open'); }
      return;
    }
    const add = event.target.closest('[data-add-product]');
    if (add) {
      const row = add.closest('[data-line-row]');
      const box = row.querySelector('[data-product-results]');
      if (box) { box.hidden = true; box.closest('.invoice-lines-card')?.classList.remove('search-open'); }
      openQuickItemDialog(row);
    }
  });

  function bindLine(row){
    const search = row.querySelector('.item-search');
    const qty = row.querySelector('[data-quantity]');
    const price = row.querySelector('[data-price]');
    const tax = row.querySelector('[data-tax]');
    if (search) {
      search.dataset.selectedValue = search.value || '';
      search.addEventListener('focus', () => showProductResults(row));
      search.addEventListener('input', () => { clearSelectedItemIfNeeded(row); showProductResults(row); });
      search.addEventListener('keydown', () => setTimeout(() => positionProductResults(row), 0));
      search.addEventListener('blur', () => setTimeout(() => {
        const box = row.querySelector('[data-product-results]');
        if (box) { box.hidden = true; box.closest('.invoice-lines-card')?.classList.remove('search-open'); }
      }, 180));
    }
    [qty, price, tax].forEach(input => {
      if (!input) return;
      bindFormattedInput(input);
      input.addEventListener('input', () => { formatIntInput(input); recalcInvoice(row.closest('[data-invoice-form]')); });
    });
    const remove = row.querySelector('[data-remove-line]');
    if (remove) {
      remove.addEventListener('click', () => {
        const body = row.closest('[data-lines-body]');
        if (body.querySelectorAll('[data-line-row]').length > 1) row.remove();
        else {
          row.querySelectorAll('input').forEach((input) => {
            if (input.matches('[data-quantity]')) input.value = '1';
            else if (input.matches('[data-price],[data-tax]')) input.value = '0';
            else input.value = '';
          });
        }
        recalcInvoice(body.closest('[data-invoice-form]'));
      });
    }
  }

  function cloneLine(form){
    const body = form.querySelector('[data-lines-body]');
    const first = body.querySelector('[data-line-row]');
    const clone = first.cloneNode(true);
    clone.querySelectorAll('input').forEach((input) => {
      input.dataset.boundFormat = '';
      if (input.matches('[data-quantity]')) input.value = '1';
      else if (input.matches('[data-price],[data-tax]')) input.value = '0';
      else input.value = '';
    });
    const total = clone.querySelector('[data-line-total]');
    if (total) total.textContent = '$ 0';
    const results = clone.querySelector('[data-product-results]');
    if (results) { results.innerHTML = ''; results.hidden = true; }
    body.appendChild(clone);
    bindLine(clone);
    recalcInvoice(form);
  }

  document.querySelectorAll('[data-invoice-form]').forEach((form) => {
    form.querySelectorAll('[data-line-row]').forEach(bindLine);
    const addBtn = form.querySelector('[data-add-line]');
    if (addBtn) addBtn.addEventListener('click', () => cloneLine(form));
    form.addEventListener('submit', (event) => {
      let valid = false;
      form.querySelectorAll('[data-line-row]').forEach(row => {
        const hidden = row.querySelector('[data-item-id]');
        if (!hidden?.value) {
          const exact = findItem(row.querySelector('.item-search')?.value);
          if (exact) fillRowWithItem(row, exact);
        }
        if (row.querySelector('[data-item-id]')?.value && numberValue(row.querySelector('[data-quantity]')?.value) > 0) valid = true;
      });
      if (!valid) {
        event.preventDefault();
        showAppAlert('Agrega al menos un producto o servicio a la factura.');
      }
    });
    recalcInvoice(form);
  });

  window.addEventListener('scroll', () => {
    document.querySelectorAll('[data-product-results]:not([hidden])').forEach(box => positionProductResults(box.closest('[data-line-row]')));
  }, true);
  window.addEventListener('resize', () => {
    document.querySelectorAll('[data-product-results]:not([hidden])').forEach(box => positionProductResults(box.closest('[data-line-row]')));
  });

  document.querySelectorAll('[data-quick-item-form]').forEach(form => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      try {
        const response = await fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar el item.');
        saleItems.push(data.item);
        fillRowWithItem(pendingItemRow, data.item);
        const dialog = form.closest('dialog');
        if (dialog) dialog.close();
        form.reset();
        form.querySelectorAll('[data-format-int]').forEach(bindFormattedInput);
      } catch (err) {
        showAppAlert(err.message || 'No se pudo guardar el item.');
      }
    });
  });

  // Dashboard charts
  const tooltip = document.getElementById('globalTooltip');
  function showTip(text, event){
    if (!tooltip) return;
    tooltip.innerHTML = text;
    tooltip.hidden = false;
    tooltip.style.left = (event.clientX + 14) + 'px';
    tooltip.style.top = (event.clientY + 14) + 'px';
  }
  function hideTip(){ if (tooltip) tooltip.hidden = true; }

  function renderCharts(){
    const script = document.getElementById('dashboard-data');
    if (!script) return;
    let data;
    try { data = JSON.parse(script.textContent || '{}'); } catch(e){ return; }
    const labels = data.labels || {ventas:'Ventas', compras:'Compras', empty:'Registra movimientos'};
    renderMonthlyChart(data.monthly || [], labels);
    // Compatibilidad con el resumen circular antiguo si existe en alguna plantilla.
    renderDonutChart(data.totals || {ventas:0, compras:0}, labels);
    // Nuevas gráficas circulares separadas por categoría.
    renderCategoryDonut('donutIngresosChart', 'donutIngresosSummary', data.distribution_ingresos || [], 'Ingresos', '#2468f2');
    renderCategoryDonut('donutEgresosChart', 'donutEgresosSummary', data.distribution_egresos || [], 'Egresos', '#f4a62a');
  }
  window.FinexCharts = { renderCharts };

  function renderMonthlyChart(rows, labels){
    const target = document.getElementById('monthlyChart');
    if (!target) return;
    const w = 900, h = 310, padL = 62, padB = 42, padT = 20, padR = 20;
    const maxVal = Math.max(1, ...rows.map(r => Math.max(r.ventas || 0, r.compras || 0)));
    const plotH = h - padT - padB;
    const plotW = w - padL - padR;
    const group = plotW / Math.max(rows.length, 1);
    let svg = `<svg viewBox="0 0 ${w} ${h}" class="svg-chart" role="img">`;
    for (let i=0; i<=4; i++) {
      const y = padT + plotH - (plotH * i / 4);
      const val = Math.round(maxVal * i / 4);
      svg += `<line class="axis" x1="${padL}" y1="${y}" x2="${w-padR}" y2="${y}"></line>`;
      svg += `<text class="label" x="8" y="${y+4}">${currency(val)}</text>`;
    }
    rows.forEach((r, idx) => {
      const baseX = padL + idx * group + group * .22;
      const bw = Math.max(7, group * .18);
      const ventaH = (Number(r.ventas || 0) / maxVal) * plotH;
      const compraH = (Number(r.compras || 0) / maxVal) * plotH;
      const yV = padT + plotH - ventaH;
      const yC = padT + plotH - compraH;
      svg += `<rect class="bar bar-ventas" data-tip="<strong>${r.mes}</strong><br>${labels.ventas || 'Ventas'}: ${currency(r.ventas)}" x="${baseX}" y="${yV}" width="${bw}" height="${ventaH}" rx="5" fill="#2468f2"></rect>`;
      svg += `<rect class="bar bar-compras" data-tip="<strong>${r.mes}</strong><br>${labels.compras || 'Compras'}: ${currency(r.compras)}" x="${baseX+bw+5}" y="${yC}" width="${bw}" height="${compraH}" rx="5" fill="#f4a62a"></rect>`;
      svg += `<text class="label" x="${padL + idx * group + group*.38}" y="${h-14}" text-anchor="middle">${r.mes}</text>`;
    });
    svg += '</svg>';
    target.innerHTML = svg;
    target.querySelectorAll('[data-tip]').forEach(el => {
      el.addEventListener('mousemove', e => showTip(el.dataset.tip, e));
      el.addEventListener('mouseleave', hideTip);
    });
  }

  function donutSegment(cx, cy, r, startAngle, endAngle) {
    const start = polar(cx, cy, r, endAngle);
    const end = polar(cx, cy, r, startAngle);
    const large = endAngle - startAngle <= 180 ? 0 : 1;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 0 ${end.x} ${end.y}`;
  }
  function polar(cx, cy, r, angle) {
    const rad = (angle - 90) * Math.PI / 180.0;
    return {x: cx + (r * Math.cos(rad)), y: cy + (r * Math.sin(rad))};
  }
  function renderDonutChart(totals, labels){
    const target = document.getElementById('donutChart');
    const summary = document.getElementById('donutSummary');
    if (!target) return;
    const ventas = Number(totals.ventas || 0), compras = Number(totals.compras || 0), sum = ventas + compras;
    if (sum <= 0) {
      target.innerHTML = `<svg viewBox="0 0 260 260" class="svg-chart"><circle cx="130" cy="130" r="82" fill="none" stroke="#dbe4ef" stroke-width="34"></circle><text class="donut-center" x="130" y="126" text-anchor="middle">Sin datos</text><text class="label" x="130" y="148" text-anchor="middle">${labels.empty || 'Registra facturas'}</text></svg>`;
      if (summary) summary.innerHTML = `<div class="summary-row"><span>${labels.ventas || 'Ventas'}</span><strong>$ 0</strong></div><div class="summary-row"><span>${labels.compras || 'Compras'}</span><strong>$ 0</strong></div>`;
      return;
    }
    const vAngle = ventas / sum * 360;
    const cAngle = compras / sum * 360;
    let svg = `<svg viewBox="0 0 260 260" class="svg-chart" role="img">`;
    svg += `<path class="donut-segment" data-tip="<strong>${labels.ventas || 'Ventas'}</strong><br>${currency(ventas)}<br>${Math.round(ventas/sum*100)}% del total" d="${donutSegment(130,130,82,0,vAngle)}" fill="none" stroke="#2468f2" stroke-width="34" stroke-linecap="round"></path>`;
    if (compras > 0) svg += `<path class="donut-segment" data-tip="<strong>${labels.compras || 'Compras'}</strong><br>${currency(compras)}<br>${Math.round(compras/sum*100)}% del total" d="${donutSegment(130,130,82,vAngle,vAngle+cAngle)}" fill="none" stroke="#f4a62a" stroke-width="34" stroke-linecap="round"></path>`;
    svg += `<text class="donut-center" x="130" y="126" text-anchor="middle">${currency(sum)}</text><text class="label" x="130" y="148" text-anchor="middle">Total general</text></svg>`;
    target.innerHTML = svg;
    if (summary) summary.innerHTML = `<div class="summary-row"><span><span class="dot ventas"></span> ${labels.ventas || 'Ventas'}</span><strong>${currency(ventas)}</strong></div><div class="summary-row"><span><span class="dot compras"></span> ${labels.compras || 'Compras'}</span><strong>${currency(compras)}</strong></div>`;
    target.querySelectorAll('[data-tip]').forEach(el => {
      el.addEventListener('mousemove', e => showTip(el.dataset.tip, e));
      el.addEventListener('mouseleave', hideTip);
    });
  }


  function renderCategoryDonut(targetId, summaryId, rows, label, baseColor){
    const target = document.getElementById(targetId);
    const summary = document.getElementById(summaryId);
    if (!target) return;
    const palette = label === 'Ingresos'
      ? ['#2468f2','#16a34a','#06b6d4','#7c3aed','#0ea5e9','#22c55e','#1d4ed8','#14b8a6']
      : ['#f4a62a','#ef4444','#f97316','#eab308','#fb7185','#dc2626','#b45309','#f59e0b'];
    rows = (rows || []).filter(r => Number(r.total || 0) > 0);
    const sum = rows.reduce((acc, r) => acc + Number(r.total || 0), 0);
    if (sum <= 0) {
      target.innerHTML = `<svg viewBox="0 0 260 260" class="svg-chart"><circle cx="130" cy="130" r="82" fill="none" stroke="#dbe4ef" stroke-width="34"></circle><text class="donut-center" x="130" y="126" text-anchor="middle">Sin datos</text><text class="label" x="130" y="148" text-anchor="middle">Registra ${label.toLowerCase()}</text></svg>`;
      if (summary) summary.innerHTML = `<div class="summary-row"><span>${label}</span><strong>$ 0</strong></div>`;
      return;
    }
    let angle = 0;
    let svg = `<svg viewBox="0 0 260 260" class="svg-chart" role="img">`;
    rows.forEach((row, idx) => {
      const value = Number(row.total || 0);
      const next = angle + (value / sum * 360);
      const color = palette[idx % palette.length] || baseColor;
      const pct = Math.round(value / sum * 100);
      svg += `<path class="donut-segment" data-tip="<strong>${escapeHtml(row.categoria || 'Sin categoría')}</strong><br>${currency(value)}<br>${pct}% de ${label.toLowerCase()}" d="${donutSegment(130,130,82,angle,next)}" fill="none" stroke="${color}" stroke-width="34" stroke-linecap="round"></path>`;
      angle = next;
    });
    svg += `<text class="donut-center" x="130" y="126" text-anchor="middle">${currency(sum)}</text><text class="label" x="130" y="148" text-anchor="middle">${label}</text></svg>`;
    target.innerHTML = svg;
    if (summary) {
      summary.innerHTML = rows.map((row, idx) => {
        const value = Number(row.total || 0);
        const pct = Math.round(value / sum * 100);
        const color = palette[idx % palette.length] || baseColor;
        return `<div class="summary-row"><span><span class="dot" style="background:${color}"></span>${escapeHtml(row.categoria || 'Sin categoría')} <small>${pct}%</small></span><strong>${currency(value)}</strong></div>`;
      }).join('');
    }
    target.querySelectorAll('[data-tip]').forEach(el => {
      el.addEventListener('mousemove', e => showTip(el.dataset.tip, e));
      el.addEventListener('mouseleave', hideTip);
    });
  }

  renderCharts();
})();



const sidebar = document.getElementById("sidebar");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const sidebarOverlay = document.getElementById("sidebarOverlay");

if (mobileMenuBtn && sidebar && sidebarOverlay) {

  function openMenu() {
  sidebar.classList.add("active");
  sidebarOverlay.classList.add("active");
  document.body.classList.add("menu-open");

  mobileMenuBtn.classList.add("hidden");
  }

  function closeMenu() {
    sidebar.classList.remove("active");
    sidebarOverlay.classList.remove("active");
    document.body.classList.remove("menu-open");

    mobileMenuBtn.classList.remove("hidden");
  }

  mobileMenuBtn.addEventListener("click", openMenu);

  sidebarOverlay.addEventListener("click", closeMenu);

  /* CERRAR AL DAR CLICK EN UN MODULO */

  const menuLinks = sidebar.querySelectorAll("nav a");

  menuLinks.forEach(link => {

  link.addEventListener("click", () => {

    /* QUITAR ANIMACIONES */
    sidebar.style.transition = "none";
    sidebarOverlay.style.transition = "none";

    /* CERRAR INMEDIATAMENTE */
    sidebar.classList.remove("active");
    sidebarOverlay.classList.remove("active");

    document.body.classList.remove("menu-open");

    mobileMenuBtn.classList.remove("hidden");

  });

});

}