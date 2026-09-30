async function getJSON(url) {
  const r = await fetch(url, { credentials: "same-origin" });
  return r.json();
}
async function postJSON(url, body) {
  const r = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return r.json();
}
function riskClass(level) {
  return "risk-" + (level || "LOW");
}
function sectorBadge(level) {
  return `<span class="sector-badge sector-${level}">${level}</span>`;
}
