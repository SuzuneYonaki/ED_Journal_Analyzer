// Addon-awareness for the frontend: (1) loads optional addon UI panels,
// and (2) wraps fetch() so that calling a disabled addon's REST endpoint
// (which now 404s instead of existing) surfaces a visible toast instead of
// failing silently. Path -> addon-id mapping mirrors the `prefix="/api"`
// routes each addon reclaims (see addons/*/addon.py).
const ADDON_PATH_RULES = [
  { addonId: 'edsm_sync', test: (p) => /^\/api\/systems\/\d+\/edsm_sync$/.test(p) },
  { addonId: 'spansh_sync', test: (p) => /^\/api\/systems\/\d+\/spansh_sync$/.test(p) },
  { addonId: 'tts', test: (p) => p === '/api/tts_settings' || p.startsWith('/api/tts/') },
  {
    addonId: 'export_share',
    test: (p) => p.startsWith('/api/export/') || p.startsWith('/api/import/') || p === '/api/system/reveal-file',
  },
];

window.__disabledAddons = window.__disabledAddons || {};
const _lastToastAt = {};

function showAddonDisabledToast(name) {
  const now = Date.now();
  if (_lastToastAt[name] && now - _lastToastAt[name] < 8000) return; // de-dupe rapid repeats
  _lastToastAt[name] = now;

  let toast = document.getElementById('addon-disabled-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'addon-disabled-toast';
    toast.style.position = 'fixed';
    toast.style.bottom = '24px';
    toast.style.left = '24px';
    toast.style.background = 'rgba(10, 16, 26, 0.96)';
    toast.style.border = '1px solid #f59e0b';
    toast.style.borderRadius = '8px';
    toast.style.padding = '12px 16px';
    toast.style.color = '#fff';
    toast.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.7)';
    toast.style.zIndex = '99999';
    toast.style.maxWidth = '420px';
    toast.style.fontSize = '0.82rem';
    toast.style.lineHeight = '1.5';
    toast.style.transition = 'opacity 0.3s';
    document.body.appendChild(toast);
  }
  const msg = (typeof t === 'function' ? t('addon_disabled_toast', { name }) : null)
    || `⚠️ This feature is currently disabled (${name}).`;
  toast.textContent = msg;
  toast.style.opacity = '1';
  clearTimeout(toast._hideTimer);
  toast._hideTimer = setTimeout(() => {
    toast.style.opacity = '0';
  }, 5000);
}

(function wrapFetchForAddonGating() {
  const originalFetch = window.fetch.bind(window);
  window.fetch = async function (input, init) {
    const response = await originalFetch(input, init);
    if (response.status === 404) {
      try {
        const rawUrl = typeof input === 'string' ? input : input.url;
        const path = new URL(rawUrl, window.location.origin).pathname;
        const rule = ADDON_PATH_RULES.find((r) => r.test(path));
        const addonName = rule && window.__disabledAddons[rule.addonId];
        if (addonName) {
          showAddonDisabledToast(addonName);
        }
      } catch (e) {
        // Never let gating logic break the caller's real request handling.
      }
    }
    return response;
  };
})();

// Lightweight loader for optional addon UI panels.
// Each enabled+loaded addon may expose a ui_entry ES module (see GET /api/addons).
// The module's default export receives the panel container div and the addon's metadata.
(async function initAddons() {
  let addons = [];
  try {
    const res = await fetch('/api/addons');
    const json = await res.json();
    addons = json.data ?? [];
  } catch (e) {
    console.warn('[Addons] Failed to fetch /api/addons', e);
    return;
  }

  window.__disabledAddons = {};
  for (const a of addons) {
    if (!a.enabled || !a.loaded) {
      window.__disabledAddons[a.id] = a.name;
    }
  }

  const host = document.getElementById('addon-panels');
  if (!host) return;

  const withUi = addons.filter((a) => a.enabled && a.loaded && a.ui_entry);
  if (withUi.length === 0) return;

  host.hidden = false;
  for (const addon of withUi) {
    const container = document.createElement('div');
    container.className = 'addon-panel';
    container.dataset.addonId = addon.id;
    host.appendChild(container);
    try {
      const mod = await import(addon.ui_entry);
      if (typeof mod.default === 'function') {
        mod.default(container, addon);
      }
    } catch (e) {
      console.error(`[Addons] Failed to load UI for '${addon.id}'`, e);
    }
  }
})();
