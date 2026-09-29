// Lightweight loader for optional addon UI panels.
// Each enabled+loaded addon may expose a ui_entry ES module (see GET /api/addons).
// The module's default export receives the panel container div and the addon's metadata.
(async function initAddons() {
  const host = document.getElementById('addon-panels');
  if (!host) return;

  let addons = [];
  try {
    const res = await fetch('/api/addons');
    const json = await res.json();
    addons = json.data ?? [];
  } catch (e) {
    console.warn('[Addons] Failed to fetch /api/addons', e);
    return;
  }

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
