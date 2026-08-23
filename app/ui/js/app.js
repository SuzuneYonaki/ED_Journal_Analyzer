// State management
let state = {
  systems: [],
  selectedSystem: null,
  selectedBody: null,
  currentSystemData: null,
  currentView: 'tree', // 'tree', 'flat', 'visits'
  searchQuery: '',
  filters: {
    has_elw: false,
    has_water_world: false,
    has_ammonia: false,
    has_terraformable: false,
    has_bio: false,
    has_first_discover: false,
    has_high_g: false,
    has_anomalies: false
  },
  sortBy: 'total_potential_value',
  sortOrder: 'desc',
  sortBy2: null,
  sortOrder2: 'desc',
  datePreset: 'all',
  dateFrom: '',
  dateTo: '',
  dateField: 'last_visited',
  bodySortBy: 'distance',
  bodySortOrder: 'asc',
  page: 1,
  limit: 50,
  totalPages: 1
};

// Utilities
function formatCredits(num) {
  if (!num) return '0 Cr';
  return Number(num).toLocaleString() + ' Cr';
}

function formatNumber(num, digits = 2) {
  if (num === null || num === undefined) return '--';
  return Number(num).toLocaleString(undefined, { maximumFractionDigits: digits });
}

function formatDistance(ls) {
  if (ls === null || ls === undefined) return '--';
  if (ls < 1) return (ls * 299792).toFixed(0) + ' km';
  if (ls > 1000000) return (ls / 1000000).toFixed(2) + ' M ls';
  return ls.toLocaleString(undefined, { maximumFractionDigits: 1 }) + ' ls';
}

function formatSecondsToDaysOrHours(sec) {
  if (!sec) return '--';
  const hours = Math.abs(sec) / 3600;
  if (hours < 48) return `${hours.toFixed(1)} ${t('hours_unit')}`;
  const days = hours / 24;
  return `${days.toFixed(1)} ${t('days_unit')}`;
}

function getStarTypeStyle(starType) {
  if (!starType) return { bg: '#181e2b', text: '#e6edf3', border: '#2a3449' };
  const st = starType.toUpperCase();

  // Black Hole
  if (st === 'H' || st.includes('BLACKHOLE')) {
    return { bg: '#050508', text: '#d8b4fe', border: '#a855f7' };
  }
  // Neutron Star
  if (st === 'N') {
    return { bg: '#00f2fe', text: '#02101e', border: '#38ef7d' };
  }
  // White Dwarf
  if (st.startsWith('D')) {
    return { bg: '#e0f2fe', text: '#0c4a6e', border: '#38bdf8' };
  }
  // Wolf-Rayet
  if (st.startsWith('W')) {
    return { bg: '#ec4899', text: '#022c22', border: '#f472b6' };
  }
  // Carbon stars
  if (st.startsWith('C') || st.startsWith('MS') || st.startsWith('S')) {
    return { bg: '#7f1d1d', text: '#67e8f9', border: '#dc2626' };
  }
  // Main sequence / Giants
  if (st.startsWith('O')) {
    return { bg: '#2563eb', text: '#fde047', border: '#60a5fa' }; // Blue -> Yellow text
  }
  if (st.startsWith('B')) {
    return { bg: '#60a5fa', text: '#0f172a', border: '#93c5fd' }; // Blue-white -> Dark text
  }
  if (st.startsWith('A')) {
    return { bg: '#f8fafc', text: '#020617', border: '#cbd5e1' }; // White -> Black text
  }
  if (st.startsWith('F')) {
    return { bg: '#fef08a', text: '#1e1b4b', border: '#fde047' }; // Yellow-white -> Navy text
  }
  if (st.startsWith('G')) {
    return { bg: '#eab308', text: '#0f172a', border: '#facc15' }; // Yellow -> Dark text
  }
  if (st.startsWith('K')) {
    return { bg: '#f97316', text: '#082f49', border: '#fb923c' }; // Orange -> Dark cyan text
  }
  if (st.startsWith('M')) {
    return { bg: '#dc2626', text: '#f0fdf4', border: '#ef4444' }; // Red -> White/Mint text
  }
  // Brown dwarfs
  if (st.startsWith('L')) {
    return { bg: '#9a3412', text: '#e0f2fe', border: '#c2410c' }; // Brown-red -> Light blue text
  }
  if (st.startsWith('T')) {
    return { bg: '#581c87', text: '#fde047', border: '#7e22ce' }; // Brown-purple -> Yellow text
  }
  if (st.startsWith('Y')) {
    return { bg: '#3b0764', text: '#4ade80', border: '#6b21a8' }; // Dark violet -> Light green text
  }

  return { bg: '#334155', text: '#f8fafc', border: '#64748b' };
}

function getBodyIconClass(body) {
  if (body.star_type) {
    const st = body.star_type.toUpperCase();
    if (st === 'H' || st === 'SUPERMASSIVEBLACKHOLE') return 'icon-black-hole';
    if (st === 'N') return 'icon-neutron';
    return 'icon-star';
  }
  const pc = (body.planet_class || '').toLowerCase();
  if (pc.includes('earthlike') || pc.includes('earth-like')) return 'icon-elw';
  if (pc.includes('ammonia')) return 'icon-ammonia';
  if (pc.includes('water world')) return 'icon-water';
  if (pc.includes('high metal') || pc.includes('metal rich')) return 'icon-hmc';
  if (pc.includes('rocky')) return 'icon-rocky';
  if (pc.includes('icy')) return 'icon-icy';
  if (pc.includes('gas giant')) return 'icon-gas';
  return 'icon-rocky';
}

function getBodyIconLabel(body) {
  if (body.star_type) return body.star_type;
  const pc = (body.planet_class || '').toLowerCase();
  if (pc.includes('earthlike')) return 'ELW';
  if (pc.includes('water world')) return 'WW';
  if (pc.includes('ammonia')) return 'AW';
  if (pc.includes('high metal')) return 'HMC';
  if (pc.includes('gas giant')) return 'GG';
  if (pc.includes('rocky')) return 'R';
  if (pc.includes('icy')) return 'I';
  return 'P';
}

// I18n UI Update
function updateStaticTexts() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (key) {
      if (el.tagName === 'INPUT') {
        el.placeholder = t(key);
      } else {
        el.innerText = t(key);
      }
    }
  });

  // Update language buttons
  const btnJa = document.getElementById('btn-lang-ja');
  const btnEn = document.getElementById('btn-lang-en');
  if (btnJa && btnEn) {
    btnJa.classList.toggle('active', currentLang === 'ja');
    btnEn.classList.toggle('active', currentLang === 'en');
  }

  // Re-render dynamic components with translated labels
  renderSystemList();
  renderSystemHeader();
  renderCurrentView();
  renderBodyInspector();
}

// API Calls
async function fetchGlobalStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('stat-systems').innerText = Number(data.total_systems).toLocaleString();
    document.getElementById('stat-bodies').innerText = Number(data.total_bodies).toLocaleString();
    document.getElementById('stat-elw').innerText = Number(data.elw_systems).toLocaleString();
    if (document.getElementById('stat-ww')) {
      document.getElementById('stat-ww').innerText = Number(data.ww_systems || 0).toLocaleString();
    }
    document.getElementById('stat-ammonia').innerText = Number(data.ammonia_systems).toLocaleString();
    const bioSysCount = Number(data.bio_systems || 0).toLocaleString();
    const bioSigCount = Number(data.total_bio_signals || 0).toLocaleString();
    document.getElementById('stat-bio').innerText = `${bioSysCount} (${bioSigCount} Sig)`;
    document.getElementById('stat-total-payout').innerText = formatCredits(data.total_potential_value);
  } catch (err) {
    console.error('Failed to fetch stats:', err);
  }
}

async function fetchSystems() {
  const params = new URLSearchParams({
    q: state.searchQuery,
    sort_by: state.sortBy,
    sort_order: state.sortOrder,
    page: state.page,
    limit: state.limit
  });

  if (state.sortBy2 && state.sortBy2 !== 'none') {
    params.append('sort_by_2', state.sortBy2);
    params.append('sort_order_2', state.sortOrder2);
  }

  if (state.dateFrom) {
    params.append('date_from', state.dateFrom);
  }
  if (state.dateTo) {
    params.append('date_to', state.dateTo);
  }
  if (state.dateField) {
    params.append('date_field', state.dateField);
  }

  Object.entries(state.filters).forEach(([k, v]) => {
    if (v) params.append(k, 'true');
  });

  try {
    const res = await fetch(`/api/systems?${params.toString()}`);
    const data = await res.json();
    state.systems = data.systems;
    state.totalPages = Math.ceil(data.total / state.limit) || 1;
    renderSystemList();
    renderPagination(data.total);
  } catch (err) {
    console.error('Failed to fetch systems:', err);
  }
}

async function selectSystem(systemAddress) {
  try {
    const res = await fetch(`/api/system/${systemAddress}`);
    const data = await res.json();
    state.currentSystemData = data;
    state.selectedSystem = data.system;
    
    // Auto select first body
    if (data.bodies && data.bodies.length > 0) {
      state.selectedBody = data.bodies[0];
    } else {
      state.selectedBody = null;
    }

    renderSystemHeader();
    renderCurrentView();
    renderBodyInspector();
    highlightSelectedSystemCard();
  } catch (err) {
    console.error('Failed to select system:', err);
  }
}

// Rendering
function renderSystemList() {
  const container = document.getElementById('system-list');
  container.innerHTML = '';

  if (state.systems.length === 0) {
    container.innerHTML = `<div style="color: var(--text-secondary); text-align: center; padding: 20px;">${t('no_systems')}</div>`;
    return;
  }

  state.systems.forEach(sys => {
    const card = document.createElement('div');
    card.className = `system-card ${state.selectedSystem && state.selectedSystem.system_address === sys.system_address ? 'selected' : ''}`;
    card.dataset.sysAddr = sys.system_address;
    card.onclick = () => selectSystem(sys.system_address);

    const tags = [];
    if (sys.has_first_discover || sys.first_discovered_bodies > 0) {
      tags.push(`<span class="tag-badge tag-first-disc">⭐ 1st Disc (${sys.first_discovered_bodies || 'Yes'})</span>`);
    }
    if (sys.has_elw) tags.push('<span class="tag-badge tag-elw">ELW</span>');
    if (sys.has_water_world) tags.push('<span class="tag-badge tag-ww">WW</span>');
    if (sys.has_ammonia) tags.push('<span class="tag-badge tag-ammonia">Ammonia</span>');
    if (sys.has_terraformable) tags.push('<span class="tag-badge tag-tf">TF</span>');
    if (sys.total_bio_signals > 0) tags.push(`<span class="tag-badge tag-bio">BIO: ${sys.total_bio_signals}</span>`);
    else if (sys.has_bio) tags.push('<span class="tag-badge tag-bio">BIO</span>');
    if (sys.sol_distance_ly > 0) tags.push(`<span class="tag-badge tag-sol-dist">Sol: ${Math.round(sys.sol_distance_ly).toLocaleString()} Ly</span>`);
    if (sys.has_high_g) tags.push('<span class="tag-badge tag-high-g">High-G</span>');
    if (sys.has_anomalies) tags.push('<span class="tag-badge tag-anomaly">Rare/Orbit</span>');

    const visitedDate = sys.last_visited ? sys.last_visited.substring(0, 10) : '--';
    let mainStar = '';
    if (sys.main_star_type) {
      const style = getStarTypeStyle(sys.main_star_type);
      mainStar = `<span class="tag-badge" style="background: ${style.bg}; color: ${style.text}; border: 1px solid ${style.border}; margin-left: 6px; font-weight: bold;">${sys.main_star_type}</span>`;
    }

    card.innerHTML = `
      <div class="system-card-header">
        <span class="system-card-title">${sys.star_system}</span>
        <span class="system-card-value">${formatCredits(sys.total_potential_value)}</span>
      </div>
      <div class="system-card-meta">
        <span>${t('bodies_count')}: ${sys.scanned_bodies} / ${sys.total_bodies || '?'}${mainStar}</span>
        <span>${t('visited_meta')}: ${visitedDate} (${sys.visit_count}${t('times')})</span>
      </div>
      <div class="system-card-tags">
        ${tags.join('')}
      </div>
    `;

    container.appendChild(card);
  });
}

function highlightSelectedSystemCard() {
  document.querySelectorAll('.system-card').forEach(card => {
    if (state.selectedSystem && card.dataset.sysAddr == state.selectedSystem.system_address) {
      card.classList.add('selected');
    } else {
      card.classList.remove('selected');
    }
  });
}

function renderPagination(totalCount) {
  document.getElementById('page-info').innerText = `${state.page} / ${state.totalPages} (${totalCount})`;
  document.getElementById('btn-prev-page').disabled = state.page <= 1;
  document.getElementById('btn-next-page').disabled = state.page >= state.totalPages;
}

function renderSystemHeader() {
  if (!state.selectedSystem) return;
  const sys = state.selectedSystem;
  document.getElementById('current-system-name').innerText = sys.star_system;
  
  const coords = (sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
    ? `[ ${sys.star_pos_x.toFixed(1)}, ${sys.star_pos_y.toFixed(1)}, ${sys.star_pos_z.toFixed(1)} ]`
    : '';
  document.getElementById('current-system-coords').innerText = coords;
  document.getElementById('current-system-fss-value').innerText = formatCredits(sys.total_fss_value || 0);
  document.getElementById('current-system-value').innerText = formatCredits(sys.total_potential_value || 0);
  
  const totalB = sys.total_bodies || sys.scanned_bodies || 0;
  document.getElementById('body-count-badge').innerText = `${t('scanned_badge')}: ${sys.scanned_bodies} / ${totalB}`;
}

function getSortedBodies(bodies) {
  if (!bodies) return [];
  const list = [...bodies];
  const by = state.bodySortBy;
  const order = state.bodySortOrder;

  list.sort((a, b) => {
    let valA = 0, valB = 0;
    if (by === 'value') {
      valA = a.max_potential_value || a.fss_value || 0;
      valB = b.max_potential_value || b.fss_value || 0;
    } else if (by === 'bio') {
      valA = a.bio_signals || 0;
      valB = b.bio_signals || 0;
    } else if (by === 'gravity') {
      valA = a.surface_gravity_g || 0;
      valB = b.surface_gravity_g || 0;
    } else { // distance
      valA = a.distance_from_arrival_ls || 0;
      valB = b.distance_from_arrival_ls || 0;
    }

    if (order === 'asc') return valA - valB;
    return valB - valA;
  });
  return list;
}

function renderCurrentView() {
  const container = document.getElementById('map-content');
  container.innerHTML = '';

  if (!state.currentSystemData) return;

  if (state.currentView === 'tree') {
    renderHierarchyTree(container, state.currentSystemData.hierarchy);
  } else if (state.currentView === 'flat') {
    const sorted = getSortedBodies(state.currentSystemData.bodies);
    renderFlatBodiesList(container, sorted);
  } else if (state.currentView === 'visits') {
    renderVisitsTimeline(container, state.currentSystemData.visits);
  }
}

function renderHierarchyTree(container, nodes) {
  if (!nodes || nodes.length === 0) {
    container.innerHTML = `<div style="color: var(--text-secondary); text-align: center;">${t('no_bodies')}</div>`;
    return;
  }

  function createNodeElement(node) {
    const nodeWrapper = document.createElement('div');
    nodeWrapper.className = 'tree-node';

    const card = document.createElement('div');
    card.className = `node-card ${state.selectedBody && state.selectedBody.body_id === node.body_id ? 'selected' : ''}`;
    card.dataset.bodyId = node.body_id;
    card.onclick = (e) => {
      e.stopPropagation();
      state.selectedBody = node;
      renderBodyInspector();
      document.querySelectorAll('.node-card').forEach(nc => nc.classList.remove('selected'));
      card.classList.add('selected');
    };

    const iconClass = getBodyIconClass(node);
    const iconLabel = getBodyIconLabel(node);

    const badges = [];
    if (node.landable) badges.push('<span class="tag-badge tag-landable">LANDABLE</span>');
    
    // High-G only shown when Landable is true
    if (node.landable && node.surface_gravity_g) {
      if (node.surface_gravity_g >= 3.0) badges.push(`<span class="tag-badge tag-high-g">${node.surface_gravity_g.toFixed(2)}G !</span>`);
      else if (node.surface_gravity_g >= 1.5) badges.push(`<span class="tag-badge" style="background: rgba(255,113,0,0.2); color: var(--ed-orange);">${node.surface_gravity_g.toFixed(2)}G</span>`);
      else badges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.1);">${node.surface_gravity_g.toFixed(2)}G</span>`);
    }

    if (node.bio_signals > 0) badges.push(`<span class="tag-badge tag-bio">BIO: ${node.bio_signals}</span>`);
    if (node.geo_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(255,113,0,0.2); color: var(--ed-orange);">GEO: ${node.geo_signals}</span>`);
    if (node.anomalies && node.anomalies.length > 0) {
      node.anomalies.forEach(a => badges.push(`<span class="tag-badge tag-anomaly">${a.tag}</span>`));
    }

    const typeDesc = node.star_type ? `${t('star_type_label')} (${node.star_type})` : (node.planet_class || 'Planet');

    card.innerHTML = `
      <div class="node-info-left">
        <div class="body-icon ${iconClass}">${iconLabel}</div>
        <div class="node-details">
          <div class="node-name">${node.body_name}</div>
          <div class="node-subtext">${typeDesc}</div>
          <div class="node-badges">${badges.join('')}</div>
        </div>
      </div>
      <div class="node-info-right">
        <span class="node-value">${formatCredits(node.max_potential_value || node.fss_value)}</span>
        <span class="node-distance">${formatDistance(node.distance_from_arrival_ls)}</span>
      </div>
    `;

    nodeWrapper.appendChild(card);

    if (node.children && node.children.length > 0) {
      const childrenWrapper = document.createElement('div');
      childrenWrapper.className = 'node-children';
      node.children.forEach(child => {
        childrenWrapper.appendChild(createNodeElement(child));
      });
      nodeWrapper.appendChild(childrenWrapper);
    }

    return nodeWrapper;
  }

  nodes.forEach(rootNode => {
    container.appendChild(createNodeElement(rootNode));
  });
}

function renderFlatBodiesList(container, bodies) {
  if (!bodies || bodies.length === 0) {
    container.innerHTML = `<div style="color: var(--text-secondary); text-align: center;">${t('no_bodies')}</div>`;
    return;
  }

  const list = document.createElement('div');
  list.style.display = 'flex';
  list.style.flexDirection = 'column';
  list.style.gap = '8px';

  bodies.forEach(body => {
    const card = document.createElement('div');
    card.className = `node-card ${state.selectedBody && state.selectedBody.body_id === body.body_id ? 'selected' : ''}`;
    card.onclick = () => {
      state.selectedBody = body;
      renderBodyInspector();
      document.querySelectorAll('.node-card').forEach(nc => nc.classList.remove('selected'));
      card.classList.add('selected');
    };

    const iconClass = getBodyIconClass(body);
    const iconLabel = getBodyIconLabel(body);

    const badges = [];
    if (body.landable) badges.push('<span class="tag-badge tag-landable">LANDABLE</span>');
    if (body.landable && body.surface_gravity_g) {
      if (body.surface_gravity_g >= 3.0) badges.push(`<span class="tag-badge tag-high-g">${body.surface_gravity_g.toFixed(2)}G !</span>`);
      else badges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.1);">${body.surface_gravity_g.toFixed(2)}G</span>`);
    }
    if (body.bio_signals > 0) badges.push(`<span class="tag-badge tag-bio">BIO: ${body.bio_signals}</span>`);

    card.innerHTML = `
      <div class="node-info-left">
        <div class="body-icon ${iconClass}">${iconLabel}</div>
        <div class="node-details">
          <div class="node-name">${body.body_name}</div>
          <div class="node-subtext">${body.star_type ? t('star_type_label') + ' ' + body.star_type : body.planet_class || 'Body'}</div>
          <div class="node-badges">${badges.join('')}</div>
        </div>
      </div>
      <div class="node-info-right">
        <span class="node-value">${formatCredits(body.max_potential_value)}</span>
        <span class="node-distance">${formatDistance(body.distance_from_arrival_ls)}</span>
      </div>
    `;
    list.appendChild(card);
  });

  container.appendChild(list);
}

function renderVisitsTimeline(container, visits) {
  if (!visits || visits.length === 0) {
    container.innerHTML = `<div style="color: var(--text-secondary); text-align: center;">${t('no_visits')}</div>`;
    return;
  }

  const list = document.createElement('div');
  list.style.display = 'flex';
  list.style.flexDirection = 'column';
  list.style.gap = '10px';

  visits.forEach(v => {
    const item = document.createElement('div');
    item.style.background = 'var(--bg-card)';
    item.style.border = '1px solid var(--border-color)';
    item.style.borderRadius = '6px';
    item.style.padding = '10px 14px';
    item.style.display = 'flex';
    item.style.justifyContent = 'space-between';
    item.style.alignItems = 'center';

    item.innerHTML = `
      <div>
        <div style="font-family: var(--font-mono); font-weight: bold; color: var(--ed-orange);">${v.timestamp}</div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px;">
          ${v.ship ? t('ship_label') + ': ' + v.ship : ''} ${v.is_taxi ? '(Apex Taxi)' : ''}
        </div>
      </div>
      <div style="text-align: right; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-primary);">
        <div>${t('jump_dist')}: ${v.jump_dist ? v.jump_dist.toFixed(2) + ' Ly' : '--'}</div>
        <div style="font-size: 0.72rem; color: var(--text-secondary);">${t('fuel_used')}: ${v.fuel_used ? v.fuel_used.toFixed(2) + ' t' : '--'}</div>
      </div>
    `;
    list.appendChild(item);
  });

  container.appendChild(list);
}

function renderBodyInspector() {
  const inspectorContent = document.getElementById('inspector-content');
  if (!state.selectedBody) {
    inspectorContent.style.display = 'none';
    document.getElementById('inspect-body-name').innerText = t('inspector_title');
    document.getElementById('inspect-body-type').innerText = t('inspector_subtitle');
    return;
  }

  inspectorContent.style.display = 'block';
  const b = state.selectedBody;

  document.getElementById('inspect-body-name').innerText = b.body_name;
  document.getElementById('inspect-body-type').innerText = b.star_type 
    ? `${t('star_type_label')}: ${b.star_type}` 
    : `${b.planet_class || 'Body'}${b.terraforming_state ? ' [' + b.terraforming_state + ']' : ''}`;

  // Anomalies
  const anomSection = document.getElementById('section-anomalies');
  const anomTags = document.getElementById('inspect-anomaly-tags');
  if (b.anomalies && b.anomalies.length > 0) {
    anomSection.style.display = 'block';
    anomTags.innerHTML = b.anomalies.map(a => `
      <div class="tag-badge tag-anomaly" title="${a.desc}" style="padding: 4px 8px; font-size: 0.75rem;">
        ★ ${a.tag}: ${a.desc}
      </div>
    `).join('');
  } else {
    anomSection.style.display = 'none';
  }

  // Value Breakdown
  document.getElementById('val-fss').innerText = formatCredits(b.fss_value);
  document.getElementById('val-dss').innerText = formatCredits(b.dss_value);
  document.getElementById('val-fd-fss').innerText = formatCredits(b.first_discovered_fss);
  document.getElementById('val-fm-dss').innerText = formatCredits(b.first_mapped_dss);
  document.getElementById('val-max-total').innerText = formatCredits(b.max_potential_value);

  // Exobiology Predictions
  const bioInfo = document.getElementById('inspect-bio-signals-info');
  const bioContainer = document.getElementById('inspect-bio-predictions');
  if (b.bio_signals > 0 || (b.exobiology && b.exobiology.length > 0)) {
    bioInfo.innerText = `${t('bio_signals_detected')}: ${b.bio_signals || 0} / ${t('bio_species_candidates')}`;
    if (b.exobiology && b.exobiology.length > 0) {
      bioContainer.innerHTML = b.exobiology.map(bio => `
        <div class="bio-pred-card">
          <div class="bio-pred-header">
            <span class="bio-species-name">🌱 ${bio.species} (${bio.genus})</span>
            <span class="bio-sample-dist">${t('bio_dist_req')} ${bio.colony_distance_m}m</span>
          </div>
          <div style="font-size: 0.72rem; color: var(--text-secondary); margin-bottom: 4px;">${bio.description}</div>
          <div class="bio-payout-row">
            <span>${t('bio_base_payout')} ${formatCredits(bio.base_value)}</span>
            <span class="bio-first-bonus">${t('bio_first_bonus')} ${formatCredits(bio.first_discovery_value)}</span>
          </div>
        </div>
      `).join('');
    } else {
      bioContainer.innerHTML = `<div style="font-size: 0.75rem; color: var(--text-secondary);">${t('bio_none_desc')}</div>`;
    }
  } else {
    bioInfo.innerText = t('bio_none');
    bioContainer.innerHTML = `<div style="font-size: 0.75rem; color: var(--text-dim);">${t('bio_none_desc')}</div>`;
  }

  // Surface & Landable
  const landableEl = document.getElementById('prop-landable');
  if (b.landable) {
    landableEl.innerText = t('landable_yes');
    landableEl.className = 'prop-val landable';
  } else {
    landableEl.innerText = t('landable_no');
    landableEl.className = 'prop-val';
  }

  const gravEl = document.getElementById('prop-gravity');
  if (b.surface_gravity_g !== null && b.surface_gravity_g !== undefined) {
    const gVal = b.surface_gravity_g;
    gravEl.innerText = `${gVal.toFixed(3)} G (${(b.surface_gravity || 0).toFixed(1)} m/s²)`;
    
    // High-G warning only for landable bodies
    if (b.landable) {
      if (gVal >= 3.0) {
        gravEl.className = 'prop-val danger';
        gravEl.innerText += ` ${t('extreme_danger')}`;
      } else if (gVal >= 1.5) {
        gravEl.className = 'prop-val warning';
        gravEl.innerText += ` ${t('high_g_warn')}`;
      } else {
        gravEl.className = 'prop-val';
      }
    } else {
      gravEl.className = 'prop-val';
    }
  } else {
    gravEl.innerText = '--';
    gravEl.className = 'prop-val';
  }

  document.getElementById('prop-temperature').innerText = b.surface_temperature ? `${b.surface_temperature.toFixed(0)} K (${(b.surface_temperature - 273.15).toFixed(0)} °C)` : '--';
  document.getElementById('prop-pressure').innerText = b.surface_pressure ? `${b.surface_pressure.toFixed(3)} atm` : (b.atmosphere ? 'Thin Atmosphere' : 'None (Vacuum)');
  document.getElementById('prop-atmosphere').innerText = b.atmosphere || 'None';
  document.getElementById('prop-volcanism').innerText = b.volcanism || 'None';

  // Orbit parameters
  document.getElementById('prop-semi-major').innerText = b.semi_major_axis ? `${(b.semi_major_axis / 149597870700).toFixed(3)} AU (${formatDistance(b.semi_major_axis / 299792458)})` : '--';
  
  const eccEl = document.getElementById('prop-eccentricity');
  if (b.eccentricity !== null && b.eccentricity !== undefined) {
    eccEl.innerText = b.eccentricity.toFixed(4);
    if (b.eccentricity >= 0.8) eccEl.className = 'prop-val warning';
    else eccEl.className = 'prop-val';
  } else {
    eccEl.innerText = '--';
  }

  document.getElementById('prop-orbital-period').innerText = formatSecondsToDaysOrHours(b.orbital_period);
  document.getElementById('prop-rotation-period').innerText = formatSecondsToDaysOrHours(b.rotation_period);
  document.getElementById('prop-inclination').innerText = b.orbital_inclination !== null && b.orbital_inclination !== undefined ? `${b.orbital_inclination.toFixed(2)}°` : '--';
  document.getElementById('prop-tidal-lock').innerText = b.tidal_lock ? t('tidal_locked_yes') : t('tidal_locked_no');

  // Rings
  const ringsSection = document.getElementById('section-rings');
  const ringsList = document.getElementById('inspect-rings-list');
  if (b.rings_list && b.rings_list.length > 0) {
    ringsSection.style.display = 'block';
    ringsList.innerHTML = b.rings_list.map(r => `
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 4px; padding: 6px 10px; margin-bottom: 6px; font-size: 0.75rem;">
        <div style="font-weight: bold; color: var(--ed-gold);">${r.Name || 'Ring'}</div>
        <div style="color: var(--text-secondary); margin-top: 2px;">Type: ${r.RingClass ? r.RingClass.replace('eRingClass_', '') : '--'}</div>
        <div style="color: var(--text-secondary);">Outer: ${(r.OuterRad / 1000).toLocaleString()} km / Mass: ${(r.MassMT || 0).toLocaleString()} MT</div>
      </div>
    `).join('');
  } else {
    ringsSection.style.display = 'none';
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  updateStaticTexts();
  fetchGlobalStats();
  fetchSystems();
  checkScanOnStartup();

  // Language Switchers
  document.getElementById('btn-lang-ja').addEventListener('click', () => setLanguage('ja'));
  document.getElementById('btn-lang-en').addEventListener('click', () => setLanguage('en'));

  // Search input
  let searchTimeout = null;
  document.getElementById('system-search').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.searchQuery = e.target.value;
      state.page = 1;
      fetchSystems();
    }, 300);
  });

  // Filter chips
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const filterKey = chip.dataset.filter;
      state.filters[filterKey] = !state.filters[filterKey];
      chip.classList.toggle('active', state.filters[filterKey]);
      state.page = 1;
      fetchSystems();
    });
  });

  // Date Preset & Filter
  const presetSelect = document.getElementById('date-preset-select');
  const customInputs = document.getElementById('custom-date-inputs');
  const dateFromInput = document.getElementById('filter-date-from');
  const dateToInput = document.getElementById('filter-date-to');
  const dateFieldSelect = document.getElementById('date-field-select');
  const btnClearDate = document.getElementById('btn-clear-date');

  function formatDateIso(d) {
    return d.toISOString().split('T')[0];
  }

  function applyDatePreset(preset) {
    const now = new Date();
    const todayStr = formatDateIso(now);

    if (preset === 'all') {
      state.dateFrom = '';
      state.dateTo = '';
      dateFromInput.value = '';
      dateToInput.value = '';
      customInputs.style.display = 'none';
    } else if (preset === 'before_today') {
      state.dateFrom = '';
      state.dateTo = todayStr;
      dateFromInput.value = '';
      dateToInput.value = todayStr;
      customInputs.style.display = 'flex';
    } else if (preset === 'last_7_days') {
      const past = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
      state.dateFrom = formatDateIso(past);
      state.dateTo = todayStr;
      dateFromInput.value = state.dateFrom;
      dateToInput.value = state.dateTo;
      customInputs.style.display = 'flex';
    } else if (preset === 'last_30_days') {
      const past = new Date(now.getTime() - 30 * 24 * 3600 * 1000);
      state.dateFrom = formatDateIso(past);
      state.dateTo = todayStr;
      dateFromInput.value = state.dateFrom;
      dateToInput.value = state.dateTo;
      customInputs.style.display = 'flex';
    } else if (preset === 'last_90_days') {
      const past = new Date(now.getTime() - 90 * 24 * 3600 * 1000);
      state.dateFrom = formatDateIso(past);
      state.dateTo = todayStr;
      dateFromInput.value = state.dateFrom;
      dateToInput.value = state.dateTo;
      customInputs.style.display = 'flex';
    } else if (preset === 'last_1_year') {
      const past = new Date(now.getTime() - 365 * 24 * 3600 * 1000);
      state.dateFrom = formatDateIso(past);
      state.dateTo = todayStr;
      dateFromInput.value = state.dateFrom;
      dateToInput.value = state.dateTo;
      customInputs.style.display = 'flex';
    } else if (preset === 'this_year') {
      const curYear = now.getFullYear();
      state.dateFrom = `${curYear}-01-01`;
      state.dateTo = `${curYear}-12-31`;
      dateFromInput.value = state.dateFrom;
      dateToInput.value = state.dateTo;
      customInputs.style.display = 'flex';
    } else if (preset === 'last_year') {
      const lastYear = now.getFullYear() - 1;
      state.dateFrom = `${lastYear}-01-01`;
      state.dateTo = `${lastYear}-12-31`;
      dateFromInput.value = state.dateFrom;
      dateToInput.value = state.dateTo;
      customInputs.style.display = 'flex';
    } else if (preset === 'custom') {
      customInputs.style.display = 'flex';
    }
    state.datePreset = preset;
    state.page = 1;
    fetchSystems();
  }

  if (presetSelect) {
    presetSelect.addEventListener('change', (e) => {
      applyDatePreset(e.target.value);
    });
  }

  if (dateFromInput) {
    dateFromInput.addEventListener('change', (e) => {
      state.dateFrom = e.target.value;
      presetSelect.value = 'custom';
      state.page = 1;
      fetchSystems();
    });
  }

  if (dateToInput) {
    dateToInput.addEventListener('change', (e) => {
      state.dateTo = e.target.value;
      presetSelect.value = 'custom';
      state.page = 1;
      fetchSystems();
    });
  }

  if (dateFieldSelect) {
    dateFieldSelect.addEventListener('change', (e) => {
      state.dateField = e.target.value;
      state.page = 1;
      fetchSystems();
    });
  }

  if (btnClearDate) {
    btnClearDate.addEventListener('click', () => {
      presetSelect.value = 'all';
      applyDatePreset('all');
    });
  }

  // Sort select 1 for systems
  document.getElementById('sort-select').addEventListener('change', (e) => {
    const [by, order] = e.target.value.split('-');
    state.sortBy = by;
    state.sortOrder = order;
    state.page = 1;
    fetchSystems();
  });

  // Sort select 2 for systems
  const sortSelect2 = document.getElementById('sort-select-2');
  if (sortSelect2) {
    sortSelect2.addEventListener('change', (e) => {
      if (e.target.value === 'none') {
        state.sortBy2 = null;
      } else {
        const [by, order] = e.target.value.split('-');
        state.sortBy2 = by;
        state.sortOrder2 = order;
      }
      state.page = 1;
      fetchSystems();
    });
  }

  // Copy System Name
  function copySelectedSystem() {
    if (!state.selectedSystem || !state.selectedSystem.star_system) return;
    const sysName = state.selectedSystem.star_system;
    navigator.clipboard.writeText(sysName).then(() => {
      const copyLabel = document.getElementById('copy-label');
      if (copyLabel) {
        const origText = copyLabel.innerText;
        copyLabel.innerText = t('copied_name');
        setTimeout(() => {
          copyLabel.innerText = t('copy_name');
        }, 1500);
      }
    }).catch(err => {
      console.error('Failed to copy system name:', err);
    });
  }

  const btnCopy = document.getElementById('btn-copy-system');
  if (btnCopy) {
    btnCopy.addEventListener('click', copySelectedSystem);
  }
  const sysNameEl = document.getElementById('current-system-name');
  if (sysNameEl) {
    sysNameEl.addEventListener('click', copySelectedSystem);
  }

  // Sort select for bodies
  document.getElementById('body-sort-select').addEventListener('change', (e) => {
    const [by, order] = e.target.value.split('-');
    state.bodySortBy = by;
    state.bodySortOrder = order;
    renderCurrentView();
  });

  // Pagination
  document.getElementById('btn-prev-page').addEventListener('click', () => {
    if (state.page > 1) {
      state.page--;
      fetchSystems();
    }
  });

  document.getElementById('btn-next-page').addEventListener('click', () => {
    if (state.page < state.totalPages) {
      state.page++;
      fetchSystems();
    }
  });

  // View Controls
  document.getElementById('btn-view-tree').addEventListener('click', () => {
    state.currentView = 'tree';
    updateViewButtons();
    renderCurrentView();
  });

  document.getElementById('btn-view-flat').addEventListener('click', () => {
    state.currentView = 'flat';
    updateViewButtons();
    renderCurrentView();
  });

  document.getElementById('btn-view-visits').addEventListener('click', () => {
    state.currentView = 'visits';
    updateViewButtons();
    renderCurrentView();
  });

  function updateViewButtons() {
    document.getElementById('btn-view-tree').classList.toggle('active', state.currentView === 'tree');
    document.getElementById('btn-view-flat').classList.toggle('active', state.currentView === 'flat');
    document.getElementById('btn-view-visits').classList.toggle('active', state.currentView === 'visits');
  }

  // Scan Button
  document.getElementById('btn-rescan').addEventListener('click', async () => {
    try {
      const res = await fetch('/api/scan_now', { method: 'POST' });
      pollScanProgress();
    } catch (err) {
      console.error('Failed to trigger scan:', err);
    }
  });
});

async function checkScanOnStartup() {
  try {
    const res = await fetch('/api/scan_status');
    const st = await res.json();
    if (st.is_scanning) {
      pollScanProgress();
    }
  } catch (err) {
    // Ignore on startup
  }
}

// Scan Polling
function pollScanProgress() {
  const banner = document.getElementById('scan-banner');
  const bannerText = document.getElementById('scan-banner-text');
  const bannerCount = document.getElementById('scan-banner-count');
  banner.style.display = 'flex';

  let pollCount = 0;
  const interval = setInterval(async () => {
    try {
      const res = await fetch('/api/scan_status');
      const st = await res.json();
      if (st.is_scanning) {
        bannerText.innerText = st.message;
        if (bannerCount) bannerCount.innerText = `${st.current} / ${st.total}`;
        pollCount++;
        // Update stats periodically during large scans
        if (pollCount % 3 === 0) {
          fetchGlobalStats();
        }
      } else {
        bannerText.innerText = st.message;
        if (bannerCount) bannerCount.innerText = `${st.total}`;
        setTimeout(() => {
          banner.style.display = 'none';
        }, 2500);
        clearInterval(interval);
        // Instant full UI refresh
        fetchGlobalStats();
        fetchSystems();
      }
    } catch (err) {
      clearInterval(interval);
    }
  }, 1000);
}
