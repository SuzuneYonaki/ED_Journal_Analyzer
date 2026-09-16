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
  starTypes: [],
  starMatchMode: 'any',
  luminosityClasses: [],
  luminosityMatchMode: 'any',
  celestialFilters: [],
  celestialMatchMode: 'all',
  externalFootprintCheck: localStorage.getItem('ed_external_footprint_check') === 'true',
  uiLayoutMode: localStorage.getItem('ed_ui_layout') || '1col',
  headerStatsCollapsed: localStorage.getItem('ed_header_stats_collapsed') === 'true',
  collapsedGroups: JSON.parse(localStorage.getItem('ed_collapsed_groups') || '{}'),
  showMiningGravity: localStorage.getItem('mining_display_gravity') !== 'false',
  showMiningTemp: localStorage.getItem('mining_display_temp') !== 'false',
  miningSubFilter: 'all',
  miningScout: '',
  hasLargePad: false,
  maxArrivalDistLs: null,
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
};

if (typeof window !== 'undefined') {
  window.state = state;
}

// Core utilities, domain parsers, and module settings are loaded from utils.js

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

  document.querySelectorAll('[data-i18n-html]').forEach(el => {
    const key = el.dataset.i18nHtml;
    if (key) {
      el.innerHTML = t(key);
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

  // Update layout toggle text
  const layoutToggleText = document.getElementById('layout-toggle-text');
  if (layoutToggleText) {
    layoutToggleText.innerText = state.uiLayoutMode === '2col' ? (t('btn_layout_1col') || '1列表示') : (t('btn_layout_2col') || '2列表示');
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

  if (state.starTypes && state.starTypes.length > 0) {
    params.append('star_types', state.starTypes.join(','));
    params.append('star_match_mode', state.starMatchMode || 'any');
  }

  if (state.luminosityClasses && state.luminosityClasses.length > 0) {
    params.append('luminosity_classes', state.luminosityClasses.join(','));
    params.append('luminosity_match_mode', state.luminosityMatchMode || 'any');
  }

  if (state.celestialFilters && state.celestialFilters.length > 0) {
    params.append('celestial_filters', state.celestialFilters.join(','));
    params.append('celestial_match_mode', state.celestialMatchMode || 'all');
  }

  Object.entries(state.filters).forEach(([k, v]) => {
    if (v) params.append(k, 'true');
  });

  if (state.miningScout) {
    params.append('mining_scout', state.miningScout);
  }
  if (state.hasLargePad) {
    params.append('has_large_pad', 'true');
  }
  if (state.maxArrivalDistLs !== null && state.maxArrivalDistLs !== undefined && state.maxArrivalDistLs !== '') {
    params.append('max_arrival_dist_ls', state.maxArrivalDistLs);
  }

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

// Module Display Settings (Exobiology & Rhino Mining) are defined in utils.js

function updateModuleVisibilityUI() {
  const modSettings = getModuleSettings();
  
  // View switcher buttons in Central Pane
  const btnViewBio = document.getElementById('btn-view-bio');
  const btnViewMining = document.getElementById('btn-view-mining');
  if (btnViewBio) btnViewBio.style.display = modSettings.exobiology ? 'inline-block' : 'none';
  if (btnViewMining) btnViewMining.style.display = modSettings.rhino ? 'inline-block' : 'none';

  // If currently selected view became hidden, fallback to sysmap
  if (state.currentView === 'bio' && !modSettings.exobiology) {
    state.currentView = 'sysmap';
    if (typeof updateViewButtons === 'function') updateViewButtons();
  }
  if (state.currentView === 'mining' && !modSettings.rhino) {
    state.currentView = 'sysmap';
    if (typeof updateViewButtons === 'function') updateViewButtons();
  }
}

// System navigation and rendering functions are defined in system_list.js

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
    } else if (by === 'pml' || by === 'mining') {
      valA = a.mining_signals || (a.rhino_mining_sites ? a.rhino_mining_sites.length : 0) || 0;
      valB = b.mining_signals || (b.rhino_mining_sites ? b.rhino_mining_sites.length : 0) || 0;
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

    if (valA !== valB) {
      if (order === 'asc') return valA - valB;
      return valB - valA;
    }
    // Tie-break by arrival distance (nearest first)
    const distA = a.distance_from_arrival_ls !== null && a.distance_from_arrival_ls !== undefined ? a.distance_from_arrival_ls : 999999999;
    const distB = b.distance_from_arrival_ls !== null && b.distance_from_arrival_ls !== undefined ? b.distance_from_arrival_ls : 999999999;
    return distA - distB;
  });
  return list;
}

function renderBodyExobiologyBlock(node) {
  const modSettings = getModuleSettings();
  if (modSettings.exobiology === false) return '';
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

// renderBodyMiningBlock() is defined in mining_view.js


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

// clearBodyInspector() is defined in inspector.js


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

  // 1. Arrived Waiting FSS (Honk) State Placeholder
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
  } else if (state.currentView === 'physics') {
    renderPhysicsReport(container, state.currentSystemData);
  }

  // Auto focus & scroll to target body
  const targetId = state.selectedBody ? state.selectedBody.body_id : state.targetBodyId;
  if (targetId !== null && targetId !== undefined && state.currentView !== 'physics') {
    focusAndScrollToTargetBody(targetId);
  }
}

// escapeHtml is defined in utils.js

async function renderPhysicsReport(container, systemData) {
  if (!systemData || !systemData.system) {
    container.innerHTML = `<div style="color: var(--text-secondary); text-align: center; padding: 40px;">${t('select_system_desc')}</div>`;
    return;
  }

  const sys = systemData.system;
  const sysAddr = sys.system_address;
  let evalData = systemData.physics_evaluation;

  // If not yet evaluated, fetch on-demand
  if (!evalData) {
    container.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 350px; color: var(--ed-cyan);">
        <div class="loading-spinner" style="width: 38px; height: 38px; border: 3px solid rgba(0, 210, 255, 0.2); border-top-color: var(--ed-cyan); border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px;"></div>
        <div style="font-size: 1.05rem; font-weight: bold;">🌌 ${t('scanning_banner') || 'ED_Analysys 天体物理解析を実行中...'}</div>
        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 6px;">2014年天文学モデル・Kopparapu HZ・Gladman Hill・古在共鳴を計算中...</div>
      </div>
    `;

    try {
      const res = await fetch(`/api/systems/${sysAddr}/physics`);
      if (res.ok) {
        const json = await res.json();
        evalData = json;
        systemData.physics_evaluation = json;
        if (json.rarity_score !== undefined && json.rarity_score !== null) {
          systemData.system.rarity_score = json.rarity_score;
          if (state.selectedSystem && state.selectedSystem.system_address === sysAddr) {
            state.selectedSystem.rarity_score = json.rarity_score;
          }
          renderSystemHeader();
        }
      } else {
        container.innerHTML = `
          <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
            <div style="font-size: 1.5rem; margin-bottom: 10px;">⚠️</div>
            <div>${t('physics_no_data')}</div>
            <button id="btn-retry-eval" class="btn-primary" style="margin-top: 14px; padding: 6px 14px; font-size: 0.8rem;">
              ${t('btn_eval_physics')}
            </button>
          </div>
        `;
        const retryBtn = document.getElementById('btn-retry-eval');
        if (retryBtn) retryBtn.onclick = () => renderPhysicsReport(container, systemData);
        return;
      }
    } catch (err) {
      console.error('Physics eval fetch failed:', err);
      container.innerHTML = `<div style="color: var(--ed-red); text-align: center; padding: 40px;">天体物理データの取得に失敗しました: ${err.message}</div>`;
      return;
    }
  }

  // Determine display language
  const isJa = currentLang === 'ja';
  const rScore = Math.round((evalData.rarity_score || 0) * 10) / 10;
  let rClass = 'rarity-score-normal';
  let rLabel = t('physics_normal');
  let rGlowColor = '#94a3b8';
  if (rScore >= 95) {
    rClass = 'rarity-score-legendary';
    rLabel = t('physics_legendary');
    rGlowColor = '#fbbf24';
  } else if (rScore >= 80) {
    rClass = 'rarity-score-epic';
    rLabel = t('physics_epic');
    rGlowColor = '#c084fc';
  } else if (rScore >= 60) {
    rClass = 'rarity-score-rare';
    rLabel = t('physics_rare');
    rGlowColor = '#38bdf8';
  }

  const anomalies = (isJa ? evalData.anomalies_ja : evalData.anomalies_en) || [];
  const narrativeReport = (isJa ? evalData.narrative_report_ja : evalData.narrative_report_en) || '';
  const rawFeats = evalData.raw_features || {};

  // Build Anomalies Pills with body highlighting and collapsible fold
  let anomaliesHtml = '';
  if (anomalies.length > 0) {
    const formatAnomalyPill = (a) => {
      let icon = '⚡';
      if (a.includes('HZ') || a.includes('ハビタブル') || a.includes('Habitable')) icon = '🌱';
      else if (a.includes('Greenhouse') || a.includes('暴走温室') || a.includes('金星')) icon = '🌋';
      else if (a.includes('Mega-Earth') || a.includes('超巨大岩石')) icon = '🪐';
      else if (a.includes('Hill') || a.includes('共鳴') || a.includes('古在') || a.includes('ヒル')) icon = '🌀';
      else if (a.includes('Tidal') || a.includes('潮汐') || a.includes('ロシュ限界') || a.includes('Roche')) icon = '🌊';
      else if (a.includes('Binary') || a.includes('連星')) icon = '✨';
      else if (a.includes('Ring') || a.includes('環')) icon = '🪐';
      else if (a.includes('Remnant') || a.includes('Black Hole') || a.includes('Neutron') || a.includes('ブラックホール') || a.includes('中性子星')) icon = '💫';

      let escaped = escapeHtml(a);
      // Highlight body names (e.g. "天体 X:" or "X confirmed" or "Category: X & Y")
      escaped = escaped
        .replace(/^(天体\s+[^:：\s]+)/, '<strong style="color: #fff; text-shadow: 0 0 6px rgba(255,255,255,0.4);">$1</strong>')
        .replace(/^(.*?[:：]\s*)([A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*(?:\s*&\s*[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*)?)/, (m, p1, p2) => {
          return `${p1}<strong style="color: #fff; text-shadow: 0 0 6px rgba(255,255,255,0.4);">${p2}</strong>`;
        });

      return `<span class="anomaly-pill">${icon} ${escaped}</span>`;
    };

    const initialCount = 5;
    const initialPills = anomalies.slice(0, initialCount).map(formatAnomalyPill).join('');
    const remainingPills = anomalies.slice(initialCount).map(formatAnomalyPill).join('');
    const hasMore = anomalies.length > initialCount;

    anomaliesHtml = `
      <div class="physics-narrative-card" style="border-left: 4px solid #ef4444;">
        <div style="font-size: 0.88rem; font-weight: bold; color: #f87171; display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            <span>★</span> <span>${t('physics_anomalies_title')} (${anomalies.length})</span>
          </div>
        </div>
        <div class="physics-anomalies-list">${initialPills}</div>
        ${hasMore ? `
          <div id="physics-anomalies-collapsed" class="physics-anomalies-collapsible hidden">
            ${remainingPills}
          </div>
          <button id="btn-toggle-anomalies" class="anomaly-collapse-btn">
            <span>${(t('physics_show_more_anomalies') || '他 {count} 件の特異点を表示 ▼').replace('{count}', anomalies.length - initialCount)}</span>
          </button>
        ` : ''}
      </div>
    `;
  }

  // Format Narrative Text (convert brackets, hyphens, markdown asterisks to colored elements)
  let formattedNarrative = escapeHtml(narrativeReport)
    .replace(/\[(\d+)\]/g, '<span class="report-idx-badge">[$1]</span>')
    .replace(/\{([^}]+)\}/g, '<span class="report-bracket-param">{$1}</span>')
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #38bdf8;">$1</strong>')
    .replace(/^([ \t]*)[-–—]\s+(.*)$/gm, '$1<span class="report-bullet-dash">◆</span> $2')
    .replace(/^#+\s*(.*)$/gm, '<h3 style="font-size: 1.05rem; color: #fed7aa; margin: 14px 0 6px 0; border-bottom: 1px solid rgba(255,113,0,0.2); padding-bottom: 4px;">$1</h3>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');

  // Build 2014 Models Cards
  const m2014 = rawFeats.astrophysics_2014_models || {};

  // 1. Habitable Zone (Kopparapu et al. 2013, 2014)
  const hzList = m2014.habitable_zone_kopparapu || [];
  const hzConservative = hzList.filter(h => h.in_conservative_hz);
  const hzOptimistic = hzList.filter(h => h.in_optimistic_hz && !h.in_conservative_hz);
  const hzTotalCount = hzConservative.length + hzOptimistic.length;

  let hzDetailHtml = '';
  if (hzTotalCount > 0) {
    const conservativeNames = hzConservative.map(h => `<strong style="color:#4ade80;">${escapeHtml(h.planet)}</strong> (S_eff=${h.received_flux_seff.toFixed(2)})`).join(', ');
    const optimisticNames = hzOptimistic.map(h => `<strong style="color:#fed7aa;">${escapeHtml(h.planet)}</strong> (S_eff=${h.received_flux_seff.toFixed(2)})`).join(', ');
    hzDetailHtml = `
      <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 4px; line-height: 1.4;">
        ${conservativeNames ? `<div>${isJa ? '保守的HZ' : 'Conservative'}: ${conservativeNames}</div>` : ''}
        ${optimisticNames ? `<div>${isJa ? '楽観的HZ' : 'Optimistic'}: ${optimisticNames}</div>` : ''}
      </div>
    `;
  } else {
    hzDetailHtml = `
      <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px;">
        ${isJa ? '放射平衡流束 (S_eff) 基準内の天体なし' : 'No terrestrial bodies within S_eff boundaries'}
      </div>
    `;
  }

  // 2. Mutual Hill Stability (Gladman 1993)
  const gladmanList = m2014.mutual_hill_stability_gladman || [];
  const unstablePairs = gladmanList.filter(h => h.is_gladman_unstable);
  let hillStatusText = '';
  let hillStatusColor = '#94a3b8';
  let hillDetailHtml = '';

  if (gladmanList.length === 0) {
    hillStatusText = isJa ? '単独・非摂動 (N/A)' : 'Single / Non-perturbed';
    hillDetailHtml = `<div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px;">${isJa ? '同一主星を周回する隣接ペアなし' : 'No adjacent planetary pairs sharing primary'}</div>`;
  } else if (unstablePairs.length > 0) {
    hillStatusText = isJa ? `⚠️ ${unstablePairs.length}組で不安定検出` : `⚠️ ${unstablePairs.length} Unstable Pairs`;
    hillStatusColor = '#ef4444';
    const pairDescriptions = unstablePairs.map(p => `&bull; ${escapeHtml(p.body1)} & ${escapeHtml(p.body2)} (Δ_H = ${p.delta_hill.toFixed(2)} &lt; 2√3)`).join('<br>');
    hillDetailHtml = `<div style="font-size: 0.78rem; color: #fca5a5; margin-top: 4px; line-height: 1.4;">${pairDescriptions}</div>`;
  } else {
    const minDeltaH = Math.min(...gladmanList.map(p => p.delta_hill));
    hillStatusText = isJa ? `✓ 長期安定 (${gladmanList.length}組評価)` : `✓ Stable (${gladmanList.length} pairs evaluated)`;
    hillStatusColor = 'var(--ed-cyan)';
    hillDetailHtml = `<div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">${isJa ? 'Gladman基準(Δ_H &gt; 3.46)適合' : 'Satisfies Gladman limit (Δ_H &gt; 3.46)'} (min Δ_H = ${minDeltaH.toFixed(2)})</div>`;
  }

  // 3. Kozai-Lidov Secular Resonance (Fabrycky & Tremaine 2007)
  const kozaiList = m2014.kozai_lidov_regime || [];
  let kozaiStatusText = '';
  let kozaiStatusColor = '#94a3b8';
  let kozaiDetailHtml = '';

  if (evalData.star_count < 2) {
    kozaiStatusText = isJa ? '非対象 (単一恒星系)' : 'Inactive (Single Star)';
    kozaiDetailHtml = `<div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px;">${isJa ? '外側摂動星が存在しないため共鳴なし' : 'No companion star perturber'}</div>`;
  } else if (kozaiList.length > 0) {
    kozaiStatusText = isJa ? `🌀 ${kozaiList.length}天体で共鳴励起` : `🌀 ${kozaiList.length} in Kozai Regime`;
    kozaiStatusColor = '#fbbf24';
    const kozaiDescriptions = kozaiList.map(k => `&bull; ${escapeHtml(k.body)}: i=${k.inclination_deg.toFixed(1)}°, e_max=${k.max_theoretical_eccentricity.toFixed(2)} (伴星: ${escapeHtml(k.companion_perturber)})`).join('<br>');
    kozaiDetailHtml = `<div style="font-size: 0.78rem; color: #fde68a; margin-top: 4px; line-height: 1.4;">${kozaiDescriptions}</div>`;
  } else {
    kozaiStatusText = isJa ? '共鳴なし (傾斜角安定)' : 'No Kozai Regime (Stable)';
    kozaiStatusColor = '#94a3b8';
    kozaiDetailHtml = `<div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px;">${isJa ? '軌道傾斜角が共鳴臨界領域 (39.2°〜140.8°) 外' : 'Inclinations outside critical 39.2°-140.8°'}</div>`;
  }

  // 4. Planetary Composition & Transition (Weiss & Marcy 2014)
  const compList = m2014.composition_weiss_marcy || [];
  const megaEarths = compList.filter(c => c.is_mega_earth);
  const superMercuries = compList.filter(c => c.is_super_mercury);
  const puffyBodies = compList.filter(c => c.is_low_density_puffy);
  const compAnomaliesCount = megaEarths.length + superMercuries.length + puffyBodies.length;

  let compDetailHtml = '';
  if (compAnomaliesCount > 0) {
    const parts = [];
    if (megaEarths.length > 0) {
      parts.push(`<div>Mega-Earth: <strong style="color: #f59e0b;">${megaEarths.length}</strong> (${megaEarths.map(c => escapeHtml(c.body)).join(', ')})</div>`);
    }
    if (superMercuries.length > 0) {
      parts.push(`<div>Super-Mercury: <strong style="color: #ef4444;">${superMercuries.length}</strong> (${superMercuries.map(c => escapeHtml(c.body)).join(', ')})</div>`);
    }
    if (puffyBodies.length > 0) {
      parts.push(`<div>Puffy Terrestrial: <strong style="color: #c084fc;">${puffyBodies.length}</strong> (${puffyBodies.map(c => escapeHtml(c.body)).join(', ')})</div>`);
    }
    compDetailHtml = `<div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 4px; line-height: 1.4;">${parts.join('')}</div>`;
  } else {
    compDetailHtml = `
      <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px;">
        ${isJa ? '岩石/ガス遷移境界 (1.5-1.6 R_Earth) に特異な偏位なし' : 'All planets conform to standard density curves'}
      </div>
    `;
  }

  const modelsHtml = `
    <div class="physics-models-grid">
      <div class="physics-model-card">
        <div class="physics-model-title">
          <span>🌱</span> <span>${t('physics_hz_title')}</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          ${isJa ? '液体の水が存在可能な放射平衡ゾーン' : 'Liquid water radiation equilibrium boundary'}
        </div>
        <div style="font-size: 1.1rem; font-weight: bold; color: ${hzTotalCount > 0 ? 'var(--ed-green)' : '#94a3b8'}; margin-top: 4px;">
          ${hzTotalCount} ${isJa ? '個の天体がHZ内に存在' : 'bodies in HZ'}
        </div>
        ${hzDetailHtml}
      </div>

      <div class="physics-model-card">
        <div class="physics-model-title">
          <span>📐</span> <span>${t('physics_hill_title')}</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          ${isJa ? '多重惑星系の相互重力摂動と軌道長期安定性' : 'Mutual gravitational perturbation & Hill limits'}
        </div>
        <div style="font-size: 1.1rem; font-weight: bold; color: ${hillStatusColor}; margin-top: 4px;">
          ${hillStatusText}
        </div>
        ${hillDetailHtml}
      </div>

      <div class="physics-model-card">
        <div class="physics-model-title">
          <span>🌀</span> <span>${t('physics_kozai_title')}</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          ${isJa ? '高軌道傾斜角と離心率の交換振動メカニズム' : 'High orbital inclination & eccentricity oscillation'}
        </div>
        <div style="font-size: 1.1rem; font-weight: bold; color: ${kozaiStatusColor}; margin-top: 4px;">
          ${kozaiStatusText}
        </div>
        ${kozaiDetailHtml}
      </div>

      <div class="physics-model-card">
        <div class="physics-model-title">
          <span>🪐</span> <span>${t('physics_classification_title')}</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          ${isJa ? '地球質量・半径限界に基づく岩石/ガス境界判定' : 'Rock-to-gas transition mass-radius boundary'}
        </div>
        <div style="font-size: 1.1rem; font-weight: bold; color: ${compAnomaliesCount > 0 ? '#f59e0b' : 'var(--ed-cyan)'}; margin-top: 4px;">
          ${compAnomaliesCount > 0 ? `${compAnomaliesCount} ${isJa ? '個の特異遷移天体' : 'boundary transition bodies'}` : (isJa ? '標準組成' : 'Standard')}
        </div>
        ${compDetailHtml}
      </div>
    </div>
  `;

  container.innerHTML = `
    <div class="physics-report-container">
      <!-- Report Top Bar -->
      <div class="physics-report-header">
        <div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🌌</span>
            <span style="font-size: 1.3rem; font-weight: 800; color: #fff;">${sys.star_system}</span>
            <span class="tag-badge ${rClass}" style="font-size: 0.85rem; padding: 3px 10px;">★ ${rLabel}</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
            ${t('physics_report_title')} &bull; ${sys.scanned_bodies || (evalData.planet_count + evalData.star_count)} ${t('bodies_count')} (★ ${evalData.star_count} / 🪐 ${evalData.planet_count})
          </div>
        </div>

        <div class="physics-score-box">
          <div style="text-align: right;">
            <div style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px;">${t('rarity_score_label')}</div>
            <div style="font-size: 0.76rem; color: ${rGlowColor}; font-weight: bold;">Rarity Index</div>
          </div>
          <div class="physics-score-number" style="color: ${rGlowColor};">
            ${rScore.toFixed(1)}<span style="font-size: 1rem; color: var(--text-secondary); font-weight: normal;"> / 100</span>
          </div>
          <button id="btn-re-eval-physics" class="btn-icon" style="background: rgba(0, 210, 255, 0.12); border: 1px solid var(--ed-cyan); color: var(--ed-cyan); border-radius: 4px; padding: 4px 8px; cursor: pointer;" title="天体物理評価を再計算">
            🔄
          </button>
        </div>
      </div>

      <!-- Anomalies List if any -->
      ${anomaliesHtml}

      <!-- System Narrative / Analogies Box -->
      <div class="physics-narrative-card" style="border-left: 4px solid #00d2ff;">
        <div style="font-size: 0.95rem; font-weight: bold; color: var(--ed-cyan); display: flex; align-items: center; gap: 6px; margin-bottom: 12px; border-bottom: 1px solid rgba(0, 210, 255, 0.2); padding-bottom: 6px;">
          <span>📖</span> <span>${t('physics_narrative_title')}</span>
        </div>
        <div class="physics-narrative-text">
          ${formattedNarrative || `<div style="color: var(--text-secondary);">${isJa ? '特異な記述はありません。' : 'No exceptional narrative notes for this system.'}</div>`}
        </div>
      </div>

      <!-- 2014 Models Analysis Grid -->
      <div style="margin-top: 6px;">
        <div style="font-size: 0.9rem; font-weight: bold; color: #fed7aa; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
          <span>🔬</span> <span>${t('physics_models_title')}</span>
        </div>
        ${modelsHtml}
      </div>
    </div>
  `;

  // Re-evaluation button click
  const reEvalBtn = document.getElementById('btn-re-eval-physics');
  if (reEvalBtn) {
    reEvalBtn.onclick = async () => {
      systemData.physics_evaluation = null;
      renderPhysicsReport(container, systemData);
    };
  }

  // Anomalies collapsible toggle button
  const toggleAnomaliesBtn = document.getElementById('btn-toggle-anomalies');
  if (toggleAnomaliesBtn) {
    toggleAnomaliesBtn.onclick = () => {
      const collapsedEl = document.getElementById('physics-anomalies-collapsed');
      if (!collapsedEl) return;
      const isHidden = collapsedEl.classList.contains('hidden');
      if (isHidden) {
        collapsedEl.classList.remove('hidden');
        toggleAnomaliesBtn.querySelector('span').textContent = t('physics_show_less_anomalies') || '特異点を折りたたむ ▲';
      } else {
        collapsedEl.classList.add('hidden');
        toggleAnomaliesBtn.querySelector('span').textContent = (t('physics_show_more_anomalies') || '他 {count} 件の特異点を表示 ▼').replace('{count}', anomalies.length - 5);
      }
    };
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
    const modSettings = getModuleSettings();
    if (modSettings.rhino !== false && node.mining_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);">⛏️ MINING: ${node.mining_signals}</span>`);
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
    const modSettings = getModuleSettings();
    if (modSettings.rhino !== false && body.mining_signals > 0) badges.push(`<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);">⛏️ MINING: ${body.mining_signals}</span>`);
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

// renderMiningView() is defined in mining_view.js

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

// renderBodyInspector() is defined in inspector.js


// Collapsible sections, stellar filters, layout and stats toggles are defined in system_list.js

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  updateStaticTexts();
  if (typeof syncLanguageFromServer === 'function') {
    syncLanguageFromServer();
  }
  initSettingsModal();
  initExportImportModals();
  initMiningSiteModal();
  initCollapsibleSections();
  initStellarFilters();
  initLayoutSwitcher();
  initHeaderStatsCollapse();
  fetchGlobalStats();
  fetchSystems();
  checkScanOnStartup();

  // Language Switchers (Header)
  document.getElementById('btn-lang-ja')?.addEventListener('click', () => setLanguage('ja'));
  document.getElementById('btn-lang-en')?.addEventListener('click', () => setLanguage('en'));

  // Language Switchers (Settings Modal)
  document.getElementById('btn-modal-lang-ja')?.addEventListener('click', () => setLanguage('ja'));
  document.getElementById('btn-modal-lang-en')?.addEventListener('click', () => setLanguage('en'));

  // Search input & External Footprint Check
  let searchTimeout = null;
  let footprintAbortController = null;

  async function triggerExternalFootprintCheck(sysName) {
    const resContainer = document.getElementById('external-footprint-result');
    if (!resContainer) return;

    const trimmed = (sysName || '').trim();
    if (!state.externalFootprintCheck || trimmed.length < 2) {
      resContainer.style.display = 'none';
      resContainer.innerHTML = '';
      return;
    }

    // Check if the system is already found in local DB (state.systems)
    const exactLocalMatch = state.systems.some(s => (s.star_system || '').toLowerCase() === trimmed.toLowerCase());
    if (exactLocalMatch) {
      resContainer.style.display = 'flex';
      resContainer.className = 'external-footprint-result local';
      resContainer.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span style="font-weight: bold;">${t('footprint_local_db')}</span>
          <span style="font-size: 0.65rem; opacity: 0.85;">${trimmed}</span>
        </div>
      `;
      return;
    }

    // Show checking animation
    resContainer.style.display = 'flex';
    resContainer.className = 'external-footprint-result checking';
    resContainer.innerHTML = `
      <div style="display: flex; align-items: center; gap: 6px;">
        <span class="spinner" style="width: 10px; height: 10px; border-width: 1.5px;"></span>
        <span>${t('footprint_checking')} (${trimmed})</span>
      </div>
    `;

    if (footprintAbortController) {
      footprintAbortController.abort();
    }
    footprintAbortController = new AbortController();

    try {
      const resp = await fetch(`/api/external_footprint?system_name=${encodeURIComponent(trimmed)}`, {
        signal: footprintAbortController.signal
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      // If user typed something else while waiting, ignore
      if ((state.searchQuery || '').trim().toLowerCase() !== trimmed.toLowerCase()) return;

      if (data.in_local_db) {
        resContainer.className = 'external-footprint-result local';
        resContainer.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-weight: bold;">${t('footprint_local_db')}</span>
            <span style="font-size: 0.65rem; opacity: 0.85;">${trimmed}</span>
          </div>
        `;
        return;
      }

      const services = data.services || {};
      const edsm = services.edsm || {};
      const spansh = services.spansh || {};
      const inara = services.inara || {};

      const edsmBadge = `
        <a href="${edsm.url || '#'}" target="_blank" rel="noopener" class="external-service-badge ${edsm.found ? 'hit' : 'miss'}" title="${edsm.found ? (edsm.details || 'EDSM登録済') : 'EDSM未登録'}">
          EDSM ${edsm.found ? '✓' : '✕'}
        </a>
      `;
      const spanshBadge = `
        <a href="${spansh.url || '#'}" target="_blank" rel="noopener" class="external-service-badge ${spansh.found ? 'hit' : 'miss'}" title="${spansh.found ? (spansh.details || 'Spansh登録済') : 'Spansh未登録'}">
          Spansh ${spansh.found ? '✓' : '✕'}
        </a>
      `;
      const inaraBadge = `
        <a href="${inara.url || '#'}" target="_blank" rel="noopener" class="external-service-badge ${inara.found ? 'hit' : 'miss'}" title="${inara.found ? 'Inara登録済' : 'Inara未登録'}">
          Inara ${inara.found ? '✓' : '✕'}
        </a>
      `;

      const loadBtnHtml = edsm.found ? `
        <div style="margin-top: 6px; padding-top: 6px; border-top: 1px dashed rgba(56, 189, 248, 0.3); display: flex; justify-content: flex-end;">
          <button id="btn-import-external-edsm" class="btn-primary" style="background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; color: #38bdf8; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;" title="未訪問星系ですが、EDSMの星系・天体データを取得してSystem Mapや天体リストで閲覧可能にします（Web共有/パッケージ書き出しは利用不可）">
            <span>🚀 EDSMから星系データをロード（未訪問参照）</span>
          </button>
        </div>
      ` : '';

      if (data.has_footprint) {
        resContainer.className = 'external-footprint-result found';
        resContainer.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: space-between; font-weight: bold;">
            <span>${t('footprint_found')}</span>
            <span style="font-size: 0.65rem; color: var(--text-dim);">${trimmed}</span>
          </div>
          <div class="external-footprint-services">
            ${edsmBadge}
            ${spanshBadge}
            ${inaraBadge}
          </div>
          ${loadBtnHtml}
        `;
      } else {
        resContainer.className = 'external-footprint-result uncharted';
        resContainer.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: space-between; font-weight: bold;">
            <span>${t('footprint_none')}</span>
            <span style="font-size: 0.65rem; color: var(--text-dim);">${trimmed}</span>
          </div>
          <div class="external-footprint-services">
            ${edsmBadge}
            ${spanshBadge}
            ${inaraBadge}
          </div>
          ${loadBtnHtml}
        `;
      }

      if (edsm.found) {
        const loadBtn = document.getElementById('btn-import-external-edsm');
        if (loadBtn) {
          loadBtn.onclick = async () => {
            loadBtn.disabled = true;
            loadBtn.innerHTML = '<span>⏳ EDSMよりデータ取得中...</span>';
            try {
              const resp = await fetch(`/api/external/import_edsm?system_name=${encodeURIComponent(trimmed)}`, { method: 'POST' });
              if (!resp.ok) {
                const errJson = await resp.json().catch(() => ({}));
                throw new Error(errJson.error || errJson.detail || `HTTP ${resp.status}`);
              }
              const resData = await resp.json();
              loadBtn.innerHTML = '<span>✓ ロード完了</span>';
              await fetchSystems();
              if (resData.system_address) {
                await selectSystem(resData.system_address);
              }
            } catch (e) {
              console.error('EDSM unvisited import error:', e);
              alert(`EDSM星系ロードエラー: ${e.message}`);
              loadBtn.disabled = false;
              loadBtn.innerHTML = '<span>🚀 EDSMから星系データをロード（未訪問参照）</span>';
            }
          };
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      resContainer.className = 'external-footprint-result';
      resContainer.innerHTML = `<span style="color: #f87171;">${t('footprint_error')}</span>`;
    }
  }

  // Checkbox toggle listener
  const cbFootprint = document.getElementById('cb-external-footprint');
  if (cbFootprint) {
    cbFootprint.checked = state.externalFootprintCheck;
    cbFootprint.addEventListener('change', () => {
      state.externalFootprintCheck = cbFootprint.checked;
      try {
        localStorage.setItem('ed_external_footprint_check', state.externalFootprintCheck);
      } catch (e) {}

      if (state.externalFootprintCheck) {
        triggerExternalFootprintCheck(state.searchQuery);
      } else {
        const resContainer = document.getElementById('external-footprint-result');
        if (resContainer) {
          resContainer.style.display = 'none';
          resContainer.innerHTML = '';
        }
      }
    });
  }

  const searchInput = document.getElementById('system-search');
  const btnSearchClear = document.getElementById('btn-search-clear');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const val = e.target.value;
      if (btnSearchClear) {
        btnSearchClear.style.display = (val && val.trim().length > 0) ? 'block' : 'none';
      }
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        state.searchQuery = val;
        state.page = 1;
        fetchSystems({ autoSelectTop: true });
        triggerExternalFootprintCheck(state.searchQuery);
      }, 300);
    });

    if (btnSearchClear) {
      btnSearchClear.addEventListener('click', () => {
        searchInput.value = '';
        btnSearchClear.style.display = 'none';
        state.searchQuery = '';
        state.page = 1;
        fetchSystems({ autoSelectTop: true });
        const resContainer = document.getElementById('external-footprint-result');
        if (resContainer) {
          resContainer.style.display = 'none';
          resContainer.innerHTML = '';
        }
        searchInput.focus();
      });
    }
  }

  // Filter chips (General & Mining)
  document.querySelectorAll('.chip[data-filter]').forEach(chip => {
    chip.addEventListener('click', () => {
      const filterKey = chip.dataset.filter;
      state.filters[filterKey] = !state.filters[filterKey];
      chip.classList.toggle('active', state.filters[filterKey]);
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  });

  // Celestial & Orbital Anomaly Filter chips
  document.querySelectorAll('.celestial-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const cKey = chip.dataset.celestial;
      if (!cKey) return;
      const idx = (state.celestialFilters || []).indexOf(cKey);
      if (idx >= 0) {
        state.celestialFilters.splice(idx, 1);
        chip.classList.remove('active');
      } else {
        if (!state.celestialFilters) state.celestialFilters = [];
        state.celestialFilters.push(cKey);
        chip.classList.add('active');
      }
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  });

  // Celestial Match Mode Radio (AND vs OR)
  document.querySelectorAll('input[name="celestial-match-mode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      state.celestialMatchMode = e.target.value;
      if (state.celestialFilters && state.celestialFilters.length > 0) {
        state.page = 1;
        fetchSystems({ autoSelectTop: true });
      }
    });
  });

  // Clear Filter Buttons (General, Celestial & Mining groups)
  const btnClearGeneral = document.getElementById('btn-clear-general-filters');
  if (btnClearGeneral) {
    btnClearGeneral.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('#group-general-filters .chip').forEach(chip => {
        chip.classList.remove('active');
        state.filters[chip.dataset.filter] = false;
      });
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  }

  const btnClearCelestial = document.getElementById('btn-clear-celestial-filters');
  if (btnClearCelestial) {
    btnClearCelestial.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.celestial-chip').forEach(chip => {
        chip.classList.remove('active');
      });
      state.celestialFilters = [];
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  }

  const btnClearMining = document.getElementById('btn-clear-mining-filters');
  if (btnClearMining) {
    btnClearMining.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('#group-mining-filters .chip').forEach(chip => {
        chip.classList.remove('active');
        if (chip.dataset.filter) {
          state.filters[chip.dataset.filter] = false;
        }
      });
      document.querySelectorAll('.scout-chip').forEach(c => {
        c.classList.toggle('active', c.dataset.scout === '');
      });
      state.miningScout = '';

      const chkPad = document.getElementById('chk-has-large-pad');
      if (chkPad) chkPad.checked = false;
      state.hasLargePad = false;

      const selDist = document.getElementById('sel-max-arrival-dist');
      if (selDist) selDist.value = '';
      state.maxArrivalDistLs = null;

      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  }

  // Mining Scout Filter Chips
  document.querySelectorAll('.scout-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const val = chip.dataset.scout || '';
      state.miningScout = val;
      document.querySelectorAll('.scout-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  });

  // Large Pad Filter Checkbox
  const chkLargePad = document.getElementById('chk-has-large-pad');
  if (chkLargePad) {
    chkLargePad.addEventListener('change', () => {
      state.hasLargePad = chkLargePad.checked;
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  }

  // Max Arrival Distance Select Dropdown
  const selArrivalDist = document.getElementById('sel-max-arrival-dist');
  if (selArrivalDist) {
    selArrivalDist.addEventListener('change', () => {
      state.maxArrivalDistLs = selArrivalDist.value ? Number(selArrivalDist.value) : null;
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  }

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
      // Previous page preserves current scroll offset/card level without jumping to top
      fetchSystems();
    }
  });

  document.getElementById('btn-next-page').addEventListener('click', () => {
    if (state.page < state.totalPages) {
      state.page++;
      // Next page shifts cursor and scrolls to the top of system cards
      fetchSystems().then(() => {
        scrollToTopOfSystemCards();
      });
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

  const btnViewPhysics = document.getElementById('btn-view-physics');
  if (btnViewPhysics) {
    btnViewPhysics.addEventListener('click', () => {
      state.currentView = 'physics';
      updateViewButtons();
      renderCurrentView();
    });
  }

  function updateViewButtons() {
    const btnSys = document.getElementById('btn-view-sysmap');
    const btnFlat = document.getElementById('btn-view-flat');
    const btnBio = document.getElementById('btn-view-bio');
    const btnMining = document.getElementById('btn-view-mining');
    const btnVis = document.getElementById('btn-view-visits');
    const btnPhys = document.getElementById('btn-view-physics');

    if (btnSys) btnSys.classList.toggle('active', state.currentView === 'sysmap');
    if (btnFlat) btnFlat.classList.toggle('active', state.currentView === 'flat');
    if (btnBio) btnBio.classList.toggle('active', state.currentView === 'bio');
    if (btnMining) btnMining.classList.toggle('active', state.currentView === 'mining');
    if (btnVis) btnVis.classList.toggle('active', state.currentView === 'visits');
    if (btnPhys) btnPhys.classList.toggle('active', state.currentView === 'physics');

    // Show completed bio filter container only on bio view
    const bioFilterContainer = document.getElementById('bio-filter-hide-completed-container');
    if (bioFilterContainer) {
      bioFilterContainer.style.display = state.currentView === 'bio' ? 'inline-flex' : 'none';
    }

    // Show body sort controls only for list-based views (flat, bio, mining)
    const bodySortWrapper = document.getElementById('body-sort-wrapper');
    if (bodySortWrapper) {
      const showSort = (state.currentView === 'flat' || state.currentView === 'bio' || state.currentView === 'mining');
      bodySortWrapper.style.display = showSort ? 'flex' : 'none';
    }
  }

  // Concept Mode Switcher Tabs (Header & Left Pane synchronization)
  function initConceptTabs() {
    const headerBtnExplorer = document.getElementById('btn-tab-explorer');
    const headerBtnPhysics = document.getElementById('btn-tab-physics');
    const paneBtnExplorer = document.getElementById('btn-pane-tab-explorer');
    const paneBtnPhysics = document.getElementById('btn-pane-tab-physics');

    function setConceptMode(mode) {
      state.conceptMode = mode;

      if (headerBtnExplorer) headerBtnExplorer.classList.toggle('active', mode === 'explorer');
      if (headerBtnPhysics) headerBtnPhysics.classList.toggle('active', mode === 'physics');
      if (paneBtnExplorer) paneBtnExplorer.classList.toggle('active', mode === 'explorer');
      if (paneBtnPhysics) paneBtnPhysics.classList.toggle('active', mode === 'physics');

      if (mode === 'physics') {
        // Switch view to physics
        if (state.selectedSystem) {
          state.currentView = 'physics';
          updateViewButtons();
          renderCurrentView();
        }
        // Set sort to astrophysical rarity desc and refresh
        const sortSelect = document.getElementById('sort-select');
        const sortPrimary = document.getElementById('sort-primary');
        if (sortPrimary) {
          sortPrimary.value = 'rarity-desc';
          state.sortPrimary = 'rarity-desc';
        }
        if (sortSelect) {
          sortSelect.value = 'rarity-desc';
          state.sort = 'rarity-desc';
        }
        fetchSystems(true);
      } else {
        // Return to journal exploration mode
        if (state.currentView === 'physics') {
          state.currentView = 'sysmap';
          updateViewButtons();
          renderCurrentView();
        }
      }
    }

    if (headerBtnExplorer) headerBtnExplorer.addEventListener('click', () => setConceptMode('explorer'));
    if (headerBtnPhysics) headerBtnPhysics.addEventListener('click', () => setConceptMode('physics'));
    if (paneBtnExplorer) paneBtnExplorer.addEventListener('click', () => setConceptMode('explorer'));
    if (paneBtnPhysics) paneBtnPhysics.addEventListener('click', () => setConceptMode('physics'));
  }

  initConceptTabs();

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

  // Live Sync Toggle Buttons (Header & Accordion)
  const btnLiveToggle = document.getElementById('btn-live-toggle');
  if (btnLiveToggle) {
    btnLiveToggle.addEventListener('click', toggleLiveSync);
  }

  const btnAccordionLiveToggle = document.getElementById('btn-accordion-live-toggle');
  if (btnAccordionLiveToggle) {
    btnAccordionLiveToggle.addEventListener('click', toggleLiveSync);
  }

  // Manual Rescan Button (Header)
  const btnRescan = document.getElementById('btn-rescan');
  if (btnRescan) {
    btnRescan.addEventListener('click', async () => {
      await triggerManualRescan();
    });
  }

  // Start Realtime Live Sync
  initLiveSync();
});

async function triggerManualRescan() {
  updateRescanButtonUI(true);
  try {
    await fetch('/api/scan_now', { method: 'POST' });
    pollScanProgress();
  } catch (err) {
    console.error('Failed to trigger scan:', err);
    updateRescanButtonUI(false);
  }
}

function updateRescanButtonUI(isScanning) {
  const btn = document.getElementById('btn-rescan');
  const icon = document.getElementById('rescan-icon');
  const text = document.getElementById('rescan-text');
  const modalBtn = document.getElementById('btn-modal-rescan');

  if (btn) {
    btn.disabled = isScanning;
    btn.style.opacity = isScanning ? '0.7' : '1';
    btn.style.cursor = isScanning ? 'wait' : 'pointer';
  }
  if (icon) {
    if (isScanning) {
      icon.style.display = 'inline-block';
      icon.style.animation = 'spin 1s linear infinite';
    } else {
      icon.style.animation = 'none';
    }
  }
  if (text) {
    text.innerText = isScanning ? (t('btn_scanning') || '解析中...') : (t('btn_rescan') || 'ログスキャン');
  }
  if (modalBtn) {
    modalBtn.disabled = isScanning;
  }
}

async function toggleLiveSync() {
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
}

function updateLiveSyncButtonUI() {
  const btn = document.getElementById('btn-live-toggle');
  const txt = document.getElementById('live-status-text');
  if (btn && txt) {
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

  // Synchronize accordion helper row
  const accRow = document.getElementById('accordion-live-sync-row');
  const accBtn = document.getElementById('btn-accordion-live-toggle');
  const accTxt = document.getElementById('accordion-live-status-text');
  const accDot = document.getElementById('accordion-live-dot');
  if (accRow && accBtn && accTxt) {
    if (state.liveSyncEnabled) {
      accRow.className = 'live-sync-accordion-row';
      accBtn.className = 'btn-live-accordion-toggle active';
      accBtn.innerText = t('sort_live_unlock_btn') || 'LIVE解除';
      accTxt.innerText = t('sort_live_hint') || '⚡ リアルタイム追従中（手動ソートするにはLIVEを解除してください）';
      if (accDot) {
        accDot.style.background = 'var(--ed-orange)';
        accDot.style.animation = 'pulse 2s infinite';
      }
    } else {
      accRow.className = 'live-sync-accordion-row paused';
      accBtn.className = 'btn-live-accordion-toggle';
      accBtn.innerText = t('sort_live_resume_btn') || 'LIVE再開';
      accTxt.innerText = '⏹️ LIVE停止中（手動ソート有効）';
      if (accDot) {
        accDot.style.background = '#888';
        accDot.style.animation = 'none';
      }
    }
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

// clearSystemBioSummary() is defined in system_list.js

function handleLiveJournalEvent(eventName, eventData) {
  if (!state.liveSyncEnabled) return;

  if (eventName === 'StartJump') {
    const jumpType = eventData.JumpType || 'Hyperspace';
    if (jumpType === 'Hyperspace') {
      state.targetJumpSystem = eventData.StarSystem || 'Unknown';
      // Hyperspace Jump中の画面は不要のため、直前の星系表示を維持
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
        updateRescanButtonUI(false);

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
      updateRescanButtonUI(false);
    }
  }, 250);
}

// =============================================================================
// Text-to-Speech (TTS) Voice Notification System
// Supports Web Speech API (Microsoft Natural / Multilingual) & VOICEVOX (Local)
// =============================================================================

const ttsState = {
  enabled: false,
  highBioEnabled: false,
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
  if (!ttsState.enabled || !ttsState.highBioEnabled) return;
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

  // Landmark Display Settings in UI Tab
  function initLandmarkSettingsUI() {
    const currentLmSettings = getLandmarkSettings();
    const cbs = document.querySelectorAll('.landmark-toggle-cb');
    cbs.forEach(cb => {
      const lmKey = cb.getAttribute('data-landmark');
      if (lmKey && currentLmSettings[lmKey] !== undefined) {
        cb.checked = Boolean(currentLmSettings[lmKey]);
      }
      cb.addEventListener('change', () => {
        const updated = getLandmarkSettings();
        updated[lmKey] = cb.checked;
        saveLandmarkSettings(updated);
        // Re-render system cards and details header immediately
        renderSystemList();
        if (state.selectedSystem) {
          updateCurrentSystemDistances(state.selectedSystem);
        }
      });
    });
  }

  // Module Display Settings in UI Tab
  function initModuleSettingsUI() {
    const currentModSettings = getModuleSettings();
    const cbs = document.querySelectorAll('.module-toggle-cb');
    cbs.forEach(cb => {
      const modKey = cb.getAttribute('data-module');
      if (modKey && currentModSettings[modKey] !== undefined) {
        cb.checked = Boolean(currentModSettings[modKey]);
      }
      cb.addEventListener('change', () => {
        const updated = getModuleSettings();
        updated[modKey] = cb.checked;
        saveModuleSettings(updated);
        updateModuleVisibilityUI();
        renderSystemList();
        renderCurrentView();
        if (state.selectedBody) {
          renderBodyInspector();
        }
      });
    });
  }

  initModuleSettingsUI();
  updateModuleVisibilityUI();
  initLandmarkSettingsUI();

  // UI Color Theme Settings in UI Tab
  function initThemeSettingsUI() {
    const themeBtns = document.querySelectorAll('.theme-card-btn');
    const validThemes = ['default', 'elite-amber', 'cyan-explorer'];

    function applyTheme(themeName) {
      if (!validThemes.includes(themeName)) {
        themeName = 'default';
      }
      if (themeName === 'default') {
        document.documentElement.removeAttribute('data-theme');
      } else {
        document.documentElement.setAttribute('data-theme', themeName);
      }
      try {
        localStorage.setItem('ed_theme', themeName);
      } catch (e) {
        console.warn('Could not save ed_theme to localStorage:', e);
      }
      themeBtns.forEach(btn => {
        if (btn.getAttribute('data-theme') === themeName) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }

    const savedTheme = localStorage.getItem('ed_theme') || 'default';
    applyTheme(savedTheme);

    themeBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const theme = btn.getAttribute('data-theme');
        if (theme) {
          applyTheme(theme);
        }
      });
    });
  }

  initThemeSettingsUI();

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
      await triggerManualRescan();
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
    if (highBioToggle) highBioToggle.checked = Boolean(ttsState.highBioEnabled);
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
  function showExportSuccessToast(title, filePath) {
    let toast = document.getElementById('app-export-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'app-export-toast';
      toast.style.position = 'fixed';
      toast.style.bottom = '24px';
      toast.style.right = '24px';
      toast.style.background = 'rgba(10, 16, 26, 0.96)';
      toast.style.border = '1px solid var(--ed-cyan)';
      toast.style.borderRadius = '8px';
      toast.style.padding = '14px 18px';
      toast.style.color = '#fff';
      toast.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.7)';
      toast.style.zIndex = '99999';
      toast.style.maxWidth = '460px';
      toast.style.fontSize = '0.85rem';
      toast.style.lineHeight = '1.5';
      document.body.appendChild(toast);
    }

    toast.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px; font-weight: bold; color: var(--ed-cyan); font-size: 0.95rem; margin-bottom: 6px;">
        <span>🌐</span> <span>${title}</span>
      </div>
      <div style="color: #cbd5e1; font-size: 0.78rem; word-break: break-all; margin-bottom: 8px; background: rgba(0,0,0,0.3); padding: 6px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.08);">
        <b>保存先:</b> <code style="color: #38bdf8;">${filePath || 'exports/ フォルダ'}</code>
      </div>
      <div style="color: #94a3b8; font-size: 0.72rem; margin-bottom: 10px;">
        🤖 <b>AI推論対応</b>: 全天体の天体物理・軌道観測JSONが内包されています。各種生成AIに本HTMLをそのまま読み込ませて星系形成史シナリオを推論できます。
      </div>
      <div style="display: flex; gap: 8px; justify-content: flex-end;">
        <button id="btn-toast-open-folder" class="btn-primary" style="padding: 4px 12px; font-size: 0.78rem; background: rgba(0, 210, 255, 0.2); border: 1px solid var(--ed-cyan); color: var(--ed-cyan); cursor: pointer;">
          📂 保存フォルダーを開く
        </button>
        <button id="btn-toast-close" class="view-btn" style="padding: 4px 10px; font-size: 0.78rem; cursor: pointer;">
          閉じる
        </button>
      </div>
    `;
    toast.style.display = 'block';

    document.getElementById('btn-toast-open-folder')?.addEventListener('click', async () => {
      try {
        await fetch('/api/export/open_location', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: filePath })
        });
      } catch (e) {}
    });

    document.getElementById('btn-toast-close')?.addEventListener('click', () => {
      toast.style.display = 'none';
    });

    setTimeout(() => {
      if (toast && toast.style.display !== 'none') {
        toast.style.display = 'none';
      }
    }, 12000);
  }

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
        
        const exportPath = res.headers.get('X-Export-Path') || '';
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${sysName}_share.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Show toast with location & trigger explorer reveal
        showExportSuccessToast('Web共有HTMLを出力しました', exportPath);
        if (exportPath) {
          try {
            await fetch('/api/export/open_location', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ path: exportPath })
            });
          } catch (e) {}
        }
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

      const cbExportOpenFolder = document.getElementById('cb-export-open-folder');
      const shouldReveal = cbExportOpenFolder ? cbExportOpenFolder.checked : true;

      try {
        const payload = {
          system_addresses: [sysAddr],
          cmdr_name: exportCmdrName ? exportCmdrName.value.trim() : '',
          notes: exportNotes ? exportNotes.value.trim() : '',
          consent_token: true,
          reveal: shouldReveal
        };

        const res = await fetch('/api/export/package/save-local', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.error || errData.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();
        const savedPath = data.saved_path;

        closeExportLockedModal();

        // Show Export Success Modal with path & reveal button
        const modalExportSuccess = document.getElementById('modal-export-success');
        const exportSavedPathDisplay = document.getElementById('export-saved-path-display');
        const btnRevealFolder = document.getElementById('btn-reveal-exported-folder');

        if (exportSavedPathDisplay) {
          exportSavedPathDisplay.innerText = savedPath || `${sysName}.edsys`;
        }
        if (btnRevealFolder) {
          btnRevealFolder.onclick = async () => {
            try {
              await fetch('/api/system/reveal-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: savedPath })
              });
            } catch (err) {
              console.error('Failed to reveal file:', err);
            }
          };
        }
        // Only show Export Success Modal if NOT auto-revealing in explorer
        if (!shouldReveal && modalExportSuccess) {
          modalExportSuccess.style.display = 'flex';
        }

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

  // Export Success Modal Close Buttons
  const modalExportSuccess = document.getElementById('modal-export-success');
  const btnCloseExportSuccess = document.getElementById('btn-close-export-success');
  const btnOkExportSuccess = document.getElementById('btn-ok-export-success');
  if (btnCloseExportSuccess) {
    btnCloseExportSuccess.addEventListener('click', () => {
      if (modalExportSuccess) modalExportSuccess.style.display = 'none';
    });
  }
  if (btnOkExportSuccess) {
    btnOkExportSuccess.addEventListener('click', () => {
      if (modalExportSuccess) modalExportSuccess.style.display = 'none';
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
        body: JSON.stringify(pkg)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || `HTTP ${res.status}`);
      }

      const preview = await res.json();
      pendingImportPackage = pkg;

      // Populate preview UI
      if (importCmdrName) importCmdrName.innerText = preview.cmdr_name || preview.created_by || '--';
      if (importExportDate) importExportDate.innerText = (preview.exported_at || preview.export_date || '').substring(0, 19).replace('T', ' ') || '--';
      if (importSysCount) importSysCount.innerText = preview.system_count != null ? preview.system_count : '--';
      if (importBodyCount) importBodyCount.innerText = preview.total_bodies != null ? preview.total_bodies : '--';
      if (importNotesText) importNotesText.innerText = preview.notes || '(なし)';

      if (importSigBadge) {
        if (preview.is_valid || preview.signature_valid) {
          importSigBadge.style.background = 'rgba(16, 185, 129, 0.15)';
          importSigBadge.style.color = '#6ee7b7';
          importSigBadge.style.border = '1px solid rgba(16, 185, 129, 0.4)';
          importSigBadge.innerHTML = `<span>✓</span> <span>${t('import_sig_ok') || '電子署名確認済み (改ざんなし)'}</span>`;
        } else {
          importSigBadge.style.background = 'rgba(239, 68, 68, 0.15)';
          importSigBadge.style.color = '#f87171';
          importSigBadge.style.border = '1px solid rgba(239, 68, 68, 0.4)';
          importSigBadge.innerHTML = `<span>⚠️</span> <span>${t('import_sig_warn') || '電子署名不一致 / 未検証 (外部データ)'}</span>`;
        }
      }

      if (importSystemsList) {
        importSystemsList.innerHTML = (preview.systems || []).map(s => `
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
            package: pendingImportPackage,
            consent_token: true
          })
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || errData.error || `HTTP ${res.status}`);
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

// Rhino Surface Mining Sites Modal & Management is defined in mining_view.js

// Window / Global Export
if (typeof window !== 'undefined') {
  window.selectSystem = selectSystem;
  window.fetchSystems = fetchSystems;
  window.fetchGlobalStats = fetchGlobalStats;
  window.renderCurrentView = renderCurrentView;
  window.getSortedBodies = getSortedBodies;
  window.renderHierarchyTree = renderHierarchyTree;
  window.renderFlatBodiesList = renderFlatBodiesList;
  window.renderBioOnlyView = renderBioOnlyView;
  window.renderVisitsTimeline = renderVisitsTimeline;
  window.renderPhysicsReport = renderPhysicsReport;
  window.handleLiveJournalEvent = handleLiveJournalEvent;
  window.updateModuleVisibilityUI = updateModuleVisibilityUI;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    state,
    selectSystem,
    fetchSystems,
    fetchGlobalStats,
    renderCurrentView,
    getSortedBodies,
    renderHierarchyTree,
    renderFlatBodiesList,
    renderBioOnlyView,
    renderVisitsTimeline,
    renderPhysicsReport,
    handleLiveJournalEvent,
    updateModuleVisibilityUI
  };
}


