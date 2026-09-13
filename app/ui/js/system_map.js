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
 * - "ABCD 1" -> { star: "ABCD", planet: 1, moon: null, submoon: null, rank: 1 }
 */
function analyzeBodyDesignation(bodyOrName, systemName, isStarOrLetterMap, rootStars = [], bodyByIdMap = new Map()) {
  const body = (typeof bodyOrName === 'object' && bodyOrName !== null)
    ? bodyOrName
    : { body_name: bodyOrName, body_type: (isStarOrLetterMap === true ? 'Star' : 'Planet') };

  const starLetterMap = (isStarOrLetterMap instanceof Map) ? isStarOrLetterMap : new Map();
  const isStarType = Boolean(body.star_type || (body.body_type && body.body_type.toLowerCase() === 'star') || isStarOrLetterMap === true);
  const isRootStar = rootStars.some(rs => rs.body_id === body.body_id);

  if (isRootStar) {
    const assignedLetter = starLetterMap.get(body.body_id) || 'A';
    const rawShort = getBodyShortName(body.body_name, systemName).trim();
    return {
      shortName: rawShort || (body.body_name ? body.body_name.trim() : 'Star'),
      starGroup: assignedLetter,
      isStar: true,
      planetNum: null,
      moonLetter: null,
      submoonLetter: null,
      level: 0
    };
  }

  const short = getBodyShortName(body.body_name, systemName).trim();
  const tokens = short.split(/\s+/).filter(Boolean);
  const parentsList = parseParentsList(body.parents);

  let starGroup = 'A';
  let planetNum = null;
  let moonLetter = null;
  let submoonLetter = null;
  let level = 1;

  // 1. Determine starGroup from direct parent if possible
  if (parentsList.length > 0) {
    const directParent = parentsList[0];
    if (directParent.Star !== undefined && starLetterMap.has(directParent.Star)) {
      starGroup = starLetterMap.get(directParent.Star);
    } else if (directParent.Planet !== undefined) {
      level = 2; // Direct parent is a planet -> this is a moon
      if (parentsList.length > 1 && parentsList[1].Planet !== undefined) {
        level = 3; // Parent of parent is planet -> submoon
      }
      // Find parent planet's starGroup
      const parentPlanet = bodyByIdMap.get(directParent.Planet);
      if (parentPlanet && parentPlanet.starGroup) {
        starGroup = parentPlanet.starGroup;
      }
    }
  }

  // 2. Parse name tokens (e.g. "A 1", "B 3", "AB 1", "Ab 2", "1", "1 a", "Founders World")
  let idx = 0;
  if (tokens.length > 0) {
    // Check star group token (A, B, AB, CD, ABCD, or Ab followed by planet number)
    if (/^[A-Z]{1,4}$/.test(tokens[0]) || (/^[A-Z][a-z]$/.test(tokens[0]) && tokens.length >= 2 && /^\d+$/.test(tokens[1]))) {
      starGroup = tokens[0].toUpperCase();
      idx = 1;
    }

    if (idx < tokens.length) {
      const numMatch = tokens[idx].match(/^(\d+)$/);
      if (numMatch) {
        planetNum = parseInt(numMatch[1], 10);
        idx++;
        if (level < 2) level = 1;

        if (idx < tokens.length && /^[a-z]$/i.test(tokens[idx])) {
          moonLetter = tokens[idx].toLowerCase();
          idx++;
          level = 2;

          if (idx < tokens.length && /^[a-z]$/i.test(tokens[idx])) {
            submoonLetter = tokens[idx].toLowerCase();
            level = 3;
          }
        }
      } else if (/^[a-z]$/i.test(tokens[idx])) {
        moonLetter = tokens[idx].toLowerCase();
        level = 2;
      }
    }
  }

  if (isStarType && planetNum === null && level < 2) {
    level = 0;
  }

  // If custom name (e.g. "Founders World", "Earth", "Moon"), keep full name as shortName
  const finalShortName = (planetNum !== null) ? short : (short || body.body_name || '');

  return {
    shortName: finalShortName,
    starGroup: starGroup,
    isStar: isStarType && (planetNum === null && level === 0),
    planetNum: planetNum,
    moonLetter: moonLetter,
    submoonLetter: submoonLetter,
    level: level
  };
}

/**
 * Calculates a logical sort score for star & barycentre keys:
 * 'A' -> 100
 * 'AB' -> 150 (between Star A and Star B)
 * 'BCD' -> 190 (companion triple system after A, before B)
 * 'B' -> 200
 * 'BC' -> 250 (between Star B and Star C)
 * 'C' -> 300
 * 'CD' -> 350 (between Star C and Star D)
 * 'D' -> 400
 * 'ABCD' -> 450 (combined multi-star system after D, before E)
 * 'E' -> 500
 */
function getStarGroupSortScore(key) {
  if (!key || typeof key !== 'string') return 9999;
  const clean = key.toUpperCase().trim();
  if (!/^[A-Z]+$/.test(clean)) return 9999;

  if (clean.length === 1) {
    return (clean.charCodeAt(0) - 65 + 1) * 100;
  }

  const startVal = (clean.charCodeAt(0) - 65 + 1) * 100;
  const endVal = (clean.charCodeAt(clean.length - 1) - 65 + 1) * 100;

  if (clean.length === 2) {
    return (startVal + endVal) / 2.0;
  } else {
    if (clean[0] !== 'A') {
      return startVal - 10;
    } else {
      return endVal + 50;
    }
  }
}

/**
 * Extracts explicit star letter from body name, e.g. "Sol A" -> "A", "Sagittarius A*" -> "A"
 */
function extractStarLetter(bodyName) {
  if (!bodyName) return null;
  const clean = bodyName.trim();
  const m = clean.match(/(?:^|\s+)([A-Z]{1,4})\*?$/);
  if (m) {
    return m[1];
  }
  return null;
}

/**
 * Pre-analyzes all stars in a system to ensure every root star
 * gets a distinct starGroup letter (A, B, C, D...) and is never overwritten.
 * Circumstellar stars orbiting another star or barycentre are separated into dwarfPlanets.
 */
function analyzeSystemStars(flatBodies, systemName) {
  const allStars = flatBodies.filter(b => Boolean(b.star_type || (b.body_type && b.body_type.toLowerCase() === 'star')));
  const rootStars = [];
  const dwarfPlanets = [];

  allStars.forEach(b => {
    let short = getBodyShortName(b.body_name, systemName).trim();
    const tokens = short.split(/\s+/).filter(Boolean);
    const parentsList = parseParentsList(b.parents);

    // If star has a direct parent Star, it is a circumstellar body orbiting that star
    const hasParentStar = parentsList.length > 0 && parentsList[0].Star !== undefined;

    // Check if name is like "A 1", "B 3", "AB 1", "Ab 2", or pure number "1"
    const isOrbitingName = (tokens.length >= 2 && /^(?:[A-Z]{1,4}|[A-Z][a-z])$/.test(tokens[0]) && /^\d+$/.test(tokens[1]))
                        || (tokens.length > 0 && /^\d+$/.test(tokens[0]));

    if (hasParentStar || isOrbitingName) {
      dwarfPlanets.push(b);
    } else {
      rootStars.push(b);
    }
  });

  // Sort root stars: primary arrival star (0 ls) first, then by distance / body_id
  rootStars.sort((a, b) => {
    const distA = a.distance_from_arrival_ls || 0;
    const distB = b.distance_from_arrival_ls || 0;
    if (Math.abs(distA - distB) > 0.001) {
      return distA - distB;
    }
    return (a.body_id || 0) - (b.body_id || 0);
  });

  // Assign unique star letter (A, B, C, D...) to each root star
  const claimedLetters = new Set();
  const starLetterMap = new Map(); // body_id -> letter

  // Pass 1: Explicit letters in name (e.g. "Sagittarius A*" -> "A", "HIP 99999 A" -> "A")
  rootStars.forEach(s => {
    const letter = extractStarLetter(s.body_name);
    if (letter && !claimedLetters.has(letter)) {
      claimedLetters.add(letter);
      starLetterMap.set(s.body_id, letter);
    }
  });

  // Pass 2: Fallback available letters in order for stars without explicit letters (e.g. "Source 2" -> "B")
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  let alphaIdx = 0;
  rootStars.forEach(s => {
    if (!starLetterMap.has(s.body_id)) {
      while (alphaIdx < alphabet.length && claimedLetters.has(alphabet[alphaIdx])) {
        alphaIdx++;
      }
      const assigned = alphaIdx < alphabet.length ? alphabet[alphaIdx] : `S${s.body_id}`;
      claimedLetters.add(assigned);
      starLetterMap.set(s.body_id, assigned);
    }
  });

  return { rootStars, dwarfPlanets, starLetterMap };
}

/**
 * Builds a strict and reliable hierarchical tree from bodies:
 * Stars & Circumbinary Barycentres -> Planets -> Moons -> Submoons
 */
function buildSystemMapTree(flatBodies, systemName) {
  if (!flatBodies || flatBodies.length === 0) return [];

  // 1. Pre-analyze stars to assign unique star letters
  const { rootStars, dwarfPlanets, starLetterMap } = analyzeSystemStars(flatBodies, systemName);

  const bodyByIdMap = new Map();
  flatBodies.forEach(b => bodyByIdMap.set(b.body_id, b));

  // 2. Tag and analyze each body
  const analyzedList = flatBodies.map(b => {
    const info = analyzeBodyDesignation(b, systemName, starLetterMap, rootStars, bodyByIdMap);
    const combined = {
      ...b,
      ...info,
      moons: [],
      submoons: []
    };
    bodyByIdMap.set(b.body_id, combined);
    return combined;
  });

  // 3. Collect Stars and Star Sections (Guaranteed unique keys per root star)
  const starMap = new Map();
  const stars = analyzedList.filter(b => b.isStar);

  if (stars.length === 0) {
    starMap.set('A', {
      starKey: 'A',
      isBarycentre: false,
      rootStar: analyzedList[0],
      planets: []
    });
  } else {
    stars.forEach(s => {
      let key = s.starGroup;
      if (starMap.has(key)) {
        key = `${key}-${s.body_id}`;
      }
      starMap.set(key, {
        starKey: key,
        isBarycentre: false,
        rootStar: s,
        planets: []
      });
    });
  }

  // Helper to dynamically get or create a star or circumbinary section
  function getOrCreateSection(sGroup, sampleBody) {
    if (starMap.has(sGroup)) {
      return starMap.get(sGroup);
    }
    const isMulti = sGroup.length > 1;
    const baryNode = {
      body_id: `barycentre-${sGroup}`,
      body_name: isMulti ? `${systemName} [${sGroup}] Orbit` : `${systemName} ${sGroup}`,
      shortName: isMulti ? `[${sGroup}]` : sGroup,
      starGroup: sGroup,
      isStar: false,
      isBarycentre: isMulti,
      planet_class: isMulti 
        ? (sGroup.length > 2 ? `Multi-Star Orbit [${sGroup}]` : `Circumbinary Orbit [${sGroup}]`)
        : 'Star System',
      barycentreStars: sGroup.split(''),
      distance_from_arrival_ls: sampleBody ? sampleBody.distance_from_arrival_ls : 0,
      level: 0,
      moons: [],
      submoons: []
    };
    const sec = {
      starKey: sGroup,
      isBarycentre: isMulti,
      rootStar: baryNode,
      planets: []
    };
    starMap.set(sGroup, sec);
    return sec;
  }

  // 3. Separate Planets, Moons, and Submoons
  const planets = analyzedList.filter(b => !b.isStar && b.level === 1);
  const moons = analyzedList.filter(b => !b.isStar && b.level === 2);
  const submoons = analyzedList.filter(b => !b.isStar && b.level === 3);

  const planetByIdMap = new Map();
  const planetKeyMap = new Map();

  planets.forEach(p => {
    const sGroup = p.starGroup || 'A';
    const sec = getOrCreateSection(sGroup, p);
    planetByIdMap.set(p.body_id, p);

    const pNum = p.planetNum !== null ? p.planetNum : (p.distance_from_arrival_ls || 0);
    const key = `${sGroup}-${pNum}`;

    planetKeyMap.set(key, p);
    sec.planets.push(p);
  });

  // 4. Attach Moons to their respective Planets
  moons.forEach(m => {
    const sGroup = m.starGroup || 'A';
    const parentsList = parseParentsList(m.parents);
    let attached = false;

    // Try direct parent planet ID first
    if (parentsList.length > 0 && parentsList[0].Planet !== undefined) {
      const parentPlanet = planetByIdMap.get(parentsList[0].Planet);
      if (parentPlanet) {
        parentPlanet.moons.push(m);
        attached = true;
      }
    }

    if (!attached) {
      const key = `${sGroup}-${m.planetNum}`;
      if (planetKeyMap.has(key)) {
        planetKeyMap.get(key).moons.push(m);
        attached = true;
      } else {
        // If parent planet not found in map (e.g. not yet scanned), create placeholder
        const sec = getOrCreateSection(sGroup, m);
        const placeholderPlanet = {
          body_id: `p-${key}`,
          body_name: `${systemName} ${sGroup} ${m.planetNum || ''}`.trim(),
          shortName: `${sGroup !== 'A' ? sGroup + ' ' : ''}${m.planetNum || 'Planet'}`,
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
        sec.planets.push(placeholderPlanet);
      }
    }
  });

  // 5. Attach Submoons to their respective Moons
  submoons.forEach(sm => {
    const sGroup = sm.starGroup || 'A';
    const parentsList = parseParentsList(sm.parents);
    let attached = false;

    if (parentsList.length > 0 && parentsList[0].Planet !== undefined) {
      const parentMoon = analyzedList.find(b => b.body_id === parentsList[0].Planet);
      if (parentMoon && parentMoon.submoons) {
        parentMoon.submoons.push(sm);
        attached = true;
      }
    }

    if (!attached) {
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
    }
  });

  // 6. Natural Sorting:
  // - Sort Star Sections by getStarGroupSortScore (A, AB, B, BC, C, CD, D, ABCD, E...)
  // - Sort Planets by orbital distance (semi_major_axis or distance_from_arrival_ls) / planetNum ascending
  // - Sort Moons by moonLetter / distance ascending
  // - Sort Submoons by submoonLetter / distance ascending
  const starSections = Array.from(starMap.values());
  starSections.sort((a, b) => getStarGroupSortScore(a.starKey) - getStarGroupSortScore(b.starKey));

  starSections.forEach(sec => {
    sec.planets.sort((a, b) => {
      const distA = (a.semi_major_axis !== undefined && a.semi_major_axis !== null) ? a.semi_major_axis : (a.distance_from_arrival_ls || 0);
      const distB = (b.semi_major_axis !== undefined && b.semi_major_axis !== null) ? b.semi_major_axis : (b.distance_from_arrival_ls || 0);
      if (Math.abs(distA - distB) > 0.001) {
        return distA - distB;
      }
      if (a.planetNum !== null && b.planetNum !== null) {
        return a.planetNum - b.planetNum;
      }
      return (a.body_id || 0) - (b.body_id || 0);
    });

    sec.planets.forEach(p => {
      p.moons.sort((a, b) => {
        if (a.moonLetter && b.moonLetter) {
          return a.moonLetter.localeCompare(b.moonLetter);
        }
        const distA = (a.semi_major_axis !== undefined && a.semi_major_axis !== null) ? a.semi_major_axis : (a.distance_from_arrival_ls || 0);
        const distB = (b.semi_major_axis !== undefined && b.semi_major_axis !== null) ? b.semi_major_axis : (b.distance_from_arrival_ls || 0);
        return distA - distB;
      });

      p.moons.forEach(m => {
        m.submoons.sort((a, b) => {
          if (a.submoonLetter && b.submoonLetter) {
            return a.submoonLetter.localeCompare(b.submoonLetter);
          }
          const distA = (a.semi_major_axis !== undefined && a.semi_major_axis !== null) ? a.semi_major_axis : (a.distance_from_arrival_ls || 0);
          const distB = (b.semi_major_axis !== undefined && b.semi_major_axis !== null) ? b.semi_major_axis : (b.distance_from_arrival_ls || 0);
          return distA - distB;
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
  const isBary = Boolean(body.isBarycentre);
  const effectiveRole = isBary ? 'barycentre-root' : role;

  const card = document.createElement('div');
  card.className = `sysmap-body-node ${effectiveRole} ${isSelected ? 'selected' : ''} ${isTarget ? 'target-pulse' : ''}`;
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
  if (isBary) {
    const isMulti = body.starGroup && body.starGroup.length > 2;
    badgeList.push(`<span class="sysmap-mini-badge" style="background: rgba(147, 51, 234, 0.25); color: #c084fc; border: 1px solid rgba(147, 51, 234, 0.6); font-weight: bold;">♊ ${isMulti ? '多重連星共通軌道' : '連星共通周回軌道'}</span>`);
  }
  const modSettings = (typeof window.getModuleSettings === 'function') ? window.getModuleSettings() : { exobiology: true, rhino: true };
  if (modSettings.exobiology !== false && body.bio_signals > 0) {
    badgeList.push(`<span class="sysmap-mini-badge bio">🌱 ${body.bio_signals}</span>`);
  }
  if (body.geo_signals > 0) {
    badgeList.push(`<span class="sysmap-mini-badge geo">🌋 ${body.geo_signals}</span>`);
  }
  if (modSettings.rhino !== false && body.mining_signals > 0) {
    badgeList.push(`<span class="sysmap-mini-badge mining" style="background: rgba(56, 189, 248, 0.25); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.6);">⛏️ ${body.mining_signals}</span>`);
  }
  if (body.has_first_discover || body.was_discovered === 0) {
    badgeList.push('<span class="sysmap-mini-badge first-disc">⭐ 1st</span>');
  }

  // Body Bookmark Badge
  if (body.bookmark) {
    const bmTitle = (body.bookmark.alias_name ? `[${body.bookmark.alias_name}] ` : '') + (body.bookmark.note_markdown || '');
    badgeList.push(`<span class="sysmap-mini-badge bookmark" title="${bmTitle}">🔖 ${body.bookmark.alias_name || 'BM'}</span>`);
  }

  // Gravity & Temperature Display (mining support toggles)
  const showGrav = (window.state && window.state.showMiningGravity !== undefined) ? window.state.showMiningGravity : true;
  const showTmp = (window.state && window.state.showMiningTemp !== undefined) ? window.state.showMiningTemp : true;
  if (showGrav && isLandable && body.surface_gravity_g !== null && body.surface_gravity_g !== undefined) {
    const gVal = body.surface_gravity_g;
    const gColor = gVal >= 3.0 ? '#ef4444' : (gVal >= 1.5 ? '#f59e0b' : '#22c55e');
    badgeList.push(`<span class="sysmap-mini-badge" style="background: rgba(0,0,0,0.4); color: ${gColor}; border: 1px solid ${gColor}; font-weight: bold;">${gVal.toFixed(2)}G</span>`);
  }
  if (showTmp && body.surface_temperature !== null && body.surface_temperature !== undefined && isLandable) {
    const tVal = Math.round(body.surface_temperature || 0);
    badgeList.push(`<span class="sysmap-mini-badge" style="background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.4);">${tVal}K</span>`);
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
  if (isBary) {
    sphere.innerHTML = `
      <div class="sysmap-sphere barycentre-sphere ${effectiveRole}">
        <span class="sysmap-icon-label" style="font-size: 1.35rem; color: #c084fc;">♊</span>
      </div>
    `;
  } else {
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
  }

  // Short Name (e.g. "1", "1 e", "1 f", "2 f", "B 4", "[AB]")
  const shortName = body.shortName || getBodyShortName(body.body_name, systemName);

  // Info labels below body with full name tooltip and neat badge plate
  const info = document.createElement('div');
  info.className = 'sysmap-body-info';

  const typeDesc = isBary
    ? (body.planet_class || `連星共通軌道 [${body.starGroup}]`)
    : (body.star_type 
        ? `Star (${body.star_type})` 
        : (body.planet_class || 'Planet'));

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

  const aliasHtml = (body.bookmark && body.bookmark.alias_name)
    ? `<div class="sysmap-body-alias" title="エイリアス: ${body.bookmark.alias_name}">🏷️ ${body.bookmark.alias_name}</div>`
    : '';

  info.innerHTML = `
    <div class="sysmap-body-shortname" title="${body.body_name}">${shortName}</div>
    ${aliasHtml}
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
