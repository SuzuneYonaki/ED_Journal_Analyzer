/**
 * inspector.js - Celestial Body Inspector & Exobiology Predictor
 * Elite Dangerous Journal Analyzer
 */

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
  let typeSubtitle = '';
  if (b.isAsteroidBelt) {
    const beltRingInfo = typeof parseRingClass === 'function' ? parseRingClass(b.ring_class) : null;
    const lang = (typeof getAppLang === 'function') ? getAppLang() : 'ja';
    const ringName = beltRingInfo ? (lang === 'en' ? (beltRingInfo.nameEn || beltRingInfo.name) : (beltRingInfo.nameJa || beltRingInfo.name)) : '';
    typeSubtitle = `🪐 Asteroid Belt${ringName ? ' (' + ringName + ')' : ''}`;
  } else if (b.star_type) {
    typeSubtitle = `${t('star_type_label')}: ${b.star_type}`;
  } else {
    typeSubtitle = `${b.planet_class || 'Body'}${b.terraforming_state ? ' [' + b.terraforming_state + ']' : ''}`;
  }
  if (b.scan_type === 'EDSM_Known') {
    typeSubtitle += ` · ⭐ ${t('edsm_known_unscanned')}`;
    if (b.edsm_discovered_by) {
      typeSubtitle += ` / ${t('discoverer_prefix')}: CMDR ${b.edsm_discovered_by}`;
    }
  }
  document.getElementById('inspect-body-type').innerText = typeSubtitle;

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

  const isBaryOrBelt = Boolean(b.isBarycentre || b.isAsteroidBelt);

  if (isBaryOrBelt) {
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
      if (inspectBmText) inspectBmText.innerText = t('bm_status_active') || 'ブックマーク中';
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
      if (inspectBmText) inspectBmText.innerText = t('filter_bookmarks') || 'ブックマーク';
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
        bmNotePreview.innerHTML = parseMarkdown(bmNoteInput.value.trim() || t('bm_no_notes'));
        bmNoteInput.style.display = 'none';
        bmNotePreview.style.display = 'block';
      };
    }

    // Insert Live CMDR Surface Coordinates Handler
    const btnInsertCoords = document.getElementById('btn-insert-cmdr-coords');
    if (btnInsertCoords && bmNoteInput) {
      btnInsertCoords.onclick = async () => {
        try {
          btnInsertCoords.disabled = true;
          const res = await fetch('/api/cmdr/coordinates');
          btnInsertCoords.disabled = false;
          if (res.ok) {
            const data = await res.json();
            if (data && data.has_coordinates && data.formatted_text) {
              const cursorPos = bmNoteInput.selectionStart || bmNoteInput.value.length;
              const textBefore = bmNoteInput.value.substring(0, cursorPos);
              const textAfter = bmNoteInput.value.substring(cursorPos);
              const insertion = (textBefore.length > 0 && !textBefore.endsWith('\n') ? '\n' : '') +
                                data.formatted_text + '\n';
              bmNoteInput.value = textBefore + insertion + textAfter;
              bmNoteInput.focus();
              const newPos = cursorPos + insertion.length;
              bmNoteInput.setSelectionRange(newPos, newPos);
            } else {
              alert(data.message || 'No surface coordinates available (CMDR not currently on surface)');
            }
          }
        } catch (e) {
          btnInsertCoords.disabled = false;
          console.error('Failed to fetch cmdr coordinates:', e);
        }
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
        <div style="font-weight: bold; color: #c084fc; margin-bottom: 4px;">♊ ${t('barycentre_title')}</div>
        <div>${t('barycentre_stars')}: <strong>${starList}</strong></div>
        <div style="margin-top: 4px; color: var(--text-secondary);">${t('barycentre_desc')} (${b.starGroup} 1, ${b.starGroup} 2...)</div>
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
  const secBio = document.getElementById('section-exobiology');
  const modSettings = getModuleSettings();
  const bioInfo = document.getElementById('inspect-bio-signals-info');
  const bioContainer = document.getElementById('inspect-bio-predictions');
  const scannedOrganics = b.scanned_organics || [];
  const potBio = b.potential_exobiology || b.exobiology || [];

  if (modSettings.exobiology === false) {
    if (secBio) secBio.style.display = 'none';
  } else if (b.bio_signals > 0 || scannedOrganics.length > 0 || potBio.length > 0) {
    if (secBio) secBio.style.display = 'block';
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
          colorBadges += `<span class="tag-badge" style="background: rgba(250, 204, 21, 0.15); color: #fde047; border: 1px solid rgba(250, 204, 21, 0.35); font-size: 0.65rem;" title="${t('bio_color_main_tip')}">🎨 ${bio.variant_color}</span>`;
        }
        if (bio.alternate_variants && bio.alternate_variants.length > 0) {
          colorBadges += bio.alternate_variants.slice(0, 3).map(c => `
            <span class="tag-badge" style="background: rgba(148, 163, 184, 0.12); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); font-size: 0.62rem;" title="${t('bio_color_candidate_tip')}">🎨 ${c}</span>
          `).join('');
        }
        const isExcluded = scannedGenusSet.has(gen) || isFullyScanned;
        const matchPct = bio.possible_pct !== undefined ? bio.possible_pct : (bio.match_percentage !== undefined ? bio.match_percentage : (bio.fit_score ? Math.round(bio.fit_score * 100) : null));
        const pctBadge = (matchPct !== null && matchPct !== undefined) 
          ? `<span class="tag-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.65rem;" title="${t('bio_match_pct_tip')}">📊 Possible: ${matchPct}%</span>` 
          : '';
        const coherentBadge = bio.is_system_coherent 
          ? `<span class="tag-badge" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); font-size: 0.65rem;" title="${t('bio_cooccurrence_tip')}">🪐 ${t('bio_cooccurrence_badge')}</span>` 
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
    if (modSettings.exobiology === false) {
      if (secBio) secBio.style.display = 'none';
    } else {
      if (secBio) secBio.style.display = 'block';
      bioInfo.innerText = t('bio_none');
      bioContainer.innerHTML = `<div style="font-size: 0.75rem; color: var(--text-dim);">${t('bio_none_desc')}</div>`;
    }
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

  // System-wide average calculations for Inspector comparisons (Observatory Criteria evaluation)
  const allSysBodies = (state.currentSystemData && state.currentSystemData.bodies) || [];
  const validSysBodies = allSysBodies.filter(x => !x.isBarycentre);
  const landableSysBodies = validSysBodies.filter(x => x.landable);

  const curSys = (state.currentSystemData && state.currentSystemData.system) || state.selectedSystem;
  let avgLandableRadius = curSys && curSys.avg_landable_radius > 0 ? curSys.avg_landable_radius : null;
  if (!avgLandableRadius && landableSysBodies.length > 0) {
    const validRadBodies = landableSysBodies.filter(x => x.radius > 0);
    if (validRadBodies.length > 0) {
      avgLandableRadius = validRadBodies.reduce((acc, x) => acc + x.radius, 0) / validRadBodies.length;
    }
  }

  const allRadBodies = validSysBodies.filter(x => x.radius > 0);
  const avgSystemRadius = allRadBodies.length > 0
    ? (allRadBodies.reduce((acc, x) => acc + x.radius, 0) / allRadBodies.length)
    : null;

  const gravBodies = landableSysBodies.filter(x => (x.surface_gravity_g > 0 || x.surface_gravity > 0));
  const avgGravity = gravBodies.length > 0
    ? (gravBodies.reduce((acc, x) => acc + (x.surface_gravity_g || (x.surface_gravity / 9.80665) || 0), 0) / gravBodies.length)
    : null;

  const tempBodies = validSysBodies.filter(x => x.surface_temperature > 0);
  const avgTemp = tempBodies.length > 0
    ? (tempBodies.reduce((acc, x) => acc + x.surface_temperature, 0) / tempBodies.length)
    : null;

  const pressBodies = validSysBodies.filter(x => x.surface_pressure > 0);
  const avgPress = pressBodies.length > 0
    ? (pressBodies.reduce((acc, x) => acc + x.surface_pressure, 0) / pressBodies.length)
    : null;

  const eccBodies = validSysBodies.filter(x => x.eccentricity !== null && x.eccentricity !== undefined);
  const avgEcc = eccBodies.length > 0
    ? (eccBodies.reduce((acc, x) => acc + x.eccentricity, 0) / eccBodies.length)
    : null;

  const smaBodies = validSysBodies.filter(x => x.semi_major_axis > 0);
  const avgSma = smaBodies.length > 0
    ? (smaBodies.reduce((acc, x) => acc + x.semi_major_axis, 0) / smaBodies.length)
    : null;

  const orbBodies = validSysBodies.filter(x => x.orbital_period > 0);
  const avgOrb = orbBodies.length > 0
    ? (orbBodies.reduce((acc, x) => acc + x.orbital_period, 0) / orbBodies.length)
    : null;

  const rotBodies = validSysBodies.filter(x => x.rotation_period > 0);
  const avgRot = rotBodies.length > 0
    ? (rotBodies.reduce((acc, x) => acc + x.rotation_period, 0) / rotBodies.length)
    : null;

  const incBodies = validSysBodies.filter(x => x.orbital_inclination !== null && x.orbital_inclination !== undefined);
  const avgInc = incBodies.length > 0
    ? (incBodies.reduce((acc, x) => acc + x.orbital_inclination, 0) / incBodies.length)
    : null;

  function formatAvgDiffBadge(diffVal, diffPct, unit = '', avgLabel = '', count = 2) {
    if (diffVal === null || isNaN(diffVal) || count <= 1) return '';
    if (Math.abs(diffVal) < 1e-5) return '';

    const isPlus = diffVal > 0;
    const sign = isPlus ? '+' : '';
    const arrow = isPlus ? '▲' : '▼';
    const cls = isPlus ? 'positive' : 'negative';

    let diffStr;
    if (Math.abs(diffVal) < 0.01) {
      diffStr = diffVal.toFixed(4);
    } else if (Math.abs(diffVal) < 1) {
      diffStr = diffVal.toFixed(3);
    } else {
      diffStr = diffVal.toLocaleString(undefined, { maximumFractionDigits: 1 });
    }

    const pctStr = (diffPct !== null && diffPct !== undefined) ? ` (${sign}${diffPct.toFixed(1)}%)` : '';
    const labelStr = avgLabel ? ` vs ${avgLabel}` : '';

    return `<span class="prop-diff-badge ${cls}" title="${t('diff_title_prefix') || '平均値との差異: '}${sign}${diffStr} ${unit}${pctStr}${labelStr}">${arrow} ${sign}${diffStr} ${unit}${pctStr}</span>`;
  }

  const gravEl = document.getElementById('prop-gravity');
  if (b.surface_gravity_g !== null && b.surface_gravity_g !== undefined) {
    const gVal = b.surface_gravity_g;
    let baseText = `${gVal.toFixed(3)} G (${(b.surface_gravity || 0).toFixed(1)} m/s²)`;
    let diffBadge = '';
    
    if (avgGravity !== null && gravBodies.length > 1) {
      const diffG = gVal - avgGravity;
      const diffPctG = (diffG / avgGravity) * 100;
      diffBadge = formatAvgDiffBadge(diffG, diffPctG, 'G', (t('prop_gravity') || '表面重力') + (t('avg_label_general') || '平均'), gravBodies.length);
      gravEl.className = diffG > 0 ? 'prop-val val-above-avg' : (diffG < 0 ? 'prop-val val-below-avg' : 'prop-val');
    } else {
      gravEl.className = 'prop-val';
    }

    // High-G warning only for landable bodies
    if (b.landable) {
      if (gVal >= 3.0) {
        gravEl.className = 'prop-val danger';
        baseText += ` ${t('extreme_danger')}`;
      } else if (gVal >= 1.5) {
        gravEl.className = 'prop-val warning';
        baseText += ` ${t('high_g_warn')}`;
      }
    }

    gravEl.innerHTML = `${baseText} ${diffBadge}`;
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

    const targetAvgRadius = b.landable ? (avgLandableRadius || avgSystemRadius) : avgSystemRadius;
    const avgLabel = b.landable ? t('avg_landable_size_label') : (t('avg_label_general') || '平均');
    const benchmarkCount = b.landable ? landableSysBodies.length : allRadBodies.length;

    let radDiffBadge = '';
    let diamDiffBadge = '';
    if (targetAvgRadius && benchmarkCount > 1) {
      const diffM = b.radius - targetAvgRadius;
      const diffKm = diffM / 1000;
      const diffPct = (diffM / targetAvgRadius) * 100;
      radDiffBadge = formatAvgDiffBadge(diffKm, diffPct, 'km', avgLabel, benchmarkCount);
      diamDiffBadge = formatAvgDiffBadge(diffKm * 2, diffPct, 'km', avgLabel, benchmarkCount);

      if (radiusEl) {
        radiusEl.className = diffM > 0 ? 'prop-val val-above-avg' : (diffM < 0 ? 'prop-val val-below-avg' : 'prop-val');
      }
      if (diamEl) {
        diamEl.className = diffM > 0 ? 'prop-val val-above-avg' : (diffM < 0 ? 'prop-val val-below-avg' : 'prop-val');
      }
    } else {
      if (radiusEl) radiusEl.className = 'prop-val';
      if (diamEl) diamEl.className = 'prop-val';
    }

    if (radiusEl) radiusEl.innerHTML = `${radKm.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})} km ${radDiffBadge}`;
    if (diamEl) diamEl.innerHTML = `${diamKm.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})} km ${diamDiffBadge}`;
  } else {
    if (radiusEl) { radiusEl.innerText = '--'; radiusEl.className = 'prop-val'; }
    if (diamEl) { diamEl.innerText = '--'; diamEl.className = 'prop-val'; }
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
    if (!rawAtmo || rawAtmo === 'None') return t('atmo_none') || 'None (なし)';
    const lang = (typeof getAppLang === 'function' ? getAppLang() : (typeof currentLang !== 'undefined' ? currentLang : 'ja'));
    if (lang === 'en') {
      return rawAtmo;
    }
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

  const tempEl = document.getElementById('prop-temperature');
  if (b.surface_temperature !== null && b.surface_temperature !== undefined && b.surface_temperature > 0) {
    let baseTempText = `${b.surface_temperature.toFixed(0)} K (${(b.surface_temperature - 273.15).toFixed(0)} °C)`;
    let tempDiffBadge = '';
    if (avgTemp !== null && tempBodies.length > 1) {
      const diffK = b.surface_temperature - avgTemp;
      const diffPctK = (diffK / avgTemp) * 100;
      tempDiffBadge = formatAvgDiffBadge(diffK, diffPctK, 'K', t('avg_label_temp') || '平均温度', tempBodies.length);
      tempEl.className = diffK > 0 ? 'prop-val val-above-avg' : (diffK < 0 ? 'prop-val val-below-avg' : 'prop-val');
    } else {
      tempEl.className = 'prop-val';
    }
    tempEl.innerHTML = `${baseTempText} ${tempDiffBadge}`;
  } else {
    tempEl.innerText = '--';
    tempEl.className = 'prop-val';
  }

  const pressEl = document.getElementById('prop-pressure');
  let basePressText = formatSurfacePressure(b.surface_pressure);
  let pressDiffBadge = '';
  if (b.surface_pressure !== null && b.surface_pressure !== undefined && avgPress !== null && pressBodies.length > 1) {
    const diffPress = b.surface_pressure - avgPress;
    const diffPctPress = (diffPress / avgPress) * 100;
    pressDiffBadge = formatAvgDiffBadge(diffPress, diffPctPress, 'atm', t('avg_label_press') || '平均気圧', pressBodies.length);
    pressEl.className = diffPress > 0 ? 'prop-val val-above-avg' : (diffPress < 0 ? 'prop-val val-below-avg' : 'prop-val');
  } else {
    pressEl.className = 'prop-val';
  }
  pressEl.innerHTML = `${basePressText} ${pressDiffBadge}`;

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
  const isLandable = Boolean(b.landable);
  const isRhinoEnabled = modSettings.rhino !== false;

  if (isRhinoEnabled && (isLandable || miningSigCount > 0 || miningSites.length > 0)) {
    if (miningSec) miningSec.style.display = 'block';
    const signalsInfoEl = document.getElementById('inspect-mining-signals-info');
    if (signalsInfoEl) {
      if (miningSigCount > 0) {
        signalsInfoEl.style.display = 'flex';
        if (miningCountEl) miningCountEl.innerText = miningSigCount;
      } else {
        signalsInfoEl.style.display = 'none';
      }
    }
    if (propCardMining) {
      propCardMining.style.display = miningSigCount > 0 ? 'block' : 'none';
      if (propMining) propMining.innerText = t('mining_locations_unit').replace('{count}', miningSigCount);
    }

    if (miningActivitiesEl) {
      // Build SVG markers for sites with coordinates
      const markersSvg = miningSites.map((site, idx) => {
        if (site.latitude === null || site.longitude === null) return '';
        const cx = Number(site.longitude);
        const cy = -Number(site.latitude);
        const commNames = (site.commodities || []).join(', ') || (site.minerals || (t('mining_subfilter_pml') || '採掘地点'));
        const latFmt = (site.latitude >= 0 ? '+' : '') + Number(site.latitude).toFixed(4);
        const lonFmt = (site.longitude >= 0 ? '+' : '') + Number(site.longitude).toFixed(4);
        const markerTitle = `${site.hotspot ? `[Hotspot: ${site.hotspot}] ` : ''}${commNames} (Lat: ${latFmt}°, Lon: ${lonFmt}°)`;
        return `
          <g class="mining-map-marker" data-site-idx="${idx}" style="cursor: pointer;">
            <circle cx="${cx}" cy="${cy}" r="6" fill="none" stroke="#38bdf8" stroke-width="1.2" class="pulse-marker" />
            <circle cx="${cx}" cy="${cy}" r="3" fill="#38bdf8" stroke="#ffffff" stroke-width="0.8" />
            <title>${escapeHtml(markerTitle)}</title>
          </g>
        `;
      }).join('');

      const hasAnyCoords = miningSites.some(s => s.latitude !== null && s.longitude !== null && !isNaN(Number(s.latitude)));

      const mapHtml = hasAnyCoords ? `
        <div class="mining-map-container" style="background: radial-gradient(circle at center, #0e1b2e 0%, #060913 100%); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 6px; padding: 8px; position: relative; margin-top: 6px; box-shadow: inset 0 0 16px rgba(0,0,0,0.6);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 0.72rem;">
            <span style="color: #38bdf8; font-weight: bold; display: flex; align-items: center; gap: 4px;">
              <span>🌐</span> <span>${t('mining_coord_map_title')}</span>
            </span>
            <span style="color: var(--text-dim); font-family: var(--font-mono); font-size: 0.68rem;">${t('mining_recorded_sites_count').replace('{count}', miningSites.length)}</span>
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
              <text x="-176" y="-3" fill="#38bdf8" font-size="6.5" font-family="sans-serif" opacity="0.8">${t('mining_equator')}</text>
              <text x="2" y="-76" fill="#38bdf8" font-size="6.5" font-family="sans-serif" opacity="0.8">${t('mining_meridian')}</text>
              <text x="-176" y="12" fill="#64748b" font-size="6.5" font-family="sans-serif">-180°</text>
              <text x="154" y="12" fill="#64748b" font-size="6.5" font-family="sans-serif">+180°</text>
              <!-- Markers -->
              ${markersSvg}
            </svg>
          </div>
          <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.62rem; color: var(--text-dim);">
            <span>${t('mining_west_hemi')}</span>
            <span>${t('mining_center_hemi')}</span>
            <span>${t('mining_east_hemi')}</span>
          </div>
        </div>
      ` : '';

      let cardsHtml = '';
      if (miningSites.length === 0) {
        cardsHtml = `
          <div style="background: rgba(15, 23, 42, 0.4); border: 1px dashed rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 12px; text-align: center; color: var(--text-dim); font-size: 0.75rem; margin-top: 8px;">
            ${t('mining_no_sites_body')}
          </div>
        `;
      } else {
        cardsHtml = `
          <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 8px;">
            ${miningSites.map((site, idx) => {
              const hasCoord = site.latitude !== null && site.longitude !== null && !isNaN(Number(site.latitude));
              const latNum = Number(site.latitude);
              const lonNum = Number(site.longitude);
              const latStr = hasCoord ? `${latNum >= 0 ? '+' : ''}${latNum.toFixed(4)}°` : '--';
              const lonStr = hasCoord ? `${lonNum >= 0 ? '+' : ''}${lonNum.toFixed(4)}°` : '--';
              const rawCoords = hasCoord ? `${latNum.toFixed(4)}, ${lonNum.toFixed(4)}` : '';
              
              const mineralsList = (site.commodities && site.commodities.length > 0)
                ? site.commodities
                : ((site.minerals || '').split(',').map(s => s.trim()).filter(Boolean));
              const mineralsStr = mineralsList.join(', ');
              
              // Standard 4-line Rhino Sharing Format:
              // Body Name
              // Hotspot Name
              // Minerals / Note description
              // Location : Lat / Lon
              const bodyName = b.body_name || site.body_name || 'Planet';
              const hotspotLine = site.hotspot || 'Hotspot';
              const descLine = [mineralsStr, site.note].filter(Boolean).join(' ') || 'Mining Site';
              const locLine = hasCoord 
                ? `Location : ${latNum.toFixed(4)} / ${lonNum.toFixed(4)}`
                : 'Location : -- / --';
              const copyText = `${bodyName}\n${hotspotLine}\n${descLine}\n${locLine}`;

              const mineralBadges = mineralsList.map(m => `
                <span class="tag-badge" style="background: rgba(56, 189, 248, 0.15); color: #e0f2fe; border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.72rem; padding: 2px 6px; font-weight: bold;">
                  💎 ${escapeHtml(m)}
                </span>
              `).join('');

              const lastTime = (site.updated_at || site.last_mined || '') ? (site.updated_at || site.last_mined).replace('T', ' ').replace('Z', '').substring(0, 19) : '';

              return `
                <div class="mining-site-card" id="mining-site-card-${idx}" style="background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 8px 10px; transition: all 0.2s;">
                  <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px; margin-bottom: 5px;">
                    <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                      <span style="color: var(--ed-orange); font-size: 0.85rem;">📍</span>
                      <span style="font-family: var(--font-mono); font-size: 0.78rem; font-weight: bold; color: #fff;">
                        ${hasCoord ? `Location : ${latNum.toFixed(4)} / ${lonNum.toFixed(4)}` : `<span style="color: var(--text-dim);">${t('mining_no_coord')}</span>`}
                      </span>
                      ${site.hotspot ? `
                        <span class="tag-badge" style="background: rgba(234, 88, 12, 0.2); color: #fb923c; border: 1px solid rgba(234, 88, 12, 0.45); font-size: 0.7rem; padding: 2px 6px; font-weight: bold;" title="${t('mining_pml_near_tip')}">
                          🎯 ${escapeHtml(site.hotspot)}
                        </span>
                      ` : ''}
                    </div>
                    <div style="display: flex; gap: 4px; align-items: center;">
                      <button type="button" class="view-btn btn-copy-mining-site" data-copy-text="${encodeURIComponent(copyText)}" data-coords="${rawCoords}" style="padding: 2px 7px; font-size: 0.68rem; background: rgba(56, 189, 248, 0.15); border-color: rgba(56, 189, 248, 0.4); color: #38bdf8; cursor: pointer;" title="${t('mining_copy_site_tip')}">
                        ${t('mining_btn_copy')}
                      </button>
                      <button type="button" class="view-btn btn-edit-mining-site" data-site-idx="${idx}" style="padding: 2px 7px; font-size: 0.68rem; background: rgba(147, 197, 253, 0.15); border-color: rgba(147, 197, 253, 0.4); color: #93c5fd; cursor: pointer;" title="${t('mining_edit_site_tip')}">
                        ${t('mining_btn_edit')}
                      </button>
                      ${site.id ? `
                        <button type="button" class="view-btn btn-delete-mining-site" data-site-id="${site.id}" style="padding: 2px 7px; font-size: 0.68rem; background: rgba(248, 113, 113, 0.15); border-color: rgba(248, 113, 113, 0.4); color: #f87171; cursor: pointer;" title="${t('mining_delete_site_tip')}">
                          ${t('mining_btn_delete')}
                        </button>
                      ` : ''}
                    </div>
                  </div>
                  <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px;">
                    <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                      ${mineralBadges || `<span style="color: var(--text-dim); font-size: 0.7rem;">${t('mining_no_minerals')}</span>`}
                    </div>
                    ${lastTime ? `
                      <span style="font-size: 0.65rem; color: var(--text-dim); font-family: var(--font-mono);">
                        🕒 ${lastTime}
                      </span>
                    ` : ''}
                  </div>
                  ${site.note ? `
                    <div style="margin-top: 5px; font-size: 0.72rem; color: #cbd5e1; background: rgba(0,0,0,0.25); border-radius: 4px; padding: 3px 6px;">
                      📝 <span style="color: #94a3b8;">${t('mining_note_label')}</span> ${escapeHtml(site.note)}
                    </div>
                  ` : ''}
                </div>
              `;
            }).join('')}
          </div>
        `;
      }

      miningActivitiesEl.innerHTML = `
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 10px; margin-top: 6px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 0.78rem; font-weight: bold; color: #38bdf8; display: flex; align-items: center; gap: 4px;">
              <span>🦏</span> <span>${t('mining_rhino_panel_title')}</span>
            </span>
            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
              <span style="font-size: 0.7rem; color: var(--text-dim); font-family: var(--font-mono);">${t('mining_recorded_sites_count').replace('{count}', miningSites.length)}</span>
              ${miningSites.length > 0 ? `
                <button type="button" id="btn-copy-all-mining-sites" class="view-btn" style="padding: 2px 8px; font-size: 0.68rem; background: rgba(56, 189, 248, 0.15); border-color: rgba(56, 189, 248, 0.4); color: #38bdf8; cursor: pointer;" title="${t('mining_copy_all_tip')}">
                  ${t('mining_copy_all_btn')}
                </button>
              ` : ''}
              <button type="button" id="btn-add-mining-site" class="view-btn" style="padding: 2px 8px; font-size: 0.68rem; background: rgba(56, 189, 248, 0.2); border-color: #38bdf8; color: #38bdf8; cursor: pointer; font-weight: bold;" title="${t('mining_add_site_tip')}">
                ${t('mining_add_site_btn')}
              </button>
            </div>
          </div>
          ${mapHtml}
          ${cardsHtml}
        </div>
      `;

      // Event: Add new mining site
      const btnAdd = document.getElementById('btn-add-mining-site');
      if (btnAdd) {
        btnAdd.addEventListener('click', (e) => {
          e.stopPropagation();
          openMiningSiteModal({ isNew: true, body: b });
        });
      }

      // Event: Copy all mining sites for this body in 4-line format
      const btnCopyAll = document.getElementById('btn-copy-all-mining-sites');
      if (btnCopyAll) {
        btnCopyAll.addEventListener('click', (e) => {
          e.stopPropagation();
          const allText = miningSites.map(st => {
            const hCoord = st.latitude !== null && st.longitude !== null && !isNaN(Number(st.latitude));
            const lNum = Number(st.latitude);
            const loNum = Number(st.longitude);
            const mList = (st.commodities && st.commodities.length > 0) ? st.commodities : ((st.minerals || '').split(',').map(s => s.trim()).filter(Boolean));
            const mStr = mList.join(', ');
            const hLine = st.hotspot || 'Hotspot';
            const dLine = [mStr, st.note].filter(Boolean).join(' ') || 'Mining Site';
            const lcLine = hCoord ? `Location : ${lNum.toFixed(4)} / ${loNum.toFixed(4)}` : 'Location : -- / --';
            return `${b.body_name || 'Planet'}\n${hLine}\n${dLine}\n${lcLine}`;
          }).join('\n\n');

          if (allText && navigator.clipboard) {
            navigator.clipboard.writeText(allText).then(() => {
              const orig = btnCopyAll.innerHTML;
              btnCopyAll.innerHTML = t('mining_copy_all_copied');
              btnCopyAll.style.color = '#38bdf8';
              btnCopyAll.style.borderColor = '#38bdf8';
              setTimeout(() => {
                btnCopyAll.innerHTML = orig;
                btnCopyAll.style.color = '';
                btnCopyAll.style.borderColor = '';
              }, 1800);
            });
          }
        });
      }

      // Event: Copy mining site info
      miningActivitiesEl.querySelectorAll('.btn-copy-mining-site').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const text = decodeURIComponent(btn.dataset.copyText || '');
          if (text && navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
              const orig = btn.innerHTML;
              btn.innerHTML = t('mining_btn_copied');
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

      // Event: Edit mining site
      miningActivitiesEl.querySelectorAll('.btn-edit-mining-site').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const sIdx = parseInt(btn.dataset.siteIdx, 10);
          const site = miningSites[sIdx];
          if (site) {
            openMiningSiteModal({ isNew: false, body: b, site: site });
          }
        });
      });

      // Event: Delete mining site
      miningActivitiesEl.querySelectorAll('.btn-delete-mining-site').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const siteId = btn.dataset.siteId;
          if (!siteId) return;
          if (!confirm(t('mining_delete_confirm_msg'))) return;
          btn.disabled = true;
          btn.innerHTML = t('mining_btn_deleting');
          try {
            const res = await fetch(`/api/mining_sites/${siteId}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            await refreshMiningSitesForBody(b);
          } catch (err) {
            console.error('Failed to delete mining site:', err);
            alert(t('mining_delete_failed') + (err.message || 'Error'));
            btn.disabled = false;
            btn.innerHTML = t('mining_btn_delete');
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
    }
  } else {
    if (miningSec) miningSec.style.display = 'none';
    if (propCardMining) propCardMining.style.display = 'none';
  }

  // Stations & Settlements section
  const stationsSec = document.getElementById('section-stations');
  const stationsListEl = document.getElementById('inspect-stations-list');
  const bodyStations = b.stations || (state.currentSystemData && state.currentSystemData.stations ? state.currentSystemData.stations.filter(st => {
    return (st.body_name && st.body_name === b.body_name) || (st.body_id !== undefined && st.body_id !== null && st.body_id === b.body_id);
  }) : []);

  if (stationsSec && stationsListEl) {
    if (bodyStations && bodyStations.length > 0) {
      stationsSec.style.display = 'block';
      stationsListEl.innerHTML = bodyStations.map((st) => {
        const isPlanetary = st.is_planetary || (st.latitude !== null && st.latitude !== undefined);
        const icon = isPlanetary ? '🏢' : '🛰️';
        const typeStr = st.station_type || (isPlanetary ? 'Planetary Base' : 'Starport');
        const distStr = (st.distance_to_arrival_ls !== null && st.distance_to_arrival_ls !== undefined)
          ? `${Math.round(st.distance_to_arrival_ls).toLocaleString()} Ls`
          : '-- Ls';

        let locStr = '';
        let copyCoordBtn = '';
        if (st.latitude !== null && st.latitude !== undefined && st.longitude !== null && st.longitude !== undefined) {
          const latNum = Number(st.latitude).toFixed(4);
          const lonNum = Number(st.longitude).toFixed(4);
          locStr = `<div style="font-family: var(--font-mono); font-size: 0.72rem; color: #a5f3fc; margin-top: 2px;">📍 Location : ${latNum} / ${lonNum}</div>`;
          copyCoordBtn = `
            <button type="button" class="btn-copy-station-coord view-btn" style="padding: 1px 6px; font-size: 0.65rem;" data-coord="${latNum} / ${lonNum}" title="${t('station_copy_coord_tip') || '地表座標をコピー'}">
              ${t('station_btn_copy_coord') || '📋 座標コピー'}
            </button>
          `;
        }

        const facStr = st.controlling_faction ? `<span style="color: #cbd5e1;">${escapeHtml(st.controlling_faction)}</span>` : '';
        const econStr = st.economy ? `<span class="tag-badge" style="font-size: 0.65rem; background: rgba(255,255,255,0.06);">${escapeHtml(st.economy)}</span>` : '';

        return `
          <div class="inspector-station-card" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; padding: 6px 8px;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 4px;">
              <div style="display: flex; align-items: center; gap: 6px; min-width: 0;">
                <span style="font-size: 0.95rem;">${icon}</span>
                <span style="font-weight: bold; font-size: 0.82rem; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(st.station_name)}</span>
                <span class="tag-badge" style="font-size: 0.65rem; background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);">${escapeHtml(typeStr)}</span>
              </div>
              <div style="display: flex; align-items: center; gap: 4px;">
                <span style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-dim);">${distStr}</span>
                ${copyCoordBtn}
              </div>
            </div>
            ${locStr}
            <div style="display: flex; align-items: center; gap: 6px; font-size: 0.68rem; margin-top: 3px;">
              ${facStr}
              ${econStr}
            </div>
          </div>
        `;
      }).join('');

      // Bind copy coord buttons
      stationsListEl.querySelectorAll('.btn-copy-station-coord').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const coord = btn.dataset.coord;
          if (coord && navigator.clipboard) {
            navigator.clipboard.writeText(coord).then(() => {
              const orig = btn.innerHTML;
              btn.innerHTML = t('station_coord_copied') || '✓ コピー済';
              btn.style.color = '#38bdf8';
              setTimeout(() => {
                btn.innerHTML = orig;
                btn.style.color = '';
              }, 1500);
            });
          }
        });
      });
    } else {
      stationsSec.style.display = 'none';
      stationsListEl.innerHTML = '';
    }
  }

  // Orbit parameters
  const smaEl = document.getElementById('prop-semi-major');
  if (b.semi_major_axis) {
    const baseSmaText = `${(b.semi_major_axis / 149597870700).toFixed(3)} AU (${formatDistance(b.semi_major_axis / 299792458)})`;
    let smaDiffBadge = '';
    if (avgSma !== null && smaBodies.length > 1) {
      const diffSma = b.semi_major_axis - avgSma;
      const diffPctSma = (diffSma / avgSma) * 100;
      const diffLs = diffSma / 299792458;
      smaDiffBadge = formatAvgDiffBadge(diffLs, diffPctSma, 'ls', t('avg_label_sma') || '平均軌道長半径', smaBodies.length);
      smaEl.className = diffSma > 0 ? 'prop-val val-above-avg' : (diffSma < 0 ? 'prop-val val-below-avg' : 'prop-val');
    } else {
      smaEl.className = 'prop-val';
    }
    smaEl.innerHTML = `${baseSmaText} ${smaDiffBadge}`;
  } else {
    smaEl.innerText = '--';
    smaEl.className = 'prop-val';
  }
  
  const eccEl = document.getElementById('prop-eccentricity');
  if (b.eccentricity !== null && b.eccentricity !== undefined) {
    const baseEccText = b.eccentricity.toFixed(4);
    let eccDiffBadge = '';
    if (avgEcc !== null && eccBodies.length > 1) {
      const diffEcc = b.eccentricity - avgEcc;
      eccDiffBadge = formatAvgDiffBadge(diffEcc, null, '', t('avg_label_ecc') || '平均離心率', eccBodies.length);
      if (b.eccentricity >= 0.8) {
        eccEl.className = 'prop-val warning';
      } else {
        eccEl.className = diffEcc > 0 ? 'prop-val val-above-avg' : (diffEcc < 0 ? 'prop-val val-below-avg' : 'prop-val');
      }
    } else {
      eccEl.className = b.eccentricity >= 0.8 ? 'prop-val warning' : 'prop-val';
    }
    eccEl.innerHTML = `${baseEccText} ${eccDiffBadge}`;
  } else {
    eccEl.innerText = '--';
    eccEl.className = 'prop-val';
  }

  const orbEl = document.getElementById('prop-orbital-period');
  if (b.orbital_period) {
    const baseOrbText = formatSecondsToDaysOrHours(b.orbital_period);
    let orbDiffBadge = '';
    if (avgOrb !== null && orbBodies.length > 1) {
      const diffOrb = b.orbital_period - avgOrb;
      const diffPctOrb = (diffOrb / avgOrb) * 100;
      orbDiffBadge = formatAvgDiffBadge(diffOrb / 86400, diffPctOrb, t('days_unit'), t('avg_label_orb') || '平均公転周期', orbBodies.length);
      orbEl.className = diffOrb > 0 ? 'prop-val val-above-avg' : (diffOrb < 0 ? 'prop-val val-below-avg' : 'prop-val');
    } else {
      orbEl.className = 'prop-val';
    }
    orbEl.innerHTML = `${baseOrbText} ${orbDiffBadge}`;
  } else {
    orbEl.innerText = '--';
    orbEl.className = 'prop-val';
  }

  const rotEl = document.getElementById('prop-rotation-period');
  if (b.rotation_period) {
    const baseRotText = formatSecondsToDaysOrHours(b.rotation_period);
    let rotDiffBadge = '';
    if (avgRot !== null && rotBodies.length > 1) {
      const diffRot = b.rotation_period - avgRot;
      const diffPctRot = (diffRot / avgRot) * 100;
      rotDiffBadge = formatAvgDiffBadge(diffRot / 86400, diffPctRot, t('days_unit'), t('avg_label_rot') || '平均自転周期', rotBodies.length);
      rotEl.className = diffRot > 0 ? 'prop-val val-above-avg' : (diffRot < 0 ? 'prop-val val-below-avg' : 'prop-val');
    } else {
      rotEl.className = 'prop-val';
    }
    rotEl.innerHTML = `${baseRotText} ${rotDiffBadge}`;
  } else {
    rotEl.innerText = '--';
    rotEl.className = 'prop-val';
  }

  const incEl = document.getElementById('prop-inclination');
  if (b.orbital_inclination !== null && b.orbital_inclination !== undefined) {
    const baseIncText = `${b.orbital_inclination.toFixed(2)}°`;
    let incDiffBadge = '';
    if (avgInc !== null && incBodies.length > 1) {
      const diffInc = b.orbital_inclination - avgInc;
      incDiffBadge = formatAvgDiffBadge(diffInc, null, '°', t('avg_label_inc') || '平均軌道傾斜角', incBodies.length);
      incEl.className = diffInc > 0 ? 'prop-val val-above-avg' : (diffInc < 0 ? 'prop-val val-below-avg' : 'prop-val');
    } else {
      incEl.className = 'prop-val';
    }
    incEl.innerHTML = `${baseIncText} ${incDiffBadge}`;
  } else {
    incEl.innerText = '--';
    incEl.className = 'prop-val';
  }

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
          <span>${reserveInfo.icon}</span> <span>${t('reserve_level_badge_label') || '資源埋蔵量 (Reserve Level):'}</span>
        </span>
        <span style="color: ${reserveInfo.color}; font-weight: bold;">${reserveInfo.label || reserveInfo.name}</span>
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

      const lang = (typeof getAppLang === 'function' ? getAppLang() : (typeof currentLang !== 'undefined' ? currentLang : 'ja'));
      const ringLabel = lang === 'en' ? `${rInfo.nameEn} ${isBelt ? 'Belt' : 'Ring'}` : `${rInfo.nameJa} (${rInfo.nameEn} ${isBelt ? 'Belt' : 'Ring'})`;

      const typeBadge = `<span class="tag-badge" style="background: ${rInfo.bg}; color: ${rInfo.color}; border: 1px solid ${rInfo.border}; font-weight: bold; font-size: 0.72rem;">
        ${rInfo.icon} ${ringLabel}
      </span>`;

      let miningHint = '';
      if (rInfo.key === 'icy') {
        miningHint = `<div style="margin-top: 5px; font-size: 0.72rem; color: #7dd3fc; background: rgba(56, 189, 248, 0.1); border-left: 3px solid #38bdf8; padding: 3px 6px; border-radius: 2px;">
          ${t('ring_hint_icy')}
        </div>`;
      } else if (rInfo.key === 'metallic') {
        miningHint = `<div style="margin-top: 5px; font-size: 0.72rem; color: #fde047; background: rgba(250, 204, 21, 0.1); border-left: 3px solid #facc15; padding: 3px 6px; border-radius: 2px;">
          ${t('ring_hint_metallic_full')}
        </div>`;
      } else if (rInfo.key === 'rocky') {
        miningHint = `<div style="margin-top: 5px; font-size: 0.72rem; color: #e2e8f0; background: rgba(203, 213, 225, 0.1); border-left: 3px solid #cbd5e1; padding: 3px 6px; border-radius: 2px;">
          ${t('ring_hint_rocky_full')}
        </div>`;
      } else if (rInfo.key === 'metal_rich') {
        miningHint = `<div style="margin-top: 5px; font-size: 0.72rem; color: #fdba74; background: rgba(251, 146, 60, 0.1); border-left: 3px solid #fb923c; padding: 3px 6px; border-radius: 2px;">
          ${t('ring_hint_metal_rich_full')}
        </div>`;
      }

      // Check DSS Hotspots on this ring
      const hotspots = r.Hotspots || {};
      if (Object.keys(hotspots).length === 0 && Array.isArray(r.signals)) {
        r.signals.forEach(s => {
          if (s && s.name) hotspots[s.name] = (hotspots[s.name] || 0) + (s.count || 1);
        });
      }

      let hotspotsHtml = '';
      if (Object.keys(hotspots).length > 0) {
        const hsBadges = Object.entries(hotspots).map(([mineral, count]) => {
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

        hotspotsHtml = `
          <div style="margin-top: 6px; padding: 5px 8px; background: rgba(250, 204, 21, 0.08); border: 1px solid rgba(250, 204, 21, 0.3); border-radius: 4px;">
            <div style="font-size: 0.72rem; font-weight: bold; color: #facc15; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
              <span>${t('ring_dss_hotspots_title')}</span>
              ${r.signals_updated_at ? `<span style="font-size: 0.65rem; color: var(--text-dim); font-weight: normal;">${t('ring_recorded_date').replace('{date}', r.signals_updated_at.split('T')[0])}</span>` : ''}
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 4px;">
              ${hsBadges}
            </div>
          </div>
        `;
      }

      return `
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 5px; padding: 8px 10px; margin-bottom: 6px;">
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 6px; flex-wrap: wrap;">
            <span style="font-weight: bold; color: var(--ed-gold); font-size: 0.8rem;">${r.Name || (isBelt ? 'Asteroid Belt' : 'Ring')}</span>
            ${typeBadge}
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 6px; font-size: 0.72rem; color: var(--text-secondary); background: rgba(0,0,0,0.25); padding: 5px 8px; border-radius: 4px;">
            <span>${t('ring_inner_rad_val') || '内径:'} <b style="color: #e2e8f0;">${innerKm.toLocaleString()} km</b></span>
            <span>${t('ring_outer_rad_val') || '外径:'} <b style="color: #e2e8f0;">${outerKm.toLocaleString()} km</b></span>
            <span>${t('ring_width_val') || '幅:'} <b style="color: #e2e8f0;">${widthKm.toLocaleString()} km</b></span>
            <span>${t('ring_total_mass_val') || '総質量:'} <b style="color: #e2e8f0;">${massStr}</b></span>
          </div>
          ${hotspotsHtml}
          ${miningHint}
        </div>
      `;
    }).join('');

    ringsList.innerHTML = reserveBadge + itemsHtml;
  } else {
    ringsSection.style.display = 'none';
  }
}


// Window / Global Export
if (typeof window !== 'undefined') {
  window.clearBodyInspector = clearBodyInspector;
  window.renderBodyInspector = renderBodyInspector;
}
