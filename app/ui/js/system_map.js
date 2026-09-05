/**
 * Elite Dangerous Official System Map View Renderer
 * Accurately parses Body Designation & Journal Parents Hierarchy:
 * - Sorts Planets strictly by Planet Index (1, 2, 3... / A 1, A 2... / B 1, B 2...)
 * - Sorts Moons strictly by Moon Letter (a, b, c, d, e, f, g...)
 * - Correctly parents moons like '1 e', '1 f' under Planet 1.
 */

function getBodyShortName(fullName, systemName) {
  if (!fullName) return '';
  const sys = systemName || (state.selectedSystem ? state.selectedSystem.star_system : '');
  if (!sys) return fullName;

  let short = fullName.trim();
  if (short.startsWith(sys)) {
    short = short.substring(sys.length).trim();
  }
  return short || fullName;
}

function parseParentsList(parentsRaw) {
  if (!parentsRaw) return [];
  if (Array.isArray(parentsRaw)) return parentsRaw;
  try {
    const parsed = JSON.parse(parentsRaw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    return [];
  }
}

/**
 * Parses body name tokens to extract Star, Planet Number, and Moon Letters.
 * Examples:
 * - "A" -> { star: "A", planet: null, moon: null, submoon: null, rank: 0 }
 * - "1" -> { star: "A", planet: 1, moon: null, submoon: null, rank: 1 }
 * - "1 e" -> { star: "A", planet: 1, moon: "e", submoon: null, rank: 2 }
 * - "1 a a" -> { star: "A", planet: 1, moon: "a", submoon: "a", rank: 3 }
 * - "B 4" -> { star: "B", planet: 4, moon: null, submoon: null, rank: 1 }
 * - "B 4 a" -> { star: "B", planet: 4, moon: "a", submoon: null, rank: 2 }
 * - "AB 1" -> { star: "AB", planet: 1, moon: null, submoon: null, rank: 1 }
 */
function analyzeBodyDesignation(bodyName, systemName, isStar) {
  const short = getBodyShortName(bodyName, systemName).trim();
  const tokens = short.split(/\s+/).filter(Boolean);

  if (isStar || tokens.length === 0) {
    return {
      shortName: short || 'Star',
      starGroup: tokens[0] || 'A',
      isStar: true,
      planetNum: null,
      moonLetter: null,
      submoonLetter: null,
      level: 0 // 0: Star, 1: Planet, 2: Moon, 3: Submoon
    };
  }

  let starGroup = 'A';
  let planetNum = null;
  let moonLetter = null;
  let submoonLetter = null;
  let level = 1;

  let idx = 0;
  // Check if first token is a Star / Barycentre letter (A, B, C, AB, CD etc.)
  if (/^[A-Z]{1,3}$/.test(tokens[0])) {
    starGroup = tokens[0];
    idx = 1;
  }

  // Next token should be Planet number (1, 2, 3...) or Moon letter
  if (idx < tokens.length) {
    const tok = tokens[idx];
    const numMatch = tok.match(/^(\d+)$/);
    if (numMatch) {
      planetNum = parseInt(numMatch[1], 10);
      idx++;
      level = 1;

      // Next token: Moon letter (a, b, c...)
      if (idx < tokens.length && /^[a-z]$/i.test(tokens[idx])) {
        moonLetter = tokens[idx].toLowerCase();
        idx++;
        level = 2;

        // Next token: Submoon letter (a, b, c...)
        if (idx < tokens.length && /^[a-z]$/i.test(tokens[idx])) {
          submoonLetter = tokens[idx].toLowerCase();
          level = 3;
        }
      }
    } else if (/^[a-z]$/i.test(tok)) {
      // Direct moon letter without number (rare)
      moonLetter = tok.toLowerCase();
      level = 2;
    }
  }

  return {
    shortName: short,
    starGroup: starGroup,
    isStar: false,
    planetNum: planetNum,
    moonLetter: moonLetter,
    submoonLetter: submoonLetter,
    level: level
  };
}

/**
 * Builds a strict and reliable hierarchical tree from bodies:
 * Stars -> Planets (sorted 1, 2, 3...) -> Moons (sorted a, b, c...) -> Submoons
 */
function buildSystemMapTree(flatBodies, systemName) {
  if (!flatBodies || flatBodies.length === 0) return [];

  // 1. Tag and analyze each body
  const analyzedList = flatBodies.map(b => {
    const isStar = Boolean(b.star_type || (b.body_type && b.body_type.toLowerCase() === 'star'));
    const info = analyzeBodyDesignation(b.body_name, systemName, isStar);
    return {
      ...b,
      ...info,
      moons: [],
      submoons: []
    };
  });

  // 2. Collect Stars and Star Sections
  const starMap = new Map();
  const stars = analyzedList.filter(b => b.isStar);

  // If no explicit star found, use a fallback 'A' section
  if (stars.length === 0) {
    starMap.set('A', {
      starKey: 'A',
      rootStar: analyzedList[0],
      planets: []
    });
  } else {
    // Sort stars alphabetically (A, B, C...)
    stars.sort((a, b) => a.starGroup.localeCompare(b.starGroup));
    stars.forEach(s => {
      starMap.set(s.starGroup, {
        starKey: s.starGroup,
        rootStar: s,
        planets: []
      });
    });
  }

  // 3. Separate Planets, Moons, and Submoons
  const planets = analyzedList.filter(b => !b.isStar && b.level === 1);
  const moons = analyzedList.filter(b => !b.isStar && b.level === 2);
  const submoons = analyzedList.filter(b => !b.isStar && b.level === 3);

  // Planet Map keyed by `${starGroup}-${planetNum}` (e.g. "A-1", "A-2", "B-4")
  const planetKeyMap = new Map();

  planets.forEach(p => {
    const sGroup = starMap.has(p.starGroup) ? p.starGroup : (starMap.keys().next().value || 'A');
    const pNum = p.planetNum !== null ? p.planetNum : (p.distance_from_arrival_ls || 0);
    const key = `${sGroup}-${pNum}`;

    planetKeyMap.set(key, p);

    if (!starMap.has(sGroup)) {
      starMap.set(sGroup, {
        starKey: sGroup,
        rootStar: p,
        planets: []
      });
    }
    starMap.get(sGroup).planets.push(p);
  });

  // 4. Attach Moons to their respective Planets
  moons.forEach(m => {
    const sGroup = starMap.has(m.starGroup) ? m.starGroup : (starMap.keys().next().value || 'A');
    const key = `${sGroup}-${m.planetNum}`;

    if (planetKeyMap.has(key)) {
      planetKeyMap.get(key).moons.push(m);
    } else {
      // If parent planet not found in map (e.g. not yet scanned), create a placeholder planet node
      const placeholderPlanet = {
        body_id: `p-${key}`,
        body_name: `${systemName} ${sGroup} ${m.planetNum}`.trim(),
        shortName: `${sGroup !== 'A' ? sGroup + ' ' : ''}${m.planetNum}`,
        starGroup: sGroup,
        isStar: false,
        planetNum: m.planetNum,
        planet_class: 'Unscanned Planet',
        distance_from_arrival_ls: m.distance_from_arrival_ls,
        level: 1,
        moons: [m],
        submoons: []
      };
      planetKeyMap.set(key, placeholderPlanet);
      if (starMap.has(sGroup)) {
        starMap.get(sGroup).planets.push(placeholderPlanet);
      }
    }
  });

  // 5. Attach Submoons to their respective Moons
  submoons.forEach(sm => {
    const sGroup = sm.starGroup;
    const key = `${sGroup}-${sm.planetNum}`;
    if (planetKeyMap.has(key)) {
      const p = planetKeyMap.get(key);
      const parentMoon = p.moons.find(m => m.moonLetter === sm.moonLetter);
      if (parentMoon) {
        parentMoon.submoons.push(sm);
      } else {
        p.moons.push(sm);
      }
    }
  });

  // 6. Natural Sorting:
  // - Sort Planets by planetNum (1, 2, 3...) ascending
  // - Sort Moons by moonLetter ('a', 'b', 'c', 'd', 'e', 'f'...) ascending
  // - Sort Submoons by submoonLetter ('a', 'b', 'c'...) ascending
  const starSections = Array.from(starMap.values());

  starSections.forEach(sec => {
    sec.planets.sort((a, b) => {
      if (a.planetNum !== null && b.planetNum !== null) {
        return a.planetNum - b.planetNum;
      }
      return (a.distance_from_arrival_ls || 0) - (b.distance_from_arrival_ls || 0);
    });

    sec.planets.forEach(p => {
      p.moons.sort((a, b) => {
        if (a.moonLetter && b.moonLetter) {
          return a.moonLetter.localeCompare(b.moonLetter);
        }
        return (a.distance_from_arrival_ls || 0) - (b.distance_from_arrival_ls || 0);
      });

      p.moons.forEach(m => {
        m.submoons.sort((a, b) => {
          if (a.submoonLetter && b.submoonLetter) {
            return a.submoonLetter.localeCompare(b.submoonLetter);
          }
          return (a.distance_from_arrival_ls || 0) - (b.distance_from_arrival_ls || 0);
        });
      });
    });
  });

  return starSections;
}

function renderSystemMapView(container, hierarchyNodes, flatBodies) {
  container.innerHTML = '';

  if (!flatBodies || flatBodies.length === 0) {
    container.innerHTML = `<div style="color: var(--text-secondary); text-align: center; padding: 40px;">${t('no_bodies') || '天体データがありません'}</div>`;
    return;
  }

  const systemName = state.selectedSystem ? state.selectedSystem.star_system : '';
  const mapWrapper = document.createElement('div');
  mapWrapper.className = 'ed-system-map-container';

  // Build accurate hierarchy tree
  const starSections = buildSystemMapTree(flatBodies, systemName);

  starSections.forEach(section => {
    const starSectionEl = document.createElement('div');
    starSectionEl.className = 'sysmap-star-system-section';

    // Primary Star / Section Root
    const rootEl = createSysMapBodyElement(section.rootStar, 'root-star', systemName);
    starSectionEl.appendChild(rootEl);

    // Horizontal Rail of Planets (Strictly ordered 1, 2, 3, 4...)
    if (section.planets && section.planets.length > 0) {
      const planetsRail = document.createElement('div');
      planetsRail.className = 'sysmap-planets-rail';

      section.planets.forEach(planetNode => {
        const planetCol = document.createElement('div');
        planetCol.className = 'sysmap-planet-column';

        // Planet Body
        const pRole = planetNode.isStar ? 'root-star' : 'planet';
        const planetEl = createSysMapBodyElement(planetNode, pRole, systemName);
        planetCol.appendChild(planetEl);

        // Moons Branch descending vertically (Strictly ordered a, b, c, d, e, f...)
        if (planetNode.moons && planetNode.moons.length > 0) {
          const moonsBranch = document.createElement('div');
          moonsBranch.className = 'sysmap-moons-branch';

          planetNode.moons.forEach(moonNode => {
            const moonItem = document.createElement('div');
            moonItem.className = 'sysmap-moon-item';

            const moonEl = createSysMapBodyElement(moonNode, 'moon', systemName);
            moonItem.appendChild(moonEl);

            // Sub-moons Branch (nested)
            if (moonNode.submoons && moonNode.submoons.length > 0) {
              const subMoonsBranch = document.createElement('div');
              subMoonsBranch.className = 'sysmap-submoons-branch';
              moonNode.submoons.forEach(subMoonNode => {
                const subMoonEl = createSysMapBodyElement(subMoonNode, 'submoon', systemName);
                subMoonsBranch.appendChild(subMoonEl);
              });
              moonItem.appendChild(subMoonsBranch);
            }

            moonsBranch.appendChild(moonItem);
          });
          planetCol.appendChild(moonsBranch);
        }

        planetsRail.appendChild(planetCol);
      });

      starSectionEl.appendChild(planetsRail);
    }

    mapWrapper.appendChild(starSectionEl);
  });

  // Enable mouse left-click drag panning
  let isDown = false;
  let startX = 0;
  let startY = 0;
  let scrollLeft = 0;
  let scrollTop = 0;
  let hasDragged = false;

  mapWrapper.addEventListener('mousedown', (e) => {
    // Only primary (left) button
    if (e.button !== 0) return;
    isDown = true;
    hasDragged = false;
    mapWrapper.classList.add('is-dragging');
    startX = e.pageX - mapWrapper.offsetLeft;
    startY = e.pageY - mapWrapper.offsetTop;
    scrollLeft = mapWrapper.scrollLeft;
    scrollTop = mapWrapper.scrollTop;
  });

  mapWrapper.addEventListener('mouseleave', () => {
    if (isDown) {
      isDown = false;
      mapWrapper.classList.remove('is-dragging');
    }
  });

  window.addEventListener('mouseup', () => {
    if (isDown) {
      isDown = false;
      mapWrapper.classList.remove('is-dragging');
      // Reset hasDragged shortly after current event loop cycle so click handler can read it once
      setTimeout(() => {
        hasDragged = false;
      }, 50);
    }
  });

  mapWrapper.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    const x = e.pageX - mapWrapper.offsetLeft;
    const y = e.pageY - mapWrapper.offsetTop;
    const walkX = x - startX;
    const walkY = y - startY;
    if (Math.hypot(walkX, walkY) > 8) {
      hasDragged = true;
    }
    mapWrapper.scrollLeft = scrollLeft - walkX;
    mapWrapper.scrollTop = scrollTop - walkY;
  });

  mapWrapper._hasDragged = () => hasDragged;

  container.appendChild(mapWrapper);
}

function createSysMapBodyElement(body, role = 'planet', systemName = '') {
  const isSelected = state.selectedBody && state.selectedBody.body_id === body.body_id;
  const isTarget = state.targetBodyId !== null && body.body_id === state.targetBodyId;

  const card = document.createElement('div');
  card.className = `sysmap-body-node ${role} ${isSelected ? 'selected' : ''} ${isTarget ? 'target-pulse' : ''}`;
  card.dataset.bodyId = body.body_id;

  card.onclick = (e) => {
    e.stopPropagation();
    const mapWrapper = card.closest('.ed-system-map-container');
    if (mapWrapper && mapWrapper._hasDragged && mapWrapper._hasDragged()) {
      return; // Suppress click when user was dragging/panning
    }
    state.selectedBody = body;
    state.targetBodyId = body.body_id;
    try {
      renderBodyInspector();
    } catch (err) {
      console.error('Failed to render body inspector:', err);
    }
    document.querySelectorAll('.sysmap-body-node').forEach(n => n.classList.remove('selected'));
    card.classList.add('selected');
  };

  // Celestial sphere styling & glow
  const sphere = document.createElement('div');
  sphere.className = 'sysmap-sphere-wrapper';

  const iconLabel = getBodyIconLabel(body);
  const iconClass = getBodyIconClass(body);

  // Check planetary rings and asteroid belts
  let rawRings = body.rings_list;
  if (!rawRings && body.rings && body.rings !== '[]' && body.rings !== '""') {
    try {
      rawRings = typeof body.rings === 'string' ? JSON.parse(body.rings) : body.rings;
    } catch (e) {
      rawRings = [];
    }
  }
  rawRings = Array.isArray(rawRings) ? rawRings : [];

  const beltItems = rawRings.filter(r => (r.Name || '').toLowerCase().includes('belt'));
  const ringItems = rawRings.filter(r => !(r.Name || '').toLowerCase().includes('belt'));
  const hasPlanetaryRings = ringItems.length > 0;
  const hasAsteroidBelts = beltItems.length > 0;

  const ringParser = window.parseRingClass || ((cls) => {
    const l = (cls || '').toLowerCase();
    if (l.includes('icy')) return { key: 'icy', nameJa: '氷', icon: '❄️', color: '#38bdf8', bg: 'rgba(56,189,248,0.18)', border: 'rgba(56,189,248,0.45)' };
    if (l.includes('metallic') || l.includes('metalic')) return { key: 'metallic', nameJa: '金属質', icon: '🪙', color: '#facc15', bg: 'rgba(250,204,21,0.18)', border: 'rgba(250,204,21,0.5)' };
    if (l.includes('metal')) return { key: 'metal_rich', nameJa: '金属豊富', icon: '🪐', color: '#fb923c', bg: 'rgba(251,146,60,0.18)', border: 'rgba(251,146,60,0.5)' };
    if (l.includes('rocky')) return { key: 'rocky', nameJa: '岩石', icon: '🪨', color: '#cbd5e1', bg: 'rgba(203,213,225,0.18)', border: 'rgba(203,213,225,0.45)' };
    return { key: 'other', nameJa: cls || '環', icon: '💍', color: '#a78bfa', bg: 'rgba(167,139,250,0.18)', border: 'rgba(167,139,250,0.45)' };
  });

  // Check Landable (Blue crescent arc in ED)
  const isLandable = Boolean(body.landable);

  // Badges & Signals
  const badgeList = [];
  if (isTarget) {
    badgeList.push('<span class="sysmap-mini-badge target">🎯 TARGET</span>');
  }
  if (body.bio_signals > 0) {
    badgeList.push(`<span class="sysmap-mini-badge bio">🌱 ${body.bio_signals}</span>`);
  }
  if (body.geo_signals > 0) {
    badgeList.push(`<span class="sysmap-mini-badge geo">🌋 ${body.geo_signals}</span>`);
  }
  if (body.mining_signals > 0) {
    badgeList.push(`<span class="sysmap-mini-badge mining" style="background: rgba(56, 189, 248, 0.25); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.6);">⛏️ ${body.mining_signals}</span>`);
  }
  if (body.has_first_discover || body.was_discovered === 0) {
    badgeList.push('<span class="sysmap-mini-badge first-disc">⭐ 1st</span>');
  }

  // Ring & Belt Badges
  let primaryRingKey = 'icy';
  if (hasPlanetaryRings) {
    const primaryInfo = ringParser(ringItems[0].RingClass);
    primaryRingKey = primaryInfo.key;
    const ringLabels = Array.from(new Set(ringItems.map(r => ringParser(r.RingClass).nameJa)));
    badgeList.push(`<span class="sysmap-mini-badge ring-${primaryRingKey}" style="background: ${primaryInfo.bg}; color: ${primaryInfo.color}; border: 1px solid ${primaryInfo.border};">💍 ${primaryInfo.icon} ${ringLabels.join('/')}</span>`);
  }

  let primaryBeltKey = 'metal_rich';
  if (hasAsteroidBelts) {
    const primaryBeltInfo = ringParser(beltItems[0].RingClass);
    primaryBeltKey = primaryBeltInfo.key;
    const beltLabels = Array.from(new Set(beltItems.map(r => ringParser(r.RingClass).nameJa)));
    badgeList.push(`<span class="sysmap-mini-badge belt" style="background: ${primaryBeltInfo.bg}; color: ${primaryBeltInfo.color}; border: 1px solid ${primaryBeltInfo.border};">🪐 ${primaryBeltInfo.icon} ${beltLabels.join('/')}ベルト</span>`);
  }

  // Sphere HTML with optional ring, belt, and landable arc
  const landableArcHtml = isLandable ? '<div class="sysmap-landable-arc"></div>' : '';
  const ringHtml = hasPlanetaryRings ? `<div class="sysmap-ring-system ${primaryRingKey}"></div>` : '';
  const beltHtml = (hasAsteroidBelts && (role === 'root-star' || body.isStar)) ? `<div class="sysmap-belt-system ${primaryBeltKey}"></div>` : '';

  sphere.innerHTML = `
    ${landableArcHtml}
    ${ringHtml}
    ${beltHtml}
    <div class="sysmap-sphere ${iconClass} ${role}">
      <span class="sysmap-icon-label">${iconLabel}</span>
    </div>
  `;

  // Short Name (e.g. "1", "1 e", "1 f", "2 f", "B 4")
  const shortName = body.shortName || getBodyShortName(body.body_name, systemName);

  // Info labels below body with full name tooltip and neat badge plate
  const info = document.createElement('div');
  info.className = 'sysmap-body-info';

  const typeDesc = body.star_type 
    ? `Star (${body.star_type})` 
    : (body.planet_class || 'Planet');

  let ringDesc = '';
  if (hasPlanetaryRings) {
    ringDesc = ` [Ring: ${ringItems.map(r => ringParser(r.RingClass).nameJa).join('/')}]`;
  } else if (hasAsteroidBelts) {
    ringDesc = ` [Belt: ${beltItems.map(r => ringParser(r.RingClass).nameJa).join('/')}]`;
  }

  card.title = `${body.body_name} - ${typeDesc}${ringDesc}`;

  const distStr = body.distance_from_arrival_ls 
    ? formatDistance(body.distance_from_arrival_ls) 
    : (role === 'root-star' ? '0 Ls' : '--');

  info.innerHTML = `
    <div class="sysmap-body-shortname" title="${body.body_name}">${shortName}</div>
    <div class="sysmap-body-type-plate" title="${body.body_name} - ${typeDesc}">
      <span class="sysmap-type-text">${typeDesc}</span>
    </div>
    <div class="sysmap-body-dist">${distStr}</div>
    ${badgeList.length > 0 ? `<div class="sysmap-badges-row">${badgeList.join('')}</div>` : ''}
  `;

  card.appendChild(sphere);
  card.appendChild(info);

  return card;
}
