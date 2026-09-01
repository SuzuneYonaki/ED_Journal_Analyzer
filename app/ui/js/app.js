// State management
let state = {
  systems: [],
  selectedSystem: null,
  selectedBody: null,
  targetBodyId: null,
  currentSystemData: null,
  currentView: 'sysmap', // 'sysmap', 'orrery', 'tree', 'flat', 'bio', 'visits'
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
  sortBy: 'last_visited',
  sortOrder: 'desc',
  sortBy2: null,
  sortOrder2: 'desc',
  savedSortBy: 'total_potential_value',
  savedSortOrder: 'desc',
  savedSortBy2: null,
  savedSortOrder2: 'desc',
  datePreset: 'all',
  dateFrom: '',
  dateTo: '',
  dateField: 'last_visited',
  bodySortBy: 'distance',
  bodySortOrder: 'asc',
  page: 1,
  limit: 50,
  liveSyncEnabled: true,
  lastEventVersion: 0,
  lastJournalEventVersion: 0,
  jumpState: 'idle', // 'idle' | 'hyperspace' | 'arrived_waiting_fss' | 'scanned'
  targetJumpSystem: ''
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
  updateLiveSyncButtonUI();
  updateSortControlsUI();
  renderSystemList();
  renderSystemHeader();
  renderCurrentView();
  renderBodyInspector();
}

// API Calls
let statsRetryTimeout = null;
let systemsRetryTimeout = null;

async function fetchGlobalStats() {
  try {
    const params = new URLSearchParams();
    if (state.dateFrom) params.append('date_from', state.dateFrom);
    if (state.dateTo) params.append('date_to', state.dateTo);
    if (state.dateField) params.append('date_field', state.dateField);

    const url = `/api/stats${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
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

    // Update Header Period Label
    const periodLabelEl = document.getElementById('header-logged-period');
    if (periodLabelEl) {
      if (!state.dateFrom && !state.dateTo) {
        periodLabelEl.innerText = '全期間';
      } else if (state.dateFrom && !state.dateTo) {
        periodLabelEl.innerText = `${state.dateFrom} 〜 今日`;
      } else if (!state.dateFrom && state.dateTo) {
        periodLabelEl.innerText = `最初 〜 ${state.dateTo}`;
      } else {
        periodLabelEl.innerText = `${state.dateFrom} 〜 ${state.dateTo}`;
      }
    }

    // CMDR Current Location
    const cmdrLocEl = document.getElementById('stat-cmdr-loc');
    if (cmdrLocEl) {
      if (data.current_location && data.current_location.star_system) {
        const cl = data.current_location;
        cmdrLocEl.innerText = cl.star_system;
        cmdrLocEl.title = `${cl.star_system} [${cl.star_pos_x.toFixed(6)}, ${cl.star_pos_y.toFixed(6)}, ${cl.star_pos_z.toFixed(6)}]`;
      } else {
        cmdrLocEl.innerText = '--';
      }
    }
  } catch (err) {
    console.warn('fetchStats failed, retrying in 1.5s:', err);
    if (!statsRetryTimeout) {
      statsRetryTimeout = setTimeout(() => {
        statsRetryTimeout = null;
        fetchGlobalStats();
      }, 1500);
    }
  }
}

async function fetchSystems() {
  const activeSortBy = state.liveSyncEnabled ? 'last_visited' : (state.savedSortBy || 'total_potential_value');
  const activeSortOrder = state.liveSyncEnabled ? 'desc' : (state.savedSortOrder || 'desc');
  const activeSortBy2 = state.liveSyncEnabled ? null : state.savedSortBy2;
  const activeSortOrder2 = state.liveSyncEnabled ? 'desc' : state.savedSortOrder2;

  const params = new URLSearchParams({
    q: state.searchQuery || '',
    sort_by: activeSortBy,
    sort_order: activeSortOrder,
    page: state.page || 1,
    limit: state.limit || 50
  });

  if (activeSortBy2 && activeSortBy2 !== 'none') {
    params.append('sort_by_2', activeSortBy2);
    params.append('sort_order_2', activeSortOrder2);
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
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.systems = data.systems;
    state.totalPages = Math.ceil(data.total / state.limit) || 1;

    // Update CMDR location in header if returned
    let jumpedToNewSystem = false;
    if (data.current_location && data.current_location.star_system) {
      const cl = data.current_location;
      const prevCmdrSys = state.currentCmdrSystemAddress;
      state.currentCmdrSystemAddress = cl.system_address;

      const cmdrLocEl = document.getElementById('stat-cmdr-loc');
      if (cmdrLocEl) {
        cmdrLocEl.innerText = cl.star_system;
        if (cl.star_pos_x !== undefined) {
          cmdrLocEl.title = `${cl.star_system} [${cl.star_pos_x.toFixed(1)}, ${cl.star_pos_y.toFixed(1)}, ${cl.star_pos_z.toFixed(1)}]`;
        }
      }

      // If LIVE sync is active and CMDR jumped to a new system, auto-switch center pane to new system!
      if (state.liveSyncEnabled && prevCmdrSys && cl.system_address && prevCmdrSys !== cl.system_address) {
        jumpedToNewSystem = true;
        selectSystem(cl.system_address);
      }
    }

    renderSystemList();
    renderPagination(data.total);

    // Auto select first system if none selected or not in current list (and not just jumped)
    if (!jumpedToNewSystem && state.systems && state.systems.length > 0) {
      if (!state.selectedSystem || !state.systems.some(s => s.system_address === state.selectedSystem.system_address)) {
        const targetAddress = (state.currentCmdrSystemAddress && state.systems.some(s => s.system_address === state.currentCmdrSystemAddress))
          ? state.currentCmdrSystemAddress
          : state.systems[0].system_address;
        selectSystem(targetAddress);
      }
    }
  } catch (err) {
    console.warn('fetchSystems failed, retrying in 1.5s:', err);
    if (!systemsRetryTimeout) {
      systemsRetryTimeout = setTimeout(() => {
        systemsRetryTimeout = null;
        fetchSystems();
      }, 1500);
    }
  }
}

async function selectSystem(systemAddress, preserveSelectedBody = false, resetJumpState = true) {
  try {
    if (resetJumpState) {
      state.jumpState = 'idle';
    }

    const res = await fetch(`/api/system/${systemAddress}`);
    const data = await res.json();
    state.currentSystemData = data;
    state.selectedSystem = data.system;

    if (data.system && data.system.last_targeted_body_id !== undefined && data.system.last_targeted_body_id !== null) {
      state.targetBodyId = data.system.last_targeted_body_id;
    }
    
    // Auto select target body, preserved body, or first body
    if (data.bodies && data.bodies.length > 0) {
      if (preserveSelectedBody && state.selectedBody) {
        const matchingBody = data.bodies.find(b => b.body_id === state.selectedBody.body_id);
        state.selectedBody = matchingBody || data.bodies[0];
      } else if (state.targetBodyId !== null && state.targetBodyId !== undefined) {
        const targetMatching = data.bodies.find(b => b.body_id === state.targetBodyId);
        state.selectedBody = targetMatching || data.bodies[0];
      } else {
        state.selectedBody = data.bodies[0];
      }

      // Check high value bio alert (40M+ Cr) on 1st discover systems
      if (ttsState.highBioEnabled) {
        data.bodies.forEach(b => {
          checkAndAnnounceHighBioBody(data.system, b);
        });
      }
    } else {
      state.selectedBody = null;
    }

    renderSystemHeader();
    renderCurrentView();
    if (state.jumpState === 'idle' || state.jumpState === 'scanned') {
      renderBodyInspector();
    }
    highlightSelectedSystemCard();
    if (state.selectedBody && (state.jumpState === 'idle' || state.jumpState === 'scanned')) {
      focusAndScrollToTargetBody(state.selectedBody.body_id);
    }
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
    
    // Distance badges
    if (sys.cmdr_distance_ly !== null && sys.cmdr_distance_ly !== undefined) {
      tags.push(`<span class="tag-badge tag-cmdr-dist">📍 CMDR: ${Math.round(sys.cmdr_distance_ly).toLocaleString()} Ly</span>`);
    }
    if (sys.sol_distance_ly > 0) {
      tags.push(`<span class="tag-badge tag-sol-dist">Sol: ${Math.round(sys.sol_distance_ly).toLocaleString()} Ly</span>`);
    }

    // EDSM Discovery Status Badges & 1st Discover Registerable Announcement
    if (sys.edsm_checked === 1) {
      if (sys.edsm_registered === 1) {
        const discText = sys.edsm_first_discoverer ? `⭐ EDSM: ${sys.edsm_first_discoverer}` : '⭐ EDSM登録済';
        tags.push(`<span class="tag-badge tag-edsm-found" title="EDSM登録済 / 発見者: ${sys.edsm_first_discoverer || '不明'}">${discText}</span>`);
      } else {
        tags.push('<span class="tag-badge tag-edsm-unreg" title="EDSM未登録 / あなたの探査データを提出して1st Discoverを登録できます！">✨ 1st Discover 登録可能 (EDSM未登録)</span>');
      }
    } else if (sys.has_first_discover || (sys.first_discovered_bodies && sys.first_discovered_bodies > 0)) {
      tags.push('<span class="tag-badge tag-edsm-unreg" title="ゲーム内初発見 / EDSM 1st Discover 登録可能">✨ 1st Discover 登録可能</span>');
    }

    if (sys.has_high_g) tags.push('<span class="tag-badge tag-high-g">High-G</span>');
    if (sys.has_anomalies) tags.push('<span class="tag-badge tag-anomaly">Rare/Orbit</span>');

    const visitedDate = sys.last_visited ? sys.last_visited.substring(0, 10) : '--';
    let mainStar = '';
    if (sys.main_star_type) {
      const style = getStarTypeStyle(sys.main_star_type);
      mainStar = `<span class="tag-badge" style="background: ${style.bg}; color: ${style.text}; border: 1px solid ${style.border}; margin-left: 6px; font-weight: bold;">${sys.main_star_type}</span>`;
    }

    const sysName = sys.star_system || (`System ${sys.system_address || ''}`);
    const coordsStr = (sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
      ? `[${sys.star_pos_x.toFixed(6)}, ${sys.star_pos_y.toFixed(6)}, ${sys.star_pos_z.toFixed(6)}]`
      : '';

    card.innerHTML = `
      <div class="system-card-header">
        <div class="system-card-title-group">
          <span class="system-card-title" title="${sysName}">${sysName}</span>
          ${coordsStr ? `<span class="system-coords" style="font-size: 0.7rem; color: var(--text-secondary); font-family: monospace; letter-spacing: -0.3px;">${coordsStr}</span>` : ''}
        </div>
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
    ? `[ ${sys.star_pos_x.toFixed(6)}, ${sys.star_pos_y.toFixed(6)}, ${sys.star_pos_z.toFixed(6)} ]`
    : '';
  document.getElementById('current-system-coords').innerText = coords;
  document.getElementById('current-system-fss-value').innerText = formatCredits(sys.total_fss_value || 0);
  document.getElementById('current-system-value').innerText = formatCredits(sys.total_potential_value || 0);
  
  // EDSM Discovery Badge in Header
  const edsmBadgeEl = document.getElementById('current-system-edsm-badge');
  if (edsmBadgeEl) {
    if (sys.edsm_checked === 1) {
      if (sys.edsm_registered === 1) {
        const discText = sys.edsm_first_discoverer ? `⭐ EDSM: ${sys.edsm_first_discoverer}` : '⭐ EDSM登録済';
        edsmBadgeEl.innerHTML = `<span class="tag-badge tag-edsm-found" title="EDSM登録済 / 発見者: ${sys.edsm_first_discoverer || '不明'}">${discText}</span>`;
      } else {
        edsmBadgeEl.innerHTML = '<span class="tag-badge tag-edsm-unreg" title="EDSM未登録 / 探査データを提出して1st Discoverを登録できます！">✨ 1st Discover 登録可能 (EDSM未登録)</span>';
      }
    } else if (sys.has_first_discover || (sys.first_discovered_bodies && sys.first_discovered_bodies > 0)) {
      edsmBadgeEl.innerHTML = '<span class="tag-badge tag-edsm-unreg" title="ゲーム内初発見 / EDSM 1st Discover 登録可能">✨ 1st Discover 登録可能</span>';
    } else {
      edsmBadgeEl.innerHTML = '';
    }
  }
  
  // Exobiology System Summary
  const bioBox = document.getElementById('system-bio-payout-box');
  const bioScannedBaseEl = document.getElementById('current-system-bio-scanned-base');
  const bioScannedFirstEl = document.getElementById('current-system-bio-scanned-first');
  const bioBaseEl = document.getElementById('current-system-bio-base');
  const bioFirstEl = document.getElementById('current-system-bio-first');

  if (sys.bio_total_base_value > 0 || sys.bio_signals_count > 0 || (state.currentSystemData && state.currentSystemData.system_bio_summary && (state.currentSystemData.system_bio_summary.total_base_value > 0 || state.currentSystemData.system_bio_summary.scanned_base_value > 0))) {
    const summary = (state.currentSystemData && state.currentSystemData.system_bio_summary) || {};
    const scannedBaseVal = sys.bio_scanned_base_value !== undefined ? sys.bio_scanned_base_value : (summary.scanned_base_value || 0);
    const scannedFirstVal = sys.bio_scanned_first_value !== undefined ? sys.bio_scanned_first_value : (summary.scanned_first_value || 0);
    const baseVal = sys.bio_total_base_value || summary.total_base_value || 0;
    const firstVal = sys.bio_total_first_value || summary.total_first_value || 0;
    const sigCount = sys.bio_signals_count || summary.total_signals || 0;
    const scCount = sys.bio_scanned_count || summary.total_scanned || 0;

    if (bioBox) bioBox.style.display = 'block';
    if (bioScannedBaseEl) bioScannedBaseEl.innerText = formatCredits(scannedBaseVal);
    if (bioScannedFirstEl) bioScannedFirstEl.innerText = formatCredits(scannedFirstVal);
    if (bioBaseEl) bioBaseEl.innerText = formatCredits(baseVal);
    if (bioFirstEl) bioFirstEl.innerText = formatCredits(firstVal);
    if (bioBox) bioBox.title = `Total Signals: ${sigCount}, Scanned: ${scCount}`;
  } else {
    if (bioBox) bioBox.style.display = 'none';
  }

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

function renderBodyExobiologyBlock(node) {
  const bioSig = node.bio_signals || 0;
  const scannedList = node.scanned_organics || [];
  const rawPotential = node.exobiology || node.potential_exobiology || [];

  if (bioSig === 0 && scannedList.length === 0) return '';

  const scannedGenusSet = new Set(scannedList.map(s => (s.genus_localised || s.genus || '').toLowerCase()));
  const scannedSpeciesSet = new Set(scannedList.map(s => (s.species_localised || s.species || '').toLowerCase()));

  const slotRows = [];

  // 1. Scanned / Confirmed Species Rows
  scannedList.forEach(org => {
    const spName = org.species_localised || org.species || org.genus_localised || org.genus || 'Confirmed Flora';
    const genName = org.genus_localised || org.genus || '';
    const baseVal = org.base_value || 0;
    const fdVal = org.first_discovery_value || (baseVal * 5);
    const dist = org.colony_distance_m || 500;
    const stage = org.stage_level || 3;
    const variant = org.variant_localised || org.variant || '';

    let stageDots = "●●●";
    let badgeClass = "bio-badge-confirmed";
    let badgeText = `✓ [3/3 ${t('bio_status_analyzed')}]`;
    let rowClass = "confirmed";

    if (stage === 1) {
      stageDots = "●○○";
      badgeClass = "tag-badge";
      badgeText = `🔬 [1/3 ${t('bio_status_sample_1')}]`;
      rowClass = "in-progress";
    } else if (stage === 2) {
      stageDots = "●●○";
      badgeClass = "tag-badge";
      badgeText = `🔬 [2/3 ${t('bio_status_sample_2')}]`;
      rowClass = "in-progress";
    }

    const varColor = variant.includes(" - ") ? variant.split(" - ")[1].trim() : "";
    const colorBadge = varColor ? `<span class="tag-badge" style="background: rgba(0, 255, 136, 0.15); color: #6ee7b7; border: 1px solid rgba(0, 255, 136, 0.35); font-size: 0.65rem;">🎨 ${varColor}</span>` : '';

    slotRows.push(`
      <div class="bio-slot-row ${rowClass}">
        <div class="bio-slot-left">
          <span class="${badgeClass}">${badgeText}</span>
          <span style="font-weight: bold; color: #f8fafc;">${spName}</span>
          ${genName && !spName.includes(genName) ? `<span style="color:var(--text-secondary); font-size:0.7rem;">(${genName})</span>` : ''}
          ${colorBadge}
          <span style="color: var(--ed-green); font-size: 0.75rem; letter-spacing: 1px; margin-left: 2px;">${stageDots}</span>
          <span class="bio-colony-tag" title="${t('bio_colony_dist')} ${dist}m">📍 ${dist}m</span>
        </div>
        <div class="bio-slot-payouts">
          <span style="color: #a7f3d0;">${t('bio_normal_val')} ${formatCredits(baseVal)}</span>
          <span style="color: var(--ed-green); font-weight: bold;">${t('bio_first_val')} ${formatCredits(fdVal)}</span>
        </div>
      </div>
    `);
  });

  // 2. Candidate Potential Species Rows (BioInsights & ED Exploration Buddy Slot Allocation)
  const isFullyScanned = (bioSig > 0 && scannedList.length >= bioSig);
  const remainingSlots = Math.max(0, bioSig - scannedList.length);

  // Filter un-scanned potential candidates
  const unscannedCandidates = [];
  const excludedCandidates = [];

  rawPotential.forEach(pot => {
    const sp = (pot.species || '').toLowerCase();
    const gen = (pot.genus || '').toLowerCase();
    if (scannedSpeciesSet.has(sp)) return;

    if (scannedGenusSet.has(gen) || isFullyScanned) {
      excludedCandidates.push(pot);
    } else {
      unscannedCandidates.push(pot);
    }
  });

  // Sort candidates by genus base_value descending (highest price first), then by probability score
  unscannedCandidates.sort((a, b) => (b.base_value || 0) - (a.base_value || 0) || (b.probability_score || 0) - (a.probability_score || 0));

  // Primary prediction slots (up to remainingSlots)
  const primaryCandidates = unscannedCandidates.slice(0, remainingSlots > 0 ? remainingSlots : undefined);
  const alternativeCandidates = unscannedCandidates.slice(remainingSlots > 0 ? remainingSlots : unscannedCandidates.length);

  primaryCandidates.forEach((pot, idx) => {
    const spName = pot.species_variant || pot.species || pot.genus || 'Candidate';
    const genName = pot.genus || '';
    const baseVal = pot.base_value || 0;
    const fdVal = pot.first_discovery_value || (baseVal * 5);
    const dist = pot.colony_distance_m || 500;
    const desc = pot.description || '';
    const variantColor = pot.variant_color || '';
    const slotNum = scannedList.length + idx + 1;
    const colorBadge = variantColor ? `<span class="tag-badge" style="background: rgba(250, 204, 21, 0.15); color: #fde047; border: 1px solid rgba(250, 204, 21, 0.35); font-size: 0.65rem;">🎨 ${variantColor}</span>` : '';
    const genusBadge = genName ? `<span class="tag-badge" style="background: rgba(0, 210, 255, 0.12); color: var(--ed-cyan); border: 1px solid rgba(0, 210, 255, 0.35); font-size: 0.68rem; font-weight: bold;">${genName}</span>` : '';

    slotRows.push(`
      <div class="bio-slot-row candidate" style="border-left: 3px solid var(--ed-green);">
        <div class="bio-slot-left">
          <span class="bio-badge-candidate">? [Slot ${slotNum}/${bioSig || '?'}]</span>
          ${genusBadge}
          <span style="color: #f1f5f9; font-weight: 600;">${spName}</span>
          ${colorBadge}
          <span class="bio-colony-tag" title="${t('bio_colony_dist')} ${dist}m">📍 ${dist}m</span>
          ${desc ? `<span style="color: var(--text-dim); font-size: 0.68rem; margin-left: 4px;">(${desc})</span>` : ''}
        </div>
        <div class="bio-slot-payouts">
          <span style="color: #94a3b8;">${t('bio_normal_val')} ${formatCredits(baseVal)}</span>
          <span style="color: var(--ed-green); font-weight: bold;">${t('bio_first_val')} ${formatCredits(fdVal)}</span>
        </div>
      </div>
    `);
  });

  // Optional alternative candidates (rendered cleanly in a collapsed or secondary block)
  if (alternativeCandidates.length > 0) {
    const altDetailsId = `alt-bio-${node.body_id || Math.random().toString(36).substr(2, 9)}`;
    const altRows = alternativeCandidates.map(pot => {
      const spName = pot.species_variant || pot.species || pot.genus || 'Candidate';
      const genName = pot.genus || '';
      const baseVal = pot.base_value || 0;
      const fdVal = pot.first_discovery_value || (baseVal * 5);
      const dist = pot.colony_distance_m || 500;
      const variantColor = pot.variant_color || '';
      const colorBadge = variantColor ? `<span class="tag-badge" style="background: rgba(250, 204, 21, 0.12); color: #fde047; font-size: 0.62rem;">🎨 ${variantColor}</span>` : '';
      const genusBadge = genName ? `<span class="tag-badge" style="background: rgba(0, 210, 255, 0.08); color: var(--ed-cyan-dim); border: 1px solid rgba(0, 210, 255, 0.2); font-size: 0.62rem;">${genName}</span>` : '';

      return `
        <div class="bio-slot-row candidate" style="opacity: 0.8; font-size: 0.8rem; padding: 4px 8px; background: rgba(0,0,0,0.15);">
          <div class="bio-slot-left">
            <span class="tag-badge" style="background: rgba(255,255,255,0.06); color: var(--text-secondary); font-size: 0.62rem;">alt</span>
            ${genusBadge}
            <span style="color: #cbd5e1;">${spName}</span>
            ${colorBadge}
            <span class="bio-colony-tag" style="font-size: 0.62rem;">📍 ${dist}m</span>
          </div>
          <div class="bio-slot-payouts" style="font-size: 0.72rem;">
            <span style="color: #94a3b8;">${formatCredits(baseVal)}</span>
            <span style="color: var(--ed-green); margin-left: 6px;">${formatCredits(fdVal)}</span>
          </div>
        </div>
      `;
    }).join('');

    slotRows.push(`
      <details style="margin-top: 4px; border: 1px dashed rgba(255,255,255,0.15); border-radius: 4px; padding: 4px 8px;">
        <summary style="font-size: 0.72rem; color: var(--text-secondary); cursor: pointer; user-select: none;">
          🔍 他の候補の可能性 (${alternativeCandidates.length}件を表示/非表示)
        </summary>
        <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 4px;">
          ${altRows}
        </div>
      </details>
    `);
  }

  // Excluded candidates (already scanned genus)
  if (excludedCandidates.length > 0) {
    excludedCandidates.forEach(pot => {
      const spName = pot.species_variant || pot.species || pot.genus || 'Candidate';
      const baseVal = pot.base_value || 0;
      const dist = pot.colony_distance_m || 500;
      slotRows.push(`
        <div class="bio-slot-row candidate" style="opacity: 0.35; filter: grayscale(50%);">
          <div class="bio-slot-left">
            <span class="tag-badge" style="background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.25); font-size: 0.62rem;">✕ ${t('bio_status_excluded') || '除外'}</span>
            <span style="color: #94a3b8; text-decoration: line-through;">${spName}</span>
            <span class="bio-colony-tag" style="opacity: 0.6;">📍 ${dist}m</span>
          </div>
          <div class="bio-slot-payouts">
            <span style="color: #64748b;">${formatCredits(baseVal)}</span>
          </div>
        </div>
      `);
    });
  }

  // Environmental info (Gravity safety & Atmosphere/Temp)
  const envBadges = [];
  if (node.landable) {
    const g = node.surface_gravity_g || 0;
    if (g >= 3.0) {
      envBadges.push(`<span class="tag-badge tag-high-g" style="font-size:0.68rem;">⚠️ ${g.toFixed(2)}G (${t('danger_gravity')})</span>`);
    } else if (g > 0) {
      envBadges.push(`<span class="tag-badge" style="background: rgba(0,255,136,0.1); color: var(--ed-green); border:1px solid rgba(0,255,136,0.3); font-size:0.68rem;">🟢 ${g.toFixed(2)}G (${t('safe_gravity')})</span>`);
    }
  }
  if (node.atmosphere && node.atmosphere.toLowerCase() !== 'none') {
    envBadges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.06); color: var(--text-secondary); font-size:0.68rem;">🌫️ ${node.atmosphere}</span>`);
  }
  if (node.surface_temperature) {
    const kelvin = Math.round(node.surface_temperature);
    const celsius = Math.round(node.surface_temperature - 273.15);
    envBadges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.06); color: var(--text-secondary); font-size:0.68rem;">🌡️ ${kelvin}K (${celsius}℃)</span>`);
  }

  const scannedBase = node.bio_scanned_base_value || 0;
  const scannedFirst = node.bio_scanned_first_value || 0;
  const totalBase = node.bio_total_base_value || 0;
  const totalFirst = node.bio_total_first_value || 0;

  const scannedSubtotalHtml = scannedBase > 0 ? `
    <div style="display: flex; align-items: baseline; gap: 4px; background: rgba(0, 255, 136, 0.12); padding: 1px 6px; border-radius: 3px; border: 1px solid rgba(0, 255, 136, 0.3);">
      <span style="color: #6ee7b7; font-size: 0.72rem; font-weight: 500;">✓ ${t('bio_body_scanned_total')}</span>
      <span style="color: #d1fae5; font-size: 0.75rem;" title="スキャン確定 (通常)">${formatCredits(scannedBase)}</span>
      <span style="color: var(--text-secondary); font-size: 0.65rem;">/ 1st:</span>
      <span style="color: var(--ed-green); font-size: 0.78rem; font-weight: bold;" title="スキャン確定 (1st 5倍)">${formatCredits(scannedFirst)}</span>
    </div>
  ` : '';

  return `
    <div class="body-bio-panel">
      <div class="body-bio-header">
        <div class="body-bio-title">
          🌱 Exobiology (${t('filter_bio')}: ${bioSig} / ${t('bio_status_confirmed')}: ${node.completed_bio_count || 0})
          <div style="display: inline-flex; gap: 4px; margin-left: 6px; flex-wrap: wrap;">${envBadges.join('')}</div>
        </div>
        <div class="body-bio-total" style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          ${scannedSubtotalHtml}
          <div style="display: flex; align-items: baseline; gap: 4px;">
            <span style="color: var(--text-secondary); font-size: 0.72rem;">${t('bio_body_total')}</span>
            <span style="color: #a7f3d0; font-size: 0.75rem;" title="見込合計 (通常)">${formatCredits(totalBase)}</span>
            <span style="color: var(--text-secondary); font-size: 0.65rem;">/ 1st:</span>
            <span style="color: var(--ed-green); font-weight: bold; font-size: 0.8rem;" title="1st Discover合計 (5倍)">${formatCredits(totalFirst)}</span>
          </div>
        </div>
      </div>
      <div class="body-bio-slots">
        ${slotRows.join('')}
      </div>
      <div style="font-size: 0.65rem; color: var(--text-dim); text-align: right; margin-top: 4px;">
        🔬 Prediction Ref: Canonn Research Group
      </div>
    </div>
  `;
}

function renderBodyGeoBlock(node) {
  const geoSig = node.geo_signals || 0;
  const volc = node.volcanism || '';
  if (geoSig === 0 && (!volc || volc.toLowerCase() === 'none')) return '';

  return `
    <div class="body-geo-panel">
      <div style="display: flex; align-items: center; gap: 6px;">
        <span style="font-weight: bold; color: var(--ed-orange);">🌋 ${t('geological_signals')} (${geoSig}):</span>
        <span>${volc || 'Active Geological Formations'}</span>
      </div>
      <span class="tag-badge" style="background: rgba(255,113,0,0.2); color: var(--ed-orange); border: 1px solid rgba(255,113,0,0.4); font-size: 0.68rem;">GEO: ${geoSig}</span>
    </div>
  `;
}

function focusAndScrollToTargetBody(bodyId) {
  const targetId = (bodyId !== null && bodyId !== undefined) ? bodyId : (state.selectedBody ? state.selectedBody.body_id : state.targetBodyId);
  if (targetId === null || targetId === undefined) return;

  setTimeout(() => {
    const targetCard = document.querySelector(`.node-card[data-body-id="${targetId}"]`);
    if (targetCard) {
      // Remove pulse from all cards
      document.querySelectorAll('.node-card').forEach(nc => nc.classList.remove('target-pulse'));

      // Ensure card is selected visually
      document.querySelectorAll('.node-card').forEach(nc => nc.classList.remove('selected'));
      targetCard.classList.add('selected');

      // Smooth scroll to center of view
      targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

      // Add visual pulse effect
      targetCard.classList.add('target-pulse');
      setTimeout(() => {
        targetCard.classList.remove('target-pulse');
      }, 3000);
    }
  }, 100);
}

function clearBodyInspector() {
  document.getElementById('inspect-body-name').innerText = '--';
  document.getElementById('inspect-planet-class').innerText = '--';
  document.getElementById('val-fss').innerText = '0 Cr';
  document.getElementById('val-dss').innerText = '0 Cr';
  document.getElementById('val-fd-fss').innerText = '0 Cr';
  document.getElementById('val-fm-dss').innerText = '0 Cr';
  document.getElementById('val-max-total').innerText = '0 Cr';
  document.getElementById('inspect-bio-signals-info').innerText = '';
  document.getElementById('inspect-bio-predictions').innerHTML = '';
  document.getElementById('prop-landable').innerText = '--';
  document.getElementById('prop-gravity').innerText = '--';
  document.getElementById('prop-temperature').innerText = '--';
  document.getElementById('prop-pressure').innerText = '--';
  document.getElementById('prop-atmosphere').innerText = '--';
  document.getElementById('prop-volcanism').innerText = '--';
  document.getElementById('prop-semi-major').innerText = '--';
  document.getElementById('prop-eccentricity').innerText = '--';
  document.getElementById('prop-orbital-period').innerText = '--';
  document.getElementById('prop-rotation-period').innerText = '--';
  document.getElementById('prop-inclination').innerText = '--';
  document.getElementById('prop-tidal-lock').innerText = '--';
  const ringsSection = document.getElementById('section-rings');
  if (ringsSection) ringsSection.style.display = 'none';
}

function renderCurrentView() {
  const container = document.getElementById('map-content');
  container.innerHTML = '';

  // 1. Hyperspace Jump State Placeholder
  if (state.jumpState === 'hyperspace') {
    const nextSys = state.targetJumpSystem || (state.selectedSystem ? state.selectedSystem.star_system : 'Unknown');
    container.innerHTML = `
      <div class="jump-status-placeholder" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; min-height: 420px; color: var(--ed-orange); text-align: center; padding: 40px;">
        <div style="font-size: 3rem; margin-bottom: 16px;">🌀</div>
        <div style="font-size: 1.2rem; font-weight: bold; letter-spacing: 1.5px; color: #fff;">HYPERSPACE JUMP IN PROGRESS</div>
        <div style="font-size: 0.95rem; color: var(--ed-orange); margin-top: 8px;">ジャンプ先星系 &rarr; <span style="color: #fff; font-weight: bold;">${nextSys}</span></div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 14px;">星系データをクリアしました。到着を待機中...</div>
      </div>
    `;
    return;
  }

  // 2. Arrived Waiting FSS (Honk) State Placeholder
  if (state.jumpState === 'arrived_waiting_fss') {
    const curSys = state.selectedSystem ? state.selectedSystem.star_system : (state.targetJumpSystem || 'Current System');
    container.innerHTML = `
      <div class="jump-status-placeholder" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; min-height: 420px; color: var(--ed-cyan); text-align: center; padding: 40px;">
        <div style="font-size: 3rem; margin-bottom: 16px;">📡</div>
        <div style="font-size: 1.2rem; font-weight: bold; letter-spacing: 1.5px; color: #fff;">ARRIVED: ${curSys}</div>
        <div style="font-size: 0.9rem; color: var(--ed-cyan); margin-top: 8px;">FSS ディスカバリースキャン (Honk) 待機中...</div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 14px;">Discovery Scanner (Honk) を実行すると System Map の確定描画を開始します</div>
      </div>
    `;
    return;
  }

  if (!state.currentSystemData) return;

  if (state.currentView === 'sysmap') {
    if (typeof renderSystemMapView === 'function') {
      renderSystemMapView(container, state.currentSystemData.hierarchy, state.currentSystemData.bodies);
    }
  } else if (state.currentView === 'flat') {
    const sorted = getSortedBodies(state.currentSystemData.bodies);
    renderFlatBodiesList(container, sorted);
  } else if (state.currentView === 'bio') {
    const sorted = getSortedBodies(state.currentSystemData.bodies);
    renderBioOnlyView(container, sorted);
  } else if (state.currentView === 'visits') {
    renderVisitsTimeline(container, state.currentSystemData.visits);
  }

  // Auto focus & scroll to target body
  const targetId = state.selectedBody ? state.selectedBody.body_id : state.targetBodyId;
  if (targetId !== null && targetId !== undefined) {
    focusAndScrollToTargetBody(targetId);
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
      state.targetBodyId = node.body_id;
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

    if (node.geo_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(255,113,0,0.2); color: var(--ed-orange);">GEO: ${node.geo_signals}</span>`);
    if (node.anomalies && node.anomalies.length > 0) {
      node.anomalies.forEach(a => badges.push(`<span class="tag-badge tag-anomaly">${a.tag}</span>`));
    }

    const typeDesc = node.star_type ? `${t('star_type_label')} (${node.star_type})` : (node.planet_class || 'Planet');

    card.innerHTML = `
      <div class="node-card-top">
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
      </div>
    `;

    nodeWrapper.appendChild(card);

    if (node.children && node.children.length > 0) {
      const childrenWrapper = document.createElement('div');
      childrenWrapper.className = 'tree-children';
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
  list.style.gap = '10px';

  bodies.forEach(body => {
    const isTarget = state.targetBodyId !== null && body.body_id === state.targetBodyId;
    const card = document.createElement('div');
    card.className = `node-card ${state.selectedBody && state.selectedBody.body_id === body.body_id ? 'selected' : ''} ${isTarget ? 'is-current-target' : ''}`;
    card.dataset.bodyId = body.body_id;
    card.onclick = () => {
      state.selectedBody = body;
      state.targetBodyId = body.body_id;
      renderBodyInspector();
      document.querySelectorAll('.node-card').forEach(nc => nc.classList.remove('selected'));
      card.classList.add('selected');
    };

    const iconClass = getBodyIconClass(body);
    const iconLabel = getBodyIconLabel(body);

    const badges = [];
    if (isTarget) badges.push('<span class="tag-badge" style="background: rgba(0, 210, 255, 0.2); color: var(--ed-cyan); border: 1px solid rgba(0, 210, 255, 0.6); font-weight: bold;">📍 ACTIVE TARGET</span>');
    if (body.landable) badges.push('<span class="tag-badge tag-landable">LANDABLE</span>');
    if (body.landable && body.surface_gravity_g) {
      if (body.surface_gravity_g >= 3.0) badges.push(`<span class="tag-badge tag-high-g">${body.surface_gravity_g.toFixed(2)}G !</span>`);
      else badges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.1);">${body.surface_gravity_g.toFixed(2)}G</span>`);
    }
    if (body.geo_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(255,113,0,0.2); color: var(--ed-orange);">GEO: ${body.geo_signals}</span>`);
    if (body.anomalies && body.anomalies.length > 0) {
      body.anomalies.forEach(a => badges.push(`<span class="tag-badge tag-anomaly">${a.tag}</span>`));
    }
    card.innerHTML = `
      <div class="node-card-top">
        <div class="node-info-left">
          <div class="body-icon ${iconClass}">${iconLabel}</div>
          <div class="node-details">
            <div class="node-name" style="${isTarget ? 'color: var(--ed-cyan); font-weight: bold;' : ''}">${body.body_name}</div>
            <div class="node-subtext">${body.star_type ? t('star_type_label') + ' ' + body.star_type : body.planet_class || 'Body'}</div>
            <div class="node-badges">${badges.join('')}</div>
          </div>
        </div>
        <div class="node-info-right">
          <span class="node-value">${formatCredits(body.max_potential_value)}</span>
          <span class="node-distance">${formatDistance(body.distance_from_arrival_ls)}</span>
        </div>
      </div>
    `;
    list.appendChild(card);
  });
  container.appendChild(list);
}

function renderBioOnlyView(container, bodies) {
  if (!bodies) return;
  let bioBodies = bodies.filter(b => (b.bio_signals > 0) || (b.scanned_organics && b.scanned_organics.length > 0));

  const hideCompletedCb = document.getElementById('cb-hide-completed-bio');
  const shouldHideCompleted = hideCompletedCb ? hideCompletedCb.checked : false;

  if (shouldHideCompleted) {
    bioBodies = bioBodies.filter(b => !b.is_bio_completed);
  }

  if (bioBodies.length === 0) {
    container.innerHTML = `
      <div style="color: var(--text-secondary); text-align: center; margin-top: 40px; padding: 20px;">
        <div style="font-size: 1.5rem; margin-bottom: 8px;">🌱</div>
        <div>${t('no_bio_bodies')}</div>
      </div>
    `;
    return;
  }

  const list = document.createElement('div');
  list.style.display = 'flex';
  list.style.flexDirection = 'column';
  list.style.gap = '12px';

  // Place active/targeted body at the top if present in bioBodies
  const targetId = state.targetBodyId !== null && state.targetBodyId !== undefined ? state.targetBodyId : (state.selectedBody ? state.selectedBody.body_id : null);
  let displayBioBodies = [...bioBodies];
  if (targetId !== null) {
    const targetIdx = displayBioBodies.findIndex(b => b.body_id === targetId);
    if (targetIdx > 0) {
      const targetBody = displayBioBodies.splice(targetIdx, 1)[0];
      displayBioBodies.unshift(targetBody);
    }
  }

  displayBioBodies.forEach(body => {
    const isTarget = targetId !== null && body.body_id === targetId;
    const card = document.createElement('div');
    card.className = `node-card ${state.selectedBody && state.selectedBody.body_id === body.body_id ? 'selected' : ''} ${isTarget ? 'is-current-target' : ''}`;
    card.dataset.bodyId = body.body_id;
    card.style.borderColor = isTarget ? 'var(--ed-green)' : (body.is_bio_completed ? 'rgba(0, 255, 136, 0.2)' : 'rgba(0, 255, 136, 0.5)');
    card.onclick = () => {
      state.selectedBody = body;
      state.targetBodyId = body.body_id;
      renderBodyInspector();
      document.querySelectorAll('.node-card').forEach(nc => nc.classList.remove('selected'));
      card.classList.add('selected');
    };

    const iconClass = getBodyIconClass(body);
    const iconLabel = getBodyIconLabel(body);
    const bioHtml = renderBodyExobiologyBlock(body);
    const geoHtml = renderBodyGeoBlock(body);

    const completionBadge = body.is_bio_completed
      ? `<span class="tag-badge" style="background: rgba(0, 255, 136, 0.2); color: var(--ed-green); border: 1px solid rgba(0, 255, 136, 0.4); font-size: 0.72rem;">✅ ${t('bio_body_all_completed')}</span>`
      : `<span class="tag-badge" style="background: rgba(255, 113, 0, 0.15); color: var(--ed-orange); border: 1px solid rgba(255, 113, 0, 0.3); font-size: 0.72rem;">🌱 採取進捗: ${body.completed_bio_count || 0} / ${body.bio_signals || 0}</span>`;

    const targetBadge = isTarget ? '<span class="tag-badge" style="background: rgba(0, 255, 136, 0.25); color: var(--ed-green); border: 1px solid rgba(0, 255, 136, 0.8); font-weight: bold; font-size: 0.72rem;">🎯 ACTIVE TARGET (探査中)</span>' : '';

    card.innerHTML = `
      <div class="node-card-top">
        <div class="node-info-left">
          <div class="body-icon ${iconClass}">${iconLabel}</div>
          <div class="node-details">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
              <div class="node-name" style="color: var(--ed-green); font-weight: bold;">${body.body_name}</div>
              ${targetBadge}
              ${completionBadge}
            </div>
            <div class="node-subtext">${body.planet_class || 'Landable World'}</div>
          </div>
        </div>
        <div class="node-info-right">
          <span class="node-distance">${formatDistance(body.distance_from_arrival_ls)}</span>
        </div>
      </div>
      ${geoHtml}
      ${bioHtml}
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

  // Exobiology Predictions & Confirmed
  const bioInfo = document.getElementById('inspect-bio-signals-info');
  const bioContainer = document.getElementById('inspect-bio-predictions');
  const scannedOrganics = b.scanned_organics || [];
  const potBio = b.potential_exobiology || b.exobiology || [];

  if (b.bio_signals > 0 || scannedOrganics.length > 0 || potBio.length > 0) {
    bioInfo.innerText = `${t('bio_signals_detected')}: ${b.bio_signals || 0} (${t('bio_status_confirmed')}: ${scannedOrganics.length})`;
    
    let html = '';
    
    // Confirmed
    if (scannedOrganics.length > 0) {
      html += scannedOrganics.map(org => {
        const spName = org.species_localised || org.species || org.genus_localised || org.genus;
        const genName = org.genus_localised || org.genus || '';
        const baseVal = org.base_value || 0;
        const fdVal = org.first_discovery_value || (baseVal * 5);
        const dist = org.colony_distance_m || 500;
        return `
          <div class="bio-pred-card" style="border-color: rgba(0, 255, 136, 0.4); background: rgba(0, 255, 136, 0.06);">
            <div class="bio-pred-header">
              <span class="bio-species-name" style="color: var(--ed-green);">✓ [${t('bio_status_confirmed')}] ${spName} ${genName && genName !== spName ? `(${genName})` : ''}</span>
              <span class="bio-sample-dist">${t('bio_dist_req')} ${dist}m</span>
            </div>
            <div class="bio-payout-row">
              <span>${t('bio_base_payout')} ${formatCredits(baseVal)}</span>
              <span class="bio-first-bonus">${t('bio_first_bonus')} ${formatCredits(fdVal)}</span>
            </div>
          </div>
        `;
      }).join('');
    }

    // Exobiology matrix
    const scannedGenusSet = new Set(scannedOrganics.map(s => (s.genus_localised || s.genus || '').toLowerCase()));
    const scannedSpeciesSet = new Set(scannedOrganics.map(s => (s.species_localised || s.species || '').toLowerCase()));
    const isFullyScanned = (b.bio_signals > 0 && scannedOrganics.length >= b.bio_signals);

    const allBio = b.exobiology || b.potential_exobiology || [];

    if (allBio.length > 0) {
      allBio.forEach(bio => {
        const sp = (bio.species || '').toLowerCase();
        const gen = (bio.genus || '').toLowerCase();

        if (scannedSpeciesSet.has(sp)) return; // Already rendered above

        let colorBadges = '';
        if (bio.variant_color) {
          colorBadges += `<span class="tag-badge" style="background: rgba(250, 204, 21, 0.15); color: #fde047; border: 1px solid rgba(250, 204, 21, 0.35); font-size: 0.65rem;" title="恒星スペクトル型による主要カラー">🎨 ${bio.variant_color}</span>`;
        }
        if (bio.alternate_variants && bio.alternate_variants.length > 0) {
          colorBadges += bio.alternate_variants.slice(0, 3).map(c => `
            <span class="tag-badge" style="background: rgba(148, 163, 184, 0.12); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); font-size: 0.62rem;" title="可能性のある他カラー候補">🎨 ${c}</span>
          `).join('');
        }
        const isExcluded = scannedGenusSet.has(gen) || isFullyScanned;
        const matchPct = bio.possible_pct !== undefined ? bio.possible_pct : (bio.match_percentage !== undefined ? bio.match_percentage : (bio.fit_score ? Math.round(bio.fit_score * 100) : null));
        const pctBadge = (matchPct !== null && matchPct !== undefined) 
          ? `<span class="tag-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.65rem;" title="環境適合度 (Possible %)">📊 Possible: ${matchPct}%</span>` 
          : '';
        const coherentBadge = bio.is_system_coherent 
          ? `<span class="tag-badge" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); font-size: 0.65rem;" title="同一星系内で他天体と同一種として共起重み付け">🪐 同星系共起</span>` 
          : '';
        const isDefinite = bio.confidence === 'definite';
        const statusLabel = isDefinite ? (t('bio_status_definite') || '有力候補') : (t('bio_status_potential') || '次点候補');
        const icon = isDefinite ? '🌱' : '🌿';

        if (isExcluded) {
          html += `
            <div class="bio-pred-card" style="opacity: 0.45; filter: grayscale(40%);">
              <div class="bio-pred-header">
                <span class="bio-species-name" style="color: #94a3b8; text-decoration: line-through;">✕ [${t('bio_status_excluded') || '除外'}] ${spName}</span>
                ${pctBadge}
                <span class="bio-sample-dist">📍 ${bio.colony_distance_m || 500}m</span>
              </div>
              <div class="bio-payout-row">
                <span style="color: #64748b;">${formatCredits(bio.base_value)}</span>
              </div>
            </div>
          `;
        } else {
          html += `
            <div class="bio-pred-card" style="${isDefinite ? 'border-color: rgba(0, 255, 136, 0.25);' : ''}">
              <div class="bio-pred-header">
                <span class="bio-species-name" style="${isDefinite ? 'color: var(--ed-green); font-weight: bold;' : ''}">${icon} [${statusLabel}] ${spName} ${bio.genus && !spName.includes(bio.genus) ? `(${bio.genus})` : ''}</span>
                ${pctBadge}
                ${coherentBadge}
                ${colorBadges}
                <span class="bio-sample-dist">📍 ${bio.colony_distance_m || 500}m</span>
              </div>
              ${bio.description ? `<div style="font-size: 0.72rem; color: var(--text-secondary); margin-bottom: 4px;">${bio.description}</div>` : ''}
              <div class="bio-payout-row">
                <span>${t('bio_base_payout')} ${formatCredits(bio.base_value)}</span>
                <span class="bio-first-bonus">${t('bio_first_bonus')} ${formatCredits(bio.first_discovery_value)}</span>
              </div>
            </div>
          `;
        }
      });
    }

    if (!html) {
      html = `<div style="font-size: 0.75rem; color: var(--text-secondary);">${t('bio_none_desc')}</div>`;
    }

    bioContainer.innerHTML = html;
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

  const ATMOSPHERE_JA_MAP = {
    'carbon dioxide': '二酸化炭素',
    'ammonia': 'アンモニア',
    'water': '水',
    'methane': 'メタン',
    'nitrogen': '窒素',
    'argon': 'アルゴン',
    'helium': 'ヘリウム',
    'oxygen': '酸素',
    'sulphur dioxide': '二酸化硫黄',
    'neon': 'ネオン',
    'silicate vapour': 'ケイ酸塩蒸気',
    'metallic vapour': '金属蒸気',
    'suitable for water-based life': '水系生命に適する'
  };

  function formatAtmosphereDescription(rawAtmo) {
    if (!rawAtmo || rawAtmo === 'None') return 'None (なし)';
    let lower = rawAtmo.toLowerCase();
    for (const [enKey, jaVal] of Object.entries(ATMOSPHERE_JA_MAP)) {
      if (lower.includes(enKey)) {
        return `${rawAtmo} (${jaVal})`;
      }
    }
    return rawAtmo;
  }

  function formatSurfacePressure(atm) {
    if (atm === null || atm === undefined) return (b.atmosphere ? 'Thin Atmosphere' : 'None (Vacuum)');
    const pa = atm * 101325;
    if (pa >= 1000000) {
      return `${atm.toFixed(4)} atm (${(pa / 1000000).toFixed(3)} MPa / ${Math.round(pa).toLocaleString()} Pa)`;
    } else if (pa >= 1000) {
      return `${atm.toFixed(4)} atm (${(pa / 1000).toFixed(2)} kPa / ${Math.round(pa).toLocaleString()} Pa)`;
    } else {
      return `${atm.toFixed(4)} atm (${Math.round(pa).toLocaleString()} Pa)`;
    }
  }

  document.getElementById('prop-temperature').innerText = b.surface_temperature ? `${b.surface_temperature.toFixed(0)} K (${(b.surface_temperature - 273.15).toFixed(0)} °C)` : '--';
  document.getElementById('prop-pressure').innerText = formatSurfacePressure(b.surface_pressure);
  document.getElementById('prop-atmosphere').innerText = formatAtmosphereDescription(b.atmosphere);
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

  // Rings & Fleet Carrier Fuel (Tritium Mining in Icy Rings)
  const ringsSection = document.getElementById('section-rings');
  const ringsList = document.getElementById('inspect-rings-list');
  if (b.rings_list && b.rings_list.length > 0) {
    ringsSection.style.display = 'block';

    const hasIcyRing = b.rings_list.some(r => (r.RingClass || '').toLowerCase().includes('icy'));
    const fcMiningBadge = hasIcyRing 
      ? `<div style="background: rgba(0, 210, 255, 0.12); border: 1px solid rgba(0, 210, 255, 0.4); border-radius: 4px; padding: 6px 10px; margin-bottom: 8px; font-size: 0.78rem; color: #a5f3fc; font-weight: bold; display: flex; align-items: center; gap: 6px;">
          <span>💎 Fleet Carrier 燃料 (Tritium) 採掘適性:</span>
          <span style="color: #38bdf8;">✓ 採掘可能 (Icy Ring 検出)</span>
         </div>`
      : `<div style="background: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 4px; padding: 6px 10px; margin-bottom: 8px; font-size: 0.78rem; color: #94a3b8; display: flex; align-items: center; gap: 6px;">
          <span>💎 Fleet Carrier 燃料 (Tritium) 採掘適性:</span>
          <span>氷リングなし (Icy Ring Not Found)</span>
         </div>`;

    ringsList.innerHTML = fcMiningBadge + b.rings_list.map(r => {
      const rClass = (r.RingClass || '').replace('eRingClass_', '');
      const isIcy = rClass.toLowerCase().includes('icy');
      const classBadge = isIcy 
        ? `<span class="tag-badge" style="background: rgba(0, 210, 255, 0.2); color: #38bdf8; border: 1px solid rgba(0, 210, 255, 0.4); font-weight: bold;">❄️ Icy Ring (氷)</span>`
        : `<span class="tag-badge">${rClass || 'Ring'}</span>`;

      return `
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 4px; padding: 8px 10px; margin-bottom: 6px; font-size: 0.75rem;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: var(--ed-gold);">${r.Name || 'Ring'}</span>
            ${classBadge}
          </div>
          <div style="color: var(--text-secondary); margin-top: 4px;">
            外径: ${(r.OuterRad / 1000).toLocaleString()} km / 質量: ${(r.MassMT || 0).toLocaleString()} MT
          </div>
        </div>
      `;
    }).join('');
  } else {
    ringsSection.style.display = 'none';
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  updateStaticTexts();
  initSettingsModal();
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
    fetchGlobalStats();
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
      fetchGlobalStats();
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
    if (state.liveSyncEnabled || e.target.value === 'live-locked') return;
    const [by, order] = e.target.value.split('-');
    state.savedSortBy = by;
    state.savedSortOrder = order;
    state.sortBy = by;
    state.sortOrder = order;
    state.page = 1;
    fetchSystems();
  });

  // Sort select 2 for systems
  const sortSelect2 = document.getElementById('sort-select-2');
  if (sortSelect2) {
    sortSelect2.addEventListener('change', (e) => {
      if (state.liveSyncEnabled) return;
      if (e.target.value === 'none') {
        state.savedSortBy2 = null;
        state.sortBy2 = null;
      } else {
        const [by, order] = e.target.value.split('-');
        state.savedSortBy2 = by;
        state.savedSortOrder2 = order;
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
  const btnViewSysmap = document.getElementById('btn-view-sysmap');
  if (btnViewSysmap) {
    btnViewSysmap.addEventListener('click', () => {
      state.currentView = 'sysmap';
      updateViewButtons();
      renderCurrentView();
    });
  }

  document.getElementById('btn-view-flat').addEventListener('click', () => {
    state.currentView = 'flat';
    updateViewButtons();
    renderCurrentView();
  });

  const btnViewBio = document.getElementById('btn-view-bio');
  if (btnViewBio) {
    btnViewBio.addEventListener('click', () => {
      state.currentView = 'bio';
      updateViewButtons();
      renderCurrentView();
    });
  }

  document.getElementById('btn-view-visits').addEventListener('click', () => {
    state.currentView = 'visits';
    updateViewButtons();
    renderCurrentView();
  });

  function updateViewButtons() {
    const btnSys = document.getElementById('btn-view-sysmap');
    const btnFlat = document.getElementById('btn-view-flat');
    const btnBio = document.getElementById('btn-view-bio');
    const btnVis = document.getElementById('btn-view-visits');

    if (btnSys) btnSys.classList.toggle('active', state.currentView === 'sysmap');
    if (btnFlat) btnFlat.classList.toggle('active', state.currentView === 'flat');
    if (btnBio) btnBio.classList.toggle('active', state.currentView === 'bio');
    if (btnVis) btnVis.classList.toggle('active', state.currentView === 'visits');

    // Show completed bio filter container only on bio view
    const bioFilterContainer = document.getElementById('bio-filter-hide-completed-container');
    if (bioFilterContainer) {
      bioFilterContainer.style.display = state.currentView === 'bio' ? 'inline-flex' : 'none';
    }
  }

  // Hide completed bio checkbox event
  const cbHideCompletedBio = document.getElementById('cb-hide-completed-bio');
  if (cbHideCompletedBio) {
    cbHideCompletedBio.addEventListener('change', () => {
      renderCurrentView();
    });
  }

  // Credits Modal Events
  const btnCreditsOpen = document.getElementById('btn-credits-open');
  const btnCreditsClose = document.getElementById('btn-credits-close');
  const creditsModal = document.getElementById('credits-modal');

  if (btnCreditsOpen && creditsModal) {
    btnCreditsOpen.addEventListener('click', () => {
      creditsModal.style.display = 'flex';
    });
  }
  if (btnCreditsClose && creditsModal) {
    btnCreditsClose.addEventListener('click', () => {
      creditsModal.style.display = 'none';
    });
  }
  if (creditsModal) {
    creditsModal.addEventListener('click', (e) => {
      if (e.target === creditsModal) {
        creditsModal.style.display = 'none';
      }
    });
  }

  // Live Sync Toggle Button
  const btnLiveToggle = document.getElementById('btn-live-toggle');
  if (btnLiveToggle) {
    btnLiveToggle.addEventListener('click', () => {
      state.liveSyncEnabled = !state.liveSyncEnabled;
      state.page = 1;
      updateLiveSyncButtonUI();
      updateSortControlsUI();
      fetchSystems();
    });
  }

  // Scan Button (if exists)
  const btnRescan = document.getElementById('btn-rescan');
  if (btnRescan) {
    btnRescan.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/scan_now', { method: 'POST' });
        pollScanProgress();
      } catch (err) {
        console.error('Failed to trigger scan:', err);
      }
    });
  }

  // Start Realtime Live Sync
  initLiveSync();
});

function updateLiveSyncButtonUI() {
  const btn = document.getElementById('btn-live-toggle');
  const txt = document.getElementById('live-status-text');
  if (!btn || !txt) return;

  if (state.liveSyncEnabled) {
    btn.className = 'btn-live active';
    btn.title = t('live_sync_tip');
    txt.innerText = t('live_sync_on');
  } else {
    btn.className = 'btn-live paused';
    btn.title = t('live_sync_tip');
    txt.innerText = t('live_sync_off');
  }
}

function updateSortControlsUI() {
  const sortSelect1 = document.getElementById('sort-select');
  const sortSelect2 = document.getElementById('sort-select-2');
  if (!sortSelect1) return;

  if (state.liveSyncEnabled) {
    sortSelect1.disabled = true;
    if (sortSelect2) sortSelect2.disabled = true;

    // Insert or update live-locked option at the top
    let optLocked = sortSelect1.querySelector('option[value="live-locked"]');
    if (!optLocked) {
      optLocked = document.createElement('option');
      optLocked.value = 'live-locked';
      sortSelect1.insertBefore(optLocked, sortSelect1.firstChild);
    }
    optLocked.innerText = t('sort_live_locked');
    sortSelect1.value = 'live-locked';
    if (sortSelect2) sortSelect2.value = 'none';

    document.querySelectorAll('.sort-row').forEach(el => el.classList.add('sort-locked'));
  } else {
    sortSelect1.disabled = false;
    if (sortSelect2) sortSelect2.disabled = false;

    // Remove live-locked option
    const optLocked = sortSelect1.querySelector('option[value="live-locked"]');
    if (optLocked) {
      optLocked.remove();
    }

    // Restore saved user sort selections
    const savedVal1 = `${state.savedSortBy || 'total_potential_value'}-${state.savedSortOrder || 'desc'}`;
    sortSelect1.value = savedVal1;
    if (sortSelect2) {
      sortSelect2.value = state.savedSortBy2 ? `${state.savedSortBy2}-${state.savedSortOrder2}` : 'none';
    }

    document.querySelectorAll('.sort-row').forEach(el => el.classList.remove('sort-locked'));
  }
}

async function triggerLiveRefresh() {
  if (!state.liveSyncEnabled) return;
  
  // Refresh global statistics
  fetchGlobalStats();

  // Refresh systems list
  await fetchSystems();

  // Refresh currently selected system in center pane if open
  if (state.selectedSystem && state.selectedSystem.system_address) {
    selectSystem(state.selectedSystem.system_address, true, false);
  }
}

// Real-time Live Sync (WebSocket + Polling Fallback)
let liveWebSocket = null;
let liveWsRetryTimeout = null;

function initLiveSync() {
  updateLiveSyncButtonUI();
  updateSortControlsUI();
  connectLiveWebSocket();

  // High-frequency polling fallback (every 600ms) to ensure instant updates
  setInterval(async () => {
    if (!state.liveSyncEnabled) return;
    try {
      const res = await fetch('/api/events/latest');
      if (res.ok) {
        const evt = await res.json();
        let changed = false;

        if (evt.event_version && evt.event_version !== state.lastJournalEventVersion) {
          state.lastJournalEventVersion = evt.event_version;
          if (evt.last_event && evt.last_event.event) {
            handleLiveJournalEvent(evt.last_event.event, evt.last_event.data || {});
            changed = true;
          }
        }

        if (evt.version && evt.version !== state.lastEventVersion) {
          state.lastEventVersion = evt.version;
          if (!changed) {
            triggerLiveRefresh();
          }
        }
      }
    } catch (err) {
      // Ignore background network jitter
    }
  }, 600);
}

const announcedFirstDiscSystems = new Set();

async function checkAndAnnounceLiveFirstDiscovery(sysAddr, defaultName = '') {
  if (!ttsState.enabled || !sysAddr) return;
  if (announcedFirstDiscSystems.has(String(sysAddr))) return;

  try {
    const res = await fetch(`/api/system/${sysAddr}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.system && (data.system.has_first_discover || (data.system.first_discovered_bodies && data.system.first_discovered_bodies > 0))) {
      announcedFirstDiscSystems.add(String(sysAddr));
      announceFirstDiscovery(data.system.star_system || defaultName, data.system.first_discovered_bodies || 1);
    }
  } catch (e) {
    console.warn('Failed to check live first discovery:', e);
  }
}

function clearSystemBioSummary() {
  const bioBox = document.getElementById('system-bio-payout-box');
  if (bioBox) bioBox.style.display = 'none';
  const bioScannedBaseEl = document.getElementById('current-system-bio-scanned-base');
  const bioScannedFirstEl = document.getElementById('current-system-bio-scanned-first');
  const bioBaseEl = document.getElementById('current-system-bio-base');
  const bioFirstEl = document.getElementById('current-system-bio-first');
  if (bioScannedBaseEl) bioScannedBaseEl.innerText = '0 Cr';
  if (bioScannedFirstEl) bioScannedFirstEl.innerText = '0 Cr';
  if (bioBaseEl) bioBaseEl.innerText = '-- Cr';
  if (bioFirstEl) bioFirstEl.innerText = '-- Cr';
}

function handleLiveJournalEvent(eventName, eventData) {
  if (!state.liveSyncEnabled) return;

  if (eventName === 'StartJump') {
    const jumpType = eventData.JumpType || 'Hyperspace';
    if (jumpType === 'Hyperspace') {
      state.jumpState = 'hyperspace';
      state.targetJumpSystem = eventData.StarSystem || 'Unknown';
      clearSystemBioSummary();
      clearBodyInspector();
      renderCurrentView();
    }
  } else if (eventName === 'FSDJump' || eventName === 'Location' || eventName === 'CarrierJump') {
    state.jumpState = 'arrived_waiting_fss';
    state.targetJumpSystem = eventData.StarSystem || '';
    clearSystemBioSummary();
    
    // Refresh global stats & systems list
    fetchGlobalStats();
    fetchSystems();

    if (eventData.SystemAddress) {
      selectSystem(eventData.SystemAddress, false, false);
      checkAndAnnounceLiveFirstDiscovery(eventData.SystemAddress, eventData.StarSystem);
    } else {
      renderCurrentView();
    }
  } else if (eventName === 'FSSDiscoveryScan') {
    state.jumpState = 'scanned';
    fetchGlobalStats();
    fetchSystems();

    const sysAddr = eventData.SystemAddress || (state.selectedSystem ? state.selectedSystem.system_address : null);
    if (sysAddr) {
      selectSystem(sysAddr, false, false);
      checkAndAnnounceLiveFirstDiscovery(sysAddr, eventData.StarSystem || (state.selectedSystem ? state.selectedSystem.star_system : ''));
    } else {
      triggerLiveRefresh();
    }
  } else if (eventName === 'Scan' || eventName === 'SAAScanComplete' || eventName === 'ScanOrganic' || eventName === 'FSSBodySignals' || eventName === 'SAASignalsFound') {
    const sysAddr = eventData.SystemAddress || (state.selectedSystem ? state.selectedSystem.system_address : null);
    fetchGlobalStats();
    fetchSystems();

    if (sysAddr && state.selectedSystem && String(state.selectedSystem.system_address) === String(sysAddr)) {
      selectSystem(sysAddr, true, false);
      checkAndAnnounceLiveFirstDiscovery(sysAddr, eventData.StarSystem || (state.selectedSystem ? state.selectedSystem.star_system : ''));
    } else {
      triggerLiveRefresh();
    }
  }
}

function connectLiveWebSocket() {
  if (liveWsRetryTimeout) {
    clearTimeout(liveWsRetryTimeout);
    liveWsRetryTimeout = null;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/live`;

  try {
    liveWebSocket = new WebSocket(wsUrl);

    liveWebSocket.onopen = () => {
      // Ping interval to keep connection alive
      if (liveWebSocket._pingInterval) clearInterval(liveWebSocket._pingInterval);
      liveWebSocket._pingInterval = setInterval(() => {
        if (liveWebSocket && liveWebSocket.readyState === WebSocket.OPEN) {
          liveWebSocket.send('ping');
        }
      }, 10000);
    };

    liveWebSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'journal_event') {
          if (data.version) state.lastJournalEventVersion = data.version;
          handleLiveJournalEvent(data.event, data.data || {});
        } else if (data.type === 'journal_updated') {
          state.lastEventVersion = data.version;
          triggerLiveRefresh();
        }
      } catch (err) {
        // Ping/pong or text messages
      }
    };

    liveWebSocket.onclose = () => {
      if (liveWebSocket && liveWebSocket._pingInterval) {
        clearInterval(liveWebSocket._pingInterval);
      }
      liveWsRetryTimeout = setTimeout(connectLiveWebSocket, 1500);
    };

    liveWebSocket.onerror = () => {
      try {
        liveWebSocket.close();
      } catch (e) {}
    };
  } catch (err) {
    liveWsRetryTimeout = setTimeout(connectLiveWebSocket, 2000);
  }
}

async function checkScanOnStartup() {
  try {
    const res = await fetch('/api/scan_status');
    const st = await res.json();
    if (st.is_scanning) {
      pollScanProgress();
    } else if (st.total === 0) {
      // If db has 0 files, trigger scan
      const triggerRes = await fetch('/api/scan_now', { method: 'POST' });
      pollScanProgress();
    }
  } catch (err) {
    // Ignore on startup
  }
}

// Scan Polling
let scanPollInterval = null;

function pollScanProgress() {
  const banner = document.getElementById('scan-banner');
  const bannerTitle = document.getElementById('scan-banner-title');
  const bannerCount = document.getElementById('scan-banner-count');
  const bannerPercent = document.getElementById('scan-banner-percent');
  const bannerFile = document.getElementById('scan-banner-file');
  const progressFill = document.getElementById('scan-progress-bar-fill');
  const spinner = document.getElementById('scan-banner-spinner');

  if (banner) {
    banner.classList.remove('completed');
    banner.style.display = 'block';
  }
  if (spinner) spinner.style.display = 'inline-block';

  if (scanPollInterval) {
    clearInterval(scanPollInterval);
    scanPollInterval = null;
  }

  let pollCount = 0;
  scanPollInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/scan_status');
      const st = await res.json();

      if (st.is_scanning) {
        if (bannerTitle) bannerTitle.innerText = t('scanning_banner');
        if (bannerCount) bannerCount.innerText = `${st.current} / ${st.total}`;
        if (bannerPercent) bannerPercent.innerText = `${st.percent || 0}%`;
        if (bannerFile) bannerFile.innerText = st.filename ? `📁 ${st.filename}` : '';
        if (progressFill) progressFill.style.width = `${Math.max(2, st.percent || 0)}%`;

        pollCount++;
        // Refresh UI list and stats every 3 polls (~750ms) so user sees progress
        if (pollCount % 3 === 0) {
          fetchGlobalStats();
          fetchSystems();
        }
      } else {
        if (bannerTitle) bannerTitle.innerText = t('scan_complete') || 'ジャーナル解析完了';
        if (bannerCount) bannerCount.innerText = `${st.total} / ${st.total}`;
        if (bannerPercent) bannerPercent.innerText = '100%';
        if (bannerFile) bannerFile.innerText = t('scan_success_tip') || `${st.total} 件のジャーナルログを正常に同期しました`;
        if (progressFill) progressFill.style.width = '100%';
        if (spinner) spinner.style.display = 'none';
        if (banner) banner.classList.add('completed');

        clearInterval(scanPollInterval);
        scanPollInterval = null;

        // Instant full UI refresh
        fetchGlobalStats();
        fetchSystems();

        setTimeout(() => {
          if (banner) {
            banner.style.display = 'none';
            banner.classList.remove('completed');
          }
        }, 2500);
      }
    } catch (err) {
      if (scanPollInterval) {
        clearInterval(scanPollInterval);
        scanPollInterval = null;
      }
    }
  }, 250);
}

// =============================================================================
// Text-to-Speech (TTS) Voice Notification System
// Supports Web Speech API (Microsoft Natural / Multilingual) & VOICEVOX (Local)
// =============================================================================

const ttsState = {
  enabled: false,
  highBioEnabled: true,
  highBioMode: 'both', // 'both' | 'tts' | 'buzzer'
  highBioText: '{body}、高額生物反応です。見込額{value}クレジット。',
  engine: 'web_speech', // 'web_speech' | 'voicevox'
  webVoiceURI: '',
  voicevoxSpeakerId: '3', // ずんだもん (ノーマル)
  voicevoxUrl: 'http://127.0.0.1:50021',
  customText: 'First discover.',
  volume: 1.0,
  rate: 1.0
};

const announcedHighBioBodies = new Set();

function playHighBioBuzzer() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    const now = ctx.currentTime;

    // Harmonic 3-tone chime: 587.33Hz (D5) -> 880Hz (A5) -> 1174.66Hz (D6)
    const notes = [
      { freq: 587.33, start: 0, dur: 0.12 },
      { freq: 880.00, start: 0.12, dur: 0.14 },
      { freq: 1174.66, start: 0.26, dur: 0.35 }
    ];

    notes.forEach(n => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(n.freq, now + n.start);

      gain.gain.setValueAtTime(0, now + n.start);
      gain.gain.linearRampToValueAtTime(0.3 * (ttsState.volume || 1.0), now + n.start + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + n.start + n.dur);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + n.start);
      osc.stop(now + n.start + n.dur);
    });
  } catch (e) {
    console.warn('Audio buzzer failed:', e);
  }
}

function checkAndAnnounceHighBioBody(sysData, bodyData) {
  if (!ttsState.highBioEnabled) return;
  if (!bodyData) return;

  const bodyName = bodyData.body_name || bodyData.BodyName;
  const sysAddr = bodyData.system_address || (sysData ? sysData.system_address : null);
  if (!bodyName) return;

  const alertKey = `${sysAddr || 'sys'}_${bodyName}`;
  if (announcedHighBioBodies.has(alertKey)) return;

  // Check if system is 1st Discover or currently unvisited / has undiscovered bodies
  const isFirstDiscoverSystem = sysData && (
    sysData.has_first_discover === 1 || 
    sysData.has_first_discover === true || 
    sysData.edsm_registered === 0 || 
    sysData.edsm_registered === false ||
    !sysData.edsm_registered
  );

  if (!isFirstDiscoverSystem) return;

  // Calculate estimated Exobiology total payout with 1st Discover bonus (5x multiplier)
  let predictedCandidates = [];
  if (bodyData.predicted_bio_candidates && Array.isArray(bodyData.predicted_bio_candidates)) {
    predictedCandidates = bodyData.predicted_bio_candidates;
  }

  if (!predictedCandidates || predictedCandidates.length === 0) return;

  // Sum top definite candidates' first_discovery_value (or base_value * 5)
  let totalEstimatedBio = 0;
  const bioBudget = bodyData.bio_signals || predictedCandidates.length;
  const definiteCandidates = predictedCandidates.slice(0, bioBudget);

  definiteCandidates.forEach(cand => {
    const bonusVal = cand.first_discovery_value || ((cand.base_value || 1000000) * 5);
    totalEstimatedBio += bonusVal;
  });

  // Threshold: 40,000,000 Cr (40M)
  if (totalEstimatedBio >= 40000000) {
    announcedHighBioBodies.add(alertKey);

    const formattedPayout = (totalEstimatedBio / 1000000).toFixed(1) + 'M';
    const msg = (ttsState.highBioText || '{body}、高額生物反応です。見込額{value}クレジット。')
      .replace(/\{body\}/gi, bodyName)
      .replace(/\{value\}/gi, formattedPayout)
      .replace(/\{payout\}/gi, formattedPayout)
      .replace(/\{system\}/gi, sysData ? (sysData.star_system || '') : '');

    // Trigger Mode
    if (ttsState.highBioMode === 'buzzer' || ttsState.highBioMode === 'both') {
      playHighBioBuzzer();
    }
    if (ttsState.highBioMode === 'tts' || ttsState.highBioMode === 'both') {
      setTimeout(() => {
        if (ttsState.engine === 'voicevox') {
          playVoicevoxSpeech(msg);
        } else {
          playWebSpeech(msg);
        }
      }, ttsState.highBioMode === 'both' ? 600 : 0);
    }
  }
}

async function loadTTSSettings() {
  try {
    const res = await fetch('/api/tts_settings');
    if (res.ok) {
      const data = await res.json();
      Object.assign(ttsState, data);
    } else {
      const saved = localStorage.getItem('ed_analyzer_tts_settings');
      if (saved) Object.assign(ttsState, JSON.parse(saved));
    }
  } catch (e) {
    const saved = localStorage.getItem('ed_analyzer_tts_settings');
    if (saved) Object.assign(ttsState, JSON.parse(saved));
  }
  updateTTSHeaderIcon();
}

async function saveTTSSettings() {
  try {
    localStorage.setItem('ed_analyzer_tts_settings', JSON.stringify(ttsState));
    await fetch('/api/tts_settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ttsState)
    });
  } catch (e) {
    console.warn('Failed to save TTS settings to server:', e);
  }
  updateTTSHeaderIcon();
}

function updateTTSHeaderIcon() {
  const iconEl = document.getElementById('tts-header-icon');
  const btnEl = document.getElementById('btn-tts-settings-open');
  if (iconEl && btnEl) {
    if (ttsState.enabled) {
      iconEl.innerText = '🔊 TTS';
      btnEl.style.color = 'var(--ed-cyan)';
      btnEl.style.borderColor = 'rgba(0, 210, 255, 0.4)';
    } else {
      iconEl.innerText = '🔇 TTS';
      btnEl.style.color = 'var(--text-secondary)';
      btnEl.style.borderColor = 'transparent';
    }
  }
}

function formatTTSMessage(template, params = {}) {
  let text = template || 'First discover.';
  const systemName = params.system || params.system_name || (state.selectedSystem ? state.selectedSystem.star_system : 'Sol');
  const bodiesCount = params.bodies !== undefined ? String(params.bodies) : '1';

  text = text.replace(/\{system\}/gi, systemName);
  text = text.replace(/\{system_name\}/gi, systemName);
  text = text.replace(/\{bodies\}/gi, bodiesCount);
  return text;
}

function populateWebVoices() {
  if (!('speechSynthesis' in window)) return;
  const select = document.getElementById('tts-web-voice-select');
  if (!select) return;

  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return;

  const currentSelection = ttsState.webVoiceURI || select.value;
  select.innerHTML = '<option value="">システム既定の音声 (Default)</option>';

  const jaVoices = [];
  const enVoices = [];
  const otherVoices = [];

  voices.forEach(v => {
    if (v.lang.startsWith('ja')) jaVoices.push(v);
    else if (v.lang.startsWith('en')) enVoices.push(v);
    else otherVoices.push(v);
  });

  const appendVoiceGroup = (groupLabel, voiceList) => {
    if (!voiceList || voiceList.length === 0) return;
    const optgroup = document.createElement('optgroup');
    optgroup.label = groupLabel;

    voiceList.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.voiceURI;
      const isOnline = v.name.includes('Online') || v.name.includes('Natural');
      const onlineTag = isOnline ? ' [🌐 Natural]' : '';
      const defTag = v.default ? ' ★' : '';
      opt.innerText = `${v.name}${onlineTag} (${v.lang})${defTag}`;
      if (v.voiceURI === currentSelection) {
        opt.selected = true;
      }
      optgroup.appendChild(opt);
    });
    select.appendChild(optgroup);
  };

  appendVoiceGroup('日本語 (Japanese)', jaVoices);
  appendVoiceGroup('英語 (English)', enVoices);
  appendVoiceGroup('その他の言語 (Other Languages)', otherVoices);
}

async function checkVoicevoxConnection() {
  const statusEl = document.getElementById('tts-voicevox-status');
  const speakerSelect = document.getElementById('tts-voicevox-speaker-select');
  if (!statusEl) return;

  try {
    const res = await fetch(`${ttsState.voicevoxUrl}/speakers`, { method: 'GET' });
    if (!res.ok) throw new Error('Status ' + res.status);
    const speakers = await res.json();
    
    if (speakerSelect && Array.isArray(speakers)) {
      speakerSelect.innerHTML = '';
      speakers.forEach(sp => {
        const group = document.createElement('optgroup');
        group.label = sp.name;
        if (sp.styles && Array.isArray(sp.styles)) {
          sp.styles.forEach(st => {
            const opt = document.createElement('option');
            opt.value = String(st.id);
            opt.innerText = `${sp.name} (${st.name})`;
            if (String(st.id) === String(ttsState.voicevoxSpeakerId)) {
              opt.selected = true;
            }
            group.appendChild(opt);
          });
        }
        speakerSelect.appendChild(group);
      });
    }

    statusEl.innerHTML = '<span style="color: #6ee7b7;">🟢 VOICEVOX 接続成功 (127.0.0.1:50021)</span>';
  } catch (err) {
    statusEl.innerHTML = '<span style="color: #94a3b8;">🔴 VOICEVOX 未検出 (起動すると自動連携されます。未起動時はWeb Speech APIが使われます)</span>';
  }
}

function playWebSpeech(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const uttr = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();
  if (ttsState.webVoiceURI && voices && voices.length > 0) {
    const v = voices.find(v => v.voiceURI === ttsState.webVoiceURI);
    if (v) uttr.voice = v;
  }
  uttr.volume = Math.max(0, Math.min(1, ttsState.volume));
  uttr.rate = Math.max(0.5, Math.min(2.0, ttsState.rate));
  window.speechSynthesis.speak(uttr);
}

async function playVoicevoxSpeech(text) {
  try {
    const queryRes = await fetch(`${ttsState.voicevoxUrl}/audio_query?text=${encodeURIComponent(text)}&speaker=${ttsState.voicevoxSpeakerId}`, {
      method: 'POST'
    });
    if (!queryRes.ok) throw new Error('Audio query failed');
    const queryData = await queryRes.json();
    queryData.speedScale = ttsState.rate;
    queryData.volumeScale = ttsState.volume;

    const synthRes = await fetch(`${ttsState.voicevoxUrl}/synthesis?speaker=${ttsState.voicevoxSpeakerId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(queryData)
    });
    if (!synthRes.ok) throw new Error('Synthesis failed');
    const blob = await synthRes.blob();
    const audio = new Audio(URL.createObjectURL(blob));
    audio.play();
  } catch (err) {
    console.warn('VOICEVOX play failed, falling back to Web Speech:', err);
    playWebSpeech(text);
  }
}

function speakText(rawText, params = {}) {
  if (!ttsState.enabled) return;
  const processedText = formatTTSMessage(rawText || ttsState.customText || 'First discover.', params);

  if (ttsState.engine === 'voicevox') {
    playVoicevoxSpeech(processedText);
  } else {
    playWebSpeech(processedText);
  }
}

function announceFirstDiscovery(systemName, bodiesCount = 1) {
  if (!ttsState.enabled) return;
  if (!systemName) return;

  if (announcedFirstDiscSystems.has(systemName)) return;
  announcedFirstDiscSystems.add(systemName);

  speakText(ttsState.customText || 'First discover.', { system: systemName, bodies: bodiesCount });
}

async function initSettingsModal() {
  await loadTTSSettings();
  updateTTSHeaderIcon();

  // Populate Web Voices when ready with multiple delayed retries for online/natural voices
  if ('speechSynthesis' in window) {
    populateWebVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      populateWebVoices();
    };
    setTimeout(populateWebVoices, 300);
    setTimeout(populateWebVoices, 1000);
    setTimeout(populateWebVoices, 2500);
  }

  // Bind Unified Settings Modal & Tabs
  const modal = document.getElementById('settings-modal');
  const btnOpen = document.getElementById('btn-settings-open');
  const btnClose = document.getElementById('btn-settings-close');
  const btnSave = document.getElementById('btn-settings-save');

  const tabBtnLogs = document.getElementById('tab-btn-logs');
  const tabBtnTTS = document.getElementById('tab-btn-tts');
  const tabBtnCredits = document.getElementById('tab-btn-credits');

  const tabPaneLogs = document.getElementById('tab-pane-logs');
  const tabPaneTTS = document.getElementById('tab-pane-tts');
  const tabPaneCredits = document.getElementById('tab-pane-credits');

  function switchTab(tabName) {
    [tabBtnLogs, tabBtnTTS, tabBtnCredits].forEach(btn => {
      if (btn) {
        btn.classList.remove('active');
        btn.style.borderBottom = 'none';
      }
    });
    [tabPaneLogs, tabPaneTTS, tabPaneCredits].forEach(pane => {
      if (pane) pane.style.display = 'none';
    });

    if (tabName === 'logs') {
      if (tabBtnLogs) {
        tabBtnLogs.classList.add('active');
        tabBtnLogs.style.borderBottom = '2px solid var(--ed-orange)';
      }
      if (tabPaneLogs) tabPaneLogs.style.display = 'flex';
      loadAppSettingsToUI();
    } else if (tabName === 'tts') {
      if (tabBtnTTS) {
        tabBtnTTS.classList.add('active');
        tabBtnTTS.style.borderBottom = '2px solid var(--ed-cyan)';
      }
      if (tabPaneTTS) tabPaneTTS.style.display = 'flex';
      updateTTSModalFields();
    } else if (tabName === 'credits') {
      if (tabBtnCredits) {
        tabBtnCredits.classList.add('active');
        tabBtnCredits.style.borderBottom = '2px solid var(--ed-green)';
      }
      if (tabPaneCredits) tabPaneCredits.style.display = 'block';
    }
  }

  if (tabBtnLogs) tabBtnLogs.addEventListener('click', () => switchTab('logs'));
  if (tabBtnTTS) tabBtnTTS.addEventListener('click', () => switchTab('tts'));
  if (tabBtnCredits) tabBtnCredits.addEventListener('click', () => switchTab('credits'));

  // App Settings (Journal Dir)
  const inputJournalDir = document.getElementById('setting-journal-dir');
  const btnResetJournalDir = document.getElementById('btn-reset-journal-dir');
  const btnModalRescan = document.getElementById('btn-modal-rescan');
  const modalScanStatusText = document.getElementById('modal-scan-status-text');

  let defaultJournalDirCache = '';

  async function loadAppSettingsToUI() {
    try {
      const res = await fetch('/api/app_settings');
      if (res.ok) {
        const data = await res.json();
        defaultJournalDirCache = data.default_journal_dir || '';
        if (inputJournalDir) inputJournalDir.value = data.journal_dir || '';
      }
    } catch (e) {
      console.warn('loadAppSettingsToUI error:', e);
    }
  }

  if (btnResetJournalDir) {
    btnResetJournalDir.addEventListener('click', () => {
      if (defaultJournalDirCache && inputJournalDir) {
        inputJournalDir.value = defaultJournalDirCache;
      }
    });
  }

  if (btnModalRescan) {
    btnModalRescan.addEventListener('click', async () => {
      // Save directory first if changed
      if (inputJournalDir && inputJournalDir.value.trim()) {
        try {
          await fetch('/api/app_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ journal_dir: inputJournalDir.value.trim() })
          });
        } catch (e) {}
      }

      // Trigger scan
      triggerScanNow();
      if (modalScanStatusText) {
        modalScanStatusText.innerText = 'ログスキャンを開始しました...';
      }
    });
  }

  // TTS Controls
  const enabledToggle = document.getElementById('tts-enabled-toggle');
  const highBioToggle = document.getElementById('tts-high-bio-toggle');
  const highBioModeSelect = document.getElementById('tts-high-bio-mode');
  const highBioTextInput = document.getElementById('tts-high-bio-text');
  const engineSelect = document.getElementById('tts-engine-select');
  const webVoiceSelect = document.getElementById('tts-web-voice-select');
  const voicevoxSpeakerSelect = document.getElementById('tts-voicevox-speaker-select');
  const voicevoxGroup = document.getElementById('tts-voicevox-group');
  const customTextInput = document.getElementById('tts-custom-text');
  const volumeRange = document.getElementById('tts-volume');
  const rateRange = document.getElementById('tts-rate');
  const volVal = document.getElementById('tts-vol-val');
  const rateVal = document.getElementById('tts-rate-val');
  const btnTest = document.getElementById('btn-tts-test');

  function updateTTSModalFields() {
    if (enabledToggle) enabledToggle.checked = Boolean(ttsState.enabled);
    if (highBioToggle) highBioToggle.checked = Boolean(ttsState.highBioEnabled !== false);
    if (highBioModeSelect) highBioModeSelect.value = ttsState.highBioMode || 'both';
    if (highBioTextInput) highBioTextInput.value = ttsState.highBioText || '{body}、高額生物反応です。見込額{value}クレジット。';
    if (engineSelect) engineSelect.value = ttsState.engine;
    if (customTextInput) customTextInput.value = ttsState.customText;
    if (volumeRange) {
      volumeRange.value = ttsState.volume;
      if (volVal) volVal.innerText = `${Math.round(ttsState.volume * 100)}%`;
    }
    if (rateRange) {
      rateRange.value = ttsState.rate;
      if (rateVal) rateVal.innerText = `${ttsState.rate.toFixed(1)}x`;
    }

    if (ttsState.engine === 'voicevox') {
      if (webVoiceSelect) webVoiceSelect.style.display = 'none';
      if (voicevoxGroup) voicevoxGroup.style.display = 'flex';
      checkVoicevoxConnection();
    } else {
      if (webVoiceSelect) webVoiceSelect.style.display = 'block';
      if (voicevoxGroup) voicevoxGroup.style.display = 'none';
      populateWebVoices();
    }
  }

  if (btnOpen && modal) {
    btnOpen.addEventListener('click', () => {
      switchTab('logs');
      modal.style.display = 'flex';
    });
  }

  if (btnClose && modal) {
    btnClose.addEventListener('click', () => {
      modal.style.display = 'none';
    });
  }

  if (btnSave && modal) {
    btnSave.addEventListener('click', async () => {
      // Save Journal Path
      if (inputJournalDir && inputJournalDir.value.trim()) {
        try {
          await fetch('/api/app_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ journal_dir: inputJournalDir.value.trim() })
          });
        } catch (e) {}
      }

      // Save TTS
      if (enabledToggle) ttsState.enabled = enabledToggle.checked;
      if (highBioToggle) ttsState.highBioEnabled = highBioToggle.checked;
      if (highBioModeSelect) ttsState.highBioMode = highBioModeSelect.value;
      if (highBioTextInput) ttsState.highBioText = highBioTextInput.value || '{body}、高額生物反応です。見込額{value}クレジット。';
      if (engineSelect) ttsState.engine = engineSelect.value;
      if (webVoiceSelect) ttsState.webVoiceURI = webVoiceSelect.value;
      if (voicevoxSpeakerSelect) ttsState.voicevoxSpeakerId = voicevoxSpeakerSelect.value;
      if (customTextInput) ttsState.customText = customTextInput.value || 'First discover.';
      if (volumeRange) ttsState.volume = parseFloat(volumeRange.value) || 1.0;
      if (rateRange) ttsState.rate = parseFloat(rateRange.value) || 1.0;

      saveTTSSettings();
      updateTTSHeaderIcon();
      modal.style.display = 'none';
    });
  }

  if (btnTest) {
    btnTest.addEventListener('click', () => {
      const tempState = {
        enabled: true,
        engine: engineSelect ? engineSelect.value : ttsState.engine,
        webVoiceURI: webVoiceSelect ? webVoiceSelect.value : ttsState.webVoiceURI,
        voicevoxSpeakerId: voicevoxSpeakerSelect ? voicevoxSpeakerSelect.value : ttsState.voicevoxSpeakerId,
        customText: customTextInput ? customTextInput.value : ttsState.customText,
        volume: volumeRange ? parseFloat(volumeRange.value) : ttsState.volume,
        rate: rateRange ? parseFloat(rateRange.value) : ttsState.rate
      };
      
      const textToSpeak = formatTTSMessage(tempState.customText || 'First discover.', {
        system: (state.selectedSystem ? state.selectedSystem.star_system : 'Hypoe Pra DM-U d3-557'),
        bodies: 4
      });

      if (tempState.engine === 'voicevox') {
        playVoicevoxSpeech(textToSpeak);
      } else {
        if (!('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();
        const uttr = new SpeechSynthesisUtterance(textToSpeak);
        const voices = window.speechSynthesis.getVoices();
        if (tempState.webVoiceURI && voices) {
          const v = voices.find(v => v.voiceURI === tempState.webVoiceURI);
          if (v) uttr.voice = v;
        }
        uttr.volume = tempState.volume;
        uttr.rate = tempState.rate;
        window.speechSynthesis.speak(uttr);
      }
    });
  }

  if (engineSelect) {
    engineSelect.addEventListener('change', () => {
      if (engineSelect.value === 'voicevox') {
        if (webVoiceSelect) webVoiceSelect.style.display = 'none';
        if (voicevoxGroup) voicevoxGroup.style.display = 'flex';
        checkVoicevoxConnection();
      } else {
        if (webVoiceSelect) webVoiceSelect.style.display = 'block';
        if (voicevoxGroup) voicevoxGroup.style.display = 'none';
        populateWebVoices();
      }
    });
  }

  if (volumeRange && volVal) {
    volumeRange.addEventListener('input', () => {
      volVal.innerText = `${Math.round(volumeRange.value * 100)}%`;
    });
  }

  if (rateRange && rateVal) {
    rateRange.addEventListener('input', () => {
      rateVal.innerText = `${parseFloat(rateRange.value).toFixed(1)}x`;
    });
  }
}
