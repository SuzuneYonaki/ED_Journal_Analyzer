// Bio Log: every organism the CMDR has logged, across all systems (center-pane "biolog" view).
const bioLogState = { q: '', genus: new Set(), status: '', sort: 'found_desc', page: 1, limit: 100 };
let bioLogRequestSeq = 0;

function bioLogGenusLabel(genus) {
  return genus === 'Geology & Anomalies' ? t('biolog_geology') : genus;
}

function bioLogStageLabel(item) {
  if (item.is_completed) return `✅ ${t('biolog_stage_done')}`;
  return `⏳ ${item.stage}/3 ${t(item.stage === 2 ? 'biolog_stage_sample' : 'biolog_stage_log')}`;
}

function bioLogParams() {
  const p = new URLSearchParams({ sort: bioLogState.sort, page: bioLogState.page, limit: bioLogState.limit });
  if (bioLogState.q) p.set('q', bioLogState.q);
  if (bioLogState.status) p.set('status', bioLogState.status);
  if (bioLogState.genus.size) p.set('genus', [...bioLogState.genus].join(','));
  return p;
}

async function openBioLogEntry(item) {
  const modSettings = (typeof getModuleSettings === 'function') ? getModuleSettings() : {};
  state.currentView = modSettings.exobiology === false ? 'sysmap' : 'bio';
  if (typeof updateViewButtons === 'function') updateViewButtons();
  await selectSystem(item.system_address, false, false);
  const body = ((state.currentSystemData && state.currentSystemData.bodies) || []).find(b => b.body_id === item.body_id);
  if (body) {
    state.selectedBody = body;
    renderCurrentView();
    if (typeof renderBodyInspector === 'function') renderBodyInspector();
  }
}

async function loadBioLogResults() {
  const box = document.getElementById('biolog-results');
  if (!box) return;
  const seq = ++bioLogRequestSeq;
  let data;
  try {
    const resp = await fetch(`/api/bio_log?${bioLogParams().toString()}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    data = await resp.json();
  } catch (e) {
    if (seq === bioLogRequestSeq) box.innerHTML = `<div class="biolog-empty">${escapeHtml(t('biolog_error'))}</div>`;
    return;
  }
  if (seq !== bioLogRequestSeq || !document.getElementById('biolog-results')) return;

  const chips = data.genus_counts.map(g => {
    const active = bioLogState.genus.has(g.genus) ? ' active' : '';
    return `<button type="button" class="chip biolog-genus-chip${active}" data-genus="${escapeHtml(g.genus)}">${escapeHtml(bioLogGenusLabel(g.genus))} <span class="biolog-chip-count">${g.count}</span></button>`;
  }).join('');

  const rows = data.items.map((it, i) => {
    const found = (it.first_found_at || '').slice(0, 16).replace('T', ' ');
    const tip = `${t('biolog_first_bonus')}: ${formatCredits(it.first_discovery_value)}`;
    return `<tr class="biolog-row" data-idx="${i}">
      <td>${escapeHtml(found)}</td>
      <td class="biolog-species">${escapeHtml(it.species)}</td>
      <td>${escapeHtml(it.variant)}</td>
      <td>${escapeHtml(bioLogGenusLabel(it.genus))}</td>
      <td>${escapeHtml(it.star_system)}</td>
      <td>${escapeHtml(it.body_name)}</td>
      <td>${bioLogStageLabel(it)}</td>
      <td class="biolog-value" title="${escapeHtml(tip)}">${formatCredits(it.base_value)}</td>
    </tr>`;
  }).join('');

  const totalPages = Math.max(1, Math.ceil(data.total / data.limit));
  const s = data.summary;
  box.innerHTML = `
    <div class="biolog-genus-row">${chips}${bioLogState.genus.size ? `<button type="button" class="btn-page biolog-genus-clear">${t('filter_clear')}</button>` : ''}</div>
    <div class="biolog-summary">${t('biolog_summary', { entries: s.entries, species: s.species, systems: s.systems })}</div>
    ${data.items.length ? `
    <table class="biolog-table">
      <thead><tr>
        <th>${t('biolog_col_found')}</th><th>${t('biolog_col_species')}</th><th>${t('biolog_col_variant')}</th>
        <th>${t('biolog_col_genus')}</th><th>${t('biolog_col_system')}</th><th>${t('biolog_col_body')}</th>
        <th>${t('biolog_col_progress')}</th><th>${t('biolog_col_value')}</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <div class="biolog-pager">
      <button type="button" class="btn-page" id="biolog-prev" ${bioLogState.page <= 1 ? 'disabled' : ''}>${t('prev_page')}</button>
      <span>${bioLogState.page} / ${totalPages}</span>
      <button type="button" class="btn-page" id="biolog-next" ${bioLogState.page >= totalPages ? 'disabled' : ''}>${t('next_page')}</button>
    </div>` : `<div class="biolog-empty">${t('biolog_empty')}</div>`}`;

  box.querySelectorAll('.biolog-genus-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const g = chip.dataset.genus;
      if (bioLogState.genus.has(g)) bioLogState.genus.delete(g); else bioLogState.genus.add(g);
      bioLogState.page = 1;
      loadBioLogResults();
    });
  });
  const clearBtn = box.querySelector('.biolog-genus-clear');
  if (clearBtn) clearBtn.addEventListener('click', () => { bioLogState.genus.clear(); bioLogState.page = 1; loadBioLogResults(); });
  box.querySelectorAll('.biolog-row').forEach(tr => {
    tr.addEventListener('click', () => openBioLogEntry(data.items[Number(tr.dataset.idx)]));
  });
  const prev = document.getElementById('biolog-prev');
  const next = document.getElementById('biolog-next');
  if (prev) prev.addEventListener('click', () => { bioLogState.page -= 1; loadBioLogResults(); });
  if (next) next.addEventListener('click', () => { bioLogState.page += 1; loadBioLogResults(); });
}

function renderBioLogView(container) {
  container.classList.remove('is-sysmap');
  const statusChip = (value, key) =>
    `<button type="button" class="chip biolog-status-chip${bioLogState.status === value ? ' active' : ''}" data-status="${value}">${t(key)}</button>`;
  const sortOption = (value, key) =>
    `<option value="${value}"${bioLogState.sort === value ? ' selected' : ''}>${t(key)}</option>`;

  container.innerHTML = `
    <div class="biolog-wrap">
      <div class="biolog-toolbar">
        <input type="text" id="biolog-search" class="search-input" value="${escapeHtml(bioLogState.q)}" placeholder="${escapeHtml(t('biolog_search_placeholder'))}">
        <div class="biolog-status-row">
          ${statusChip('', 'biolog_status_all')}${statusChip('completed', 'biolog_status_completed')}${statusChip('in_progress', 'biolog_status_in_progress')}
        </div>
        <select id="biolog-sort" class="sort-select">
          ${sortOption('found_desc', 'biolog_sort_found_desc')}${sortOption('found_asc', 'biolog_sort_found_asc')}
          ${sortOption('value_desc', 'biolog_sort_value')}${sortOption('species', 'biolog_sort_species')}${sortOption('system', 'biolog_sort_system')}
        </select>
      </div>
      <div id="biolog-results"></div>
    </div>`;

  let timer = null;
  document.getElementById('biolog-search').addEventListener('input', (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => { bioLogState.q = e.target.value.trim(); bioLogState.page = 1; loadBioLogResults(); }, 250);
  });
  document.getElementById('biolog-sort').addEventListener('change', (e) => {
    bioLogState.sort = e.target.value; bioLogState.page = 1; loadBioLogResults();
  });
  container.querySelectorAll('.biolog-status-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      bioLogState.status = chip.dataset.status;
      container.querySelectorAll('.biolog-status-chip').forEach(c => c.classList.toggle('active', c === chip));
      bioLogState.page = 1;
      loadBioLogResults();
    });
  });
  loadBioLogResults();
}

window.renderBioLogView = renderBioLogView;
