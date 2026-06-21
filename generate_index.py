#!/usr/bin/env python3
"""Generate index.html with plants_db.json inlined."""
import json

with open("plants_db.json") as f:
    db = json.load(f)

db_json = json.dumps(db, separators=(',', ':'), ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#4a7c59">
<title>Plant Tracker</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --green-dark:#2d5a3d;
  --green:#4a7c59;
  --green-light:#6fa37b;
  --green-pale:#d4ead9;
  --green-mist:#eef6f0;
  --earth:#8b6f47;
  --earth-light:#c4a882;
  --earth-pale:#f5ede0;
  --cream:#faf8f4;
  --white:#ffffff;
  --text:#1e2820;
  --text-mid:#4a5249;
  --text-light:#788076;
  --border:#dde8dc;
  --status-green:#2d7a3d;
  --status-green-bg:#e8f5eb;
  --status-yellow:#8a6d00;
  --status-yellow-bg:#fff9e0;
  --status-red:#c0392b;
  --status-red-bg:#fdecea;
  --radius:14px;
  --radius-sm:8px;
  --shadow:0 2px 12px rgba(0,0,0,.08);
  --shadow-lg:0 6px 28px rgba(0,0,0,.12);
}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--cream);color:var(--text);min-height:100vh;overscroll-behavior-y:none}}
a{{color:inherit;text-decoration:none}}
button{{cursor:pointer;border:none;background:none;font:inherit;color:inherit}}

/* ── Layout ── */
#app{{max-width:520px;margin:0 auto;min-height:100vh;display:flex;flex-direction:column}}
header{{background:var(--green-dark);color:#fff;padding:18px 20px 14px;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.18)}}
header h1{{font-size:1.25rem;font-weight:700;letter-spacing:-.01em;display:flex;align-items:center;gap:8px}}
header .subtitle{{font-size:.78rem;opacity:.75;margin-top:2px}}
#main-content{{flex:1;padding:16px}}

/* ── Nav ── */
nav{{display:flex;gap:8px;margin-bottom:18px}}
nav button{{flex:1;padding:9px 0;border-radius:var(--radius-sm);font-size:.88rem;font-weight:600;transition:background .15s,color .15s;background:var(--white);color:var(--text-mid);border:1.5px solid var(--border)}}
nav button.active{{background:var(--green);color:#fff;border-color:var(--green)}}

/* ── Dashboard ── */
#dashboard-empty{{text-align:center;padding:56px 24px;color:var(--text-light)}}
#dashboard-empty .big-icon{{font-size:3.5rem;margin-bottom:16px}}
#dashboard-empty p{{font-size:1rem;line-height:1.6;max-width:260px;margin:0 auto 20px}}
.btn-primary{{display:inline-flex;align-items:center;gap:6px;padding:11px 22px;border-radius:var(--radius-sm);background:var(--green);color:#fff;font-size:.92rem;font-weight:600;transition:background .15s}}
.btn-primary:hover{{background:var(--green-dark)}}
.btn-danger{{background:var(--status-red-bg);color:var(--status-red);border:1.5px solid #f5c6c2;padding:8px 16px;border-radius:var(--radius-sm);font-size:.85rem;font-weight:600}}
.btn-danger:hover{{background:#f8d7d7}}

/* ── Plant cards ── */
.plant-card{{background:var(--white);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:12px;overflow:hidden;border:1.5px solid var(--border);transition:box-shadow .15s}}
.plant-card:hover{{box-shadow:var(--shadow-lg)}}
.card-header{{display:flex;align-items:flex-start;gap:12px;padding:14px 16px;cursor:pointer;user-select:none}}
.card-status-bar{{width:4px;border-radius:2px;align-self:stretch;flex-shrink:0}}
.status-green .card-status-bar{{background:var(--status-green)}}
.status-yellow .card-status-bar{{background:#f0b100}}
.status-red .card-status-bar{{background:var(--status-red)}}
.card-info{{flex:1;min-width:0}}
.card-name{{font-size:1.02rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card-species{{font-size:.78rem;color:var(--text-light);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card-meta{{display:flex;align-items:center;gap:8px;margin-top:7px;flex-wrap:wrap}}
.sunlight-tag{{display:inline-flex;align-items:center;gap:3px;font-size:.75rem;font-weight:600;padding:2px 8px;border-radius:99px;background:var(--earth-pale);color:var(--earth)}}
.water-status{{font-size:.8rem;font-weight:600;padding:3px 9px;border-radius:99px}}
.status-green .water-status{{background:var(--status-green-bg);color:var(--status-green)}}
.status-yellow .water-status{{background:var(--status-yellow-bg);color:var(--status-yellow)}}
.status-red .water-status{{background:var(--status-red-bg);color:var(--status-red)}}
.card-actions{{display:flex;align-items:center;gap:4px;margin-left:auto;flex-shrink:0}}
.btn-water{{background:var(--green);color:#fff;padding:8px 14px;border-radius:var(--radius-sm);font-size:.82rem;font-weight:700;transition:background .15s;white-space:nowrap}}
.btn-water:hover{{background:var(--green-dark)}}
.btn-expand{{width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:50%;color:var(--text-light);transition:background .15s,transform .2s}}
.btn-expand:hover{{background:var(--green-mist)}}
.btn-expand.open{{transform:rotate(180deg)}}

/* ── Expanded card body ── */
.card-body{{display:none;border-top:1.5px solid var(--border);padding:14px 16px;background:var(--green-mist)}}
.card-body.open{{display:block}}
.card-body-section{{margin-bottom:14px}}
.card-body-section h4{{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--text-light);margin-bottom:8px}}
.log-empty{{font-size:.85rem;color:var(--text-light);font-style:italic}}
.log-list{{list-style:none;max-height:160px;overflow-y:auto}}
.log-list li{{font-size:.83rem;padding:5px 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;gap:8px}}
.log-list li:last-child{{border-bottom:none}}
.log-date{{color:var(--text-mid);font-weight:600;white-space:nowrap}}
.log-note{{color:var(--text-light);flex:1;text-align:right}}

/* ── Edit form inside card ── */
.edit-grid{{display:grid;gap:10px}}
.field-row{{display:flex;flex-direction:column;gap:3px}}
.field-row label{{font-size:.78rem;font-weight:600;color:var(--text-mid)}}
.field-row input,.field-row select,.field-row textarea{{padding:8px 10px;border:1.5px solid var(--border);border-radius:var(--radius-sm);font:inherit;font-size:.88rem;background:var(--white);color:var(--text);transition:border-color .15s}}
.field-row input:focus,.field-row select:focus,.field-row textarea:focus{{outline:none;border-color:var(--green)}}
.note-row{{display:flex;gap:6px}}
.note-row input{{flex:1}}
.btn-save-edit{{background:var(--green);color:#fff;padding:9px 18px;border-radius:var(--radius-sm);font-size:.88rem;font-weight:700;margin-top:4px}}
.btn-save-edit:hover{{background:var(--green-dark)}}
.card-actions-bottom{{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}}

/* ── Add plant form ── */
#add-form{{background:var(--white);border-radius:var(--radius);box-shadow:var(--shadow);padding:20px;border:1.5px solid var(--border)}}
#add-form h2{{font-size:1.08rem;font-weight:700;margin-bottom:16px;color:var(--green-dark)}}
.form-grid{{display:grid;gap:12px}}
.field-label{{font-size:.82rem;font-weight:600;color:var(--text-mid);display:block;margin-bottom:3px}}
.field-input{{width:100%;padding:10px 12px;border:1.5px solid var(--border);border-radius:var(--radius-sm);font:inherit;font-size:.92rem;background:var(--cream);color:var(--text)}}
.field-input:focus{{outline:none;border-color:var(--green);background:var(--white)}}
.species-wrap{{position:relative}}
#species-results{{position:absolute;top:calc(100% + 4px);left:0;right:0;background:var(--white);border:1.5px solid var(--green);border-radius:var(--radius-sm);box-shadow:var(--shadow-lg);z-index:200;max-height:220px;overflow-y:auto;display:none}}
.species-item{{padding:10px 12px;cursor:pointer;font-size:.88rem;border-bottom:1px solid var(--border)}}
.species-item:last-child{{border-bottom:none}}
.species-item:hover{{background:var(--green-mist)}}
.species-item strong{{color:var(--green-dark)}}
.species-item span{{color:var(--text-light);font-size:.8rem;display:block}}
.row-2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.field-hint{{font-size:.75rem;color:var(--text-light);margin-top:3px}}
.btn-submit{{width:100%;padding:13px;border-radius:var(--radius-sm);background:var(--green);color:#fff;font-size:.95rem;font-weight:700;margin-top:6px;transition:background .15s}}
.btn-submit:hover{{background:var(--green-dark)}}
.form-divider{{border:none;border-top:1.5px solid var(--border);margin:4px 0}}
.matched-badge{{background:var(--green-pale);color:var(--green-dark);font-size:.75rem;font-weight:600;padding:3px 9px;border-radius:99px;display:inline-block;margin-top:4px}}

/* ── Toast ── */
#toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(80px);background:var(--green-dark);color:#fff;padding:10px 20px;border-radius:99px;font-size:.88rem;font-weight:600;box-shadow:var(--shadow-lg);transition:transform .3s ease,opacity .3s;opacity:0;z-index:999;pointer-events:none;white-space:nowrap}}
#toast.show{{transform:translateX(-50%) translateY(0);opacity:1}}

/* ── Scrollbar ── */
::-webkit-scrollbar{{width:4px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:var(--green-light);border-radius:2px}}

/* ── Sunlight icon styles ── */
.sun-low{{color:#74a57f}}
.sun-medium{{color:#c4a020}}
.sun-medium-high{{color:#d07010}}
.sun-high{{color:#d04010}}

@media(max-width:400px){{
  .card-header{{padding:12px}}
  .card-body{{padding:12px}}
  #add-form{{padding:16px}}
}}
</style>
</head>
<body>
<div id="app">
  <header>
    <h1>
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V12"/><path d="M5 12C5 7 8 4 12 4s7 3 7 8"/><path d="M5 12c-2-1-3-3-2-5a7 7 0 0 1 4-4"/><path d="M19 12c2-1 3-3 2-5a7 7 0 0 0-4-4"/></svg>
      Plant Tracker
    </h1>
    <div class="subtitle">Watering &amp; sunlight care</div>
  </header>

  <div id="main-content">
    <nav>
      <button id="tab-dashboard" class="active" onclick="showTab('dashboard')">Dashboard</button>
      <button id="tab-add" onclick="showTab('add')">+ Add Plant</button>
    </nav>

    <!-- Dashboard -->
    <div id="view-dashboard">
      <div id="plant-list"></div>
      <div id="dashboard-empty" style="display:none">
        <div class="big-icon">🌱</div>
        <p>No plants yet. Add your first plant to start tracking watering and care.</p>
        <button class="btn-primary" onclick="showTab('add')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Add your first plant
        </button>
      </div>
    </div>

    <!-- Add Plant -->
    <div id="view-add" style="display:none">
      <div id="add-form">
        <h2>Add a new plant</h2>
        <div class="form-grid">
          <div>
            <label class="field-label" for="inp-name">Plant name <span style="color:var(--status-red)">*</span></label>
            <input class="field-input" id="inp-name" type="text" placeholder="e.g. Kitchen Pothos" autocomplete="off">
          </div>

          <div>
            <label class="field-label" for="inp-species">Species (optional)</label>
            <div class="species-wrap">
              <input class="field-input" id="inp-species" type="text" placeholder="Search common or scientific name…" autocomplete="off" autocorrect="off" spellcheck="false">
              <div id="species-results"></div>
            </div>
            <div id="matched-info"></div>
          </div>

          <hr class="form-divider">

          <div class="row-2">
            <div>
              <label class="field-label" for="inp-sunlight">Sunlight</label>
              <select class="field-input" id="inp-sunlight">
                <option value="low">Low</option>
                <option value="medium" selected>Medium</option>
                <option value="medium-high">Medium-High</option>
                <option value="high">High</option>
              </select>
            </div>
            <div>
              <label class="field-label" for="inp-days">Water every (days)</label>
              <input class="field-input" id="inp-days" type="number" min="1" max="90" value="7">
            </div>
          </div>

          <div>
            <label class="field-label" for="inp-last-watered">Last watered</label>
            <input class="field-input" id="inp-last-watered" type="date">
            <div class="field-hint">Leave blank to set as today</div>
          </div>

          <button class="btn-submit" onclick="addPlant()">Save plant</button>
        </div>
      </div>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
// ── Plant database (inlined) ──────────────────────────────────────────────
const PLANTS_DB = {db_json};

// ── Storage ───────────────────────────────────────────────────────────────
const STORAGE_KEY = 'plant-tracker-data';
let plants = [];

function load() {{
  try {{
    const raw = localStorage.getItem(STORAGE_KEY);
    plants = raw ? JSON.parse(raw) : [];
  }} catch(e) {{ plants = []; }}
}}
function save() {{
  localStorage.setItem(STORAGE_KEY, JSON.stringify(plants));
}}
function genId() {{
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}}

// ── Date helpers ──────────────────────────────────────────────────────────
function todayStr() {{
  return new Date().toISOString().slice(0, 10);
}}
function daysBetween(a, b) {{
  // a, b are 'YYYY-MM-DD' strings; returns b - a in days
  return Math.round((new Date(b) - new Date(a)) / 86400000);
}}
function formatDate(d) {{
  if (!d) return '—';
  const dt = new Date(d + 'T00:00:00');
  return dt.toLocaleDateString(undefined, {{month:'short', day:'numeric', year:'numeric'}});
}}

// ── Status calculation ────────────────────────────────────────────────────
function getStatus(plant) {{
  if (!plant.last_watered) return {{ cls:'status-red', label:'Never watered', daysSince: Infinity }};
  const daysSince = daysBetween(plant.last_watered, todayStr());
  const threshold = plant.watering_days || 7;
  if (daysSince <= threshold - 2) return {{ cls:'status-green', label:`Watered ${{daysSince === 0 ? 'today' : daysSince + 'd ago'}}`, daysSince }};
  if (daysSince <= threshold) return {{ cls:'status-yellow', label:`Due in ${{threshold - daysSince}}d`, daysSince }};
  const over = daysSince - threshold;
  return {{ cls:'status-red', label:`Overdue by ${{over}}d`, daysSince }};
}}

// ── Sunlight helpers ──────────────────────────────────────────────────────
const SUN_ICONS = {{
  'low': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" class="sun-low"><circle cx="12" cy="12" r="5"/></svg>',
  'medium': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" class="sun-medium"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
  'medium-high': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" class="sun-medium-high"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
  'high': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" class="sun-high"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
}};
const SUN_LABELS = {{ 'low':'Low light', 'medium':'Medium', 'medium-high':'Med-High', 'high':'Full sun' }};

function sunTag(sunlight) {{
  const icon = SUN_ICONS[sunlight] || SUN_ICONS['medium'];
  const label = SUN_LABELS[sunlight] || sunlight;
  return `<span class="sunlight-tag">${{icon}} ${{label}}</span>`;
}}

// ── Render dashboard ─────────────────────────────────────────────────────
function renderDashboard() {{
  const list = document.getElementById('plant-list');
  const empty = document.getElementById('dashboard-empty');

  if (!plants.length) {{
    list.innerHTML = '';
    empty.style.display = '';
    return;
  }}
  empty.style.display = 'none';

  // Sort most overdue first
  const sorted = [...plants].sort((a, b) => {{
    const sa = getStatus(a), sb = getStatus(b);
    const score = s => s.cls === 'status-red' ? 2 : s.cls === 'status-yellow' ? 1 : 0;
    const diff = score(sb) - score(sa);
    if (diff !== 0) return diff;
    return (sb.daysSince||0) - (sa.daysSince||0);
  }});

  list.innerHTML = sorted.map(p => renderCard(p)).join('');
}}

function renderCard(plant) {{
  const status = getStatus(plant);
  const isOpen = window._openCards && window._openCards.has(plant.id);
  return `<div class="plant-card ${{status.cls}}" id="card-${{plant.id}}">
    <div class="card-header" onclick="toggleCard('${{plant.id}}')">
      <div class="card-status-bar"></div>
      <div class="card-info">
        <div class="card-name">${{esc(plant.name)}}</div>
        ${{plant.species ? `<div class="card-species">${{esc(plant.species)}}</div>` : ''}}
        <div class="card-meta">
          ${{sunTag(plant.sunlight || 'medium')}}
          <span class="water-status">${{status.label}}</span>
        </div>
      </div>
      <div class="card-actions">
        <button class="btn-water" onclick="waterNow(event,'${{plant.id}}')" title="Water now">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 2C6.48 2 2 9 2 13a10 10 0 0 0 20 0c0-4-4.48-11-10-11z"/></svg>
          Water
        </button>
        <button class="btn-expand ${{isOpen ? 'open' : ''}}" onclick="toggleCard('${{plant.id}}')" title="Details">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </button>
      </div>
    </div>
    <div class="card-body ${{isOpen ? 'open' : ''}}" id="body-${{plant.id}}">
      ${{renderCardBody(plant)}}
    </div>
  </div>`;
}}

function renderCardBody(plant) {{
  const logItems = (plant.log || []).slice().reverse().map(e =>
    `<li><span class="log-date">${{formatDate(e.date)}}</span><span class="log-note">${{esc(e.note||'')}}</span></li>`
  ).join('');

  return `
    <div class="card-body-section">
      <h4>Watering history</h4>
      ${{logItems ? `<ul class="log-list">${{logItems}}</ul>` : '<p class="log-empty">No watering recorded yet.</p>'}}
    </div>
    <div class="card-body-section">
      <h4>Water with note</h4>
      <div class="note-row">
        <input type="text" id="note-${{plant.id}}" class="field-input" placeholder="Optional note…" style="font-size:.85rem;padding:7px 10px">
        <button class="btn-water" onclick="waterNowNote('${{plant.id}}')">Log</button>
      </div>
    </div>
    <div class="card-body-section">
      <h4>Edit details</h4>
      <div class="edit-grid">
        <div class="field-row">
          <label>Name</label>
          <input type="text" id="edit-name-${{plant.id}}" value="${{esc(plant.name)}}" class="field-input" style="font-size:.88rem;padding:7px 10px">
        </div>
        <div class="field-row">
          <label>Species</label>
          <input type="text" id="edit-species-${{plant.id}}" value="${{esc(plant.species||'')}}" class="field-input" style="font-size:.88rem;padding:7px 10px">
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <div class="field-row">
            <label>Sunlight</label>
            <select id="edit-sun-${{plant.id}}" class="field-input" style="font-size:.88rem;padding:7px 10px">
              ${{['low','medium','medium-high','high'].map(v=>`<option value="${{v}}" ${{plant.sunlight===v?'selected':''}}>${{v}}</option>`).join('')}}
            </select>
          </div>
          <div class="field-row">
            <label>Water (days)</label>
            <input type="number" id="edit-days-${{plant.id}}" value="${{plant.watering_days||7}}" min="1" max="90" class="field-input" style="font-size:.88rem;padding:7px 10px">
          </div>
        </div>
        <div class="field-row">
          <label>Last watered</label>
          <input type="date" id="edit-date-${{plant.id}}" value="${{plant.last_watered||''}}" class="field-input" style="font-size:.88rem;padding:7px 10px">
        </div>
      </div>
      <div class="card-actions-bottom">
        <button class="btn-save-edit" onclick="saveEdit('${{plant.id}}')">Save changes</button>
        <button class="btn-danger" onclick="deletePlant('${{plant.id}}')">Delete plant</button>
      </div>
    </div>
  `;
}}

// ── Card interactions ─────────────────────────────────────────────────────
window._openCards = new Set();

function toggleCard(id) {{
  if (_openCards.has(id)) _openCards.delete(id); else _openCards.add(id);
  renderDashboard();
}}

function waterNow(e, id) {{
  e.stopPropagation();
  const plant = plants.find(p => p.id === id);
  if (!plant) return;
  plant.last_watered = todayStr();
  plant.log = plant.log || [];
  plant.log.push({{date: todayStr(), note: ''}});
  save();
  toast('Watered ' + plant.name + ' today!');
  renderDashboard();
}}

function waterNowNote(id) {{
  const plant = plants.find(p => p.id === id);
  if (!plant) return;
  const noteEl = document.getElementById('note-' + id);
  const note = noteEl ? noteEl.value.trim() : '';
  plant.last_watered = todayStr();
  plant.log = plant.log || [];
  plant.log.push({{date: todayStr(), note}});
  save();
  toast('Logged watering' + (note ? ' with note' : ''));
  renderDashboard();
}}

function saveEdit(id) {{
  const plant = plants.find(p => p.id === id);
  if (!plant) return;
  plant.name = document.getElementById('edit-name-' + id).value.trim() || plant.name;
  plant.species = document.getElementById('edit-species-' + id).value.trim();
  plant.sunlight = document.getElementById('edit-sun-' + id).value;
  plant.watering_days = parseInt(document.getElementById('edit-days-' + id).value) || plant.watering_days;
  const dateVal = document.getElementById('edit-date-' + id).value;
  if (dateVal) plant.last_watered = dateVal;
  save();
  toast('Plant updated!');
  renderDashboard();
}}

function deletePlant(id) {{
  if (!confirm('Delete this plant? This cannot be undone.')) return;
  plants = plants.filter(p => p.id !== id);
  _openCards.delete(id);
  save();
  toast('Plant removed.');
  renderDashboard();
}}

// ── Add plant ─────────────────────────────────────────────────────────────
let _matchedDbEntry = null;

function addPlant() {{
  const name = document.getElementById('inp-name').value.trim();
  if (!name) {{ toast('Please enter a plant name'); return; }}
  const species = document.getElementById('inp-species').value.trim();
  const sunlight = document.getElementById('inp-sunlight').value;
  const days = parseInt(document.getElementById('inp-days').value) || 7;
  const lastWatered = document.getElementById('inp-last-watered').value || todayStr();

  const plant = {{
    id: genId(),
    name,
    species,
    sunlight,
    watering_days: days,
    last_watered: lastWatered,
    log: [{{date: lastWatered, note: 'Added to tracker'}}],
  }};
  plants.push(plant);
  save();
  toast(name + ' added!');
  resetAddForm();
  showTab('dashboard');
}}

function resetAddForm() {{
  document.getElementById('inp-name').value = '';
  document.getElementById('inp-species').value = '';
  document.getElementById('inp-sunlight').value = 'medium';
  document.getElementById('inp-days').value = '7';
  document.getElementById('inp-last-watered').value = '';
  document.getElementById('matched-info').innerHTML = '';
  document.getElementById('species-results').style.display = 'none';
  _matchedDbEntry = null;
}}

// ── Species autocomplete ──────────────────────────────────────────────────
const speciesInput = document.getElementById('inp-species');
const speciesResults = document.getElementById('species-results');

function normalise(s) {{
  return s.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
}}

speciesInput.addEventListener('input', function() {{
  const q = this.value.trim();
  if (q.length < 2) {{ speciesResults.style.display = 'none'; return; }}
  const qn = normalise(q);
  const hits = PLANTS_DB.filter(p =>
    normalise(p.common_name).includes(qn) ||
    normalise(p.scientific_name).includes(qn)
  ).slice(0, 8);
  if (!hits.length) {{ speciesResults.style.display = 'none'; return; }}
  speciesResults.innerHTML = hits.map((p, i) =>
    `<div class="species-item" data-idx="${{i}}" onclick="selectSpecies(${{JSON.stringify(p).replace(/</g,'&lt;')}})">
      <strong>${{esc(p.common_name)}}</strong>
      <span>${{esc(p.scientific_name)}}</span>
    </div>`
  ).join('');
  speciesResults.style.display = '';
}});

speciesInput.addEventListener('blur', function() {{
  setTimeout(() => {{ speciesResults.style.display = 'none'; }}, 200);
}});

function selectSpecies(p) {{
  _matchedDbEntry = p;
  speciesInput.value = p.common_name;
  document.getElementById('inp-sunlight').value = p.sunlight || 'medium';
  document.getElementById('inp-days').value = p.watering_days || 7;
  document.getElementById('matched-info').innerHTML =
    `<span class="matched-badge">✓ Auto-filled from database</span>`;
  speciesResults.style.display = 'none';
}}

// ── Navigation ────────────────────────────────────────────────────────────
function showTab(tab) {{
  document.getElementById('view-dashboard').style.display = tab === 'dashboard' ? '' : 'none';
  document.getElementById('view-add').style.display = tab === 'add' ? '' : 'none';
  document.getElementById('tab-dashboard').className = tab === 'dashboard' ? 'active' : '';
  document.getElementById('tab-add').className = tab === 'add' ? 'active' : '';
  if (tab === 'dashboard') renderDashboard();
}}

// ── Toast notification ────────────────────────────────────────────────────
let _toastTimer;
function toast(msg) {{
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}}

// ── Escape HTML ───────────────────────────────────────────────────────────
function esc(s) {{
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

// ── Init ──────────────────────────────────────────────────────────────────
load();
renderDashboard();
</script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(HTML)

size = len(HTML.encode("utf-8"))
print(f"index.html written — {size:,} bytes ({size//1024} KB)")
print("Database entries inlined:", len(db))
