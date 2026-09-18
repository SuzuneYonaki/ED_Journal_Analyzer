/**
 * utils.js - Core Formatting, Domain Parsers & Utility Functions
 * Elite Dangerous Journal Analyzer
 */

// Numeric & Unit Formatting
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

// App Language Helper
function getAppLang() {
  if (typeof currentLang !== 'undefined' && (currentLang === 'en' || currentLang === 'ja')) {
    return currentLang;
  }
  if (typeof window !== 'undefined' && window.currentLang) {
    return window.currentLang;
  }
  return 'ja';
}

function formatSecondsToDaysOrHours(sec) {
  if (!sec) return '--';
  const hours = Math.abs(sec) / 3600;
  const lang = getAppLang();
  const hUnit = (typeof t === 'function' ? t('hours_unit') : null) || (lang === 'en' ? 'h' : '時間');
  const dUnit = (typeof t === 'function' ? t('days_unit') : null) || (lang === 'en' ? 'd' : '日');
  if (hours < 48) return `${hours.toFixed(1)} ${hUnit}`;
  const days = hours / 24;
  return `${days.toFixed(1)} ${dUnit}`;
}

// HTML Escaper
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Markdown Parser
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

// Ring Classification Parser
function parseRingClass(rawClass) {
  const lang = getAppLang();
  if (!rawClass || rawClass === '不明' || String(rawClass).toLowerCase() === 'unknown' || String(rawClass).toLowerCase() === 'eringclass_unknown') {
    return {
      key: 'unknown',
      nameEn: 'Unknown',
      nameJa: '不明',
      name: lang === 'en' ? 'Unknown' : '不明',
      color: '#94a3b8',
      icon: '💍',
      bg: 'rgba(148,163,184,0.15)',
      border: 'rgba(148,163,184,0.4)',
      descriptionEn: '',
      descriptionJa: '',
      description: ''
    };
  }
  const lower = rawClass.toLowerCase();
  let res;
  if (lower.includes('icy')) {
    res = {
      key: 'icy',
      nameEn: 'Icy',
      nameJa: '氷',
      icon: '❄️',
      color: '#38bdf8',
      bg: 'rgba(56, 189, 248, 0.18)',
      border: 'rgba(56, 189, 248, 0.45)',
      descriptionEn: 'Fleet Carrier fuel (Tritium) / Low Temperature Diamonds (LTD) source',
      descriptionJa: 'Fleet Carrier燃料 (Tritium) / 低温ダイヤモンド (LTD) 産地'
    };
  } else if (lower.includes('metallic') || lower.includes('metalic')) {
    res = {
      key: 'metallic',
      nameEn: 'Metallic',
      nameJa: '金属質',
      icon: '🪙',
      color: '#facc15',
      bg: 'rgba(250, 204, 21, 0.18)',
      border: 'rgba(250, 204, 21, 0.5)',
      descriptionEn: 'High-value laser mining (Platinum, Painite, etc.) optimal',
      descriptionJa: 'プラチナ (Platinum) / ペイン石 (Painite) 等 最も高価値なレーザー採掘適性'
    };
  } else if (lower.includes('metal')) {
    res = {
      key: 'metal_rich',
      nameEn: 'Metal Rich',
      nameJa: '金属豊富',
      icon: '🪐',
      color: '#fb923c',
      bg: 'rgba(251, 146, 60, 0.18)',
      border: 'rgba(251, 146, 60, 0.5)',
      descriptionEn: 'Industrial and precious metal commodities',
      descriptionJa: '各種工業用・貴金属素材'
    };
  } else if (lower.includes('rocky')) {
    res = {
      key: 'rocky',
      nameEn: 'Rocky',
      nameJa: '岩石',
      icon: '🪨',
      color: '#cbd5e1',
      bg: 'rgba(203, 213, 225, 0.18)',
      border: 'rgba(203, 213, 225, 0.45)',
      descriptionEn: 'High-value deep core mining (Musgravite, Alexandrite, etc.)',
      descriptionJa: 'マスグラバイト / アレキサンドライト等 高額深部鉱石コア採掘適性'
    };
  } else {
    const cleanName = rawClass.replace('eRingClass_', '');
    const isUnk = !cleanName || cleanName === '不明' || cleanName.toLowerCase() === 'unknown';
    const nameEn = isUnk ? 'Unknown' : cleanName;
    const nameJa = isUnk ? '不明' : cleanName;
    res = {
      key: isUnk ? 'unknown' : 'other',
      nameEn: nameEn,
      nameJa: nameJa,
      icon: '💍',
      color: isUnk ? '#94a3b8' : '#a78bfa',
      bg: isUnk ? 'rgba(148,163,184,0.15)' : 'rgba(167, 139, 250, 0.18)',
      border: isUnk ? 'rgba(148,163,184,0.4)' : 'rgba(167, 139, 250, 0.45)',
      descriptionEn: '',
      descriptionJa: ''
    };
  }
  res.name = lang === 'en' ? res.nameEn : res.nameJa;
  res.description = lang === 'en' ? res.descriptionEn : res.descriptionJa;
  return res;
}

// Reserve Level Parser
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
  const base = map[key] || { en: reserve, ja: reserve, color: '#94a3b8', icon: '📊' };
  const lang = getAppLang();
  return {
    ...base,
    name: lang === 'en' ? base.en : base.ja,
    label: lang === 'en' ? base.en : `${base.en} (${base.ja})`
  };
}

// Star Spectrum Styles
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
  // Proto-stars / Young Stellar Objects
  if (st.startsWith('AEBE')) {
    return { bg: '#3b0764', text: '#d8b4fe', border: '#c084fc' }; // Herbig Ae/Be -> Purple
  }
  if (st.startsWith('TTS')) {
    return { bg: '#831843', text: '#fbcfe8', border: '#f472b6' }; // T Tauri -> Pink
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

// Celestial Body Icons & Badges
function getBodyIconClass(body) {
  if (!body) return 'icon-rocky';
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
  if (!body) return 'P';
  if (body.star_type) {
    if (body.star_type.toUpperCase() === 'SUPERMASSIVEBLACKHOLE') return 'SMBH';
    return body.star_type;
  }
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

// Module Settings (Exobiology, Rhino Mining, Population/Faction)
const defaultModuleSettings = {
  exobiology: true,
  rhino: false,
  faction: false
};

function getModuleSettings() {
  try {
    const raw = (typeof localStorage !== 'undefined') ? localStorage.getItem('ed_module_settings') : null;
    if (raw) {
      return { ...defaultModuleSettings, ...JSON.parse(raw) };
    }
  } catch (e) {
    console.warn('Failed to load module settings:', e);
  }
  return { ...defaultModuleSettings };
}

function saveModuleSettings(settings) {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ed_module_settings', JSON.stringify(settings));
    }
    if (typeof fetch === 'function') {
      fetch('/api/module_settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      }).catch(() => {});
    }
  } catch (e) {
    console.warn('Failed to save module settings:', e);
  }
}

// Window / Global Export
if (typeof window !== 'undefined') {
  window.getAppLang = getAppLang;
  window.formatCredits = formatCredits;
  window.formatNumber = formatNumber;
  window.formatDistance = formatDistance;
  window.formatSecondsToDaysOrHours = formatSecondsToDaysOrHours;
  window.escapeHtml = escapeHtml;
  window.parseMarkdown = parseMarkdown;
  window.parseRingClass = parseRingClass;
  window.parseReserveLevel = parseReserveLevel;
  window.getStarTypeStyle = getStarTypeStyle;
  window.getBodyIconClass = getBodyIconClass;
  window.getBodyIconLabel = getBodyIconLabel;
  window.defaultModuleSettings = defaultModuleSettings;
  window.getModuleSettings = getModuleSettings;
  window.saveModuleSettings = saveModuleSettings;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getAppLang,
    formatCredits,
    formatNumber,
    formatDistance,
    formatSecondsToDaysOrHours,
    escapeHtml,
    parseMarkdown,
    parseRingClass,
    parseReserveLevel,
    getStarTypeStyle,
    getBodyIconClass,
    getBodyIconLabel,
    defaultModuleSettings,
    getModuleSettings,
    saveModuleSettings
  };
}

