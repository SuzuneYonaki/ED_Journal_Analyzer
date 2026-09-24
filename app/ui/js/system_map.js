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
      distance_from_arrival_ls: (() => {
        if (rootStars && rootStars.length > 0) {
          const memberStars = rootStars.filter(s => sGroup.includes(starLetterMap.get(s.body_id) || ''));
          if (memberStars.length > 0) {
            return memberStars.reduce((sum, s) => sum + (s.distance_from_arrival_ls || 0), 0) / memberStars.length;
          }
        }
        return 0;
      })(),
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

  // 5.5 Extract Asteroid Belts from Stars and add as independent orbital nodes in the rail
  stars.forEach(s => {
    let rawRings = s.rings_list;
    if (!rawRings && s.rings && s.rings !== '[]' && s.rings !== '""') {
      try {
        rawRings = typeof s.rings === 'string' ? JSON.parse(s.rings) : s.rings;
      } catch (e) {
        rawRings = [];
      }
    }
    rawRings = Array.isArray(rawRings) ? rawRings : [];
    const beltItems = rawRings.filter(r => r && (r.Name || '').toLowerCase().includes('belt'));

    if (beltItems.length > 0) {
      const sGroup = s.starGroup || 'A';
      const sec = getOrCreateSection(sGroup, s);

      beltItems.forEach((belt, bIdx) => {
        const beltAvgDistM = (belt.InnerRad && belt.OuterRad) ? (belt.InnerRad + belt.OuterRad) / 2 : (belt.InnerRad || belt.OuterRad || 0);
        const beltDistLs = beltAvgDistM ? (beltAvgDistM / 299792458) : (s.distance_from_arrival_ls || 0);

        let cleanShortName = belt.Name || 'Belt';
        if (systemName && cleanShortName.startsWith(systemName)) {
          cleanShortName = cleanShortName.substring(systemName.length).trim();
        }
        if (s.starGroup && cleanShortName.startsWith(s.starGroup + ' ')) {
          cleanShortName = cleanShortName.substring(s.starGroup.length + 1).trim();
        }
        cleanShortName = cleanShortName.replace(/^Asteroid\s+Belt/i, 'Belt').trim();
        if (!cleanShortName) cleanShortName = `Belt ${bIdx + 1}`;

        const beltNode = {
          body_id: `belt-${s.body_id}-${bIdx}`,
          body_name: belt.Name || `${s.body_name} Belt`,
          shortName: cleanShortName,
          starGroup: sGroup,
          isStar: false,
          isAsteroidBelt: true,
          planetNum: null,
          semi_major_axis: beltAvgDistM,
          distance_from_arrival_ls: beltDistLs,
          planet_class: 'Asteroid Belt',
          ring_class: belt.RingClass,
          inner_radius: belt.InnerRad,
          outer_radius: belt.OuterRad,
          mass: belt.MassMT,
          signals: belt.signals || [],
          Hotspots: belt.Hotspots || {},
          reserve_level: s.reserve_level || '',
          rings_list: [belt],
          level: 1,
          moons: [],
          submoons: []
        };

        sec.planets.push(beltNode);
      });
    }
  });

  // Helper to get orbital distance in Light Seconds (Ls) for comparison:
  // - If body orbits an intermediate/sub-barycentre (binary planet pair), semi_major_axis is
  //   only the mutual orbit radius around that local barycentre, NOT around the host star/system.
  //   In this case, distance_from_arrival_ls relative to the parent star/barycentre is used.
  // - Otherwise, SemiMajorAxis in meters (m) is converted to Ls (m / 299792458).
  // - Fallback to distance_from_arrival_ls if semi_major_axis is not present.
  function getBodyOrbitalDistanceLs(body, parentStar) {
    const parentsList = parseParentsList(body.parents);
    const orbitsSubBarycentre = parentsList.length > 1 && parentsList[0].Null !== undefined;

    if (!orbitsSubBarycentre) {
      if (body.semi_major_axis !== undefined && body.semi_major_axis !== null && body.semi_major_axis > 0) {
        return body.semi_major_axis / 299792458.0;
      }
    }
    if (body.distance_from_arrival_ls !== undefined && body.distance_from_arrival_ls !== null) {
      if (parentStar && parentStar.distance_from_arrival_ls !== undefined && parentStar.distance_from_arrival_ls !== null) {
        return Math.abs(body.distance_from_arrival_ls - parentStar.distance_from_arrival_ls);
      }
      return body.distance_from_arrival_ls;
    }
    return 0;
  }

  // 6. Natural Sorting:
  // - Sort Star Sections by getStarGroupSortScore (A, AB, B, BC, C, CD, D, ABCD, E...)
  // - Sort Planets by planetNum / orbital distance in light seconds ascending
  // - Sort Moons by moonLetter / distance ascending
  // - Sort Submoons by submoonLetter / distance ascending
  const starSections = Array.from(starMap.values());
  starSections.sort((a, b) => getStarGroupSortScore(a.starKey) - getStarGroupSortScore(b.starKey));

  starSections.forEach(sec => {
    const parentStar = sec.rootStar;
    sec.planets.sort((a, b) => {
      if (a.planetNum !== null && b.planetNum !== null && a.planetNum !== b.planetNum) {
        return a.planetNum - b.planetNum;
      }
      const distA = getBodyOrbitalDistanceLs(a, parentStar);
      const distB = getBodyOrbitalDistanceLs(b, parentStar);
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
        if (a.moonLetter && b.moonLetter && a.moonLetter !== b.moonLetter) {
          return a.moonLetter.localeCompare(b.moonLetter);
        }
        const distA = getBodyOrbitalDistanceLs(a);
        const distB = getBodyOrbitalDistanceLs(b);
        if (Math.abs(distA - distB) > 0.001) {
          return distA - distB;
        }
        return (a.body_id || 0) - (b.body_id || 0);
      });

      p.moons.forEach(m => {
        m.submoons.sort((a, b) => {
          if (a.submoonLetter && b.submoonLetter && a.submoonLetter !== b.submoonLetter) {
            return a.submoonLetter.localeCompare(b.submoonLetter);
          }
          const distA = getBodyOrbitalDistanceLs(a);
          const distB = getBodyOrbitalDistanceLs(b);
          if (Math.abs(distA - distB) > 0.001) {
            return distA - distB;
          }
          return (a.body_id || 0) - (b.body_id || 0);
        });
      });
    });
  });

  return starSections;
}

function renderSystemMapView(container, hierarchyNodes, flatBodies) {
  container.classList.add('is-sysmap');
  container.innerHTML = '';

  if (!flatBodies || flatBodies.length === 0) {
    container.innerHTML = `<div style="color: var(--text-secondary); text-align: center; padding: 40px;">${t('no_bodies') || '天体データがありません'}</div>`;
    return;
  }

  const systemName = state.selectedSystem ? state.selectedSystem.star_system : '';
  const mapWrapper = document.createElement('div');
  mapWrapper.className = 'ed-system-map-container';

  // Inner stage for zoom scaling
  const stage = document.createElement('div');
  stage.className = 'sysmap-zoom-stage';

  let currentZoom = (state.sysmapZoom !== undefined && state.sysmapZoom !== null) ? state.sysmapZoom : 1.0;

  function applySysmapZoom(zoom) {
    stage.style.zoom = zoom;
    stage.style.transformOrigin = '0 0';
  }

  applySysmapZoom(currentZoom);


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

    stage.appendChild(starSectionEl);
  });

  mapWrapper.appendChild(stage);

  // Floating HUD zoom controls
  const controls = document.createElement('div');
  controls.className = 'sysmap-zoom-controls';

  const btnOut = document.createElement('button');
  btnOut.type = 'button';
  btnOut.className = 'sysmap-zoom-btn';
  btnOut.id = 'btn-sysmap-zoom-out';
  btnOut.title = typeof t === 'function' ? t('sysmap_zoom_out_tip') : 'ズームアウト (ホイール下 / 最小40%)';
  btnOut.textContent = '−';

  const label = document.createElement('span');
  label.className = 'sysmap-zoom-label';
  label.id = 'sysmap-zoom-label';
  label.title = typeof t === 'function' ? t('sysmap_zoom_reset_tip') : '100%にリセット (中クリック)';
  label.textContent = `${Math.round(currentZoom * 100)}%`;

  const btnIn = document.createElement('button');
  btnIn.type = 'button';
  btnIn.className = 'sysmap-zoom-btn';
  btnIn.id = 'btn-sysmap-zoom-in';
  btnIn.title = typeof t === 'function' ? t('sysmap_zoom_in_tip') : 'ズームイン (ホイール上 / 最大200%)';
  btnIn.textContent = '+';

  const btnReset = document.createElement('button');
  btnReset.type = 'button';
  btnReset.className = 'sysmap-zoom-btn';
  btnReset.id = 'btn-sysmap-zoom-reset';
  btnReset.title = typeof t === 'function' ? t('sysmap_zoom_reset_tip') : '100%にリセット (中クリック)';
  btnReset.textContent = '⟲';

  controls.appendChild(btnOut);
  controls.appendChild(label);
  controls.appendChild(btnIn);
  controls.appendChild(btnReset);

  function updateZoomLabel() {
    label.textContent = `${Math.round(currentZoom * 100)}%`;
  }

  function resetZoom() {
    if (Math.abs(currentZoom - 1.0) < 0.01) return;
    const centerX = mapWrapper.clientWidth / 2;
    const centerY = mapWrapper.clientHeight / 2;
    const contentX = (mapWrapper.scrollLeft + centerX) / currentZoom;
    const contentY = (mapWrapper.scrollTop + centerY) / currentZoom;

    currentZoom = 1.0;
    state.sysmapZoom = 1.0;
    applySysmapZoom(1.0);
    updateZoomLabel();

    mapWrapper.scrollLeft = contentX * 1.0 - centerX;
    mapWrapper.scrollTop = contentY * 1.0 - centerY;
  }

  function stepZoom(direction) {
    const centerX = mapWrapper.clientWidth / 2;
    const centerY = mapWrapper.clientHeight / 2;
    const contentX = (mapWrapper.scrollLeft + centerX) / currentZoom;
    const contentY = (mapWrapper.scrollTop + centerY) / currentZoom;

    const factor = direction > 0 ? 1.15 : (1 / 1.15);
    let nextZoom = Math.min(2.0, Math.max(0.4, currentZoom * factor));
    nextZoom = Math.round(nextZoom * 100) / 100;
    if (nextZoom === currentZoom) return;

    currentZoom = nextZoom;
    state.sysmapZoom = currentZoom;
    applySysmapZoom(currentZoom);
    updateZoomLabel();

    mapWrapper.scrollLeft = contentX * currentZoom - centerX;
    mapWrapper.scrollTop = contentY * currentZoom - centerY;
  }

  btnIn.addEventListener('click', (e) => {
    e.stopPropagation();
    stepZoom(1);
  });
  btnOut.addEventListener('click', (e) => {
    e.stopPropagation();
    stepZoom(-1);
  });
  btnReset.addEventListener('click', (e) => {
    e.stopPropagation();
    resetZoom();
  });
  label.addEventListener('click', (e) => {
    e.stopPropagation();
    resetZoom();
  });

  // Wheel zoom centered on mouse cursor
  const onSysmapWheel = (e) => {
    if (typeof e.preventDefault === 'function') e.preventDefault();
    if (typeof e.stopPropagation === 'function') e.stopPropagation();


    const rect = mapWrapper.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const prevZoom = currentZoom;
    const contentX = (mapWrapper.scrollLeft + mouseX) / prevZoom;
    const contentY = (mapWrapper.scrollTop + mouseY) / prevZoom;

    // Smooth geometric zoom
    const factor = e.deltaY < 0 ? 1.12 : (1 / 1.12);
    let nextZoom = Math.min(2.0, Math.max(0.4, prevZoom * factor));
    nextZoom = Math.round(nextZoom * 100) / 100;

    if (nextZoom === prevZoom) return;

    currentZoom = nextZoom;
    state.sysmapZoom = currentZoom;
    applySysmapZoom(currentZoom);
    updateZoomLabel();

    mapWrapper.scrollLeft = contentX * currentZoom - mouseX;
    mapWrapper.scrollTop = contentY * currentZoom - mouseY;
  };

  mapWrapper.addEventListener('wheel', onSysmapWheel, { passive: false });
  controls.addEventListener('wheel', onSysmapWheel, { passive: false });

  // Keyboard zoom shortcuts (+ / - / 0) when hovering System Map
  const onKeyDown = (e) => {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT')) {
      return;
    }
    if (e.key === '+' || e.key === '=') {
      e.preventDefault();
      stepZoom(1);
    } else if (e.key === '-' || e.key === '_') {
      e.preventDefault();
      stepZoom(-1);
    } else if (e.key === '0') {
      e.preventDefault();
      resetZoom();
    }
  };
  mapWrapper.addEventListener('mouseenter', () => {
    window.addEventListener('keydown', onKeyDown);
  });
  mapWrapper.addEventListener('mouseleave', () => {
    window.removeEventListener('keydown', onKeyDown);
  });

  // Middle mouse click (button 1) to reset zoom
  mapWrapper.addEventListener('auxclick', (e) => {
    if (e.button === 1) {
      e.preventDefault();
      resetZoom();
    }
  });

  // Double click on empty background to reset zoom
  mapWrapper.addEventListener('dblclick', (e) => {
    if (e.target.closest('.sysmap-body-node') || e.target.closest('.sysmap-zoom-controls')) {
      return;
    }
    resetZoom();
  });

  // Enable mouse left-click drag panning (Horizontal, Vertical, and Diagonal)
  let isDown = false;
  let startX = 0;
  let startY = 0;
  let scrollLeft = 0;
  let scrollTop = 0;
  let parentScrollTop = 0;
  let hasDragged = false;

  const onMouseMove = (e) => {
    if (!isDown) return;
    const walkX = e.pageX - startX;
    const walkY = e.pageY - startY;
    if (Math.hypot(walkX, walkY) > 5) {
      hasDragged = true;
    }
    // Update both axes simultaneously for seamless horizontal, vertical, and diagonal panning
    mapWrapper.scrollLeft = scrollLeft - walkX;
    mapWrapper.scrollTop = scrollTop - walkY;
    if (mapWrapper.parentElement && mapWrapper.parentElement.scrollTop !== undefined) {
      mapWrapper.parentElement.scrollTop = parentScrollTop - walkY;
    }
  };

  const onMouseUp = () => {
    if (isDown) {
      isDown = false;
      mapWrapper.classList.remove('is-dragging');
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      // Reset hasDragged shortly after current event loop cycle so click handler can read it once
      setTimeout(() => {
        hasDragged = false;
      }, 50);
    }
  };

  mapWrapper.addEventListener('mousedown', (e) => {
    // Only primary (left) button
    if (e.button !== 0) return;
    isDown = true;
    hasDragged = false;
    mapWrapper.classList.add('is-dragging');
    startX = e.pageX;
    startY = e.pageY;
    scrollLeft = mapWrapper.scrollLeft;
    scrollTop = mapWrapper.scrollTop;
    parentScrollTop = mapWrapper.parentElement ? mapWrapper.parentElement.scrollTop : 0;

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  });

  mapWrapper._hasDragged = () => hasDragged;

  container.appendChild(mapWrapper);
  container.appendChild(controls);
}

function createSysMapBodyElement(body, role = 'planet', systemName = '') {
  const isSelected = state.selectedBody && state.selectedBody.body_id === body.body_id;
  const isTarget = state.targetBodyId !== null && body.body_id === state.targetBodyId;
  const isBary = Boolean(body.isBarycentre);
  const effectiveRole = isBary ? 'barycentre-root' : role;

  const card = document.createElement('div');
  card.className = `sysmap-body-node sysmap-node ${effectiveRole} ${isSelected ? 'selected' : ''} ${isTarget ? 'target-pulse' : ''}`;
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

  const beltItems = rawRings.filter(r => r && (r.Name || '').toLowerCase().includes('belt'));
  const ringItems = rawRings.filter(r => r && !(r.Name || '').toLowerCase().includes('belt'));
  const hasPlanetaryRings = ringItems.length > 0;
  const hasAsteroidBelts = beltItems.length > 0;

  const lang = (typeof getAppLang === 'function') ? getAppLang() : 'ja';
  const ringParser = window.parseRingClass || ((cls) => {
    const l = (cls || '').toLowerCase();
    if (l.includes('icy')) return { key: 'icy', nameEn: 'Icy', nameJa: '氷', name: lang === 'en' ? 'Icy' : '氷', icon: '❄️', color: '#38bdf8', bg: 'rgba(56,189,248,0.18)', border: 'rgba(56,189,248,0.45)' };
    if (l.includes('metallic') || l.includes('metalic')) return { key: 'metallic', nameEn: 'Metallic', nameJa: '金属質', name: lang === 'en' ? 'Metallic' : '金属質', icon: '🪙', color: '#facc15', bg: 'rgba(250,204,21,0.18)', border: 'rgba(250,204,21,0.5)' };
    if (l.includes('metal')) return { key: 'metal_rich', nameEn: 'Metal Rich', nameJa: '金属豊富', name: lang === 'en' ? 'Metal Rich' : '金属豊富', icon: '🪐', color: '#fb923c', bg: 'rgba(251,146,60,0.18)', border: 'rgba(251,146,60,0.5)' };
    if (l.includes('rocky')) return { key: 'rocky', nameEn: 'Rocky', nameJa: '岩石', name: lang === 'en' ? 'Rocky' : '岩石', icon: '🪨', color: '#cbd5e1', bg: 'rgba(203,213,225,0.18)', border: 'rgba(203,213,225,0.45)' };
    const clean = (cls || '').replace('eRingClass_', '');
    const isUnk = !clean || clean === '不明' || clean.toLowerCase() === 'unknown';
    const nameEn = isUnk ? 'Unknown' : clean;
    const nameJa = isUnk ? '不明' : clean;
    return { key: isUnk ? 'unknown' : 'other', nameEn, nameJa, name: lang === 'en' ? nameEn : nameJa, icon: '💍', color: isUnk ? '#94a3b8' : '#a78bfa', bg: isUnk ? 'rgba(148,163,184,0.15)' : 'rgba(167,139,250,0.18)', border: isUnk ? 'rgba(148,163,184,0.4)' : 'rgba(167,139,250,0.45)' };
  });

  // Check Landable (Blue crescent arc in ED)
  const isLandable = Boolean(body.landable);

  // Badges & Signals
  const badgeList = [];

  // GGG (Green Gas Giant) Badges: Confirmed [GGG] & Candidate [GGG？]
  let isConfirmedGgg = Boolean(body.is_confirmed_ggg);
  let confirmedVariant = body.confirmed_ggg_variant || '';
  let isGggCandidate = Boolean(body.ggg_evaluation && body.ggg_evaluation.is_candidate);

  let anomaliesList = body.anomalies;
  if (!anomaliesList && body.anomalies_json) {
    try {
      anomaliesList = typeof body.anomalies_json === 'string' ? JSON.parse(body.anomalies_json) : body.anomalies_json;
    } catch (e) {
      anomaliesList = [];
    }
  }
  if (Array.isArray(anomaliesList)) {
    for (const a of anomaliesList) {
      if (!a) continue;
      const tagStr = typeof a === 'string' ? a : (a.tag || '');
      const typeStr = typeof a === 'object' ? (a.type || '') : '';
      if (typeStr === 'confirmed_ggg' || tagStr.includes('Confirmed GGG')) {
        isConfirmedGgg = true;
        if (!confirmedVariant) {
          if (a.desc && a.desc.includes('確定GGG:')) {
            confirmedVariant = a.desc.replace('確定GGG:', '').trim();
          } else {
            const vMatch = tagStr.match(/Confirmed GGG \((.+)\)/);
            if (vMatch) confirmedVariant = vMatch[1];
          }
        }
      } else if (typeStr === 'ggg_candidate' || tagStr.includes('GGG Candidate')) {
        isGggCandidate = true;
      }
    }
  }

  if (isConfirmedGgg) {
    const gggTitle = `確定グリーンガスジャイアント: ${confirmedVariant || (lang === 'en' ? 'Codex Verified' : 'Codex確認済')}`;
    badgeList.push(`<span class="sysmap-mini-badge ggg-confirmed" title="${gggTitle}">[GGG]</span>`);
  } else if (isGggCandidate) {
    const candTitle = lang === 'en'
      ? 'グリーンガスジャイアント候補 (FSSまたは目視確認推奨)'
      : 'グリーンガスジャイアント候補 (FSSまたは目視確認推奨)';
    badgeList.push(`<span class="sysmap-mini-badge ggg-candidate" title="${candTitle}">[GGG？]</span>`);
  }
  if (isBary) {
    const isMulti = body.starGroup && body.starGroup.length > 2;
    const baryLabel = isMulti
      ? (typeof t === 'function' ? t('barycenter_multi') : '多重連星共通軌道')
      : (typeof t === 'function' ? t('barycenter_binary') : '連星共通周回軌道');
    badgeList.push(`<span class="sysmap-mini-badge" style="background: rgba(147, 51, 234, 0.25); color: #c084fc; border: 1px solid rgba(147, 51, 234, 0.6); font-weight: bold;">♊ ${baryLabel}</span>`);
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

  const isAsteroidBelt = Boolean(body.isAsteroidBelt);

  // Ring & Belt Badges
  let primaryRingKey = 'icy';
  if (!isAsteroidBelt && hasPlanetaryRings) {
    const primaryInfo = ringParser(ringItems[0].RingClass);
    primaryRingKey = primaryInfo.key;
    const ringLabels = Array.from(new Set(ringItems.map(r => {
      const p = ringParser(r.RingClass);
      return lang === 'en' ? (p.nameEn || p.name) : (p.nameJa || p.name);
    })));
    badgeList.push(`<span class="sysmap-mini-badge ring-${primaryRingKey}" style="background: ${primaryInfo.bg}; color: ${primaryInfo.color}; border: 1px solid ${primaryInfo.border};">💍 ${primaryInfo.icon} ${ringLabels.join('/')}</span>`);
  }

  if (isAsteroidBelt) {
    const primaryBeltInfo = ringParser(body.ring_class);
    const beltSuffix = lang === 'en' ? ' Belt' : 'ベルト';
    const beltName = lang === 'en' ? (primaryBeltInfo.nameEn || primaryBeltInfo.name) : (primaryBeltInfo.nameJa || primaryBeltInfo.name);
    badgeList.push(`<span class="sysmap-mini-badge belt" style="background: ${primaryBeltInfo.bg}; color: ${primaryBeltInfo.color}; border: 1px solid ${primaryBeltInfo.border}; font-weight: bold;">🪐 ${primaryBeltInfo.icon} ${beltName}${beltSuffix}</span>`);
    if (body.reserve_level) {
      const reserveParser = (typeof parseReserveLevel === 'function')
        ? parseReserveLevel
        : ((typeof window !== 'undefined' && typeof window.parseReserveLevel === 'function') ? window.parseReserveLevel : null);
      const resInfo = reserveParser ? reserveParser(body.reserve_level) : null;
      const resLabel = resInfo ? (lang === 'en' ? resInfo.en : resInfo.ja) : body.reserve_level;
      badgeList.push(`<span class="sysmap-mini-badge" style="background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.4); font-weight: bold;">${resLabel}</span>`);
    }
  }

  // Ring Hotspots Detection:
  // For Stars: only detect hotspots on genuine circumstellar rings (ringItems), not extracted belts.
  // For Belts / Planets: inspect target rings (for asteroid belts, rawRings is [belt]).
  const targetHotspotRings = (body.isStar || role === 'root-star') ? ringItems : rawRings;
  const allHotspots = {};
  targetHotspotRings.forEach(r => {
    if (!r) return;
    const hs = r.Hotspots || {};
    if (Object.keys(hs).length > 0) {
      for (const [mineral, cnt] of Object.entries(hs)) {
        allHotspots[mineral] = (allHotspots[mineral] || 0) + cnt;
      }
    } else if (Array.isArray(r.signals)) {
      r.signals.forEach(s => {
        if (s && s.name) {
          allHotspots[s.name] = (allHotspots[s.name] || 0) + (s.count || 1);
        }
      });
    }
  });

  const hotspotCount = Object.values(allHotspots).reduce((a, b) => a + b, 0);
  if (hotspotCount > 0) {
    const hsSummary = Object.entries(allHotspots)
      .map(([m, c]) => `${m} x${c}`)
      .join(', ');
    
    const highlights = [];
    if (allHotspots['Platinum']) highlights.push(`Pt x${allHotspots['Platinum']}`);
    if (allHotspots['Painite']) highlights.push(`Pa x${allHotspots['Painite']}`);
    if (allHotspots['Tritium']) highlights.push(`Tri x${allHotspots['Tritium']}`);
    if (allHotspots['Void Opal']) highlights.push(`VO x${allHotspots['Void Opal']}`);
    if (allHotspots['Monazite']) highlights.push(`Mon x${allHotspots['Monazite']}`);
    if (allHotspots['Musgravite']) highlights.push(`Mus x${allHotspots['Musgravite']}`);
    if (allHotspots['Alexandrite']) highlights.push(`Alex x${allHotspots['Alexandrite']}`);

    const badgeText = highlights.length > 0 ? `🎯 ${highlights.slice(0, 2).join(' ')}` : `🎯 HS: ${hotspotCount}`;
    const hsTitle = (typeof t === 'function' ? t('ring_hotspot_title', { minerals: hsSummary }) : null) || ((lang === 'en' ? 'Ring Hotspots: ' : '環ホットスポット: ') + hsSummary);
    badgeList.push(`<span class="sysmap-mini-badge hotspot" style="background: rgba(250, 204, 21, 0.25); color: #facc15; border: 1px solid rgba(250, 204, 21, 0.6); font-weight: bold;" title="${hsTitle}">${badgeText}</span>`);
  }

  // Sphere HTML with optional ring, belt, and landable arc
  if (isBary) {
    sphere.innerHTML = `
      <div class="sysmap-sphere barycentre-sphere ${effectiveRole}">
        <span class="sysmap-icon-label" style="font-size: 1.35rem; color: #c084fc;">♊</span>
      </div>
    `;
  } else if (isAsteroidBelt) {
    const primaryBeltInfo = ringParser(body.ring_class);
    sphere.innerHTML = `
      <div class="sysmap-sphere asteroid-belt-sphere ${primaryBeltInfo.key}">
        <div class="sysmap-asteroid-orbit-ring ${primaryBeltInfo.key}"></div>
        <span class="sysmap-icon-label" style="font-size: 1.15rem;">🪐</span>
      </div>
    `;
  } else {
    const landableArcHtml = isLandable ? '<div class="sysmap-landable-arc"></div>' : '';
    const ringHtml = hasPlanetaryRings ? `<div class="sysmap-ring-system ${primaryRingKey}"></div>` : '';

    sphere.innerHTML = `
      ${landableArcHtml}
      ${ringHtml}
      <div class="sysmap-sphere ${iconClass} ${role}">
        <span class="sysmap-icon-label">${iconLabel}</span>
      </div>
    `;
  }

  // Short Name (e.g. "1", "1 e", "1 f", "2 f", "B 4", "[AB]", "Belt A")
  const shortName = body.shortName || getBodyShortName(body.body_name, systemName);

  // Info labels below body with full name tooltip and neat badge plate
  const info = document.createElement('div');
  info.className = 'sysmap-body-info';

  const baryOrbitLabel = typeof t === 'function' ? t('barycenter_binary') : '連星共通軌道';
  const beltBodyInfo = isAsteroidBelt ? ringParser(body.ring_class) : null;
  const beltBodyName = beltBodyInfo ? (lang === 'en' ? (beltBodyInfo.nameEn || beltBodyInfo.name) : (beltBodyInfo.nameJa || beltBodyInfo.name)) : '';

  const typeDesc = isBary
    ? (body.planet_class || `${baryOrbitLabel} [${body.starGroup}]`)
    : (isAsteroidBelt
        ? `Asteroid Belt (${beltBodyName})`
        : (body.star_type 
            ? `Star (${body.star_type})` 
            : (body.planet_class || 'Planet')));

  let ringDesc = '';
  if (!isAsteroidBelt && hasPlanetaryRings) {
    const ringNames = ringItems.map(r => {
      const p = ringParser(r.RingClass);
      return lang === 'en' ? (p.nameEn || p.name) : (p.nameJa || p.name);
    });
    ringDesc = ` [Ring: ${ringNames.join('/')}]`;
  } else if (isAsteroidBelt) {
    ringDesc = ` [Belt: ${beltBodyName}]`;
  }

  card.title = `${body.body_name} - ${typeDesc}${ringDesc}`;

  const distStr = body.distance_from_arrival_ls 
    ? formatDistance(body.distance_from_arrival_ls) 
    : (role === 'root-star' ? '0 Ls' : '--');

  const aliasTitle = (typeof t === 'function' && body.bookmark && body.bookmark.alias_name)
    ? t('bookmark_alias_title', { alias: body.bookmark.alias_name })
    : ((lang === 'en' ? 'Alias: ' : 'エイリアス: ') + ((body.bookmark && body.bookmark.alias_name) || ''));
  const aliasHtml = (body.bookmark && body.bookmark.alias_name)
    ? `<div class="sysmap-body-alias" title="${aliasTitle}">🏷️ ${body.bookmark.alias_name}</div>`
    : '';

  // Price Badge (FSS or DSS Bonus) at the very bottom on a dedicated new line
  const isMapped = Boolean(body.is_mapped_by_user || body.was_mapped);
  let priceBadgeHtml = '';
  const kiloFormatter = (typeof formatKiloCredits === 'function')
    ? formatKiloCredits
    : ((typeof window !== 'undefined' && typeof window.formatKiloCredits === 'function') ? window.formatKiloCredits : null);

  if (kiloFormatter) {
    let targetPrice = null;
    let priceLabel = 'FSS';
    let badgeClass = 'fss';

    if (isMapped && body.dss_value > 0) {
      targetPrice = body.dss_value;
      priceLabel = 'DSS Bonus';
      badgeClass = 'dss';
    } else if (body.fss_value > 0) {
      targetPrice = body.fss_value;
      priceLabel = 'FSS';
      badgeClass = 'fss';
    }

    if (targetPrice !== null) {
      const formattedPrice = kiloFormatter(targetPrice);
      if (formattedPrice) {
        const creditsStr = (typeof formatCredits === 'function') ? formatCredits(targetPrice) : `${targetPrice} Cr`;
        priceBadgeHtml = `<div class="sysmap-price-row"><span class="sysmap-mini-badge price-badge ${badgeClass}" title="${priceLabel}: ${creditsStr}">${priceLabel} ${formattedPrice}</span></div>`;
      }
    }
  }

  info.innerHTML = `
    <div class="sysmap-body-shortname" title="${body.body_name}">${shortName}</div>
    ${aliasHtml}
    <div class="sysmap-body-type-plate" title="${body.body_name} - ${typeDesc}">
      <span class="sysmap-type-text">${typeDesc}</span>
    </div>
    <div class="sysmap-body-dist">${distStr}</div>
    ${badgeList.length > 0 ? `<div class="sysmap-badges-row">${badgeList.join('')}</div>` : ''}
    ${priceBadgeHtml}
  `;

  card.appendChild(sphere);
  card.appendChild(info);

  return card;
}
