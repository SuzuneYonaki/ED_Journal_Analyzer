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
    has_anomalies: false,
    has_landable_hmc: false,
    has_landable_metal_rich: false,
    has_landable_rocky: false,
    has_landable_icy: false,
    has_landable_rocky_ice: false,
    has_landable_ringed: false,
    has_mining_signals: false,
    has_bookmarks: false,
    is_shared: false
  },
  showMiningGravity: localStorage.getItem('mining_display_gravity') !== 'false',
  showMiningTemp: localStorage.getItem('mining_display_temp') !== 'false',
  miningSubFilter: 'all',
  sortBy: 'last_visited',
  sortOrder: 'desc',
  sortBy2: null,
  sortOrder2: 'desc',
  sortBy3: null,
  sortOrder3: 'desc',
  savedSortBy: 'total_potential_value',
  savedSortOrder: 'desc',
  savedSortBy2: null,
  savedSortOrder2: 'desc',
  savedSortBy3: null,
  savedSortOrder3: 'desc',
  sortMode: 'composite',
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
  targetJumpSystem: '',
  autoSelectTopNext: false
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

function parseMarkdown(md) {
  if (!md) return '';
  let escaped = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

  escaped = escaped.replace(/```([\s\S]*?)```/g, (match, p1) => `<pre><code>${p1}</code></pre>`);
  escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
  escaped = escaped.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  escaped = escaped.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  escaped = escaped.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  escaped = escaped.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
  escaped = escaped.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');
  escaped = escaped.replace(/^[\*\-] (.*$)/gim, '<li>$1</li>');
  escaped = escaped.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
  escaped = escaped.replace(/<\/ul>\s*<ul>/g, '');
  escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color: var(--ed-cyan);">$1</a>');
  escaped = escaped.replace(/\n/g, '<br>');
  escaped = escaped.replace(/<\/(h[1-3]|pre|ul|blockquote)><br>/g, '</$1>');
  escaped = escaped.replace(/<br><(h[1-3]|pre|ul|blockquote)/g, '<$1');
  return escaped;
}

function parseRingClass(rawClass) {
  if (!rawClass) return { key: 'unknown', nameEn: 'Unknown', nameJa: '不明', color: '#94a3b8', icon: '💍', bg: 'rgba(148,163,184,0.15)', border: 'rgba(148,163,184,0.4)', description: '' };
  const lower = rawClass.toLowerCase();
  if (lower.includes('icy')) {
    return {
      key: 'icy',
      nameEn: 'Icy',
      nameJa: '氷',
      icon: '❄️',
      color: '#38bdf8',
      bg: 'rgba(56, 189, 248, 0.18)',
      border: 'rgba(56, 189, 248, 0.45)',
      description: 'Fleet Carrier燃料 (Tritium) / 低温ダイヤモンド (LTD) 産地'
    };
  }
  if (lower.includes('metallic') || lower.includes('metalic')) {
    return {
      key: 'metallic',
      nameEn: 'Metallic',
      nameJa: '金属質',
      icon: '🪙',
      color: '#facc15',
      bg: 'rgba(250, 204, 21, 0.18)',
      border: 'rgba(250, 204, 21, 0.5)',
      description: 'プラチナ (Platinum) / ペイン石 (Painite) 等 最も高価値なレーザー採掘適性'
    };
  }
  if (lower.includes('metal')) {
    return {
      key: 'metal_rich',
      nameEn: 'Metal Rich',
      nameJa: '金属豊富',
      icon: '🪐',
      color: '#fb923c',
      bg: 'rgba(251, 146, 60, 0.18)',
      border: 'rgba(251, 146, 60, 0.5)',
      description: '各種工業用・貴金属素材'
    };
  }
  if (lower.includes('rocky')) {
    return {
      key: 'rocky',
      nameEn: 'Rocky',
      nameJa: '岩石',
      icon: '🪨',
      color: '#cbd5e1',
      bg: 'rgba(203, 213, 225, 0.18)',
      border: 'rgba(203, 213, 225, 0.45)',
      description: 'マスグラバイト / アレキサンドライト等 高額深部鉱石コア採掘適性'
    };
  }
  const cleanName = rawClass.replace('eRingClass_', '');
  return {
    key: 'other',
    nameEn: cleanName,
    nameJa: cleanName,
    icon: '💍',
    color: '#a78bfa',
    bg: 'rgba(167, 139, 250, 0.18)',
    border: 'rgba(167, 139, 250, 0.45)',
    description: ''
  };
}
window.parseRingClass = parseRingClass;

function parseReserveLevel(reserve) {
  if (!reserve) return null;
  const map = {
    'pristineresources': { en: 'Pristine', ja: '無傷 (最高)', color: '#22c55e', icon: '💎' },
    'majorresources': { en: 'Major', ja: '主要', color: '#38bdf8', icon: '✨' },
    'commonresources': { en: 'Common', ja: '普通', color: '#94a3b8', icon: '⚖️' },
    'lowresources': { en: 'Low', ja: '低', color: '#f59e0b', icon: '⚠️' },
    'depletedresources': { en: 'Depleted', ja: '枯渇', color: '#ef4444', icon: '🚫' },
  };
  const key = reserve.toLowerCase().replace(/[^a-z]/g, '');
  return map[key] || { en: reserve, ja: reserve, color: '#94a3b8', icon: '📊' };
}
window.parseReserveLevel = parseReserveLevel;

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
  const modalBtnJa = document.getElementById('btn-modal-lang-ja');
  const modalBtnEn = document.getElementById('btn-modal-lang-en');
  if (modalBtnJa && modalBtnEn) {
    modalBtnJa.classList.toggle('active', currentLang === 'ja');
    modalBtnEn.classList.toggle('active', currentLang === 'en');
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

async function fetchSystems(options = {}) {
  const autoSelectTop = (options && options.autoSelectTop) || state.autoSelectTopNext || false;
  state.autoSelectTopNext = false;

  const activeSortBy = state.liveSyncEnabled ? 'last_visited' : (state.savedSortBy || 'total_potential_value');
  const activeSortOrder = state.liveSyncEnabled ? 'desc' : (state.savedSortOrder || 'desc');
  const activeSortBy2 = state.liveSyncEnabled ? null : state.savedSortBy2;
  const activeSortOrder2 = state.liveSyncEnabled ? 'desc' : state.savedSortOrder2;
  const activeSortBy3 = state.liveSyncEnabled ? null : state.savedSortBy3;
  const activeSortOrder3 = state.liveSyncEnabled ? 'desc' : state.savedSortOrder3;
  const activeSortMode = state.liveSyncEnabled ? 'strict' : (state.sortMode || 'composite');

  const params = new URLSearchParams({
    q: state.searchQuery || '',
    sort_by: activeSortBy,
    sort_order: activeSortOrder,
    sort_mode: activeSortMode,
    page: state.page || 1,
    limit: state.limit || 50
  });

  if (activeSortBy2 && activeSortBy2 !== 'none') {
    params.append('sort_by_2', activeSortBy2);
    params.append('sort_order_2', activeSortOrder2);
  }

  if (activeSortBy3 && activeSortBy3 !== 'none') {
    params.append('sort_by_3', activeSortBy3);
    params.append('sort_order_3', activeSortOrder3);
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

    // Auto select first system if requested by user sort/filter, or if none selected or not in current list (and not just jumped)
    if (!jumpedToNewSystem && state.systems && state.systems.length > 0) {
      if (autoSelectTop) {
        state.jumpState = 'idle';
        selectSystem(state.systems[0].system_address);
      } else if (!state.selectedSystem || !state.systems.some(s => s.system_address === state.selectedSystem.system_address)) {
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
    
    // 5 Key Galactic Distances (CMDR, Sol, Colonia, Rainbow's End, Explorer's Anchorage)
    const distanceBadges = [];
    if (sys.cmdr_distance_ly !== null && sys.cmdr_distance_ly !== undefined) {
      const cmdrSys = state.currentLocation && state.currentLocation.star_system ? ` (${state.currentLocation.star_system})` : '';
      distanceBadges.push(`<span class="tag-badge tag-cmdr-dist" title="現在地${cmdrSys}からの距離: ${Math.round(sys.cmdr_distance_ly).toLocaleString()} Ly">📍 CMDR: ${Math.round(sys.cmdr_distance_ly).toLocaleString()} Ly</span>`);
    }

    const solDist = (sys.sol_distance_ly !== undefined && sys.sol_distance_ly !== null && sys.sol_distance_ly > 0)
      ? sys.sol_distance_ly
      : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
        ? Math.hypot(sys.star_pos_x, sys.star_pos_y, sys.star_pos_z)
        : null);
    if (solDist !== null && solDist !== undefined) {
      distanceBadges.push(`<span class="tag-badge tag-sol-dist" title="太陽系 (Sol) からの距離: ${Math.round(solDist).toLocaleString()} Ly">Sol: ${Math.round(solDist).toLocaleString()} Ly</span>`);
    }

    const coloniaDist = (sys.colonia_distance_ly !== undefined && sys.colonia_distance_ly !== null)
      ? sys.colonia_distance_ly
      : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
        ? Math.hypot(sys.star_pos_x - (-9530.5), sys.star_pos_y - (-910.28125), sys.star_pos_z - 19808.125)
        : null);
    if (coloniaDist !== null && coloniaDist !== undefined) {
      distanceBadges.push(`<span class="tag-badge tag-colonia-dist" title="第2の人類居住圏 (Colonia) からの距離: ${Math.round(coloniaDist).toLocaleString()} Ly">Colonia: ${Math.round(coloniaDist).toLocaleString()} Ly</span>`);
    }

    const rbDist = (sys.rainbows_end_distance_ly !== undefined && sys.rainbows_end_distance_ly !== null)
      ? sys.rainbows_end_distance_ly
      : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
        ? Math.hypot(sys.star_pos_x - 21481.40625, sys.star_pos_y - (-1004.5625), sys.star_pos_z - 43369.4375)
        : null);
    if (rbDist !== null && rbDist !== undefined) {
      distanceBadges.push(`<span class="tag-badge tag-rainbow-dist" title="最遠方宇宙港 Rainbow's End (Roefoo ZE-H d10-0 / DW3) からの距離: ${Math.round(rbDist).toLocaleString()} Ly">Rainbow's End: ${Math.round(rbDist).toLocaleString()} Ly</span>`);
    }

    const eaDist = (sys.explorers_anchorage_distance_ly !== undefined && sys.explorers_anchorage_distance_ly !== null)
      ? sys.explorers_anchorage_distance_ly
      : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
        ? Math.hypot(sys.star_pos_x - 28.6875, sys.star_pos_y - (-19.78125), sys.star_pos_z - 25899.6875)
        : null);
    if (eaDist !== null && eaDist !== undefined) {
      distanceBadges.push(`<span class="tag-badge tag-eanch-dist" title="銀河中心探査基地 Explorer's Anchorage (Stuemeae FG-Y d7561 / Sgr A*近傍) からの距離: ${Math.round(eaDist).toLocaleString()} Ly">E.Anchorage: ${Math.round(eaDist).toLocaleString()} Ly</span>`);
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
    if (sys.bookmarks && sys.bookmarks.length > 0) {
      const firstBm = sys.bookmarks[0];
      const bmText = firstBm.alias_name ? `🔖 ${firstBm.alias_name}` : `🔖 ${firstBm.body_name}`;
      const moreBm = sys.bookmarks.length > 1 ? ` (+${sys.bookmarks.length - 1})` : '';
      const bmTip = sys.bookmarks.map(b => (b.alias_name ? `[${b.alias_name}] ` : '') + b.body_name + (b.note_snippet ? `: ${b.note_snippet}` : '')).join('\n');
      tags.push(`<span class="tag-badge tag-bookmark" title="${bmTip}">${bmText}${moreBm}</span>`);
    }
    if (sys.is_shared) {
      const sharedTip = sys.shared_by ? `${t('shared_by_label')}: ${sys.shared_by}` : t('shared_system');
      tags.push(`<span class="tag-badge tag-shared" style="background: rgba(167, 139, 250, 0.2); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.6); font-weight: bold;" title="${sharedTip}">🤝 Shared</span>`);
    }
    if (sys.composite_score !== null && sys.composite_score !== undefined) {
      tags.push(`<span class="tag-badge" style="background: rgba(0, 255, 136, 0.18); color: #00ff88; border: 1px solid rgba(0, 255, 136, 0.5); font-weight: bold;" title="総合ブレンドスコア: ${sys.composite_score}pt">★ スコア: ${Math.round(sys.composite_score)}pt</span>`);
    }

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

    let distanceHtml = '';
    if (distanceBadges.length > 0) {
      distanceHtml = `
        <div class="system-distance-bar">
          ${distanceBadges.join('')}
        </div>
      `;
    }

    let landableHtml = '';
    const activeMiningFilters = {
      hmc: !!state.filters.has_landable_hmc,
      metal_rich: !!state.filters.has_landable_metal_rich,
      rocky: !!state.filters.has_landable_rocky,
      icy: !!state.filters.has_landable_icy,
      rocky_ice: !!state.filters.has_landable_rocky_ice,
      ringed: !!state.filters.has_landable_ringed,
      mining: !!state.filters.has_mining_signals
    };
    const hasAnyMiningFilter = Object.values(activeMiningFilters).some(Boolean);

    if (hasAnyMiningFilter && sys.landable_bodies && sys.landable_bodies.length > 0) {
      const matchedBodies = sys.landable_bodies.filter(lb => {
        if (activeMiningFilters.hmc && lb.type === 'HMC') return true;
        if (activeMiningFilters.metal_rich && lb.type === 'Metal Rich') return true;
        if (activeMiningFilters.rocky && lb.type === 'Rocky') return true;
        if (activeMiningFilters.icy && lb.type === 'Icy') return true;
        if (activeMiningFilters.rocky_ice && lb.type === 'Icy Rocky') return true;
        if (activeMiningFilters.ringed && lb.is_ringed) return true;
        if (activeMiningFilters.mining && lb.mining_signals > 0) return true;
        return false;
      });

      if (matchedBodies.length > 0) {
        const landableBadges = matchedBodies.slice(0, 6).map(lb => {
          const isRing = lb.is_ringed;
          const icon = isRing ? '💍' : '🪐';
          let colorStyle = 'background: rgba(203, 213, 225, 0.12); color: #cbd5e1; border: 1px solid rgba(203, 213, 225, 0.3);';
          if (lb.type === 'HMC') {
            colorStyle = 'background: rgba(96, 165, 250, 0.15); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.4);';
          } else if (lb.type === 'Metal Rich') {
            colorStyle = 'background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.4);';
          } else if (lb.type === 'Icy') {
            colorStyle = 'background: rgba(103, 232, 249, 0.15); color: #67e8f9; border: 1px solid rgba(103, 232, 249, 0.4);';
          } else if (lb.type === 'Icy Rocky') {
            colorStyle = 'background: rgba(147, 197, 253, 0.15); color: #93c5fd; border: 1px solid rgba(147, 197, 253, 0.4);';
          }
          if (isRing) {
            colorStyle += ' border-color: rgba(244, 114, 182, 0.7); box-shadow: 0 0 3px rgba(244, 114, 182, 0.3);';
          }

          const statParts = [];
          if (state.showMiningGravity && lb.gravity_g !== null && lb.gravity_g !== undefined) {
            statParts.push(`${lb.gravity_g.toFixed(2)}G`);
          }
          if (state.showMiningTemp && lb.temp_k !== null && lb.temp_k !== undefined) {
            statParts.push(`${lb.temp_k}K`);
          }
          const statSuffix = statParts.length > 0 ? ` [${statParts.join(' | ')}]` : '';

          const tip = `${lb.body_name} (${lb.type}) - 重力: ${lb.gravity_g ? lb.gravity_g.toFixed(2) + 'G' : '--'} | 温度: ${lb.temp_k ? lb.temp_k + 'K' : '--'}${isRing ? ' | 環付き (Ringed)' : ''}${lb.mining_signals > 0 ? ' | 採掘拠点: ' + lb.mining_signals + '箇所' : ''}`;
          return `<span class="tag-badge" style="${colorStyle} font-size: 0.67rem; padding: 1px 4px; margin-right: 2px;" title="${tip}">${icon} ${lb.type}${statSuffix}</span>`;
        });
        if (matchedBodies.length > 6) {
          landableBadges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.06); color: var(--text-dim); font-size: 0.65rem; padding: 1px 4px;" title="他 ${matchedBodies.length - 6} 件のマッチ天体">+${matchedBodies.length - 6}</span>`);
        }
        landableHtml = `
          <div class="system-landable-bar" style="display: flex; flex-wrap: wrap; gap: 2px; margin-top: 4px; padding-top: 3px; border-top: 1px dashed rgba(255,255,255,0.07);">
            ${landableBadges.join('')}
          </div>
        `;
      }
    }

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
      ${distanceHtml}
      ${landableHtml}
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

  // 5 Key Galactic Distances in Header
  const distEl = document.getElementById('current-system-distances');
  if (distEl) {
    const badges = [];
    if (sys.cmdr_distance_ly !== null && sys.cmdr_distance_ly !== undefined) {
      badges.push(`<span class="tag-badge tag-cmdr-dist" title="現在地からの距離">📍 CMDR: ${Math.round(sys.cmdr_distance_ly).toLocaleString()} Ly</span>`);
    }
    const solDist = (sys.sol_distance_ly > 0) ? sys.sol_distance_ly : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null) ? Math.hypot(sys.star_pos_x, sys.star_pos_y, sys.star_pos_z) : null);
    if (solDist !== null) {
      badges.push(`<span class="tag-badge tag-sol-dist" title="太陽系 (Sol) からの距離">Sol: ${Math.round(solDist).toLocaleString()} Ly</span>`);
    }
    const colDist = sys.colonia_distance_ly ?? ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null) ? Math.hypot(sys.star_pos_x - (-9530.5), sys.star_pos_y - (-910.28125), sys.star_pos_z - 19808.125) : null);
    if (colDist !== null) {
      badges.push(`<span class="tag-badge tag-colonia-dist" title="第2の人類居住圏 (Colonia) からの距離">Colonia: ${Math.round(colDist).toLocaleString()} Ly</span>`);
    }
    const rbDist = sys.rainbows_end_distance_ly ?? ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null) ? Math.hypot(sys.star_pos_x - 21481.40625, sys.star_pos_y - (-1004.5625), sys.star_pos_z - 43369.4375) : null);
    if (rbDist !== null) {
      badges.push(`<span class="tag-badge tag-rainbow-dist" title="最遠方宇宙港 Rainbow's End (Roefoo ZE-H d10-0 / DW3) からの距離">Rainbow's End: ${Math.round(rbDist).toLocaleString()} Ly</span>`);
    }
    const eaDist = sys.explorers_anchorage_distance_ly ?? ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null) ? Math.hypot(sys.star_pos_x - 28.6875, sys.star_pos_y - (-19.78125), sys.star_pos_z - 25899.6875) : null);
    if (eaDist !== null) {
      badges.push(`<span class="tag-badge tag-eanch-dist" title="銀河中心探査基地 Explorer's Anchorage (Stuemeae FG-Y d7561 / Sgr A*近傍) からの距離">E.Anchorage: ${Math.round(eaDist).toLocaleString()} Ly</span>`);
    }
    distEl.innerHTML = badges.join('');
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

  // Export buttons & Shared Badge in Header
  const btnExportHtml = document.getElementById('btn-export-html');
  const btnExportPkg = document.getElementById('btn-export-pkg');
  const btnToggleShared = document.getElementById('btn-toggle-shared');
  const sharedBadge = document.getElementById('current-system-shared-badge');
  const sharedIcon = document.getElementById('shared-toggle-icon');
  const sharedLabel = document.getElementById('shared-toggle-label');

  if (btnExportHtml) btnExportHtml.style.display = 'inline-flex';
  if (btnExportPkg) btnExportPkg.style.display = 'inline-flex';
  if (btnToggleShared) btnToggleShared.style.display = 'inline-flex';

  if (sharedBadge) {
    if (sys.is_shared) {
      const byText = sys.shared_by ? `${t('shared_by_label')}: ${sys.shared_by}` : t('shared_system');
      sharedBadge.innerHTML = `<span class="tag-badge tag-shared" style="background: rgba(167, 139, 250, 0.25); color: #c4b5fd; border: 1px solid #a78bfa; font-weight: bold;" title="${byText}">🤝 ${t('shared_system')}</span>`;
      sharedBadge.style.display = 'inline-flex';
    } else {
      sharedBadge.innerHTML = '';
      sharedBadge.style.display = 'none';
    }
  }

  if (sharedIcon && sharedLabel && btnToggleShared) {
    if (sys.is_shared) {
      sharedIcon.innerText = '✅';
      sharedLabel.innerText = t('unshare_label') || '共有解除';
      btnToggleShared.style.background = 'rgba(167, 139, 250, 0.25)';
      btnToggleShared.style.borderColor = '#a78bfa';
    } else {
      sharedIcon.innerText = '🤝';
      sharedLabel.innerText = t('share_label') || '共有マーク';
      btnToggleShared.style.background = 'rgba(167, 139, 250, 0.1)';
      btnToggleShared.style.borderColor = 'rgba(167, 139, 250, 0.4)';
    }
  }
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
    } else if (by === 'radius') {
      valA = a.radius || 0;
      valB = b.radius || 0;
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

function renderBodyMiningBlock(node) {
  const miningSig = node.mining_signals || 0;
  if (miningSig === 0) return '';

  return `
    <div class="body-geo-panel" style="border-left-color: #38bdf8; background: rgba(56, 189, 248, 0.06);">
      <div style="display: flex; align-items: center; gap: 6px;">
        <span style="font-weight: bold; color: #38bdf8;">⛏️ ${t('mining_signals') || '惑星採掘拠点'} (${miningSig}):</span>
        <span style="color: #cbd5e1;">Planetary Mining Locations</span>
      </div>
      <span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.68rem;">MINING: ${miningSig}</span>
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

async function dismissHonkWaitingAndShowCurrent() {
  state.jumpState = 'idle';
  const targetAddress = state.currentCmdrSystemAddress 
    || (state.selectedSystem ? state.selectedSystem.system_address : null)
    || (state.systems && state.systems.length > 0 ? state.systems[0].system_address : null);
  if (targetAddress) {
    await selectSystem(targetAddress, false, false);
  } else {
    renderCurrentView();
  }
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
        <button id="btn-dismiss-honk" class="btn-page" style="margin-top: 16px; padding: 6px 14px; font-size: 0.8rem; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; cursor: pointer; border-radius: 4px; display: inline-flex; align-items: center; gap: 6px;">
          <span>▶ 現状判明している星系マップを表示 (Live)</span>
        </button>
      </div>
    `;
    const btnDismiss = document.getElementById('btn-dismiss-honk');
    if (btnDismiss) {
      btnDismiss.addEventListener('click', () => {
        dismissHonkWaitingAndShowCurrent();
      });
    }
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
  } else if (state.currentView === 'mining') {
    const sorted = getSortedBodies(state.currentSystemData.bodies);
    renderMiningView(container, sorted);
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
    if (node.bookmark) {
      const bmTitle = (node.bookmark.alias_name ? `[${node.bookmark.alias_name}] ` : '') + (node.bookmark.note_markdown || '');
      badges.push(`<span class="tag-badge tag-bookmark" title="${bmTitle}">🔖 ${node.bookmark.alias_name || 'BOOKMARK'}</span>`);
    }
    if (node.landable) badges.push('<span class="tag-badge tag-landable">LANDABLE</span>');
    
    // Gravity display
    if (state.showMiningGravity && node.landable && node.surface_gravity_g) {
      if (node.surface_gravity_g >= 3.0) badges.push(`<span class="tag-badge tag-high-g">${node.surface_gravity_g.toFixed(2)}G !</span>`);
      else if (node.surface_gravity_g >= 1.5) badges.push(`<span class="tag-badge" style="background: rgba(255,113,0,0.2); color: var(--ed-orange);">${node.surface_gravity_g.toFixed(2)}G</span>`);
      else badges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.1);">${node.surface_gravity_g.toFixed(2)}G</span>`);
    }

    // Temperature display
    if (state.showMiningTemp && node.landable && node.surface_temperature !== null && node.surface_temperature !== undefined) {
      badges.push(`<span class="tag-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);">🌡️ ${Math.round(node.surface_temperature)}K</span>`);
    }

    if (node.geo_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(255,113,0,0.2); color: var(--ed-orange);">GEO: ${node.geo_signals}</span>`);
    if (node.mining_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);">⛏️ MINING: ${node.mining_signals}</span>`);
    if (node.anomalies && node.anomalies.length > 0) {
      node.anomalies.forEach(a => badges.push(`<span class="tag-badge tag-anomaly">${a.tag}</span>`));
    }

    const typeDesc = node.star_type ? `${t('star_type_label')} (${node.star_type})` : (node.planet_class || 'Planet');
    const aliasTag = (node.bookmark && node.bookmark.alias_name)
      ? `<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5); font-size: 0.7rem; margin-left: 6px;">🏷️ ${node.bookmark.alias_name}</span>`
      : '';

    card.innerHTML = `
      <div class="node-card-top">
        <div class="node-info-left">
          <div class="body-icon ${iconClass}">${iconLabel}</div>
          <div class="node-details">
            <div class="node-name" style="display: flex; align-items: center; flex-wrap: wrap;">${node.body_name}${aliasTag}</div>
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
    if (body.bookmark) {
      const bmTitle = (body.bookmark.alias_name ? `[${body.bookmark.alias_name}] ` : '') + (body.bookmark.note_markdown || '');
      badges.push(`<span class="tag-badge tag-bookmark" title="${bmTitle}">🔖 ${body.bookmark.alias_name || 'BOOKMARK'}</span>`);
    }
    if (body.landable) badges.push('<span class="tag-badge tag-landable">LANDABLE</span>');
    let bRings = body.rings_list;
    if (!bRings && body.rings && body.rings !== '[]' && body.rings !== '""') {
      try { bRings = typeof body.rings === 'string' ? JSON.parse(body.rings) : body.rings; } catch (e) { bRings = []; }
    }
    bRings = Array.isArray(bRings) ? bRings : [];
    if (bRings.length > 0) {
      bRings.forEach(r => {
        const isB = (r.Name || '').toLowerCase().includes('belt');
        const info = parseRingClass(r.RingClass);
        if (isB) {
          badges.push(`<span class="tag-badge" style="background: ${info.bg}; color: ${info.color}; border: 1px solid ${info.border}; font-weight: bold;" title="${r.Name || ''} - ${info.description}">🪐 ${info.icon} ${info.nameJa}ベルト</span>`);
        } else {
          badges.push(`<span class="tag-badge" style="background: ${info.bg}; color: ${info.color}; border: 1px solid ${info.border}; font-weight: bold;" title="${r.Name || ''} - ${info.description}">💍 ${info.icon} ${info.nameJa}環</span>`);
        }
      });
    }
    if (state.showMiningGravity && body.landable && body.surface_gravity_g) {
      if (body.surface_gravity_g >= 3.0) badges.push(`<span class="tag-badge tag-high-g">${body.surface_gravity_g.toFixed(2)}G !</span>`);
      else badges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.1);">${body.surface_gravity_g.toFixed(2)}G</span>`);
    }
    if (state.showMiningTemp && body.surface_temperature !== null && body.surface_temperature !== undefined && body.landable) {
      badges.push(`<span class="tag-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);">🌡️ ${Math.round(body.surface_temperature)}K</span>`);
    }
    if (body.geo_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(255,113,0,0.2); color: var(--ed-orange);">GEO: ${body.geo_signals}</span>`);
    if (body.mining_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);">⛏️ MINING: ${body.mining_signals}</span>`);
    if (body.anomalies && body.anomalies.length > 0) {
      body.anomalies.forEach(a => badges.push(`<span class="tag-badge tag-anomaly">${a.tag}</span>`));
    }
    const aliasTag = (body.bookmark && body.bookmark.alias_name)
      ? `<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5); font-size: 0.7rem; margin-left: 6px;">🏷️ ${body.bookmark.alias_name}</span>`
      : '';

    card.innerHTML = `
      <div class="node-card-top">
        <div class="node-info-left">
          <div class="body-icon ${iconClass}">${iconLabel}</div>
          <div class="node-details">
            <div class="node-name" style="display: flex; align-items: center; flex-wrap: wrap; ${isTarget ? 'color: var(--ed-cyan); font-weight: bold;' : ''}">${body.body_name}${aliasTag}</div>
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
    const miningHtml = renderBodyMiningBlock(body);

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
      ${miningHtml}
      ${bioHtml}
    `;
    list.appendChild(card);
  });
  container.appendChild(list);
}

function renderMiningView(container, bodies) {
  if (!bodies) return;
  const landableBodies = bodies.filter(b => b.landable === 1);

  if (landableBodies.length === 0) {
    container.innerHTML = `
      <div style="color: var(--text-secondary); text-align: center; margin-top: 40px; padding: 20px;">
        <div style="font-size: 2rem; margin-bottom: 8px;">⛏️</div>
        <div style="font-size: 1.1rem; font-weight: bold; color: #fff;">${t('no_landable_bodies')}</div>
        <div style="font-size: 0.8rem; color: var(--text-dim); margin-top: 6px;">この星系には着陸（Landable）可能な天体、およびRhino SRV採掘対象天体は存在しません。</div>
      </div>
    `;
    return;
  }

  // Count statistics
  const totalLandable = landableBodies.length;
  const totalMiningSignals = landableBodies.reduce((acc, b) => acc + (b.mining_signals || 0), 0);
  const ringedBodies = landableBodies.filter(b => b.rings && b.rings !== '[]' && b.rings !== '""');

  const hmcCount = landableBodies.filter(b => (b.planet_class || '').toLowerCase().includes('high metal')).length;
  const mrCount = landableBodies.filter(b => (b.planet_class || '').toLowerCase().includes('metal rich')).length;
  const rockyCount = landableBodies.filter(b => (b.planet_class || '').toLowerCase().includes('rocky body')).length;
  const icyCount = landableBodies.filter(b => (b.planet_class || '').toLowerCase().includes('icy body')).length;
  const rockyIceCount = landableBodies.filter(b => (b.planet_class || '').toLowerCase().includes('rocky ice') || (b.planet_class || '').toLowerCase().includes('icy rocky')).length;

  // Filter based on state.miningSubFilter
  let displayBodies = [...landableBodies];
  if (state.miningSubFilter === 'hmc') {
    displayBodies = displayBodies.filter(b => (b.planet_class || '').toLowerCase().includes('high metal'));
  } else if (state.miningSubFilter === 'metal_rich') {
    displayBodies = displayBodies.filter(b => (b.planet_class || '').toLowerCase().includes('metal rich'));
  } else if (state.miningSubFilter === 'rocky') {
    displayBodies = displayBodies.filter(b => (b.planet_class || '').toLowerCase().includes('rocky body'));
  } else if (state.miningSubFilter === 'icy') {
    displayBodies = displayBodies.filter(b => (b.planet_class || '').toLowerCase().includes('icy body'));
  } else if (state.miningSubFilter === 'rocky_ice') {
    displayBodies = displayBodies.filter(b => (b.planet_class || '').toLowerCase().includes('rocky ice') || (b.planet_class || '').toLowerCase().includes('icy rocky'));
  } else if (state.miningSubFilter === 'ringed') {
    displayBodies = displayBodies.filter(b => b.rings && b.rings !== '[]' && b.rings !== '""');
  } else if (state.miningSubFilter === 'has_mining') {
    displayBodies = displayBodies.filter(b => (b.mining_signals || 0) > 0);
  }

  const wrapper = document.createElement('div');
  wrapper.style.display = 'flex';
  wrapper.style.flexDirection = 'column';
  wrapper.style.gap = '12px';

  // Field Guide & Summary Banner
  const guideCard = document.createElement('div');
  guideCard.className = 'rhino-field-guide-card';
  guideCard.style.cssText = 'background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 6px; padding: 10px 14px; font-size: 0.78rem;';
  guideCard.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
      <span style="font-weight: bold; color: #38bdf8; font-size: 0.85rem; display: flex; align-items: center; gap: 6px;">
        <span>⛏️</span> <span>${t('mining_field_guide_title') || '採掘・Landable天体サマリー'}</span>
      </span>
      <div style="display: flex; gap: 6px; flex-wrap: wrap;">
        <span class="tag-badge" style="background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);">🪐 着陸可能: ${totalLandable} 天体</span>
        <span class="tag-badge" style="background: rgba(0, 255, 136, 0.15); color: #00ff88; border: 1px solid rgba(0, 255, 136, 0.35);">⛏️ 採掘地点: ${totalMiningSignals} 箇所</span>
        ${ringedBodies.length > 0 ? `<span class="tag-badge" style="background: rgba(244, 114, 182, 0.18); color: #f472b6; border: 1px solid rgba(244, 114, 182, 0.4);">💍 環付きLandable: ${ringedBodies.length} 天体</span>` : ''}
      </div>
    </div>
    <div style="color: var(--text-secondary); margin-top: 6px; line-height: 1.45; font-size: 0.73rem; border-top: 1px dashed rgba(255,255,255,0.06); padding-top: 6px;">
      ・<b>推奨天体</b>: <b>Rocky / Metal Rich / HMC</b> はバストネサイト（Bastnäsite）等の希少鉱石・高価値素材の主産地。<br>
      ・<b>天体半径 & 重力</b>: 大半径天体は平坦な平原が広がりやすく操縦・リグ展開に有利。高重力(3G+)での着陸には注意。<br>
      ・<b>環付きLandable</b>: 景観美に加え、固有の鉱物密集地帯としてコミュニティで最重要探索対象。
    </div>
  `;
  wrapper.appendChild(guideCard);

  // Sub-filter button bar
  const subFilterBar = document.createElement('div');
  subFilterBar.style.cssText = 'display: flex; align-items: center; gap: 6px; flex-wrap: wrap; background: rgba(0,0,0,0.25); padding: 6px 8px; border-radius: 4px; border: 1px solid var(--border-color);';
  
  const subFilters = [
    { key: 'all', label: `すべて (${totalLandable})`, icon: '🪐' },
    { key: 'hmc', label: `HMC (${hmcCount})`, icon: '🪐', color: '#60a5fa' },
    { key: 'metal_rich', label: `Metal Rich (${mrCount})`, icon: '🪐', color: '#fb923c' },
    { key: 'rocky', label: `Rocky (${rockyCount})`, icon: '🪐', color: '#cbd5e1' },
    { key: 'icy', label: `Icy (${icyCount})`, icon: '❄️', color: '#67e8f9' },
    { key: 'rocky_ice', label: `Icy Rocky (${rockyIceCount})`, icon: '🧊', color: '#93c5fd' },
    { key: 'ringed', label: `💍 Ringed (${ringedBodies.length})`, icon: '', color: '#f472b6' },
    { key: 'has_mining', label: `⛏️ 採掘地点あり (${landableBodies.filter(b => (b.mining_signals || 0) > 0).length})`, icon: '', color: '#38bdf8' }
  ];

  subFilters.forEach(sf => {
    const btn = document.createElement('button');
    btn.className = `view-btn ${state.miningSubFilter === sf.key ? 'active' : ''}`;
    btn.style.cssText = `padding: 2px 8px; font-size: 0.72rem; ${sf.color ? 'color: ' + sf.color + ';' : ''}`;
    btn.innerText = sf.label;
    btn.onclick = () => {
      state.miningSubFilter = sf.key;
      renderCurrentView();
    };
    subFilterBar.appendChild(btn);
  });
  wrapper.appendChild(subFilterBar);

  // Body Cards list
  if (displayBodies.length === 0) {
    const emptySub = document.createElement('div');
    emptySub.style.cssText = 'color: var(--text-secondary); text-align: center; padding: 25px;';
    emptySub.innerText = '選択された絞り込み条件に一致するLandable天体はありません。';
    wrapper.appendChild(emptySub);
  } else {
    displayBodies.forEach(body => {
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
      const rad = body.radius || 0;
      const radKm = Math.round(rad / 1000);
      const diamKm = radKm * 2;
      const isRinged = Boolean(body.rings && body.rings !== '[]' && body.rings !== '""');

      // Classify type
      const pLower = (body.planet_class || '').toLowerCase();
      let typeName = 'Landable';
      let typeStyle = 'background: rgba(203, 213, 225, 0.15); color: #cbd5e1; border: 1px solid rgba(203, 213, 225, 0.4);';
      let suitabilityBadge = '';

      if (pLower.includes('high metal')) {
        typeName = 'High Metal Content (HMC)';
        typeStyle = 'background: rgba(96, 165, 250, 0.18); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.5);';
        suitabilityBadge = `<span class="tag-badge" style="background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.4); font-weight: bold;">${t('rhino_suitability_high')}</span>`;
      } else if (pLower.includes('metal rich')) {
        typeName = 'Metal Rich body';
        typeStyle = 'background: rgba(251, 146, 60, 0.18); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.5);';
        suitabilityBadge = `<span class="tag-badge" style="background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.4); font-weight: bold;">${t('rhino_suitability_high')}</span>`;
      } else if (pLower.includes('rocky body') || (pLower.includes('rocky') && !pLower.includes('ice'))) {
        typeName = 'Rocky body';
        typeStyle = 'background: rgba(203, 213, 225, 0.18); color: #cbd5e1; border: 1px solid rgba(203, 213, 225, 0.5);';
        suitabilityBadge = `<span class="tag-badge" style="background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.4); font-weight: bold;">${t('rhino_suitability_high')}</span>`;
      } else if (pLower.includes('rocky ice') || pLower.includes('icy rocky')) {
        typeName = 'Rocky Ice body';
        typeStyle = 'background: rgba(147, 197, 253, 0.18); color: #93c5fd; border: 1px solid rgba(147, 197, 253, 0.5);';
        suitabilityBadge = `<span class="tag-badge" style="background: rgba(234, 179, 8, 0.15); color: #eab308; border: 1px solid rgba(234, 179, 8, 0.3);">${t('rhino_suitability_moderate')}</span>`;
      } else if (pLower.includes('icy')) {
        typeName = 'Icy body';
        typeStyle = 'background: rgba(103, 232, 249, 0.18); color: #67e8f9; border: 1px solid rgba(103, 232, 249, 0.5);';
        suitabilityBadge = `<span class="tag-badge" style="background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3);">${t('rhino_suitability_low')}</span>`;
      }

      // Gravity style
      const gVal = body.surface_gravity_g || 0;
      let gStyle = 'background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3);';
      if (gVal >= 3.0) {
        gStyle = 'background: rgba(239, 68, 68, 0.25); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.6); font-weight: bold;';
      } else if (gVal >= 1.5) {
        gStyle = 'background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4);';
      }

      // Materials chips
      let matHtml = '';
      if (body.materials) {
        try {
          const mats = typeof body.materials === 'string' ? JSON.parse(body.materials) : body.materials;
          if (Array.isArray(mats) && mats.length > 0) {
            const matChips = mats.slice(0, 8).map(m => {
              const mName = m.Name || m.name || '';
              const mPct = m.Percent !== undefined ? m.Percent.toFixed(1) + '%' : '';
              return `<span class="tag-badge" style="background: rgba(255,255,255,0.06); color: #e2e8f0; font-size: 0.65rem; padding: 1px 4px;">${mName} ${mPct}</span>`;
            });
            matHtml = `
              <div style="display: flex; flex-wrap: wrap; gap: 3px; margin-top: 6px; padding-top: 4px; border-top: 1px dashed rgba(255,255,255,0.06); align-items: center;">
                <span style="font-size: 0.68rem; color: var(--text-dim); margin-right: 2px;">地表含有素材:</span>
                ${matChips.join('')}
              </div>
            `;
          }
        } catch (e) {}
      }

      // Rhino mined activities: show WHERE (Lat/Lon) and WHAT (mined commodities), omit counts and raw materials
      let minedActHtml = '';
      const miningSites = body.rhino_mining_sites || [];
      if (miningSites.length > 0) {
        const allCommodities = new Set();
        const coordBadges = [];
        miningSites.forEach(s => {
          (s.commodities || []).forEach(c => allCommodities.add(c));
          if (s.latitude !== null && s.longitude !== null) {
            const latStr = (s.latitude >= 0 ? '+' : '') + s.latitude.toFixed(2);
            const lonStr = (s.longitude >= 0 ? '+' : '') + s.longitude.toFixed(2);
            coordBadges.push(`📍 ${latStr}°, ${lonStr}°`);
          }
        });

        const commBadges = Array.from(allCommodities).map(cName => `
          <span class="tag-badge" style="background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.68rem; padding: 1px 5px; font-weight: bold;">
            💎 ${cName}
          </span>
        `).join('');

        const locBadges = coordBadges.slice(0, 3).map(cStr => `
          <span class="tag-badge" style="background: rgba(251, 146, 60, 0.15); color: #fed7aa; border: 1px solid rgba(251, 146, 60, 0.4); font-size: 0.65rem; padding: 1px 4px; font-family: var(--font-mono);">
            ${cStr}
          </span>
        `).join('');

        minedActHtml = `
          <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; padding-top: 4px; border-top: 1px dashed rgba(56, 189, 248, 0.25); align-items: center;">
            <span style="font-size: 0.68rem; color: #38bdf8; font-weight: bold; margin-right: 2px;">🦏 Rhino採掘:</span>
            ${commBadges}
            ${locBadges}
          </div>
        `;
      }

      const aliasTag = (body.bookmark && body.bookmark.alias_name)
        ? `<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5); font-size: 0.75rem; font-weight: bold;">🏷️ ${body.bookmark.alias_name}</span>`
        : '';
      const bookmarkBadge = body.bookmark
        ? `<span class="tag-badge tag-bookmark" title="${(body.bookmark.alias_name ? `[${body.bookmark.alias_name}] ` : '') + (body.bookmark.note_markdown || '')}">🔖 ${body.bookmark.alias_name || 'BOOKMARK'}</span>`
        : '';

      card.innerHTML = `
        <div class="node-card-top">
          <div class="node-info-left" style="width: 100%;">
            <div class="body-icon ${iconClass}">${iconLabel}</div>
            <div class="node-details" style="flex: 1;">
              <div style="display: flex; align-items: center; justify-content: space-between; gap: 6px; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                  <span class="node-name" style="font-size: 0.95rem; ${isTarget ? 'color: var(--ed-cyan); font-weight: bold;' : ''}">${body.body_name}</span>
                  ${aliasTag}
                  <button class="view-btn btn-copy-body-sub" style="padding: 1px 5px; font-size: 0.68rem;" title="天体名をクリップボードにコピー">📋</button>
                </div>
                <div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary);">
                  ${formatDistance(body.distance_from_arrival_ls)} LS
                </div>
              </div>

              <!-- Main Badges Row -->
              <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; align-items: center;">
                ${bookmarkBadge}
                <span class="tag-badge" style="${typeStyle} font-weight: bold;">${typeName}</span>
                ${(() => {
                  if (!isRinged) return '';
                  let rList = body.rings_list;
                  if (!rList && body.rings) {
                    try { rList = typeof body.rings === 'string' ? JSON.parse(body.rings) : body.rings; } catch (e) { rList = []; }
                  }
                  rList = Array.isArray(rList) ? rList : [];
                  if (rList.length > 0) {
                    return rList.map(r => {
                      const info = parseRingClass(r.RingClass);
                      const isB = (r.Name || '').toLowerCase().includes('belt');
                      return `<span class="tag-badge" style="background: ${info.bg}; color: ${info.color}; border: 1px solid ${info.border}; font-weight: bold; box-shadow: 0 0 4px ${info.bg};" title="${r.Name || ''} - ${info.description}">
                        💍 環: ${info.icon} ${info.nameJa} (${info.nameEn}${isB ? ' Belt' : ''})
                      </span>`;
                    }).join(' ');
                  }
                  return '<span class="tag-badge" style="background: rgba(244, 114, 182, 0.2); color: #f472b6; border: 1px solid rgba(244, 114, 182, 0.6); font-weight: bold;">💍 環付き (Ringed Landable)</span>';
                })()}
                <span class="tag-badge" style="background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); font-weight: bold;">
                  🪐 半径: ${radKm.toLocaleString()} km (直径: ${diamKm.toLocaleString()} km)
                </span>
                ${state.showMiningGravity ? `<span class="tag-badge" style="${gStyle}">${gVal.toFixed(2)} G</span>` : ''}
                ${state.showMiningTemp ? `<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5); font-weight: bold;">🌡️ ${Math.round(body.surface_temperature || 0)} K</span>` : ''}
                ${body.mining_signals > 0 ? `<span class="tag-badge" style="background: rgba(56, 189, 248, 0.25); color: #38bdf8; border: 1px solid #38bdf8; font-weight: bold;">⛏️ 採掘地点: ${body.mining_signals} 箇所 (Rhino適格)</span>` : ''}
                ${suitabilityBadge}
              </div>

              <!-- Physical Details & Atmosphere -->
              <div style="display: flex; gap: 12px; margin-top: 5px; font-size: 0.72rem; color: var(--text-secondary); flex-wrap: wrap; align-items: center;">
                <span style="${state.showMiningTemp ? 'color: #38bdf8; font-weight: bold;' : ''}">表面温度: <b style="color: #fff;">${Math.round(body.surface_temperature || 0)} K (${Math.round((body.surface_temperature || 0) - 273.15)} ℃)</b></span>
                <span style="${state.showMiningGravity ? 'color: var(--ed-orange); font-weight: bold;' : ''}">重力: <b style="color: #fff;">${gVal.toFixed(2)} G</b></span>
                <span>大気: <b style="color: #fff;">${body.atmosphere || 'None'}</b></span>
                ${body.volcanism ? `<span>火山活動: <b style="color: #fff;">${body.volcanism}</b></span>` : ''}
              </div>

              ${matHtml}
              ${minedActHtml}
            </div>
          </div>
        </div>
      `;

      // Copy body name button handler
      const btnCopy = card.querySelector('.btn-copy-body-sub');
      if (btnCopy) {
        btnCopy.addEventListener('click', (e) => {
          e.stopPropagation();
          navigator.clipboard.writeText(body.body_name);
          btnCopy.innerText = '✓';
          setTimeout(() => { btnCopy.innerText = '📋'; }, 1200);
        });
      }

      wrapper.appendChild(card);
    });
  }

  container.appendChild(wrapper);
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
  const btnBmToggle = document.getElementById('btn-inspect-bookmark-toggle');
  const inspectAlias = document.getElementById('inspect-body-alias');

  if (!state.selectedBody) {
    inspectorContent.style.display = 'none';
    if (btnBmToggle) btnBmToggle.style.display = 'none';
    if (inspectAlias) {
      inspectAlias.style.display = 'none';
      inspectAlias.innerText = '';
    }
    document.getElementById('inspect-body-name').innerText = t('inspector_title');
    document.getElementById('inspect-body-type').innerText = t('inspector_subtitle');
    return;
  }

  inspectorContent.style.display = 'block';
  const b = state.selectedBody;
  const isBary = Boolean(b.isBarycentre);

  document.getElementById('inspect-body-name').innerText = b.body_name;
  document.getElementById('inspect-body-type').innerText = b.star_type 
    ? `${t('star_type_label')}: ${b.star_type}` 
    : `${b.planet_class || 'Body'}${b.terraforming_state ? ' [' + b.terraforming_state + ']' : ''}`;

  // Bookmark UI elements
  const bmSection = document.getElementById('section-bookmark');
  const bmStatusIndicator = document.getElementById('bm-status-indicator');
  const btnBmSave = document.getElementById('btn-save-bookmark');
  const btnBmDelete = document.getElementById('btn-delete-bookmark');
  const bmAliasInput = document.getElementById('bm-alias-input');
  const bmNoteInput = document.getElementById('bm-note-input');
  const bmNotePreview = document.getElementById('bm-note-preview');
  const bmTabEdit = document.getElementById('bm-note-tab-edit');
  const bmTabPreview = document.getElementById('bm-note-tab-preview');
  const inspectBmIcon = document.getElementById('inspect-bm-icon');
  const inspectBmText = document.getElementById('inspect-bm-text');

  if (isBary) {
    if (btnBmToggle) btnBmToggle.style.display = 'none';
    if (bmSection) bmSection.style.display = 'none';
    if (inspectAlias) {
      inspectAlias.style.display = 'none';
      inspectAlias.innerText = '';
    }
  } else {
    if (btnBmToggle) btnBmToggle.style.display = 'inline-flex';
    if (bmSection) bmSection.style.display = 'block';

    const isBookmarked = Boolean(b.bookmark);
    if (isBookmarked) {
      if (inspectBmIcon) inspectBmIcon.innerText = '★';
      if (inspectBmText) inspectBmText.innerText = 'ブックマーク中';
      if (btnBmToggle) {
        btnBmToggle.classList.add('active');
        btnBmToggle.style.background = 'rgba(251, 191, 36, 0.2)';
      }
      if (bmStatusIndicator) bmStatusIndicator.style.display = 'inline-block';
      if (btnBmDelete) btnBmDelete.style.display = 'inline-block';
      if (bmAliasInput) bmAliasInput.value = b.bookmark.alias_name || '';
      if (bmNoteInput) bmNoteInput.value = b.bookmark.note_markdown || '';
      if (inspectAlias) {
        if (b.bookmark.alias_name) {
          inspectAlias.innerText = `🏷️ ${b.bookmark.alias_name}`;
          inspectAlias.style.display = 'block';
        } else {
          inspectAlias.innerText = '';
          inspectAlias.style.display = 'none';
        }
      }
    } else {
      if (inspectBmIcon) inspectBmIcon.innerText = '☆';
      if (inspectBmText) inspectBmText.innerText = 'ブックマーク';
      if (btnBmToggle) {
        btnBmToggle.classList.remove('active');
        btnBmToggle.style.background = '';
      }
      if (bmStatusIndicator) bmStatusIndicator.style.display = 'none';
      if (btnBmDelete) btnBmDelete.style.display = 'none';
      if (bmAliasInput) bmAliasInput.value = '';
      if (bmNoteInput) bmNoteInput.value = '';
      if (inspectAlias) {
        inspectAlias.innerText = '';
        inspectAlias.style.display = 'none';
      }
    }

    // Default to Edit tab
    if (bmTabEdit && bmTabPreview && bmNoteInput && bmNotePreview) {
      bmTabEdit.classList.add('active');
      bmTabPreview.classList.remove('active');
      bmNoteInput.style.display = 'block';
      bmNotePreview.style.display = 'none';

      bmTabEdit.onclick = () => {
        bmTabEdit.classList.add('active');
        bmTabPreview.classList.remove('active');
        bmNoteInput.style.display = 'block';
        bmNotePreview.style.display = 'none';
      };

      bmTabPreview.onclick = () => {
        bmTabPreview.classList.add('active');
        bmTabEdit.classList.remove('active');
        bmNotePreview.innerHTML = parseMarkdown(bmNoteInput.value.trim() || '*メモは入力されていません*');
        bmNoteInput.style.display = 'none';
        bmNotePreview.style.display = 'block';
      };
    }

    // Save Bookmark Handler
    if (btnBmSave) {
      btnBmSave.onclick = async () => {
        const curSys = state.currentSystemData ? state.currentSystemData.system : state.selectedSystem;
        if (!curSys || !b) return;
        const payload = {
          system_address: curSys.system_address,
          body_id: b.body_id,
          body_name: b.body_name,
          star_system: curSys.star_system,
          alias_name: (bmAliasInput ? bmAliasInput.value.trim() : ''),
          note_markdown: (bmNoteInput ? bmNoteInput.value : '')
        };
        try {
          btnBmSave.disabled = true;
          const res = await fetch('/api/bookmark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          btnBmSave.disabled = false;
          if (res.ok) {
            b.bookmark = payload;
            if (curSys) {
              if (!curSys.bookmarks) curSys.bookmarks = [];
              const existIdx = curSys.bookmarks.findIndex(x => x.body_id === b.body_id);
              const bmObj = {
                body_id: b.body_id,
                body_name: b.body_name,
                alias_name: payload.alias_name,
                has_note: Boolean(payload.note_markdown.trim()),
                note_snippet: payload.note_markdown.trim().substring(0, 60)
              };
              if (existIdx >= 0) curSys.bookmarks[existIdx] = bmObj;
              else curSys.bookmarks.push(bmObj);
            }
            renderBodyInspector();
            renderCurrentView();
            renderSystemList();
          }
        } catch (e) {
          btnBmSave.disabled = false;
          console.error('Failed to save bookmark:', e);
        }
      };
    }

    // Delete Bookmark Handler
    if (btnBmDelete) {
      btnBmDelete.onclick = async () => {
        const curSys = state.currentSystemData ? state.currentSystemData.system : state.selectedSystem;
        if (!curSys || !b) return;
        try {
          btnBmDelete.disabled = true;
          const res = await fetch(`/api/bookmark/${curSys.system_address}/${b.body_id}`, {
            method: 'DELETE'
          });
          btnBmDelete.disabled = false;
          if (res.ok) {
            b.bookmark = null;
            if (curSys && curSys.bookmarks) {
              curSys.bookmarks = curSys.bookmarks.filter(x => x.body_id !== b.body_id);
            }
            renderBodyInspector();
            renderCurrentView();
            renderSystemList();
          }
        } catch (e) {
          btnBmDelete.disabled = false;
          console.error('Failed to delete bookmark:', e);
        }
      };
    }

    // Header Bookmark toggle button
    if (btnBmToggle) {
      btnBmToggle.onclick = () => {
        if (b.bookmark) {
          if (bmSection) bmSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          if (bmAliasInput) bmAliasInput.focus();
        } else {
          if (btnBmSave) btnBmSave.click();
        }
      };
    }
  }

  // Anomalies & Barycentre Info
  const anomSection = document.getElementById('section-anomalies');
  const anomTags = document.getElementById('inspect-anomaly-tags');
  if (b.isBarycentre) {
    anomSection.style.display = 'block';
    const starList = (b.barycentreStars || []).map(s => `Star ${s}`).join(' & ');
    anomTags.innerHTML = `
      <div style="background: rgba(147, 51, 234, 0.15); border: 1px solid rgba(147, 51, 234, 0.5); padding: 8px; border-radius: 6px; color: #e9d5ff; font-size: 0.8rem; line-height: 1.4;">
        <div style="font-weight: bold; color: #c084fc; margin-bottom: 4px;">♊ 連星系共通重心（Barycentre）</div>
        <div>構成恒星: <strong>${starList}</strong></div>
        <div style="margin-top: 4px; color: var(--text-secondary);">この共通重心軌道上を周回する天体（${b.starGroup} 1, ${b.starGroup} 2...）の親軌道ノードです。</div>
      </div>
    `;
  } else if (b.anomalies && b.anomalies.length > 0) {
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
        const spName = bio.species_variant || bio.species_localised || bio.species || bio.genus_localised || bio.genus || 'Candidate';

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
    landableEl.innerHTML = `<span>✓</span> <span>Landable</span>`;
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

  // Radius & Diameter
  const radiusEl = document.getElementById('prop-radius');
  const diamEl = document.getElementById('prop-diameter');
  if (b.radius !== null && b.radius !== undefined && b.radius > 0) {
    const radKm = b.radius / 1000;
    const diamKm = (b.radius * 2) / 1000;
    if (radiusEl) radiusEl.innerText = `${radKm.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})} km`;
    if (diamEl) diamEl.innerText = `${diamKm.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})} km`;
  } else {
    if (radiusEl) radiusEl.innerText = '--';
    if (diamEl) diamEl.innerText = '--';
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

  // Planetary Mining Locations Section & Property Card
  const miningSec = document.getElementById('section-mining-activities') || document.getElementById('section-mining');
  const miningCountEl = document.getElementById('inspect-mining-count');
  const propCardMining = document.getElementById('prop-card-mining');
  const propMining = document.getElementById('prop-mining');
  const miningActivitiesEl = document.getElementById('inspect-mining-activities');
  const miningSigCount = b.mining_signals || 0;
  const miningSites = b.rhino_mining_sites || [];

  if (miningSigCount > 0 || miningSites.length > 0) {
    if (miningSec) miningSec.style.display = 'block';
    if (miningCountEl) miningCountEl.innerText = miningSigCount;
    if (propCardMining) propCardMining.style.display = 'block';
    if (propMining) propMining.innerText = `${miningSigCount} 箇所 (Planetary Mining Locations)`;

    if (miningActivitiesEl) {
      if (miningSites.length > 0) {
        // Build SVG markers for sites with coordinates
        const markersSvg = miningSites.map((site, idx) => {
          if (site.latitude === null || site.longitude === null) return '';
          const cx = site.longitude;
          const cy = -site.latitude;
          const commNames = (site.commodities || []).join(', ');
          const latFmt = (site.latitude >= 0 ? '+' : '') + site.latitude.toFixed(4);
          const lonFmt = (site.longitude >= 0 ? '+' : '') + site.longitude.toFixed(4);
          return `
            <g class="mining-map-marker" data-site-idx="${idx}" style="cursor: pointer;">
              <circle cx="${cx}" cy="${cy}" r="6" fill="none" stroke="#38bdf8" stroke-width="1.2" class="pulse-marker" />
              <circle cx="${cx}" cy="${cy}" r="3" fill="#38bdf8" stroke="#ffffff" stroke-width="0.8" />
              <title>${commNames} (Lat: ${latFmt}°, Lon: ${lonFmt}°)</title>
            </g>
          `;
        }).join('');

        const hasAnyCoords = miningSites.some(s => s.latitude !== null && s.longitude !== null);

        const mapHtml = hasAnyCoords ? `
          <div class="mining-map-container" style="background: radial-gradient(circle at center, #0e1b2e 0%, #060913 100%); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 6px; padding: 8px; position: relative; margin-top: 6px; box-shadow: inset 0 0 16px rgba(0,0,0,0.6);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 0.72rem;">
              <span style="color: #38bdf8; font-weight: bold; display: flex; align-items: center; gap: 4px;">
                <span>🌐</span> <span>惑星表面 採掘座標マップ (2D Grid)</span>
              </span>
              <span style="color: var(--text-dim); font-family: var(--font-mono); font-size: 0.68rem;">記録地点: ${miningSites.length} 箇所</span>
            </div>
            <div style="position: relative; width: 100%;">
              <svg viewBox="-180 -90 360 180" style="width: 100%; height: auto; max-height: 150px; display: block; background: rgba(5, 10, 20, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px;">
                <!-- Latitudes -->
                <line x1="-180" y1="0" x2="180" y2="0" stroke="rgba(56, 189, 248, 0.45)" stroke-width="0.8" stroke-dasharray="2,2" />
                <line x1="-180" y1="-45" x2="180" y2="-45" stroke="rgba(255, 255, 255, 0.12)" stroke-width="0.5" stroke-dasharray="2,3" />
                <line x1="-180" y1="45" x2="180" y2="45" stroke="rgba(255, 255, 255, 0.12)" stroke-width="0.5" stroke-dasharray="2,3" />
                <!-- Longitudes -->
                <line x1="0" y1="-90" x2="0" y2="90" stroke="rgba(56, 189, 248, 0.45)" stroke-width="0.8" stroke-dasharray="2,2" />
                <line x1="-90" y1="-90" x2="-90" y2="90" stroke="rgba(255, 255, 255, 0.12)" stroke-width="0.5" stroke-dasharray="2,3" />
                <line x1="90" y1="-90" x2="90" y2="90" stroke="rgba(255, 255, 255, 0.12)" stroke-width="0.5" stroke-dasharray="2,3" />
                <!-- Labels -->
                <text x="-176" y="-76" fill="#64748b" font-size="7" font-family="sans-serif">N 90°</text>
                <text x="-176" y="86" fill="#64748b" font-size="7" font-family="sans-serif">S -90°</text>
                <text x="-176" y="-3" fill="#38bdf8" font-size="6.5" font-family="sans-serif" opacity="0.8">0° (赤道)</text>
                <text x="2" y="-76" fill="#38bdf8" font-size="6.5" font-family="sans-serif" opacity="0.8">0° (子午線)</text>
                <text x="-176" y="12" fill="#64748b" font-size="6" font-family="sans-serif">-180°</text>
                <text x="154" y="12" fill="#64748b" font-size="6" font-family="sans-serif">+180°</text>
                <!-- Markers -->
                ${markersSvg}
              </svg>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.62rem; color: var(--text-dim);">
              <span>西半球 (-180° ~ 0°)</span>
              <span>子午線 (0°) / 赤道 (0°)</span>
              <span>東半球 (0° ~ +180°)</span>
            </div>
          </div>
        ` : '';

        // Build Cards List
        const cardsHtml = `
          <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 8px;">
            ${miningSites.map((site, idx) => {
              const hasCoord = site.latitude !== null && site.longitude !== null;
              const latStr = hasCoord ? `${site.latitude >= 0 ? '+' : ''}${site.latitude.toFixed(4)}°` : '--';
              const lonStr = hasCoord ? `${site.longitude >= 0 ? '+' : ''}${site.longitude.toFixed(4)}°` : '--';
              const copyVal = hasCoord ? `${site.latitude.toFixed(4)}, ${site.longitude.toFixed(4)}` : '';
              const minerals = (site.commodities || []).map(m => `
                <span class="tag-badge" style="background: rgba(56, 189, 248, 0.15); color: #e0f2fe; border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.72rem; padding: 2px 6px; font-weight: bold;">
                  💎 ${m}
                </span>
              `).join('');
              const lastTime = site.last_mined ? site.last_mined.replace('T', ' ').replace('Z', '') : '';

              return `
                <div class="mining-site-card" id="mining-site-card-${idx}" style="background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 8px 10px; transition: all 0.2s;">
                  <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px; margin-bottom: 5px;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                      <span style="color: var(--ed-orange); font-size: 0.85rem;">📍</span>
                      <span style="font-family: var(--font-mono); font-size: 0.78rem; font-weight: bold; color: #fff;">
                        ${hasCoord ? `緯度: ${latStr}  経度: ${lonStr}` : '<span style="color: var(--text-dim);">座標記録なし</span>'}
                      </span>
                    </div>
                    ${hasCoord ? `
                      <button type="button" class="view-btn btn-copy-coords" data-coords="${copyVal}" style="padding: 2px 8px; font-size: 0.68rem; background: rgba(56, 189, 248, 0.15); border-color: rgba(56, 189, 248, 0.4); color: #38bdf8; cursor: pointer;" title="クリップボードに座標 (${copyVal}) をコピー">
                        📋 座標コピー
                      </button>
                    ` : ''}
                  </div>
                  <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px;">
                    <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                      ${minerals || '<span style="color: var(--text-dim); font-size: 0.7rem;">精製鉱物なし</span>'}
                    </div>
                    ${lastTime ? `
                      <span style="font-size: 0.65rem; color: var(--text-dim); font-family: var(--font-mono);">
                        🕒 ${lastTime}
                      </span>
                    ` : ''}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `;

        miningActivitiesEl.innerHTML = `
          <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 10px; margin-top: 6px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
              <span style="font-size: 0.78rem; font-weight: bold; color: #38bdf8; display: flex; align-items: center; gap: 4px;">
                <span>🦏</span> <span>Rhino 惑星表面採掘地点 & 鉱物</span>
              </span>
              <span style="font-size: 0.7rem; color: var(--text-dim); font-family: var(--font-mono);">採掘地点: ${miningSites.length} 箇所</span>
            </div>
            ${mapHtml}
            ${cardsHtml}
          </div>
        `;

        // Bind copy buttons
        miningActivitiesEl.querySelectorAll('.btn-copy-coords').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const coords = btn.dataset.coords;
            if (coords && navigator.clipboard) {
              navigator.clipboard.writeText(coords).then(() => {
                const orig = btn.innerHTML;
                btn.innerHTML = '✓ コピー済';
                btn.style.color = '#38bdf8';
                btn.style.borderColor = '#38bdf8';
                setTimeout(() => {
                  btn.innerHTML = orig;
                  btn.style.color = '';
                  btn.style.borderColor = '';
                }, 1800);
              });
            }
          });
        });

        // Bind map markers hover/click to highlight cards
        miningActivitiesEl.querySelectorAll('.mining-map-marker').forEach(marker => {
          const sIdx = marker.dataset.siteIdx;
          const targetCard = document.getElementById(`mining-site-card-${sIdx}`);
          marker.addEventListener('mouseenter', () => {
            if (targetCard) targetCard.classList.add('highlighted');
          });
          marker.addEventListener('mouseleave', () => {
            if (targetCard) targetCard.classList.remove('highlighted');
          });
          marker.addEventListener('click', () => {
            if (targetCard) {
              targetCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
              targetCard.classList.add('highlighted');
              setTimeout(() => targetCard.classList.remove('highlighted'), 2000);
            }
          });
        });

      } else {
        miningActivitiesEl.innerHTML = `
          <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 6px; padding: 6px 8px; background: rgba(15, 23, 42, 0.4); border: 1px dashed rgba(56, 189, 248, 0.2); border-radius: 4px;">
            まだこの天体でのRhino採掘ログ（鉱物精製）は記録されていません。<br>
            現地（PML）でRhino採掘Rigを展開して鉱物精製を行うと、採掘地点（緯度・経度）と鉱物種別が自動マッピングされます。
          </div>
        `;
      }
    }
  } else {
    if (miningSec) miningSec.style.display = 'none';
    if (propCardMining) propCardMining.style.display = 'none';
  }

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

  // Rings & Asteroid Belts Section
  const ringsSection = document.getElementById('section-rings');
  const ringsList = document.getElementById('inspect-rings-list');
  let ringsData = b.rings_list;
  if (!ringsData && b.rings && b.rings !== '[]' && b.rings !== '""') {
    try { ringsData = typeof b.rings === 'string' ? JSON.parse(b.rings) : b.rings; } catch (e) { ringsData = []; }
  }
  ringsData = Array.isArray(ringsData) ? ringsData : [];

  if (ringsData && ringsData.length > 0) {
    ringsSection.style.display = 'block';

    const hasBelts = ringsData.some(r => (r.Name || '').toLowerCase().includes('belt'));
    const hasRings = ringsData.some(r => !(r.Name || '').toLowerCase().includes('belt'));
    const headingEl = ringsSection.querySelector('.section-heading');
    if (headingEl) {
      if (hasBelts && !hasRings) {
        headingEl.innerText = t('section_rings_belts') || '🪐 アステロイドベルト (Asteroid Belts)';
      } else if (hasRings && !hasBelts) {
        headingEl.innerText = t('section_rings_planet') || '💍 プラネタリーリング (Planetary Rings)';
      } else {
        headingEl.innerText = t('section_rings') || '💍 リング / アステロイドベルト';
      }
    }

    // Reserve Level Badge
    const reserveInfo = parseReserveLevel(b.reserve_level);
    const reserveBadge = reserveInfo ? `
      <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.35); border-radius: 4px; padding: 6px 10px; margin-bottom: 8px; font-size: 0.78rem; display: flex; align-items: center; justify-content: space-between;">
        <span style="color: var(--text-secondary); display: flex; align-items: center; gap: 4px;">
          <span>${reserveInfo.icon}</span> <span>資源埋蔵量 (Reserve Level):</span>
        </span>
        <span style="color: ${reserveInfo.color}; font-weight: bold;">${reserveInfo.en} (${reserveInfo.ja})</span>
      </div>
    ` : '';

    const itemsHtml = ringsData.map(r => {
      const isBelt = (r.Name || '').toLowerCase().includes('belt');
      const rInfo = parseRingClass(r.RingClass);
      const innerKm = Math.round((r.InnerRad || 0) / 1000);
      const outerKm = Math.round((r.OuterRad || 0) / 1000);
      const widthKm = Math.max(0, outerKm - innerKm);
      const massMt = r.MassMT || 0;
      const massStr = massMt >= 1e6 
        ? `${(massMt / 1e6).toLocaleString(undefined, {maximumFractionDigits: 1})} M MT` 
        : `${Math.round(massMt).toLocaleString()} MT`;

      const typeBadge = `<span class="tag-badge" style="background: ${rInfo.bg}; color: ${rInfo.color}; border: 1px solid ${rInfo.border}; font-weight: bold; font-size: 0.72rem;">
        ${rInfo.icon} ${rInfo.nameJa} (${rInfo.nameEn} ${isBelt ? 'Belt' : 'Ring'})
      </span>`;

      let miningHint = '';
      if (rInfo.key === 'icy') {
        miningHint = `<div style="margin-top: 5px; font-size: 0.72rem; color: #7dd3fc; background: rgba(56, 189, 248, 0.1); border-left: 3px solid #38bdf8; padding: 3px 6px; border-radius: 2px;">
          💎 Fleet Carrier燃料（トリチウム / Tritium）採掘適性あり
        </div>`;
      } else if (rInfo.key === 'metallic') {
        miningHint = `<div style="margin-top: 5px; font-size: 0.72rem; color: #fde047; background: rgba(250, 204, 21, 0.1); border-left: 3px solid #facc15; padding: 3px 6px; border-radius: 2px;">
          🪙 プラチナ / ペイン石 / オスミウム等 高額金属レーザー採掘の最重要スポット
        </div>`;
      } else if (rInfo.key === 'rocky') {
        miningHint = `<div style="margin-top: 5px; font-size: 0.72rem; color: #e2e8f0; background: rgba(203, 213, 225, 0.1); border-left: 3px solid #cbd5e1; padding: 3px 6px; border-radius: 2px;">
          🪨 マスグラバイト / アレキサンドライト等 高額深部鉱石のコア破砕採掘適性
        </div>`;
      } else if (rInfo.key === 'metal_rich') {
        miningHint = `<div style="margin-top: 5px; font-size: 0.72rem; color: #fdba74; background: rgba(251, 146, 60, 0.1); border-left: 3px solid #fb923c; padding: 3px 6px; border-radius: 2px;">
          🪐 金属豊富ベルト/リング (各種工業用・貴金属素材)
        </div>`;
      }

      return `
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 5px; padding: 8px 10px; margin-bottom: 6px;">
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 6px; flex-wrap: wrap;">
            <span style="font-weight: bold; color: var(--ed-gold); font-size: 0.8rem;">${r.Name || (isBelt ? 'Asteroid Belt' : 'Ring')}</span>
            ${typeBadge}
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 6px; font-size: 0.72rem; color: var(--text-secondary); background: rgba(0,0,0,0.25); padding: 5px 8px; border-radius: 4px;">
            <span>内径: <b style="color: #e2e8f0;">${innerKm.toLocaleString()} km</b></span>
            <span>外径: <b style="color: #e2e8f0;">${outerKm.toLocaleString()} km</b></span>
            <span>幅: <b style="color: #e2e8f0;">${widthKm.toLocaleString()} km</b></span>
            <span>総質量: <b style="color: #e2e8f0;">${massStr}</b></span>
          </div>
          ${miningHint}
        </div>
      `;
    }).join('');

    ringsList.innerHTML = reserveBadge + itemsHtml;
  } else {
    ringsSection.style.display = 'none';
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  updateStaticTexts();
  if (typeof syncLanguageFromServer === 'function') {
    syncLanguageFromServer();
  }
  initSettingsModal();
  initExportImportModals();
  fetchGlobalStats();
  fetchSystems();
  checkScanOnStartup();

  // Language Switchers (Header)
  document.getElementById('btn-lang-ja')?.addEventListener('click', () => setLanguage('ja'));
  document.getElementById('btn-lang-en')?.addEventListener('click', () => setLanguage('en'));

  // Language Switchers (Settings Modal)
  document.getElementById('btn-modal-lang-ja')?.addEventListener('click', () => setLanguage('ja'));
  document.getElementById('btn-modal-lang-en')?.addEventListener('click', () => setLanguage('en'));

  // Search input
  let searchTimeout = null;
  document.getElementById('system-search').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.searchQuery = e.target.value;
      state.page = 1;
      fetchSystems({ autoSelectTop: true });
    }, 300);
  });

  // Filter chips
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const filterKey = chip.dataset.filter;
      state.filters[filterKey] = !state.filters[filterKey];
      chip.classList.toggle('active', state.filters[filterKey]);
      state.page = 1;
      fetchSystems({ autoSelectTop: true });
    });
  });

  // Mining display toggles (Gravity & Temperature)
  const toggleGrav = document.getElementById('toggle-mining-gravity');
  const toggleTemp = document.getElementById('toggle-mining-temp');
  if (toggleGrav) {
    toggleGrav.checked = state.showMiningGravity;
    toggleGrav.addEventListener('change', () => {
      state.showMiningGravity = toggleGrav.checked;
      localStorage.setItem('mining_display_gravity', state.showMiningGravity);
      renderSystemList();
      renderCurrentView();
    });
  }
  if (toggleTemp) {
    toggleTemp.checked = state.showMiningTemp;
    toggleTemp.addEventListener('change', () => {
      state.showMiningTemp = toggleTemp.checked;
      localStorage.setItem('mining_display_temp', state.showMiningTemp);
      renderSystemList();
      renderCurrentView();
    });
  }

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
    fetchSystems({ autoSelectTop: true });
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
      fetchSystems({ autoSelectTop: true });
      fetchGlobalStats();
    });
  }

  if (dateToInput) {
    dateToInput.addEventListener('change', (e) => {
      state.dateTo = e.target.value;
      presetSelect.value = 'custom';
      state.page = 1;
      fetchSystems({ autoSelectTop: true });
    });
  }

  if (dateFieldSelect) {
    dateFieldSelect.addEventListener('change', (e) => {
      state.dateField = e.target.value;
      state.page = 1;
      fetchSystems({ autoSelectTop: true });
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
    fetchSystems({ autoSelectTop: true });
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
      fetchSystems({ autoSelectTop: true });
    });
  }

  // Sort select 3 for systems
  const sortSelect3 = document.getElementById('sort-select-3');
  if (sortSelect3) {
    sortSelect3.addEventListener('change', (e) => {
      if (state.liveSyncEnabled) return;
      if (e.target.value === 'none') {
        state.savedSortBy3 = null;
        state.sortBy3 = null;
      } else {
        const [by, order] = e.target.value.split('-');
        state.savedSortBy3 = by;
        state.savedSortOrder3 = order;
        state.sortBy3 = by;
        state.sortOrder3 = order;
      }
      state.page = 1;
      fetchSystems({ autoSelectTop: true });
    });
  }

  // Composite sort mode toggle checkbox
  const cbSortComposite = document.getElementById('cb-sort-composite');
  if (cbSortComposite) {
    cbSortComposite.addEventListener('change', (e) => {
      state.sortMode = e.target.checked ? 'composite' : 'strict';
      state.page = 1;
      fetchSystems({ autoSelectTop: true });
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

  const btnViewMining = document.getElementById('btn-view-mining');
  if (btnViewMining) {
    btnViewMining.addEventListener('click', () => {
      state.currentView = 'mining';
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
    const btnMining = document.getElementById('btn-view-mining');
    const btnVis = document.getElementById('btn-view-visits');

    if (btnSys) btnSys.classList.toggle('active', state.currentView === 'sysmap');
    if (btnFlat) btnFlat.classList.toggle('active', state.currentView === 'flat');
    if (btnBio) btnBio.classList.toggle('active', state.currentView === 'bio');
    if (btnMining) btnMining.classList.toggle('active', state.currentView === 'mining');
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
    btnLiveToggle.addEventListener('click', async () => {
      // If currently on Honk waiting screen or hyperspace, dismiss it and show current known system
      if (state.jumpState === 'arrived_waiting_fss' || state.jumpState === 'hyperspace') {
        state.liveSyncEnabled = true;
        updateLiveSyncButtonUI();
        updateSortControlsUI();
        await dismissHonkWaitingAndShowCurrent();
        return;
      }

      state.liveSyncEnabled = !state.liveSyncEnabled;
      state.page = 1;
      updateLiveSyncButtonUI();
      updateSortControlsUI();
      if (state.liveSyncEnabled) {
        state.jumpState = 'idle';
        await fetchSystems({ autoSelectTop: false });
        if (state.currentCmdrSystemAddress) {
          selectSystem(state.currentCmdrSystemAddress, false, false);
        } else if (state.systems && state.systems.length > 0) {
          selectSystem(state.systems[0].system_address, false, false);
        }
      } else {
        fetchSystems();
      }
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
  const sortSelect3 = document.getElementById('sort-select-3');
  const cbSortComposite = document.getElementById('cb-sort-composite');
  if (!sortSelect1) return;

  if (state.liveSyncEnabled) {
    sortSelect1.disabled = true;
    if (sortSelect2) sortSelect2.disabled = true;
    if (sortSelect3) sortSelect3.disabled = true;
    if (cbSortComposite) cbSortComposite.disabled = true;

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
    if (sortSelect3) sortSelect3.value = 'none';

    document.querySelectorAll('.sort-row').forEach(el => el.classList.add('sort-locked'));
  } else {
    sortSelect1.disabled = false;
    if (sortSelect2) sortSelect2.disabled = false;
    if (sortSelect3) sortSelect3.disabled = false;
    if (cbSortComposite) cbSortComposite.disabled = false;

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
    if (sortSelect3) {
      sortSelect3.value = state.savedSortBy3 ? `${state.savedSortBy3}-${state.savedSortOrder3}` : 'none';
    }
    if (cbSortComposite) {
      cbSortComposite.checked = (state.sortMode === 'composite');
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

  // UI Font Size / Scaling Control
  function initFontSizeControl() {
    const inputSize = document.getElementById('input-font-size');
    const btnDec = document.getElementById('btn-font-dec');
    const btnInc = document.getElementById('btn-font-inc');
    const btnReset = document.getElementById('btn-reset-font-size');
    const presetBtns = document.querySelectorAll('.btn-font-preset');

    function getCurrentFontSize() {
      const saved = localStorage.getItem('app_base_font_size');
      const parsed = saved ? parseInt(saved, 10) : 18;
      return (!isNaN(parsed) && parsed >= 8 && parsed <= 60) ? parsed : 18;
    }

    function setFontSize(sizePx) {
      const clamped = Math.max(8, Math.min(60, sizePx));
      document.documentElement.style.fontSize = `${clamped}px`;
      localStorage.setItem('app_base_font_size', clamped);
      if (inputSize) inputSize.value = clamped;

      if (presetBtns) {
        presetBtns.forEach(btn => {
          const bSize = parseInt(btn.dataset.size, 10);
          if (bSize === clamped) {
            btn.classList.add('active');
            btn.style.borderColor = 'var(--ed-cyan)';
            btn.style.color = 'var(--ed-cyan)';
            btn.style.fontWeight = 'bold';
          } else {
            btn.classList.remove('active');
            btn.style.borderColor = 'var(--border-color)';
            btn.style.color = 'var(--text-primary)';
            btn.style.fontWeight = 'normal';
          }
        });
      }
    }

    // Initial apply
    const curSize = getCurrentFontSize();
    setFontSize(curSize);

    if (inputSize) {
      inputSize.addEventListener('change', (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) setFontSize(val);
      });
      inputSize.addEventListener('input', (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val) && val >= 8 && val <= 60) setFontSize(val);
      });
    }

    if (btnDec) {
      btnDec.addEventListener('click', () => {
        const current = getCurrentFontSize();
        setFontSize(current - 1);
      });
    }

    if (btnInc) {
      btnInc.addEventListener('click', () => {
        const current = getCurrentFontSize();
        setFontSize(current + 1);
      });
    }

    if (btnReset) {
      btnReset.addEventListener('click', () => {
        setFontSize(18);
      });
    }

    if (presetBtns) {
      presetBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const targetSize = parseInt(btn.dataset.size, 10);
          if (!isNaN(targetSize)) setFontSize(targetSize);
        });
      });
    }

    // Emergency safety keyboard shortcut: Ctrl + 0 or Alt + 0 resets font size to standard 18px
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === '0' || e.code === 'Digit0' || e.code === 'Numpad0')) {
        e.preventDefault();
        setFontSize(18);
      }
    });
  }

  // Bind Unified Settings Modal & Tabs
  const modal = document.getElementById('settings-modal');
  const btnOpen = document.getElementById('btn-settings-open');
  const btnClose = document.getElementById('btn-settings-close');
  const btnSave = document.getElementById('btn-settings-save');

  const tabBtnLogs = document.getElementById('tab-btn-logs');
  const tabBtnUI = document.getElementById('tab-btn-ui');
  const tabBtnTTS = document.getElementById('tab-btn-tts');
  const tabBtnCredits = document.getElementById('tab-btn-credits');

  const tabPaneLogs = document.getElementById('tab-pane-logs');
  const tabPaneUI = document.getElementById('tab-pane-ui');
  const tabPaneTTS = document.getElementById('tab-pane-tts');
  const tabPaneCredits = document.getElementById('tab-pane-credits');

  function switchTab(tabName) {
    [tabBtnLogs, tabBtnUI, tabBtnTTS, tabBtnCredits].forEach(btn => {
      if (btn) {
        btn.classList.remove('active');
        btn.style.borderBottom = 'none';
      }
    });
    [tabPaneLogs, tabPaneUI, tabPaneTTS, tabPaneCredits].forEach(pane => {
      if (pane) pane.style.display = 'none';
    });

    if (tabName === 'logs') {
      if (tabBtnLogs) {
        tabBtnLogs.classList.add('active');
        tabBtnLogs.style.borderBottom = '2px solid var(--ed-orange)';
      }
      if (tabPaneLogs) tabPaneLogs.style.display = 'flex';
      loadAppSettingsToUI();
    } else if (tabName === 'ui') {
      if (tabBtnUI) {
        tabBtnUI.classList.add('active');
        tabBtnUI.style.borderBottom = '2px solid var(--ed-cyan)';
      }
      if (tabPaneUI) tabPaneUI.style.display = 'flex';
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
  if (tabBtnUI) tabBtnUI.addEventListener('click', () => switchTab('ui'));
  if (tabBtnTTS) tabBtnTTS.addEventListener('click', () => switchTab('tts'));
  if (tabBtnCredits) tabBtnCredits.addEventListener('click', () => switchTab('credits'));

  initFontSizeControl();

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

function initExportImportModals() {
  // Method 2: Standalone Web Share HTML Export
  const btnExportHtml = document.getElementById('btn-export-html');
  if (btnExportHtml) {
    btnExportHtml.addEventListener('click', async () => {
      if (!state.selectedSystem || !state.selectedSystem.system_address) return;
      const sysAddr = state.selectedSystem.system_address;
      const sysName = (state.selectedSystem.star_system || 'System').replace(/[^a-zA-Z0-9_-]/g, '_');
      
      const origHtml = btnExportHtml.innerHTML;
      btnExportHtml.innerHTML = `<span>⏳ ${t('exporting') || '生成中...'}</span>`;
      btnExportHtml.disabled = true;

      try {
        const res = await fetch(`/api/export/html/${sysAddr}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${sysName}_share.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Failed to export HTML:', err);
        alert(t('export_failed') || 'HTML出力に失敗しました');
      } finally {
        btnExportHtml.innerHTML = origHtml;
        btnExportHtml.disabled = false;
      }
    });
  }

  // Method 1: Locked Package Export (.edsys)
  const modalExportLocked = document.getElementById('modal-export-locked');
  const btnExportPkg = document.getElementById('btn-export-pkg');
  const btnCloseExportModal = document.getElementById('btn-close-export-modal');
  const btnCancelExport = document.getElementById('btn-cancel-export');
  const btnSubmitExportPkg = document.getElementById('btn-submit-export-pkg');
  const cbExportConsent = document.getElementById('cb-export-consent');
  const exportTargetSysName = document.getElementById('export-target-system-name');
  const exportCmdrName = document.getElementById('export-cmdr-name');
  const exportNotes = document.getElementById('export-notes');

  function openExportLockedModal() {
    if (!state.selectedSystem) return;
    if (exportTargetSysName) exportTargetSysName.innerText = state.selectedSystem.star_system || '--';
    if (cbExportConsent) cbExportConsent.checked = false;
    if (btnSubmitExportPkg) {
      btnSubmitExportPkg.disabled = true;
      btnSubmitExportPkg.style.opacity = '0.5';
      btnSubmitExportPkg.style.cursor = 'not-allowed';
    }
    if (modalExportLocked) modalExportLocked.style.display = 'flex';
  }

  function closeExportLockedModal() {
    if (modalExportLocked) modalExportLocked.style.display = 'none';
  }

  if (btnExportPkg) {
    btnExportPkg.addEventListener('click', openExportLockedModal);
  }
  if (btnCloseExportModal) {
    btnCloseExportModal.addEventListener('click', closeExportLockedModal);
  }
  if (btnCancelExport) {
    btnCancelExport.addEventListener('click', closeExportLockedModal);
  }

  if (cbExportConsent && btnSubmitExportPkg) {
    cbExportConsent.addEventListener('change', () => {
      btnSubmitExportPkg.disabled = !cbExportConsent.checked;
      btnSubmitExportPkg.style.opacity = cbExportConsent.checked ? '1' : '0.5';
      btnSubmitExportPkg.style.cursor = cbExportConsent.checked ? 'pointer' : 'not-allowed';
    });
  }

  if (btnSubmitExportPkg) {
    btnSubmitExportPkg.addEventListener('click', async () => {
      if (!cbExportConsent.checked || !state.selectedSystem) return;
      const sysAddr = state.selectedSystem.system_address;
      const sysName = (state.selectedSystem.star_system || 'System').replace(/[^a-zA-Z0-9_-]/g, '_');
      
      const origHtml = btnSubmitExportPkg.innerHTML;
      btnSubmitExportPkg.innerHTML = `<span>⏳ ${t('exporting') || '作成中...'}</span>`;
      btnSubmitExportPkg.disabled = true;

      try {
        const payload = {
          system_addresses: [sysAddr],
          created_by: exportCmdrName ? exportCmdrName.value.trim() : '',
          notes: exportNotes ? exportNotes.value.trim() : '',
          consent_token: true
        };

        const res = await fetch('/api/export/package', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `HTTP ${res.status}`);
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${sysName}.edsys`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        closeExportLockedModal();

        // Mark current system as shared in UI
        if (state.selectedSystem) {
          state.selectedSystem.is_shared = 1;
          if (state.currentSystemData && state.currentSystemData.system) {
            state.currentSystemData.system.is_shared = 1;
          }
          const listSys = state.systems.find(s => s.system_address === sysAddr);
          if (listSys) listSys.is_shared = 1;
          renderSystemHeader();
          renderSystemList();
        }
      } catch (err) {
        console.error('Failed to export package:', err);
        alert(err.message || 'パッケージ書き出しに失敗しました');
      } finally {
        btnSubmitExportPkg.innerHTML = origHtml;
        btnSubmitExportPkg.disabled = false;
      }
    });
  }

  // Toggle Shared Bookmark Button
  const btnToggleShared = document.getElementById('btn-toggle-shared');
  if (btnToggleShared) {
    btnToggleShared.addEventListener('click', async () => {
      if (!state.selectedSystem || !state.selectedSystem.system_address) return;
      const sysAddr = state.selectedSystem.system_address;
      try {
        const res = await fetch(`/api/systems/${sysAddr}/toggle-shared`, { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        state.selectedSystem.is_shared = data.is_shared;
        if (state.currentSystemData && state.currentSystemData.system) {
          state.currentSystemData.system.is_shared = data.is_shared;
        }
        const listSys = state.systems.find(s => s.system_address === sysAddr);
        if (listSys) listSys.is_shared = data.is_shared;
        renderSystemHeader();
        renderSystemList();
      } catch (err) {
        console.error('Failed to toggle shared status:', err);
      }
    });
  }

  // Import Package Modal (.edsys)
  const modalImportPkg = document.getElementById('modal-import-pkg');
  const btnImportOpen = document.getElementById('btn-import-open');
  const btnCloseImportModal = document.getElementById('btn-close-import-modal');
  const btnCancelImport = document.getElementById('btn-cancel-import');
  const importDropZone = document.getElementById('import-drop-zone');
  const importFileInput = document.getElementById('import-file-input');
  const importPreviewSection = document.getElementById('import-preview-section');
  const importSigBadge = document.getElementById('import-signature-badge');
  const importCmdrName = document.getElementById('import-cmdr-name');
  const importExportDate = document.getElementById('import-export-date');
  const importSysCount = document.getElementById('import-sys-count');
  const importBodyCount = document.getElementById('import-body-count');
  const importNotesText = document.getElementById('import-notes-text');
  const importSystemsList = document.getElementById('import-systems-list');
  const cbImportConsent = document.getElementById('cb-import-consent');
  const btnExecuteImport = document.getElementById('btn-execute-import-pkg');

  let pendingImportPackage = null;

  function resetImportModal() {
    pendingImportPackage = null;
    if (importFileInput) importFileInput.value = '';
    if (importPreviewSection) importPreviewSection.style.display = 'none';
    if (cbImportConsent) cbImportConsent.checked = false;
    if (btnExecuteImport) {
      btnExecuteImport.disabled = true;
      btnExecuteImport.style.opacity = '0.5';
      btnExecuteImport.style.cursor = 'not-allowed';
    }
  }

  function openImportModal() {
    resetImportModal();
    if (modalImportPkg) modalImportPkg.style.display = 'flex';
  }

  function closeImportModal() {
    if (modalImportPkg) modalImportPkg.style.display = 'none';
    resetImportModal();
  }

  if (btnImportOpen) {
    btnImportOpen.addEventListener('click', openImportModal);
  }
  if (btnCloseImportModal) {
    btnCloseImportModal.addEventListener('click', closeImportModal);
  }
  if (btnCancelImport) {
    btnCancelImport.addEventListener('click', closeImportModal);
  }

  if (importDropZone && importFileInput) {
    importDropZone.addEventListener('click', () => importFileInput.click());
    
    importDropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      importDropZone.style.borderColor = 'var(--ed-cyan)';
      importDropZone.style.background = 'rgba(0, 210, 255, 0.1)';
    });

    importDropZone.addEventListener('dragleave', () => {
      importDropZone.style.borderColor = 'rgba(167, 139, 250, 0.4)';
      importDropZone.style.background = 'rgba(167, 139, 250, 0.05)';
    });

    importDropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      importDropZone.style.borderColor = 'rgba(167, 139, 250, 0.4)';
      importDropZone.style.background = 'rgba(167, 139, 250, 0.05)';
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleImportFile(e.dataTransfer.files[0]);
      }
    });

    importFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleImportFile(e.target.files[0]);
      }
    });
  }

  async function handleImportFile(file) {
    try {
      const text = await file.text();
      let pkg;
      try {
        pkg = JSON.parse(text);
      } catch (pe) {
        throw new Error(t('import_invalid_format') || 'ファイルの形式が不正です (.edsys または JSON を指定してください)');
      }

      // Call preview API
      const res = await fetch('/api/import/package/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package_data: pkg })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      const preview = await res.json();
      pendingImportPackage = pkg;

      // Populate preview UI
      if (importCmdrName) importCmdrName.innerText = preview.created_by || '--';
      if (importExportDate) importExportDate.innerText = preview.export_date ? preview.export_date.substring(0, 19).replace('T', ' ') : '--';
      if (importSysCount) importSysCount.innerText = preview.system_count;
      if (importBodyCount) importBodyCount.innerText = preview.total_bodies;
      if (importNotesText) importNotesText.innerText = preview.notes || '(なし)';

      if (importSigBadge) {
        if (preview.signature_valid) {
          importSigBadge.style.background = 'rgba(16, 185, 129, 0.15)';
          importSigBadge.style.color = '#6ee7b7';
          importSigBadge.style.border = '1px solid rgba(16, 185, 129, 0.4)';
          importSigBadge.innerHTML = `<span>✓</span> <span>${t('import_sig_ok')}</span>`;
        } else {
          importSigBadge.style.background = 'rgba(239, 68, 68, 0.15)';
          importSigBadge.style.color = '#f87171';
          importSigBadge.style.border = '1px solid rgba(239, 68, 68, 0.4)';
          importSigBadge.innerHTML = `<span>⚠️</span> <span>${t('import_sig_warn')}</span>`;
        }
      }

      if (importSystemsList) {
        importSystemsList.innerHTML = preview.systems.map(s => `
          <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <span style="font-weight: bold; color: var(--ed-orange);">${s.star_system || 'System ' + s.system_address}</span>
            <span style="color: var(--text-secondary);">${s.body_count || 0} 天体</span>
          </div>
        `).join('');
      }

      if (importPreviewSection) importPreviewSection.style.display = 'block';
    } catch (err) {
      console.error('Import preview failed:', err);
      alert(err.message || 'パッケージの読み込みに失敗しました');
    }
  }

  if (cbImportConsent && btnExecuteImport) {
    cbImportConsent.addEventListener('change', () => {
      const ready = cbImportConsent.checked && pendingImportPackage !== null;
      btnExecuteImport.disabled = !ready;
      btnExecuteImport.style.opacity = ready ? '1' : '0.5';
      btnExecuteImport.style.cursor = ready ? 'pointer' : 'not-allowed';
    });
  }

  if (btnExecuteImport) {
    btnExecuteImport.addEventListener('click', async () => {
      if (!cbImportConsent.checked || !pendingImportPackage) return;

      const origHtml = btnExecuteImport.innerHTML;
      btnExecuteImport.innerHTML = `<span>⏳ ${t('importing') || '取り込み中...'}</span>`;
      btnExecuteImport.disabled = true;

      try {
        const res = await fetch('/api/import/package/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            package_data: pendingImportPackage,
            consent_token: true
          })
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `HTTP ${res.status}`);
        }

        const resData = await res.json();
        closeImportModal();
        alert(`${resData.imported_systems} ${t('import_success')} (${resData.imported_bodies} 天体)`);

        // Refresh system list and select the first imported system
        await fetchSystems();
        if (pendingImportPackage.systems && pendingImportPackage.systems.length > 0) {
          const firstAddr = pendingImportPackage.systems[0].system_address;
          if (firstAddr) {
            selectSystem(firstAddr);
          }
        }
      } catch (err) {
        console.error('Import execution failed:', err);
        alert(err.message || 'パッケージの取り込みに失敗しました');
      } finally {
        btnExecuteImport.innerHTML = origHtml;
        btnExecuteImport.disabled = false;
      }
    });
  }
}

