/**
 * system_list.js - System Navigation, Filtering, Landmark Distances & Collapsible Groups
 * Elite Dangerous Journal Analyzer
 */

// Landmark Display Settings & Badge Generator
const defaultLandmarkSettings = {
  cmdr: true,
  sol: true,
  colonia: true,
  rainbow: true,
  eanch: true
};

function getLandmarkSettings() {
  try {
    const raw = localStorage.getItem('ed_landmark_settings');
    if (raw) {
      return { ...defaultLandmarkSettings, ...JSON.parse(raw) };
    }
  } catch (e) {
    console.warn('Failed to load landmark settings:', e);
  }
  return { ...defaultLandmarkSettings };
}

function saveLandmarkSettings(settings) {
  try {
    localStorage.setItem('ed_landmark_settings', JSON.stringify(settings));
  } catch (e) {
    console.warn('Failed to save landmark settings:', e);
  }
}

function generateLandmarkDistanceBadges(sys) {
  const lmSettings = getLandmarkSettings();
  const badges = [];

  // CMDR distance
  if (lmSettings.cmdr && sys.cmdr_distance_ly !== null && sys.cmdr_distance_ly !== undefined) {
    const cmdrSys = state.currentLocation && state.currentLocation.star_system ? ` (${state.currentLocation.star_system})` : '';
    const tip = (t('lm_cmdr_dist_tip') || '現在地{cmdrSys}からの距離: {dist} Ly')
      .replace('{cmdrSys}', cmdrSys)
      .replace('{dist}', Math.round(sys.cmdr_distance_ly).toLocaleString());
    badges.push(`<span class="tag-badge tag-cmdr-dist" title="${tip}">📍 CMDR: ${Math.round(sys.cmdr_distance_ly).toLocaleString()} Ly</span>`);
  }

  // Sol distance
  if (lmSettings.sol) {
    const solDist = (sys.sol_distance_ly !== undefined && sys.sol_distance_ly !== null && sys.sol_distance_ly > 0)
      ? sys.sol_distance_ly
      : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
        ? Math.hypot(sys.star_pos_x, sys.star_pos_y, sys.star_pos_z)
        : null);
    if (solDist !== null && solDist !== undefined) {
      const tip = (t('lm_sol_dist_tip') || '太陽系 (Sol) からの距離: {dist} Ly')
        .replace('{dist}', Math.round(solDist).toLocaleString());
      badges.push(`<span class="tag-badge tag-sol-dist" title="${tip}">Sol: ${Math.round(solDist).toLocaleString()} Ly</span>`);
    }
  }

  // Colonia distance
  if (lmSettings.colonia) {
    const coloniaDist = (sys.colonia_distance_ly !== undefined && sys.colonia_distance_ly !== null)
      ? sys.colonia_distance_ly
      : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
        ? Math.hypot(sys.star_pos_x - (-9530.5), sys.star_pos_y - (-910.28125), sys.star_pos_z - 19808.125)
        : null);
    if (coloniaDist !== null && coloniaDist !== undefined) {
      const tip = (t('lm_colonia_dist_tip') || '第2の人類居住圏 (Colonia) からの距離: {dist} Ly')
        .replace('{dist}', Math.round(coloniaDist).toLocaleString());
      badges.push(`<span class="tag-badge tag-colonia-dist" title="${tip}">Colonia: ${Math.round(coloniaDist).toLocaleString()} Ly</span>`);
    }
  }

  // Rainbow's End distance
  if (lmSettings.rainbow) {
    const rbDist = (sys.rainbows_end_distance_ly !== undefined && sys.rainbows_end_distance_ly !== null)
      ? sys.rainbows_end_distance_ly
      : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
        ? Math.hypot(sys.star_pos_x - 21481.40625, sys.star_pos_y - (-1004.5625), sys.star_pos_z - 43369.4375)
        : null);
    if (rbDist !== null && rbDist !== undefined) {
      const tip = (t('lm_rainbow_dist_tip') || "最遠方宇宙港 Rainbow's End (Roefoo ZE-H d10-0 / DW3) からの距離: {dist} Ly")
        .replace('{dist}', Math.round(rbDist).toLocaleString());
      badges.push(`<span class="tag-badge tag-rainbow-dist" title="${tip}">Rainbow's End: ${Math.round(rbDist).toLocaleString()} Ly</span>`);
    }
  }

  // Explorer's Anchorage distance
  if (lmSettings.eanch) {
    const eaDist = (sys.explorers_anchorage_distance_ly !== undefined && sys.explorers_anchorage_distance_ly !== null)
      ? sys.explorers_anchorage_distance_ly
      : ((sys.star_pos_x !== null && sys.star_pos_y !== null && sys.star_pos_z !== null)
        ? Math.hypot(sys.star_pos_x - 28.6875, sys.star_pos_y - (-19.78125), sys.star_pos_z - 25899.6875)
        : null);
    if (eaDist !== null && eaDist !== undefined) {
      const tip = (t('lm_eanch_dist_tip') || "銀河中心探査基地 Explorer's Anchorage (Stuemeae FG-Y d7561 / Sgr A*近傍) からの距離: {dist} Ly")
        .replace('{dist}', Math.round(eaDist).toLocaleString());
      badges.push(`<span class="tag-badge tag-eanch-dist" title="${tip}">E.Anchorage: ${Math.round(eaDist).toLocaleString()} Ly</span>`);
    }
  }

  return badges;
}

function updateCurrentSystemDistances(sys) {
  const distEl = document.getElementById('current-system-distances');
  if (distEl && sys) {
    const badges = generateLandmarkDistanceBadges(sys);
    distEl.innerHTML = badges.join('');
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
    
    const modSettings = getModuleSettings();
    if (modSettings.exobiology !== false) {
      if (sys.total_bio_signals > 0) tags.push(`<span class="tag-badge tag-bio">BIO: ${sys.total_bio_signals}</span>`);
      else if (sys.has_bio) tags.push('<span class="tag-badge tag-bio">BIO</span>');
    }
    
    // Configurable Key Galactic Distances (CMDR, Sol, Colonia, Rainbow's End, Explorer's Anchorage)
    const distanceBadges = generateLandmarkDistanceBadges(sys);

    // EDSM Discovery Status Badges & 1st Discover Registerable Announcement
    if (sys.edsm_checked === 1) {
      if (sys.edsm_registered === 1) {
        const discText = sys.edsm_first_discoverer ? `⭐ EDSM: ${sys.edsm_first_discoverer}` : (t('edsm_found_badge') || '⭐ EDSM登録済');
        const tip = (t('edsm_found_tip') || 'EDSM登録済 / 発見者: {discoverer}').replace('{discoverer}', sys.edsm_first_discoverer || (t('edsm_unknown_discoverer') || '不明'));
        tags.push(`<span class="tag-badge tag-edsm-found" title="${tip}">${discText}</span>`);
      } else {
        tags.push(`<span class="tag-badge tag-edsm-unreg" title="${t('edsm_unreg_full_tip') || 'EDSM未登録 / あなたの探査データを提出して1st Discoverを登録できます！'}">${t('edsm_unreg_full_badge') || '✨ 1st Discover 登録可能 (EDSM未登録)'}</span>`);
      }
    } else if (sys.has_first_discover || (sys.first_discovered_bodies && sys.first_discovered_bodies > 0)) {
      tags.push(`<span class="tag-badge tag-edsm-unreg" title="${t('edsm_first_disc_tip') || 'ゲーム内初発見 / EDSM 1st Discover 登録可能'}">${t('badge_first_discover') || '✨ 1st Discover 登録可能'}</span>`);
    }

    // EDSM System State (Boom, Investment)
    if (sys.system_state && sys.system_state.toLowerCase().includes('boom')) {
      tags.push(`<span class="tag-badge" style="background: rgba(34, 197, 94, 0.2); color: #22c55e; border: 1px solid #22c55e; font-weight: bold;" title="${t('edsm_boom_tip') || 'EDSM星系経済状態: Boom (好況)'}">📈 Boom</span>`);
    } else if (sys.system_state && sys.system_state.toLowerCase().includes('investment')) {
      tags.push(`<span class="tag-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; font-weight: bold;" title="${t('edsm_investment_tip') || 'EDSM星系状態: Investment (投資)'}">💼 Investment</span>`);
    }

    // Mining Scout Candidate Badges
    if (sys.mining_scout_grade === 'High') {
      tags.push('<span class="tag-badge badge-scout-high" title="Mining Scout High (Pristine + Metallic Rings)">⛏️ Scout: High</span>');
    } else if (sys.mining_scout_grade === 'Medium') {
      tags.push('<span class="tag-badge badge-scout-medium" title="Mining Scout Medium (Pristine + Icy Rings)">⛏️ Scout: Med</span>');
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
    if (sys.is_external || sys.visit_count === 0) {
      tags.push(`<span class="tag-badge tag-external" style="background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5); font-weight: bold;" title="${t('badge_external_unvisited_tip') || '未訪問・EDSM外部参照星系（Web共有/パッケージ書出は不可）'}">${t('badge_external_unvisited') || '🌐 外部参照 (未訪問)'}</span>`);
    }
    if (sys.composite_score !== null && sys.composite_score !== undefined) {
      const compTip = (t('composite_score_tip') || '総合ブレンドスコア: {score}pt').replace('{score}', sys.composite_score);
      const compLabel = (t('badge_score') || '★ スコア: {score}pt').replace('{score}', Math.round(sys.composite_score));
      tags.push(`<span class="tag-badge" style="background: rgba(0, 255, 136, 0.18); color: #00ff88; border: 1px solid rgba(0, 255, 136, 0.5); font-weight: bold;" title="${compTip}">${compLabel}</span>`);
    }
    if (sys.rarity_score !== null && sys.rarity_score !== undefined) {
      const rScore = Math.round(sys.rarity_score * 10) / 10;
      let rClass = 'rarity-score-normal';
      let rLabel = t('physics_normal');
      if (rScore >= 95) {
        rClass = 'rarity-score-legendary';
        rLabel = t('physics_legendary');
      } else if (rScore >= 80) {
        rClass = 'rarity-score-epic';
        rLabel = t('physics_epic');
      } else if (rScore >= 60) {
        rClass = 'rarity-score-rare';
        rLabel = t('physics_rare');
      }
      const rarityTip = (t('astro_rarity_tip') || 'ED_Analysys 天体物理レア度: {score} pt [{label}]')
        .replace('{score}', rScore)
        .replace('{label}', rLabel);
      tags.unshift(`<span class="tag-badge ${rClass}" title="${rarityTip}">🌌 ★ ${rScore} pt</span>`);
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

    // Quick Landable Bodies Visual Bar
    let landableHtml = '';
    if (modSettings.rhino !== false && typeof getMatchedLandableBodies === 'function') {
      const matchedBodies = getMatchedLandableBodies(sys);
      if (matchedBodies && matchedBodies.length > 0) {
        const landableBadges = matchedBodies.slice(0, 6).map(lb => {
          let icon = '🪐';
          let colorStyle = 'background: rgba(203, 213, 225, 0.12); color: #cbd5e1; border: 1px solid rgba(203, 213, 225, 0.35);';
          if (lb.type === 'HMC') {
            colorStyle = 'background: rgba(96, 165, 250, 0.15); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.4);';
          } else if (lb.type === 'MR') {
            colorStyle = 'background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.4);';
          } else if (lb.type === 'Icy') {
            icon = '❄️';
            colorStyle = 'background: rgba(103, 232, 249, 0.15); color: #67e8f9; border: 1px solid rgba(103, 232, 249, 0.4);';
          } else if (lb.type === 'RockyIce') {
            icon = '🧊';
            colorStyle = 'background: rgba(147, 197, 253, 0.15); color: #93c5fd; border: 1px solid rgba(147, 197, 253, 0.4);';
          }
          const isRing = Boolean(lb.has_rings);
          const statParts = [];
          if (state.showMiningGravity && lb.gravity_g !== null && lb.gravity_g !== undefined) {
            statParts.push(`${lb.gravity_g.toFixed(2)}G`);
          }
          if (state.showMiningTemp && lb.temp_k !== null && lb.temp_k !== undefined) {
            statParts.push(`${lb.temp_k}K`);
          }
          const statSuffix = statParts.length > 0 ? ` [${statParts.join(' | ')}]` : '';

          const ringStr = isRing ? (t('ringed_tag') || ' | 環付き (Ringed)') : '';
          const miningStr = lb.mining_signals > 0 ? (t('mining_sites_tip_tag') || ' | 採掘拠点: {count}箇所').replace('{count}', lb.mining_signals) : '';
          const tip = (t('landable_tip') || '{name} ({type}) - 重力: {gravity} | 温度: {temp}{ring}{mining}')
            .replace('{name}', lb.body_name)
            .replace('{type}', lb.type)
            .replace('{gravity}', lb.gravity_g ? lb.gravity_g.toFixed(2) + 'G' : '--')
            .replace('{temp}', lb.temp_k ? lb.temp_k + 'K' : '--')
            .replace('{ring}', ringStr)
            .replace('{mining}', miningStr);
          return `<span class="tag-badge" style="${colorStyle} font-size: 0.67rem; padding: 1px 4px; margin-right: 2px;" title="${tip}">${icon} ${lb.type}${statSuffix}</span>`;
        });
        if (matchedBodies.length > 6) {
          const countDiff = matchedBodies.length - 6;
          const moreTip = (t('other_matched_bodies_tip') || '他 {count} 件のマッチ天体').replace('{count}', countDiff);
          landableBadges.push(`<span class="tag-badge" style="background: rgba(255,255,255,0.06); color: var(--text-dim); font-size: 0.65rem; padding: 1px 4px;" title="${moreTip}">+${countDiff}</span>`);
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

function scrollToTopOfSystemCards() {
  const container = document.getElementById('system-list');
  if (!container) return;

  if (state.uiLayoutMode === '2col') {
    container.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    const firstCard = container.querySelector('.system-card');
    if (firstCard) {
      firstCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
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
        const discText = sys.edsm_first_discoverer ? `⭐ EDSM: ${sys.edsm_first_discoverer}` : (t('edsm_found_badge') || '⭐ EDSM登録済');
        const tip = (t('edsm_found_tip') || 'EDSM登録済 / 発見者: {discoverer}').replace('{discoverer}', sys.edsm_first_discoverer || (t('edsm_unknown_discoverer') || '不明'));
        edsmBadgeEl.innerHTML = `<span class="tag-badge tag-edsm-found" title="${tip}">${discText}</span>`;
      } else {
        edsmBadgeEl.innerHTML = `<span class="tag-badge tag-edsm-unreg" title="${t('edsm_unreg_full_tip') || 'EDSM未登録 / 探査データを提出して1st Discoverを登録できます！'}">${t('edsm_unreg_full_badge') || '✨ 1st Discover 登録可能 (EDSM未登録)'}</span>`;
      }
    } else if (sys.has_first_discover || (sys.first_discovered_bodies && sys.first_discovered_bodies > 0)) {
      edsmBadgeEl.innerHTML = `<span class="tag-badge tag-edsm-unreg" title="${t('edsm_first_disc_tip') || 'ゲーム内初発見 / EDSM 1st Discover 登録可能'}">${t('badge_first_discover') || '✨ 1st Discover 登録可能'}</span>`;
    } else {
      edsmBadgeEl.innerHTML = '';
    }
  }

  // EDSM Sync Button
  const btnSyncEdsm = document.getElementById('btn-sync-edsm');
  if (btnSyncEdsm) {
    btnSyncEdsm.style.display = 'inline-flex';
    btnSyncEdsm.onclick = async () => {
      btnSyncEdsm.disabled = true;
      btnSyncEdsm.innerHTML = `<span>${t('sync_edsm_running') || '⏳ 同期中...'}</span>`;
      try {
        const resp = await fetch(`/api/systems/${sys.system_address}/edsm_sync`, { method: 'POST' });
        const resData = await resp.json();
        btnSyncEdsm.innerHTML = `<span>${t('sync_done_label') || '✓ 完了'}</span>`;
        setTimeout(() => {
          btnSyncEdsm.disabled = false;
          btnSyncEdsm.innerHTML = `<span>${t('btn_sync_edsm_label') || '🔄 EDSM同期'}</span>`;
        }, 1500);
        await selectSystem(sys.system_address, true, false);
      } catch (err) {
        console.error('EDSM Sync error:', err);
        btnSyncEdsm.disabled = false;
        btnSyncEdsm.innerHTML = `<span>${t('sync_failed_label') || '❌ 失敗'}</span>`;
        setTimeout(() => {
          btnSyncEdsm.innerHTML = `<span>${t('btn_sync_edsm_label') || '🔄 EDSM同期'}</span>`;
        }, 2000);
      }
    };
  }

  // Spansh Sync Button
  const btnSyncSpansh = document.getElementById('btn-sync-spansh');
  if (btnSyncSpansh) {
    btnSyncSpansh.style.display = 'inline-flex';
    btnSyncSpansh.onclick = async () => {
      btnSyncSpansh.disabled = true;
      btnSyncSpansh.innerHTML = `<span>${t('sync_spansh_running') || '⏳ 照会中...'}</span>`;
      try {
        const resp = await fetch(`/api/systems/${sys.system_address}/spansh_sync`, { method: 'POST' });
        const resData = await resp.json();
        const hsFound = resData.hotspots_found || 0;
        const pmlFound = resData.pml_found || 0;
        const resultMsg = (t('sync_spansh_result') || '✓ 完了 ({hs} HS / {pml} PML)')
          .replace('{hs}', hsFound)
          .replace('{pml}', pmlFound);
        btnSyncSpansh.innerHTML = `<span>${resultMsg}</span>`;
        setTimeout(() => {
          btnSyncSpansh.disabled = false;
          btnSyncSpansh.innerHTML = `<span>${t('btn_sync_spansh_label') || '🪐 Spansh照会'}</span>`;
        }, 2000);
        await selectSystem(sys.system_address, true, false);
      } catch (err) {
        console.error('Spansh Sync error:', err);
        btnSyncSpansh.disabled = false;
        btnSyncSpansh.innerHTML = `<span>${t('sync_failed_label') || '❌ 失敗'}</span>`;
        setTimeout(() => {
          btnSyncSpansh.innerHTML = `<span>${t('btn_sync_spansh_label') || '🪐 Spansh照会'}</span>`;
        }, 2000);
      }
    };
  }

  // System State Badge & Economy Info
  const stateBadgeEl = document.getElementById('current-system-state-badge');
  const econInfoEl = document.getElementById('current-system-economy-info');
  if (stateBadgeEl) {
    const sState = (sys.system_state || '').trim();
    if (sState && sState.toLowerCase() !== 'none') {
      let badgeStyle = 'background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.35);';
      let icon = '🏛️';
      let label = sState;
      const lower = sState.toLowerCase();
      if (lower.includes('boom')) {
        badgeStyle = 'background: rgba(34, 197, 94, 0.2); color: #22c55e; border: 1px solid #22c55e; font-weight: bold; box-shadow: 0 0 8px rgba(34, 197, 94, 0.3);';
        icon = '📈';
        label = t('bgs_boom_label') || 'Boom (好況)';
      } else if (lower.includes('investment')) {
        badgeStyle = 'background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; font-weight: bold;';
        icon = '💼';
        label = t('bgs_investment_label') || 'Investment (投資)';
      } else if (lower.includes('expansion')) {
        badgeStyle = 'background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #c084fc; font-weight: bold;';
        icon = '🚀';
        label = t('bgs_expansion_label') || 'Expansion (拡張)';
      } else if (lower.includes('war') || lower.includes('unrest') || lower.includes('lockdown')) {
        badgeStyle = 'background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #f87171; font-weight: bold;';
        icon = '⚠️';
      } else if (lower.includes('bust')) {
        badgeStyle = 'background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #facc15; font-weight: bold;';
        icon = '📉';
        label = t('bgs_bust_label') || 'Bust (不況)';
      }
      const bgsTip = (t('bgs_state_tip') || 'EDSM星系経済・BGS状態: {state}').replace('{state}', escapeHtml(sState));
      stateBadgeEl.innerHTML = `<span class="tag-badge" style="${badgeStyle} font-size: 0.72rem; padding: 2px 7px;" title="${bgsTip}">${icon} ${escapeHtml(label)}</span>`;
      stateBadgeEl.style.display = 'inline-flex';
    } else if (sState && sState.toLowerCase() === 'none') {
      stateBadgeEl.innerHTML = `<span class="tag-badge" style="background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); font-size: 0.7rem; padding: 2px 6px;" title="${t('bgs_none_tip') || 'EDSM星系状態: 平常 (None)'}">${t('bgs_none_label') || '⚪ 平常 (None)'}</span>`;
      stateBadgeEl.style.display = 'inline-flex';
    } else if (sys.population === 0) {
      stateBadgeEl.innerHTML = `<span class="tag-badge" style="background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); font-size: 0.7rem; padding: 2px 6px;" title="${t('bgs_uninhabited_tip') || '無人星系 (深宇宙)'}">${t('bgs_uninhabited_label') || '🌌 無人星系'}</span>`;
      stateBadgeEl.style.display = 'inline-flex';
    } else {
      stateBadgeEl.innerHTML = '';
      stateBadgeEl.style.display = 'none';
    }

    if (sys.mining_scout_grade === 'High') {
      stateBadgeEl.innerHTML += `<span class="tag-badge badge-scout-high" style="font-size: 0.72rem; padding: 2px 7px;" title="Mining Scout High (Pristine + Metallic Rings)">⛏️ Scout: High</span>`;
      stateBadgeEl.style.display = 'inline-flex';
    } else if (sys.mining_scout_grade === 'Medium') {
      stateBadgeEl.innerHTML += `<span class="tag-badge badge-scout-medium" style="font-size: 0.72rem; padding: 2px 7px;" title="Mining Scout Medium (Pristine + Icy Rings)">⛏️ Scout: Medium</span>`;
      stateBadgeEl.style.display = 'inline-flex';
    }
  }

  if (econInfoEl) {
    const parts = [];
    if (sys.controlling_faction) {
      parts.push(`<span style="color: #cbd5e1;" title="${t('faction_controlling_tip') || '支配勢力'}">🎯 ${escapeHtml(sys.controlling_faction)}</span>`);
    }
    if (sys.system_reserve) {
      const isPristine = sys.system_reserve.toLowerCase().includes('pristine');
      const rColor = isPristine ? '#38bdf8; font-weight: bold;' : '#cbd5e1;';
      parts.push(`<span style="color: ${rColor}" title="${t('reserve_level_tip') || '資源埋蔵量'}">💎 ${escapeHtml(sys.system_reserve)} Reserves</span>`);
    }
    if (sys.system_economy) {
      const econStr = sys.system_economy + (sys.system_second_economy ? ` / ${sys.system_second_economy}` : '');
      parts.push(`<span style="color: #94a3b8;" title="${t('economy_primary_tip') || '主要経済'}">🏭 ${escapeHtml(econStr)}</span>`);
    }
    if (parts.length > 0) {
      econInfoEl.innerHTML = `<div style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.7rem; background: rgba(0,0,0,0.3); border: 1px solid var(--border-color); border-radius: 4px; padding: 2px 6px;">${parts.join('<span style="color: var(--text-dim);">|</span>')}</div>`;
      econInfoEl.style.display = 'inline-flex';
    } else {
      econInfoEl.innerHTML = '';
      econInfoEl.style.display = 'none';
    }
  }

  // Configurable Key Galactic Distances in Header
  updateCurrentSystemDistances(sys);

  // Astrophysical Rarity Badge in Header
  const physBadgeEl = document.getElementById('current-system-physics-badge');
  if (physBadgeEl) {
    const rScore = (sys.rarity_score !== undefined && sys.rarity_score !== null)
      ? sys.rarity_score
      : (state.currentSystemData && state.currentSystemData.physics_evaluation ? state.currentSystemData.physics_evaluation.rarity_score : null);

    if (rScore !== null && rScore !== undefined) {
      const roundedScore = Math.round(rScore * 10) / 10;
      let rClass = 'rarity-score-normal';
      let rLabel = t('physics_normal');
      if (roundedScore >= 95) {
        rClass = 'rarity-score-legendary';
        rLabel = t('physics_legendary');
      } else if (roundedScore >= 80) {
        rClass = 'rarity-score-epic';
        rLabel = t('physics_epic');
      } else if (roundedScore >= 60) {
        rClass = 'rarity-score-rare';
        rLabel = t('physics_rare');
      }
      physBadgeEl.className = `tag-badge ${rClass}`;
      physBadgeEl.innerHTML = `🌌 ★ ${roundedScore} pt <span style="font-size: 0.68rem; opacity: 0.9;">(${rLabel})</span>`;
      physBadgeEl.style.display = 'inline-flex';
      physBadgeEl.onclick = () => {
        state.currentView = 'physics';
        updateViewButtons();
        renderCurrentView();
      };
    } else {
      physBadgeEl.style.display = 'none';
      physBadgeEl.onclick = null;
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

  // Export buttons & Shared / External Badge in Header
  const btnExportHtml = document.getElementById('btn-export-html');
  const btnExportPkg = document.getElementById('btn-export-pkg');
  const btnToggleShared = document.getElementById('btn-toggle-shared');
  const sharedBadge = document.getElementById('current-system-shared-badge');
  const extBadge = document.getElementById('current-system-external-badge');
  const sharedIcon = document.getElementById('shared-toggle-icon');
  const sharedLabel = document.getElementById('shared-toggle-label');

  const isUnvisitedExternal = Boolean(sys.is_external || (sys.visit_count === 0));

  if (extBadge) {
    if (isUnvisitedExternal) {
      extBadge.innerHTML = `<span class="tag-badge tag-external" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.6); font-weight: bold;" title="${t('external_unvisited_header_tip') || '未訪問・EDSM外部参照星系（Web共有およびパッケージ書出は利用できません）'}">${t('badge_external_unvisited') || '🌐 外部参照 (未訪問)'}</span>`;
      extBadge.style.display = 'inline-flex';
    } else {
      extBadge.innerHTML = '';
      extBadge.style.display = 'none';
    }
  }

  if (isUnvisitedExternal) {
    // 外部参照・未訪問星系は、Web共有・パッケージ書出・共有マーク付与を禁止（非表示化）
    if (btnExportHtml) btnExportHtml.style.display = 'none';
    if (btnExportPkg) btnExportPkg.style.display = 'none';
    if (btnToggleShared) btnToggleShared.style.display = 'none';
    if (sharedBadge) {
      sharedBadge.innerHTML = '';
      sharedBadge.style.display = 'none';
    }
  } else {
    if (btnExportHtml) btnExportHtml.style.display = 'inline-flex';
    if (btnExportPkg) btnExportPkg.style.display = 'inline-flex';

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

    if (btnToggleShared) {
      if (sys.is_shared) {
        // Once shared, "共有解除" is not needed because it doesn't notify counterparty.
        btnToggleShared.style.display = 'none';
      } else {
        btnToggleShared.style.display = 'inline-flex';
        if (sharedIcon) sharedIcon.innerText = '🤝';
        if (sharedLabel) sharedLabel.innerText = t('share_label') || '共有マーク';
        btnToggleShared.style.background = 'rgba(167, 139, 250, 0.1)';
        btnToggleShared.style.borderColor = 'rgba(167, 139, 250, 0.4)';
      }
    }
  }
}

// Collapsible Groups & Badges
function updateCollapsibleBadges() {
  const generalKeys = ['has_elw', 'has_water_world', 'has_ammonia', 'has_terraformable', 'has_bio', 'has_first_discover', 'has_bookmarks', 'is_shared', 'has_high_g', 'has_anomalies'];
  const generalCount = generalKeys.filter(k => state.filters[k]).length;
  const badgeGen = document.getElementById('badge-general-filters');
  if (badgeGen) {
    badgeGen.innerText = generalCount > 0 ? generalCount : '';
    badgeGen.classList.toggle('active', generalCount > 0);
  }

  const miningKeys = ['has_landable_hmc', 'has_landable_metal_rich', 'has_landable_rocky', 'has_landable_icy', 'has_landable_rocky_ice', 'has_landable_ringed', 'has_mining_signals'];
  let miningCount = miningKeys.filter(k => state.filters[k]).length;
  if (state.miningScout) miningCount++;
  if (state.hasLargePad) miningCount++;
  if (state.maxArrivalDistLs !== null && state.maxArrivalDistLs !== undefined && state.maxArrivalDistLs !== '') miningCount++;
  const badgeMine = document.getElementById('badge-mining-filters');
  if (badgeMine) {
    badgeMine.innerText = miningCount > 0 ? miningCount : '';
    badgeMine.classList.toggle('active', miningCount > 0);
  }

  const celestialCount = (state.celestialFilters || []).length;
  const badgeCelestial = document.getElementById('badge-celestial-filters');
  if (badgeCelestial) {
    badgeCelestial.innerText = celestialCount > 0 ? celestialCount : '';
    badgeCelestial.classList.toggle('active', celestialCount > 0);
  }

  const starCount = (state.starTypes || []).length + (state.luminosityClasses || []).length;
  const badgeStar = document.getElementById('badge-stars-filters');
  if (badgeStar) {
    badgeStar.innerText = starCount > 0 ? starCount : '';
    badgeStar.classList.toggle('active', starCount > 0);
  }
}

function initCollapsibleSections() {
  const groups = document.querySelectorAll('.collapsible-group');
  groups.forEach(grp => {
    const header = grp.querySelector('.collapsible-header');
    const groupKey = header ? header.dataset.group : null;
    if (groupKey && state.collapsedGroups[groupKey]) {
      grp.classList.add('collapsed');
    }
    if (header) {
      header.addEventListener('click', () => {
        grp.classList.toggle('collapsed');
        if (groupKey) {
          state.collapsedGroups[groupKey] = grp.classList.contains('collapsed');
          try {
            localStorage.setItem('ed_collapsed_groups', JSON.stringify(state.collapsedGroups));
          } catch (e) {}
        }
      });
    }
  });
  updateCollapsibleBadges();
}

// Stellar Multi-Search Filters
function initStellarFilters() {
  const cbs = document.querySelectorAll('.star-filter-cb');
  cbs.forEach(cb => {
    cb.addEventListener('change', () => {
      const selected = Array.from(document.querySelectorAll('.star-filter-cb:checked')).map(el => el.value);
      state.starTypes = selected;
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  });

  const modeRadios = document.querySelectorAll('input[name="star-match-mode"]');
  modeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      state.starMatchMode = e.target.value;
      if (state.starTypes.length > 0) {
        state.page = 1;
        fetchSystems({ autoSelectTop: true });
      }
    });
  });

  const btnClear = document.getElementById('btn-clear-star-filters');
  if (btnClear) {
    btnClear.addEventListener('click', () => {
      document.querySelectorAll('.star-filter-cb').forEach(cb => { cb.checked = false; });
      state.starTypes = [];
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  }

  // Stellar Luminosity & Evolutionary Stages (Independent Filter)
  const lumCbs = document.querySelectorAll('.lum-filter-cb');
  lumCbs.forEach(cb => {
    cb.addEventListener('change', () => {
      const selected = Array.from(document.querySelectorAll('.lum-filter-cb:checked')).map(el => el.value);
      state.luminosityClasses = selected;
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  });

  const lumRadios = document.querySelectorAll('input[name="lum-match-mode"]');
  lumRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      state.luminosityMatchMode = e.target.value;
      if (state.luminosityClasses.length > 0) {
        state.page = 1;
        fetchSystems({ autoSelectTop: true });
      }
    });
  });

  const btnClearLum = document.getElementById('btn-clear-lum-filters');
  if (btnClearLum) {
    btnClearLum.addEventListener('click', () => {
      document.querySelectorAll('.lum-filter-cb').forEach(cb => { cb.checked = false; });
      state.luminosityClasses = [];
      state.page = 1;
      updateCollapsibleBadges();
      fetchSystems({ autoSelectTop: true });
    });
  }
}

// UI Layout Mode Switcher (1-Column vs 2-Column Left Pane)
function initLayoutSwitcher() {
  const btnToggleLayout = document.getElementById('btn-toggle-layout');
  const mainContainer = document.querySelector('.main-container');
  const layoutIcon = document.getElementById('layout-toggle-icon');
  const layoutText = document.getElementById('layout-toggle-text');

  function applyLayout(mode) {
    state.uiLayoutMode = mode;
    if (mainContainer) {
      mainContainer.classList.toggle('layout-2col-left', mode === '2col');
    }
    if (layoutText) {
      layoutText.innerText = mode === '2col' ? (t('btn_layout_1col') || '1列表示') : (t('btn_layout_2col') || '2列表示');
    }
    if (layoutIcon) {
      layoutIcon.innerText = mode === '2col' ? '🗖' : '◫';
    }
    try {
      localStorage.setItem('ed_ui_layout', mode);
    } catch (e) {}
  }

  // Restore initial layout mode
  applyLayout(state.uiLayoutMode);

  if (btnToggleLayout) {
    btnToggleLayout.addEventListener('click', () => {
      const nextMode = state.uiLayoutMode === '2col' ? '1col' : '2col';
      applyLayout(nextMode);
    });
  }
}

// Collapsible Header Exploration Stats Panel
function initHeaderStatsCollapse() {
  const headerGroup = document.getElementById('header-logged-group');
  const btnToggle = document.getElementById('btn-toggle-header-stats');
  if (!headerGroup || !btnToggle) return;

  function applyCollapse(collapsed) {
    state.headerStatsCollapsed = collapsed;
    headerGroup.classList.toggle('collapsed', collapsed);
    try {
      localStorage.setItem('ed_header_stats_collapsed', collapsed ? 'true' : 'false');
    } catch (e) {}
  }

  applyCollapse(state.headerStatsCollapsed);

  btnToggle.addEventListener('click', () => {
    applyCollapse(!headerGroup.classList.contains('collapsed'));
  });
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

// Window / Global Export
if (typeof window !== 'undefined') {
  window.defaultLandmarkSettings = defaultLandmarkSettings;
  window.getLandmarkSettings = getLandmarkSettings;
  window.saveLandmarkSettings = saveLandmarkSettings;
  window.generateLandmarkDistanceBadges = generateLandmarkDistanceBadges;
  window.updateCurrentSystemDistances = updateCurrentSystemDistances;
  window.renderSystemList = renderSystemList;
  window.highlightSelectedSystemCard = highlightSelectedSystemCard;
  window.scrollToTopOfSystemCards = scrollToTopOfSystemCards;
  window.renderPagination = renderPagination;
  window.renderSystemHeader = renderSystemHeader;
  window.updateCollapsibleBadges = updateCollapsibleBadges;
  window.initCollapsibleSections = initCollapsibleSections;
  window.initStellarFilters = initStellarFilters;
  window.initLayoutSwitcher = initLayoutSwitcher;
  window.initHeaderStatsCollapse = initHeaderStatsCollapse;
  window.clearSystemBioSummary = clearSystemBioSummary;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    defaultLandmarkSettings,
    getLandmarkSettings,
    saveLandmarkSettings,
    generateLandmarkDistanceBadges,
    updateCurrentSystemDistances,
    renderSystemList,
    highlightSelectedSystemCard,
    scrollToTopOfSystemCards,
    renderPagination,
    renderSystemHeader,
    updateCollapsibleBadges,
    initCollapsibleSections,
    initStellarFilters,
    initLayoutSwitcher,
    initHeaderStatsCollapse,
    clearSystemBioSummary
  };
}
