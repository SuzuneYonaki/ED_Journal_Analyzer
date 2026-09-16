/**
 * mining_view.js - Rhino Mining & Hotspot Management
 * Elite Dangerous Journal Analyzer
 */

function renderBodyMiningBlock(node) {
  const modSettings = getModuleSettings();
  if (modSettings.rhino === false) return '';
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

function renderMiningView(container, bodies) {
  if (!bodies) return;

  // Collect all ring hotspots across bodies in the system
  const systemRingHotspots = [];
  (bodies || []).forEach(b => {
    let rList = b.rings_list;
    if (!rList && b.rings && b.rings !== '[]' && b.rings !== '""') {
      try { rList = typeof b.rings === 'string' ? JSON.parse(b.rings) : b.rings; } catch (e) { rList = []; }
    }
    (rList || []).forEach(r => {
      const hs = r.Hotspots || {};
      if (Object.keys(hs).length === 0 && Array.isArray(r.signals)) {
        r.signals.forEach(s => {
          if (s && s.name) hs[s.name] = (hs[s.name] || 0) + (s.count || 1);
        });
      }
      if (Object.keys(hs).length > 0) {
        systemRingHotspots.push({
          body: b,
          body_name: b.body_name,
          body_id: b.body_id,
          ring_name: r.Name || 'Ring',
          ring_class: r.RingClass,
          reserve_level: b.reserve_level || (state.currentSystemData && state.currentSystemData.system && state.currentSystemData.system.system_reserve) || '',
          hotspots: hs,
          signals_updated_at: r.signals_updated_at
        });
      }
    });
  });

  function buildRingHotspotCard(hotspotsList) {
    const card = document.createElement('div');
    card.className = 'rhino-ring-hotspots-card';
    card.style.cssText = 'background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(250, 204, 21, 0.4); border-radius: 6px; padding: 10px 14px; font-size: 0.78rem;';

    const ringItemsHtml = hotspotsList.map(item => {
      const rInfo = parseRingClass(item.ring_class);
      const isBelt = (item.ring_name || '').toLowerCase().includes('belt');
      const rBadge = `<span class="tag-badge" style="background: ${rInfo.bg}; color: ${rInfo.color}; border: 1px solid ${rInfo.border}; font-weight: bold; font-size: 0.72rem;">
        ${rInfo.icon} ${rInfo.nameJa} (${rInfo.nameEn} ${isBelt ? 'Belt' : 'Ring'})
      </span>`;

      const reserveInfo = parseReserveLevel(item.reserve_level);
      const reserveBadge = reserveInfo ? `<span class="tag-badge" style="background: rgba(34, 197, 94, 0.15); color: ${reserveInfo.color}; border: 1px solid rgba(34, 197, 94, 0.35); font-size: 0.7rem;">
        ${reserveInfo.icon} ${reserveInfo.ja}
      </span>` : '';

      const hsBadges = Object.entries(item.hotspots).map(([mineral, count]) => {
        const lmin = mineral.toLowerCase();
        let bColor = '#facc15';
        let bBg = 'rgba(250, 204, 21, 0.18)';
        let bBorder = 'rgba(250, 204, 21, 0.5)';
        let icon = '🎯';

        if (lmin.includes('platinum')) {
          icon = '🪙'; bColor = '#38bdf8'; bBg = 'rgba(56, 189, 248, 0.2)'; bBorder = '#38bdf8';
        } else if (lmin.includes('painite')) {
          icon = '💎'; bColor = '#facc15'; bBg = 'rgba(250, 204, 21, 0.2)'; bBorder = '#facc15';
        } else if (lmin.includes('tritium')) {
          icon = '⛽'; bColor = '#22c55e'; bBg = 'rgba(34, 197, 94, 0.2)'; bBorder = '#22c55e';
        } else if (lmin.includes('void opal') || lmin.includes('low temperature diamond')) {
          icon = '🧊'; bColor = '#a78bfa'; bBg = 'rgba(167, 139, 250, 0.2)'; bBorder = '#a78bfa';
        } else if (lmin.includes('monazite') || lmin.includes('musgravite') || lmin.includes('alexandrite') || lmin.includes('benitoite') || lmin.includes('serendibite') || lmin.includes('rhodplumsite')) {
          icon = '🟣'; bColor = '#e879f9'; bBg = 'rgba(232, 121, 249, 0.2)'; bBorder = '#e879f9';
        }

        return `<span class="tag-badge" style="background: ${bBg}; color: ${bColor}; border: 1px solid ${bBorder}; font-weight: bold; font-size: 0.72rem; padding: 2px 6px;">
          ${icon} ${mineral} ${count > 1 ? `x${count}` : ''}
        </span>`;
      }).join(' ');

      return `
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 5px; padding: 8px 10px; margin-bottom: 6px;">
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 6px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 6px;">
              <span style="font-weight: bold; color: var(--ed-gold); font-size: 0.82rem;">🪐 ${escapeHtml(item.body_name)} - ${escapeHtml(item.ring_name)}</span>
            </div>
            <div style="display: flex; gap: 4px; align-items: center;">
              ${rBadge}
              ${reserveBadge}
              <button class="btn-page btn-ring-body-detail" data-body-id="${item.body_id}" style="padding: 2px 8px; font-size: 0.7rem; cursor: pointer;">🔍 詳細</button>
            </div>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;">
            ${hsBadges}
          </div>
        </div>
      `;
    }).join('');

    card.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
        <span style="font-weight: bold; color: #facc15; font-size: 0.85rem; display: flex; align-items: center; gap: 6px;">
          <span>🪐</span> <span>${t('section_ring_hotspots') || '🪐 環状帯ホットスポット (Ring Mining Hotspots)'}</span>
        </span>
        <div style="display: flex; gap: 6px; align-items: center;">
          <span class="tag-badge" style="background: rgba(250, 204, 21, 0.18); color: #facc15; border: 1px solid rgba(250, 204, 21, 0.4); font-weight: bold;">
            🎯 検出: ${hotspotsList.length} 環
          </span>
          <button id="btn-mining-spansh-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; background: rgba(250, 204, 21, 0.2); border-color: #facc15; color: #facc15; cursor: pointer;">🪐 Spansh照会</button>
        </div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 4px;">
        ${ringItemsHtml}
      </div>
    `;

    setTimeout(() => {
      const detailBtns = card.querySelectorAll('.btn-ring-body-detail');
      detailBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const bId = parseInt(btn.getAttribute('data-body-id'), 10);
          const targetBody = bodies.find(b => b.body_id === bId);
          if (targetBody && typeof showBodyDetailModal === 'function') {
            showBodyDetailModal(targetBody);
          }
        });
      });

      const btnSpansh = card.querySelector('#btn-mining-spansh-sync');
      if (btnSpansh) {
        btnSpansh.addEventListener('click', async (e) => {
          e.stopPropagation();
          const curAddr = (state.selectedSystem && state.selectedSystem.system_address) || (state.currentSystemData && state.currentSystemData.system && state.currentSystemData.system.system_address);
          if (!curAddr) return;
          btnSpansh.disabled = true;
          btnSpansh.innerHTML = '⏳ 照会中...';
          try {
            const resp = await fetch(`/api/systems/${curAddr}/spansh_sync`, { method: 'POST' });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const resData = await resp.json();
            btnSpansh.innerHTML = `✓ 完了 (${resData.hotspots_found || 0} HS)`;
            setTimeout(() => {
              btnSpansh.disabled = false;
              btnSpansh.innerHTML = '🪐 Spansh照会';
            }, 2000);
            await selectSystem(curAddr, true, false);
          } catch (err) {
            console.error('Failed Spansh sync in mining view:', err);
            btnSpansh.disabled = false;
            btnSpansh.innerHTML = '❌ 照会失敗';
            setTimeout(() => {
              btnSpansh.innerHTML = '🪐 Spansh照会';
            }, 2000);
          }
        });
      }
    }, 0);

    return card;
  }

  const landableBodies = bodies.filter(b => b.landable === 1);

  if (landableBodies.length === 0) {
    if (systemRingHotspots.length > 0) {
      const wrapper = document.createElement('div');
      wrapper.style.display = 'flex';
      wrapper.style.flexDirection = 'column';
      wrapper.style.gap = '12px';

      const infoBanner = document.createElement('div');
      infoBanner.style.cssText = 'background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 6px; padding: 10px 14px; font-size: 0.78rem; color: #cbd5e1;';
      infoBanner.innerHTML = `
        <div style="font-weight: bold; color: #38bdf8; font-size: 0.85rem; margin-bottom: 4px;">⛏️ 星系採掘サマリー</div>
        <div>この星系には着陸可能な陸上天体はありませんが、<b>${systemRingHotspots.length} 環</b>で環状帯ホットスポットが検出されています。</div>
      `;
      wrapper.appendChild(infoBanner);
      wrapper.appendChild(buildRingHotspotCard(systemRingHotspots));
      container.innerHTML = '';
      container.appendChild(wrapper);
      return;
    }

    container.innerHTML = `
      <div style="color: var(--text-secondary); text-align: center; margin-top: 40px; padding: 20px;">
        <div style="font-size: 2rem; margin-bottom: 8px;">⛏️</div>
        <div style="font-size: 1.1rem; font-weight: bold; color: #fff;">${t('no_landable_bodies')}</div>
        <div style="font-size: 0.8rem; color: var(--text-dim); margin-top: 6px;">この星系には着陸（Landable）可能な天体、および環ホットスポット採掘対象は存在しません。</div>
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
  const curSys = state.selectedSystem || (state.currentSystemData && state.currentSystemData.system) || {};
  const sState = (curSys.system_state || '').trim();
  const sStateLower = sState.toLowerCase();
  let stateImpactHtml = '';
  if (sStateLower.includes('boom')) {
    stateImpactHtml = `
      <div style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.45); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: #4ade80; font-weight: bold; font-size: 0.76rem;">📈 【星系経済状態: Boom (好況)】採掘物資の高額売却ボーナス & 需要急増中！Rhino採掘素材の放出やミッションに最適な状態です。</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; background: rgba(34, 197, 94, 0.2); border-color: #4ade80; color: #4ade80; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  } else if (sStateLower.includes('investment')) {
    stateImpactHtml = `
      <div style="background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.45); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: #38bdf8; font-weight: bold; font-size: 0.76rem;">💼 【星系経済状態: Investment (投資)】開発・インフラ需要拡大中！工業用金属・鉱物の需要が高まっています。</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; color: #38bdf8; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  } else if (sStateLower.includes('expansion')) {
    stateImpactHtml = `
      <div style="background: rgba(192, 132, 252, 0.12); border: 1px solid rgba(192, 132, 252, 0.45); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: #c084fc; font-weight: bold; font-size: 0.76rem;">🚀 【星系状態: Expansion (拡張)】勢力拡大フェーズ。素材支援や探査データの価値が向上しています。</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; color: #c084fc; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  } else if (sStateLower.includes('war') || sStateLower.includes('civil war')) {
    stateImpactHtml = `
      <div style="background: rgba(248, 113, 113, 0.12); border: 1px solid rgba(248, 113, 113, 0.45); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: #f87171; font-weight: bold; font-size: 0.76rem;">⚔️ 【星系状態: War / Civil War (戦争)】交戦宙域。鉱物需要が高まる一方、敵対勢力や海賊の活動リスクに注意。</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; color: #f87171; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  } else if (sStateLower.includes('famine') || sStateLower.includes('outbreak')) {
    stateImpactHtml = `
      <div style="background: rgba(250, 204, 21, 0.12); border: 1px solid rgba(250, 204, 21, 0.45); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: #facc15; font-weight: bold; font-size: 0.76rem;">⚠️ 【星系状態: Crisis (${escapeHtml(sState)})】危機状態。特定支援物資の価値が高騰しています。</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; color: #facc15; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  } else if (sStateLower.includes('unrest') || sStateLower.includes('lockdown')) {
    stateImpactHtml = `
      <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: #f87171; font-size: 0.76rem;">⚠️ 【星系状態: 紛争・治安悪化 (${escapeHtml(sState)})】ステーション機能制限や治安悪化の懸念があります。輸送時の海賊にご注意ください。</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; color: #f87171; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  } else if (sStateLower.includes('bust')) {
    stateImpactHtml = `
      <div style="background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.4); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: #facc15; font-size: 0.76rem;">📉 【星系状態: Bust (不況)】市場価格が低迷傾向です。近隣の好況星系（Boom）での売却を推奨します。</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; color: #facc15; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  } else if (curSys.population === 0) {
    stateImpactHtml = `
      <div style="background: rgba(100, 116, 139, 0.08); border: 1px solid rgba(100, 116, 139, 0.3); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: #94a3b8; font-size: 0.76rem;">🌌 【無人星系】ステーション等はありませんが、未開拓の豊富な資源（Pristine Reserves等）に恵まれた採掘適地です。</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; color: #38bdf8; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  } else {
    stateImpactHtml = `
      <div style="background: rgba(0, 0, 0, 0.2); border: 1px solid var(--border-color); border-radius: 4px; padding: 6px 10px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="color: var(--text-secondary); font-size: 0.76rem;">🏛️ 星系状態: ${sState ? escapeHtml(sState) : '平常 (None)'} ${curSys.controlling_faction ? `| 支配: ${escapeHtml(curSys.controlling_faction)}` : ''} ${curSys.system_reserve ? `| 埋蔵量: ${escapeHtml(curSys.system_reserve)}` : ''}</span>
        <button id="btn-mining-edsm-sync" class="btn-page" style="padding: 2px 8px; font-size: 0.7rem; color: #38bdf8; cursor: pointer;">🔄 EDSM最新状態同期</button>
      </div>
    `;
  }

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
    ${stateImpactHtml}
    <div style="color: var(--text-secondary); margin-top: 6px; line-height: 1.45; font-size: 0.73rem; border-top: 1px dashed rgba(255,255,255,0.06); padding-top: 6px;">
      ・<b>推奨天体</b>: <b>Rocky / Metal Rich / HMC</b> はバストネサイト（Bastnäsite）等の希少鉱石・高価値素材の主産地。<br>
      ・<b>天体半径 & 重力</b>: 大半径天体は平坦な平原が広がりやすく操縦・リグ展開に有利。高重力(3G+)での着陸には注意。<br>
      ・<b>環付きLandable</b>: 景観美に加え、固有の鉱物密集地帯としてコミュニティで最重要探索対象。
    </div>
  `;
  wrapper.appendChild(guideCard);

  if (systemRingHotspots.length > 0) {
    wrapper.appendChild(buildRingHotspotCard(systemRingHotspots));
  }

  // Bind EDSM sync button in mining view
  setTimeout(() => {
    const btnMiningSync = guideCard.querySelector('#btn-mining-edsm-sync');
    if (btnMiningSync) {
      btnMiningSync.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!curSys.system_address) return;
        btnMiningSync.disabled = true;
        btnMiningSync.innerHTML = '⏳ 取得中...';
        try {
          const resp = await fetch(`/api/systems/${curSys.system_address}/edsm_sync`, { method: 'POST' });
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          await selectSystem(curSys.system_address, true, false);
          btnMiningSync.innerHTML = '✓ 更新完了';
          setTimeout(() => {
            btnMiningSync.disabled = false;
            btnMiningSync.innerHTML = '🔄 EDSM最新状態同期';
          }, 1500);
        } catch (err) {
          console.error('Failed to sync EDSM in mining view:', err);
          btnMiningSync.disabled = false;
          btnMiningSync.innerHTML = '❌ 取得失敗';
          setTimeout(() => {
            btnMiningSync.innerHTML = '🔄 EDSM最新状態同期';
          }, 2000);
        }
      });
    }
  }, 0);

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

// ==========================================
// Rhino Surface Mining Sites Modal & Management
// ==========================================
let activeMiningModalBody = null;

async function refreshMiningSitesForBody(body) {
  if (!body) return;
  try {
    const sysAddr = body.system_address;
    const bodyId = body.body_id;
    const url = (bodyId !== undefined && bodyId !== null)
      ? `/api/mining_sites/${sysAddr}?body_id=${bodyId}` 
      : `/api/mining_sites/${sysAddr}`;
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      const updatedSites = data.sites || [];
      body.rhino_mining_sites = updatedSites;
      if (state.currentSystemData && state.currentSystemData.bodies) {
        const found = state.currentSystemData.bodies.find(x => x.body_id === bodyId);
        if (found) found.rhino_mining_sites = updatedSites;
      }
      if (state.currentSystemData && state.currentSystemData.rhino_mining_sites) {
        const allRes = await fetch(`/api/mining_sites/${sysAddr}`);
        if (allRes.ok) {
          const allData = await allRes.json();
          state.currentSystemData.rhino_mining_sites = allData.sites || [];
        }
      }
      renderBodyInspector();
    }
  } catch (err) {
    console.error('Failed to refresh mining sites:', err);
  }
}

function openMiningSiteModal(opts) {
  const modal = document.getElementById('modal-mining-site');
  if (!modal) return;
  activeMiningModalBody = opts.body;
  const titleEl = document.getElementById('modal-mining-site-title');
  const bodyNameEl = document.getElementById('modal-mining-site-body-name');
  const idInput = document.getElementById('input-mining-site-id');
  const latInput = document.getElementById('input-mining-lat');
  const lonInput = document.getElementById('input-mining-lon');
  const hotspotInput = document.getElementById('input-mining-hotspot');
  const hotspotDatalist = document.getElementById('mining-hotspots-datalist');
  const mineralsInput = document.getElementById('input-mining-minerals');
  const noteInput = document.getElementById('input-mining-note');
  const errEl = document.getElementById('modal-mining-site-error');

  if (errEl) {
    errEl.style.display = 'none';
    errEl.innerText = '';
  }

  if (bodyNameEl) {
    bodyNameEl.innerText = opts.body ? opts.body.body_name : '--';
  }

  // Populate candidate hotspots in datalist
  if (hotspotDatalist) {
    const candidates = new Set();
    const sigCount = (opts.body && opts.body.mining_signals) || 0;
    for (let i = 1; i <= sigCount; i++) {
      candidates.add(`Hotspot ${i}`);
    }
    const existingSites = (opts.body && opts.body.rhino_mining_sites) || [];
    existingSites.forEach(st => {
      if (st.hotspot && st.hotspot.trim()) candidates.add(st.hotspot.trim());
    });
    hotspotDatalist.innerHTML = Array.from(candidates).map(name => `<option value="${escapeHtml(name)}"></option>`).join('');
  }

  if (opts.isNew) {
    if (titleEl) titleEl.innerHTML = '<span>➕</span> <span>採掘地点の追加</span>';
    if (idInput) idInput.value = '';
    if (latInput) latInput.value = '';
    if (lonInput) lonInput.value = '';
    if (hotspotInput) hotspotInput.value = '';
    if (mineralsInput) mineralsInput.value = '';
    if (noteInput) noteInput.value = '';
  } else {
    const s = opts.site || {};
    if (titleEl) titleEl.innerHTML = '<span>⛏️</span> <span>採掘地点の編集</span>';
    if (idInput) idInput.value = s.id || '';
    if (latInput) latInput.value = (s.latitude !== null && s.latitude !== undefined) ? s.latitude : '';
    if (lonInput) lonInput.value = (s.longitude !== null && s.longitude !== undefined) ? s.longitude : '';
    if (hotspotInput) hotspotInput.value = s.hotspot || '';
    const minText = (s.commodities && s.commodities.length > 0)
      ? s.commodities.join(', ')
      : (s.minerals || '');
    if (mineralsInput) mineralsInput.value = minText;
    if (noteInput) noteInput.value = s.note || '';
  }

  const quickPasteArea = document.getElementById('input-mining-quick-paste');
  if (quickPasteArea) quickPasteArea.value = '';

  modal.style.display = 'flex';
  setTimeout(() => {
    if (latInput) latInput.focus();
  }, 50);
}

function closeMiningSiteModal() {
  const modal = document.getElementById('modal-mining-site');
  if (modal) modal.style.display = 'none';
  activeMiningModalBody = null;
}

function initMiningSiteModal() {
  const modal = document.getElementById('modal-mining-site');
  if (!modal) return;
  const btnClose = document.getElementById('btn-close-mining-site-modal');
  const btnCancel = document.getElementById('btn-cancel-mining-site');
  const btnSave = document.getElementById('btn-save-mining-site');
  const btnApplyPaste = document.getElementById('btn-apply-mining-paste');
  const errEl = document.getElementById('modal-mining-site-error');

  if (btnClose) btnClose.addEventListener('click', closeMiningSiteModal);
  if (btnCancel) btnCancel.addEventListener('click', closeMiningSiteModal);

  // Quick Paste text parsing (e.g. Kuk B 2 / Hotspot 26 / Iridium spot for 3 rig / Location : -28.8859 / -66.7179)
  if (btnApplyPaste) {
    btnApplyPaste.addEventListener('click', () => {
      const raw = (document.getElementById('input-mining-quick-paste')?.value || '').trim();
      if (!raw) return;

      const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);
      let foundLat = null, foundLon = null;
      let foundHotspot = '';
      let foundDesc = '';

      for (const line of lines) {
        // Check for Location line: e.g. "Location : -28.8859 / -66.7179" or "-28.8859 / -66.7179"
        const locMatch = line.match(/(?:Location|Pos|Coords?|座標)?\s*[:：]?\s*([+-]?\d+(?:\.\d+)?)\s*[\/,\s]\s*([+-]?\d+(?:\.\d+)?)/i);
        if (locMatch && !isNaN(parseFloat(locMatch[1])) && !isNaN(parseFloat(locMatch[2]))) {
          foundLat = parseFloat(locMatch[1]);
          foundLon = parseFloat(locMatch[2]);
          continue;
        }
        // Check for Hotspot line (e.g. "Hotspot 26", "Hotspot 1", "PML #3")
        if (/^(?:Hotspot|PML|採掘拠点)/i.test(line)) {
          foundHotspot = line;
          continue;
        }
        // Check if line matches current body name (e.g. "Kuk B 2")
        if (activeMiningModalBody && activeMiningModalBody.body_name && line.toLowerCase() === activeMiningModalBody.body_name.toLowerCase()) {
          continue;
        }
        // Otherwise treat as minerals / description / note
        if (!foundDesc) {
          foundDesc = line;
        } else {
          foundDesc += ', ' + line;
        }
      }

      if (foundLat !== null) document.getElementById('input-mining-lat').value = foundLat;
      if (foundLon !== null) document.getElementById('input-mining-lon').value = foundLon;
      if (foundHotspot) document.getElementById('input-mining-hotspot').value = foundHotspot;
      if (foundDesc) {
        const minInput = document.getElementById('input-mining-minerals');
        const noteInput = document.getElementById('input-mining-note');
        if (!minInput.value) {
          minInput.value = foundDesc;
        } else if (!noteInput.value) {
          noteInput.value = foundDesc;
        } else {
          noteInput.value += ' ' + foundDesc;
        }
      }
    });
  }

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeMiningSiteModal();
  });

  if (btnSave) {
    btnSave.addEventListener('click', async () => {
      const b = activeMiningModalBody || state.selectedBody;
      if (!b) return;

      const idVal = document.getElementById('input-mining-site-id').value.trim();
      const latRaw = document.getElementById('input-mining-lat').value.trim();
      const lonRaw = document.getElementById('input-mining-lon').value.trim();
      const hotspotVal = (document.getElementById('input-mining-hotspot')?.value || '').trim();
      const mineralsVal = document.getElementById('input-mining-minerals').value.trim();
      const noteVal = document.getElementById('input-mining-note').value.trim();

      const showError = (msg) => {
        if (errEl) {
          errEl.innerText = msg;
          errEl.style.display = 'block';
        }
      };

      if (!latRaw || isNaN(parseFloat(latRaw))) {
        showError('有効な緯度 (-90 ～ +90) を入力してください。');
        return;
      }
      if (!lonRaw || isNaN(parseFloat(lonRaw))) {
        showError('有効な経度 (-180 ～ +180) を入力してください。');
        return;
      }

      const lat = parseFloat(latRaw);
      const lon = parseFloat(lonRaw);
      if (lat < -90 || lat > 90) {
        showError('緯度は -90 ～ +90 の範囲で入力してください。');
        return;
      }
      if (lon < -180 || lon > 180) {
        showError('経度は -180 ～ +180 の範囲で入力してください。');
        return;
      }

      const origText = btnSave.innerHTML;
      btnSave.disabled = true;
      btnSave.innerHTML = '⏳ 保存中...';

      try {
        if (idVal) {
          // Update existing site
          const resp = await fetch(`/api/mining_sites/${idVal}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              latitude: lat,
              longitude: lon,
              hotspot: hotspotVal,
              minerals: mineralsVal,
              note: noteVal
            })
          });
          if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            throw new Error(errData.detail || errData.error || `HTTP ${resp.status}`);
          }
        } else {
          // Create new site
          const curSys = state.currentSystemData ? state.currentSystemData.system : state.selectedSystem;
          const starSys = (curSys && curSys.star_system) || b.star_system || 'Unknown';
          const resp = await fetch('/api/mining_sites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              system_address: b.system_address,
              star_system: starSys,
              body_id: b.body_id,
              body_name: b.body_name,
              latitude: lat,
              longitude: lon,
              hotspot: hotspotVal,
              minerals: mineralsVal,
              note: noteVal
            })
          });
          if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            throw new Error(errData.detail || errData.error || `HTTP ${resp.status}`);
          }
        }

        closeMiningSiteModal();
        await refreshMiningSitesForBody(b);
      } catch (err) {
        console.error('Failed to save mining site:', err);
        showError('保存に失敗しました: ' + (err.message || 'エラーが発生しました'));
      } finally {
        btnSave.disabled = false;
        btnSave.innerHTML = origText;
      }
    });
  }
}

// Window / Global Export
if (typeof window !== 'undefined') {
  window.renderBodyMiningBlock = renderBodyMiningBlock;
  window.renderMiningView = renderMiningView;
  window.refreshMiningSitesForBody = refreshMiningSitesForBody;
  window.openMiningSiteModal = openMiningSiteModal;
  window.closeMiningSiteModal = closeMiningSiteModal;
  window.initMiningSiteModal = initMiningSiteModal;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    renderBodyMiningBlock,
    renderMiningView,
    refreshMiningSitesForBody,
    openMiningSiteModal,
    closeMiningSiteModal,
    initMiningSiteModal
  };
}
