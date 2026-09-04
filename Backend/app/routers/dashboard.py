from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Classy Municipal Dashboard"])

DASHBOARD_CLASSY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CleanCity Copilot | Municipal Triage Engine (Hyderabad, Sindh)</title>
    
    <!-- Google Fonts & Font Awesome -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Real Leaflet Geographic Map -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <style>
        :root {
            --bg-page: #f8fafc;
            --surface: #ffffff;
            --surface-muted: #f1f5f9;
            --border: #e2e8f0;
            --border-strong: #cbd5e1;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --text-sub: #475569;
            
            --civic-blue: #1e40af;
            --civic-blue-hover: #1d4ed8;
            --civic-blue-light: #eff6ff;
            
            --crit-bg: #fef2f2;
            --crit-text: #b91c1c;
            --crit-border: #fecaca;
            
            --high-bg: #fffbeb;
            --high-text: #b45309;
            --high-border: #fde68a;
            
            --med-bg: #eff6ff;
            --med-text: #1d4ed8;
            --med-border: #bfdbfe;
            
            --res-bg: #ecfdf5;
            --res-text: #047857;
            --res-border: #a7f3d0;
        }

        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            background-color: var(--bg-page);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
            min-height: 100vh;
            padding: 1.5rem 2rem;
        }

        /* Top Government / Municipal Brand Bar */
        .top-navbar {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1rem 1.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03), 0 4px 6px -2px rgba(0,0,0,0.02);
            margin-bottom: 1.5rem;
        }

        .brand-box {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .gov-seal {
            width: 44px;
            height: 44px;
            background: var(--civic-blue-light);
            border: 1px solid #bfdbfe;
            color: var(--civic-blue);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
        }

        .brand-title {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text-main);
            letter-spacing: -0.5px;
        }

        .brand-sub {
            font-size: 0.85rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 2px;
        }

        .location-badge {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            color: #334155;
            font-weight: 600;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 6px;
        }

        .nav-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .btn-action {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 0.55rem 1rem;
            font-size: 0.88rem;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
        }

        .btn-outline {
            background: var(--surface);
            border: 1px solid var(--border-strong);
            color: var(--text-sub);
        }
        .btn-outline:hover {
            background: var(--surface-muted);
            color: var(--text-main);
        }

        .btn-primary {
            background: var(--civic-blue);
            border: 1px solid var(--civic-blue);
            color: #ffffff;
        }
        .btn-primary:hover {
            background: var(--civic-blue-hover);
        }

        /* KPI Executive Metric Cards */
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .kpi-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            position: relative;
        }

        .kpi-title {
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .kpi-value {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.85rem;
            font-weight: 800;
            color: var(--text-main);
            margin: 0.35rem 0 0.2rem 0;
            letter-spacing: -0.5px;
        }

        .kpi-desc {
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        /* Tab Navigation Bar */
        .tab-bar {
            display: flex;
            gap: 8px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.5rem;
        }

        .tab-btn {
            background: none;
            border: none;
            border-bottom: 2px solid transparent;
            padding: 0.75rem 1.25rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.15s ease;
        }

        .tab-btn:hover {
            color: var(--text-main);
        }

        .tab-btn.active {
            color: var(--civic-blue);
            border-bottom-color: var(--civic-blue);
        }

        .tab-pane { display: none; }
        .tab-pane.active { display: block; }

        /* Real Leaflet Map Container */
        .map-section {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }

        .map-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        #real-map {
            width: 100%;
            height: 520px;
            border-radius: 10px;
            border: 1px solid var(--border);
            z-index: 1;
        }

        .map-legend {
            margin-top: 0.75rem;
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            font-size: 0.82rem;
            color: var(--text-sub);
            padding: 8px 12px;
            background: var(--surface-muted);
            border-radius: 8px;
        }

        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
        }

        /* Database Table */
        .db-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }

        .db-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            margin-top: 1rem;
        }

        .db-table th {
            background: var(--surface-muted);
            color: var(--text-main);
            font-weight: 600;
            text-align: left;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .db-table td {
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border);
            color: var(--text-sub);
        }

        .db-table tr:hover {
            background-color: #fcfdfe;
        }

        /* Status & Severity Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .badge-Critical { background: var(--crit-bg); color: var(--crit-text); border: 1px solid var(--crit-border); }
        .badge-High { background: var(--high-bg); color: var(--high-text); border: 1px solid var(--high-border); }
        .badge-Medium { background: var(--med-bg); color: var(--med-text); border: 1px solid var(--med-border); }
        .badge-Resolved { background: var(--res-bg); color: var(--res-text); border: 1px solid var(--res-border); }
        .badge-Open { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
        .badge-InProgress { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }

        /* Forms */
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }
        @media(max-width: 900px){ .form-grid { grid-template-columns: 1fr; } }

        .form-group { margin-bottom: 1rem; }
        label {
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 6px;
        }
        input, select, textarea {
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border-strong);
            border-radius: 8px;
            padding: 0.65rem 0.9rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            color: var(--text-main);
            transition: border-color 0.15s ease;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--civic-blue);
            box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
        }
    </style>
</head>
<body>

    <!-- Top Government Brand Navbar -->
    <header class="top-navbar">
        <div class="brand-box">
            <div class="gov-seal"><i class="fa-solid fa-landmark"></i></div>
            <div>
                <h1 class="brand-title">CleanCity Copilot</h1>
                <div class="brand-sub">
                    <span>Municipal Triage & AI Dispatch Engine</span>
                    &bull; <span class="location-badge"><i class="fa-solid fa-location-dot"></i> Hyderabad, Sindh</span>
                </div>
            </div>
        </div>
        <div class="nav-actions">
            <button class="btn-action btn-outline" onclick="seedHyderabadData()"><i class="fa-solid fa-database"></i> Seed 12 Hyderabad Landmarks</button>
            <a href="http://localhost:8501" target="_blank" class="btn-action btn-outline"><i class="fa-solid fa-desktop"></i> Open Streamlit Frontend</a>
            <a href="/docs" target="_blank" class="btn-action btn-primary"><i class="fa-solid fa-code"></i> API Docs</a>
        </div>
    </header>

    <!-- Top KPI Cards -->
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">Active Open Issues</div>
            <div class="kpi-value" id="kpi-open">--</div>
            <div class="kpi-desc">Awaiting municipal field crew</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Critical Road/Drain Hazards</div>
            <div class="kpi-value" style="color: var(--crit-text);" id="kpi-crit">--</div>
            <div class="kpi-desc">High risk to vehicular safety</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Resolved Today</div>
            <div class="kpi-value" style="color: var(--res-text);" id="kpi-res">--</div>
            <div class="kpi-desc">Sanitation & patch work completed</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Total Verified Reports</div>
            <div class="kpi-value" id="kpi-total">--</div>
            <div class="kpi-desc">Spatial 50-meter cluster deduplicated</div>
        </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tab-bar">
        <button class="tab-btn active" onclick="switchTab('tab-map')"><i class="fa-solid fa-map-location-dot"></i> Real Hyderabad Street Map & 50m Deduplication</button>
        <button class="tab-btn" onclick="switchTab('tab-db')"><i class="fa-solid fa-table-list"></i> Municipal Admin Database Explorer</button>
        <button class="tab-btn" onclick="switchTab('tab-submit')"><i class="fa-solid fa-paper-plane"></i> Citizen Issue Submission & AI Triage</button>
        <button class="tab-btn" onclick="switchTab('tab-system')"><i class="fa-solid fa-server"></i> System Architecture & Frontend Bridge</button>
    </div>

    <!-- TAB 1: REAL HYDERABAD GEOGRAPHIC MAP -->
    <div id="tab-map" class="tab-pane active">
        <div class="map-section">
            <div class="map-header">
                <div>
                    <h3 style="font-size: 1.1rem; font-weight: 700;">Real Geographic Map &bull; Hyderabad, Sindh</h3>
                    <p style="font-size: 0.82rem; color: var(--text-muted);">Real street-level coordinates with 50-meter deduplication zones.</p>
                </div>
                <button class="btn-action btn-outline" onclick="loadDashboardData()"><i class="fa-solid fa-arrows-rotate"></i> Refresh Map</button>
            </div>
            
            <div id="real-map"></div>

            <div class="map-legend">
                <div><span class="legend-dot" style="background:#dc2626;"></span> <b>Critical:</b> Immediate road/sewage danger</div>
                <div><span class="legend-dot" style="background:#d97706;"></span> <b>High:</b> Significant refuse/pothole</div>
                <div><span class="legend-dot" style="background:#2563eb;"></span> <b>Medium:</b> Localized issue</div>
                <div><span style="border: 2px dashed #2563eb; width:12px; height:12px; border-radius:50%; display:inline-block; margin-right:4px;"></span> <b>50m Perimeter:</b> Automated duplicate absorption perimeter</div>
            </div>
        </div>
    </div>

    <!-- TAB 2: DATABASE EXPLORER -->
    <div id="tab-db" class="tab-pane">
        <div class="db-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <h3 style="font-size: 1.1rem; font-weight: 700;">SQLite Database Explorer (`complaints` Table)</h3>
                    <p style="font-size: 0.82rem; color: var(--text-muted);">Live records connected directly with Mir's Streamlit frontend.</p>
                </div>
                <button class="btn-action btn-outline" onclick="loadDashboardData()"><i class="fa-solid fa-rotate"></i> Refresh Table</button>
            </div>

            <div style="overflow-x: auto;">
                <table class="db-table">
                    <thead>
                        <tr>
                            <th>Ticket ID</th>
                            <th>Category</th>
                            <th>Severity</th>
                            <th>Landmark / GPS</th>
                            <th>AI Action Plan</th>
                            <th>Duplicates</th>
                            <th>Status (Click to Update)</th>
                        </tr>
                    </thead>
                    <tbody id="db-tbody">
                        <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading SQLite records...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TAB 3: CITIZEN REPORT SUBMISSION -->
    <div id="tab-submit" class="tab-pane">
        <div class="db-card">
            <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem;">Citizen Complaint Submission</h3>
            <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1.5rem;">Submit photos and descriptions. The backend will verify, deduplicate, and dispatch.</p>
            
            <form id="report-form" class="form-grid">
                <div>
                    <div class="form-group">
                        <label><i class="fa-solid fa-camera"></i> Issue Photo (JPEG, PNG, WebP)</label>
                        <input type="file" id="form-image" accept="image/*" required>
                    </div>
                    <div class="form-group">
                        <label><i class="fa-solid fa-microphone"></i> Voice Note in Urdu / Sindhi (Optional)</label>
                        <input type="file" id="form-audio" accept="audio/*">
                    </div>
                    <div class="form-group">
                        <label><i class="fa-solid fa-pen"></i> Description</label>
                        <input type="text" id="form-desc" placeholder="e.g. Autobahn road Latifabad main deep pothole ban chuka hai">
                    </div>
                </div>

                <div>
                    <div class="form-group">
                        <label><i class="fa-solid fa-location-dot"></i> Hyderabad Landmark Presets</label>
                        <select id="landmark-select" onchange="applyLandmarkPreset()">
                            <option value="25.392000,68.373500">Pacco Qillo (Pakka Qila), Shahi Bazaar Gate</option>
                            <option value="25.378000,68.352000">Autobahn Road, Latifabad Unit 2</option>
                            <option value="25.395000,68.332000">Naseem Nagar Chowk, Qasimabad</option>
                            <option value="25.367000,68.358000">Latifabad Unit 7, Near General Hospital</option>
                            <option value="25.405000,68.338000">Wadhu Wah Road, Qasimabad</option>
                            <option value="25.391000,68.362000">Haider Chowk / Saddar Hyderabad</option>
                            <option value="25.397000,68.369000">Station Road / Resham Gali</option>
                            <option value="25.432000,68.315000">Kotri Barrage Indus Bridge Approach</option>
                            <option value="25.402000,68.356000">Thandi Sarak / Hyderabad Gymkhana</option>
                            <option value="25.394000,68.365000">Hirabad / Tower Market Chowk</option>
                            <option value="25.388000,68.341000">Citizen Colony, Qasimabad</option>
                            <option value="25.385000,68.318000">SITE Industrial Area Hyderabad</option>
                        </select>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;" class="form-group">
                        <div>
                            <label>Latitude</label>
                            <input type="text" id="form-lat" value="25.392000" required>
                        </div>
                        <div>
                            <label>Longitude</label>
                            <input type="text" id="form-lon" value="68.373500" required>
                        </div>
                    </div>

                    <button type="submit" class="btn-action btn-primary" id="btn-sub" style="width: 100%; justify-content: center; padding: 0.8rem; margin-top: 10px;">
                        <i class="fa-solid fa-bolt"></i> Submit to AI Triage Pipeline
                    </button>
                </div>
            </form>

            <div id="ai-resp-card" style="display: none; margin-top: 1.5rem; padding: 1.25rem; background: var(--surface-muted); border: 1px solid var(--border); border-radius: 10px;">
                <h4 style="font-size: 1rem; font-weight: 700; color: var(--civic-blue);" id="resp-tkt"></h4>
                <div id="resp-meta" style="margin: 6px 0; font-size: 0.88rem;"></div>
                <div id="resp-dedup" style="font-size: 0.85rem; font-weight: 600; color: #b45309;"></div>
                <p style="margin-top: 8px; font-size: 0.88rem;"><b>AI Action Plan:</b> <span id="resp-plan"></span></p>
            </div>
        </div>
    </div>

    <!-- TAB 4: SYSTEM ARCHITECTURE -->
    <div id="tab-system" class="tab-pane">
        <div class="db-card">
            <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;">System Integration Architecture</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <div style="background: var(--surface-muted); padding: 1.25rem; border-radius: 10px; border: 1px solid var(--border);">
                    <h4 style="color: var(--civic-blue); margin-bottom: 0.75rem;"><i class="fa-solid fa-arrows-split-up-and-left"></i> Endpoints Connected with Mir's Frontend:</h4>
                    <ul style="line-height: 1.9; font-size: 0.88rem; color: var(--text-sub);">
                        <li><code>POST /api/submit-report</code> &mdash; Receives citizen photo, audio, description, and GPS coordinates.</li>
                        <li><code>GET /api/tickets</code> &mdash; Returns list of complaints serialized for Pandas DataFrame & Streamlit map.</li>
                        <li><code>PATCH /api/update-status/{id}</code> &mdash; Updates complaint status in SQLite with instant cache refresh.</li>
                        <li><code>GET /api/stats</code> &mdash; Summarizes municipal KPIs for dashboard cards.</li>
                    </ul>
                </div>
                <div style="background: var(--surface-muted); padding: 1.25rem; border-radius: 10px; border: 1px solid var(--border);">
                    <h4 style="color: var(--res-text); margin-bottom: 0.75rem;"><i class="fa-solid fa-shield-halved"></i> Engineering Safeguards:</h4>
                    <ul style="line-height: 1.9; font-size: 0.88rem; color: var(--text-sub);">
                        <li><b>Exact Haversine Metric:</b> $R=6,371,000\text{ m}$ spherical great-circle calculation.</li>
                        <li><b>Centroid Anchor Lock:</b> Deduplication queries only match against root primary tickets (`duplicate_of.is_(None)`).</li>
                        <li><b>MIME Security:</b> Header inspection rejects executables and unverified files.</li>
                        <li><b>Dual Format Support:</b> Seamlessly parses coordinates whether sent as `latitude`/`longitude` or `lat`/`lng`.</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        const ADMIN_KEY = "cleancity-admin-secret-key-2026";
        let map, markersLayer, circlesLayer;

        // Center on Hyderabad, Sindh
        const HYD_LAT = 25.392000;
        const HYD_LON = 68.362000;

        function initMap() {
            map = L.map('real-map').setView([HYD_LAT, HYD_LON], 13);
            
            // Clean high-resolution real street tiles (OpenStreetMap — free, no API key)
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(map);

            markersLayer = L.layerGroup().addTo(map);
            circlesLayer = L.layerGroup().addTo(map);
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
            if (tabId === 'tab-map' && map) {
                setTimeout(() => map.invalidateSize(), 150);
            }
        }

        function applyLandmarkPreset() {
            const p = document.getElementById('landmark-select').value.split(',');
            document.getElementById('form-lat').value = p[0].trim();
            document.getElementById('form-lon').value = p[1].trim();
        }

        async function loadDashboardData() {
            try {
                // Fetch stats
                const stats = await (await fetch('/api/stats', { headers: { 'X-Admin-API-Key': ADMIN_KEY } })).json();
                document.getElementById('kpi-open').innerText = stats.total_open;
                document.getElementById('kpi-crit').innerText = stats.critical_alerts;
                document.getElementById('kpi-res').innerText = stats.resolved_today;
                document.getElementById('kpi-total').innerText = stats.total_reports;

                // Fetch tickets
                const resp = await (await fetch('/api/tickets?limit=100', { headers: { 'X-Admin-API-Key': ADMIN_KEY } })).json();
                const tickets = resp.tickets || resp || [];

                renderMapMarkers(tickets);
                renderDatabaseTable(tickets);
            } catch(e) {
                console.error("Error loading data:", e);
            }
        }

        function renderMapMarkers(tickets) {
            if (!map || !markersLayer || !circlesLayer) return;
            markersLayer.clearLayers();
            circlesLayer.clearLayers();

            tickets.forEach(t => {
                const isCrit = t.severity === 'Critical';
                const isHigh = t.severity === 'High';
                const color = isCrit ? '#dc2626' : (isHigh ? '#d97706' : '#2563eb');

                // 50-meter perimeter circle
                L.circle([t.latitude, t.longitude], {
                    radius: 50,
                    color: color,
                    weight: 1.5,
                    opacity: 0.7,
                    fillColor: color,
                    fillOpacity: 0.12,
                    dashArray: '4, 4'
                }).addTo(circlesLayer);

                // Marker dot
                const marker = L.circleMarker([t.latitude, t.longitude], {
                    radius: 8,
                    fillColor: color,
                    color: '#ffffff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.95
                }).addTo(markersLayer);

                marker.bindPopup(`
                    <div style="font-family:'Inter',sans-serif; min-width:200px;">
                        <div style="font-weight:700; font-size:0.95rem; color:#0f172a; margin-bottom:4px;">${t.ticket_id}</div>
                        <div style="margin-bottom:6px;">
                            <span class="badge badge-${t.severity}">${t.severity}</span>
                            <span class="badge" style="background:#f1f5f9; color:#334155;">${t.category}</span>
                        </div>
                        <p style="font-size:0.82rem; color:#475569; margin:4px 0;">${t.translated_text || t.address || 'Hyderabad Civic Issue'}</p>
                        <div style="font-size:0.78rem; color:#1e40af; font-weight:600; margin-top:6px;">AI Action: ${t.ai_action_plan}</div>
                        ${t.duplicate_count > 0 ? `<div style="font-size:0.75rem; color:#b45309; margin-top:4px;">🔄 ${t.duplicate_count} citizen reports merged within 50m</div>` : ''}
                    </div>
                `);
            });
        }

        function renderDatabaseTable(tickets) {
            const tbody = document.getElementById('db-tbody');
            tbody.innerHTML = '';

            if (tickets.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No records in database.</td></tr>';
                return;
            }

            tickets.forEach(t => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:700; color:var(--civic-blue);">${t.ticket_id}</td>
                    <td><b>${t.category}</b></td>
                    <td><span class="badge badge-${t.severity}">${t.severity}</span></td>
                    <td style="font-size:0.82rem; color:var(--text-sub);">${t.translated_text || t.address || 'Hyderabad'}<br><span style="font-family:monospace; color:var(--text-muted);">${t.latitude.toFixed(4)}, ${t.longitude.toFixed(4)}</span></td>
                    <td style="font-size:0.82rem; color:var(--text-sub); max-width:280px;">${t.ai_action_plan || 'Triage underway'}</td>
                    <td><span style="font-weight:600; color:var(--civic-blue);">${t.duplicate_count} merged</span></td>
                    <td>
                        <select onchange="updateTicketStatus('${t.ticket_id}', this.value)" style="padding:4px 8px; font-size:0.82rem; border-radius:6px;">
                            <option value="Open" ${t.status === 'Open' ? 'selected' : ''}>Open</option>
                            <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                            <option value="Resolved" ${t.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                        </select>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function updateTicketStatus(id, newStatus) {
            try {
                await fetch(`/api/update-status/${id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', 'X-Admin-API-Key': ADMIN_KEY },
                    body: JSON.stringify({ status: newStatus })
                });
                loadDashboardData();
            } catch(e) {
                console.error("Failed to update status:", e);
            }
        }

        async function seedHyderabadData() {
            try {
                const res = await (await fetch('/api/seed-demo-data', { method: 'POST', headers: { 'X-Admin-API-Key': ADMIN_KEY } })).json();
                alert(res.message);
                loadDashboardData();
            } catch(e) {
                alert("Error seeding data: " + e);
            }
        }

        // Form submission
        document.getElementById('report-form').onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn-sub');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing AI Triage...';

            const fd = new FormData();
            fd.append('image', document.getElementById('form-image').files[0]);
            if (document.getElementById('form-audio').files[0]) {
                fd.append('audio', document.getElementById('form-audio').files[0]);
            }
            fd.append('latitude', document.getElementById('form-lat').value);
            fd.append('longitude', document.getElementById('form-lon').value);
            fd.append('description', document.getElementById('form-desc').value);

            try {
                const res = await (await fetch('/api/submit-report', { method: 'POST', body: fd })).json();
                document.getElementById('ai-resp-card').style.display = 'block';
                document.getElementById('resp-tkt').innerText = `Ticket ID: ${res.ticket_id}`;
                document.getElementById('resp-meta').innerHTML = `<b>Category:</b> ${res.category} &bull; <b>Severity:</b> <span class="badge badge-${res.severity}">${res.severity}</span>`;
                document.getElementById('resp-dedup').innerText = res.is_duplicate ? '🔄 Merged with active issue in 50m radius' : '🆕 New verified civic issue registered';
                document.getElementById('resp-plan').innerText = res.ai_action_plan;
                loadDashboardData();
            } catch(err) {
                alert('Submission error: ' + err);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Submit to AI Triage Pipeline';
            }
        };

        window.onload = () => {
            initMap();
            loadDashboardData();
        };
    </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """
    Serves the natural, classy municipal dashboard with real Hyderabad map.
    """
    return DASHBOARD_CLASSY_HTML
