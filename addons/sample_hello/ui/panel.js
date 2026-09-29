export default function init(container, addon) {
  container.innerHTML = `
    <div class="addon-card">
      <strong>${addon.name}</strong> v${addon.version}
      <div class="addon-card-sub">Scan events seen this session: <span data-role="count">…</span></div>
    </div>
  `;
  fetch(`/api/addons/${addon.id}/status`)
    .then((r) => r.json())
    .then((data) => {
      const el = container.querySelector('[data-role="count"]');
      if (el) el.textContent = data.scan_events_seen;
    })
    .catch(() => {});
}
