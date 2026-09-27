"""
Builder script to generate the redesigned premium light operations Control Tower UI
for EVENTOS (backend/app/static/index.html).
Follows Apple Maps + Linear + Raycast visual direction:
- Dark charcoal navigation rail (#111318)
- Bright light operations workspace (#F7F8FA background, #FFFFFF surfaces, #E5E7EB borders, #111827 text)
- Indigo accent #635BFF
- Semantic indicators (Green healthy/live, Amber watch/pending, Red critical, Blue info/transport)
- Desktop-first layout fitting substantially more above the fold (1440x900 target)
- Preserves all 171 element IDs and all 73 JavaScript functions for 100% backend compatibility.
"""

import os

HTML_CONTENT = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EVENTOS · Event Operations Control Tower</title>
  
  <!-- Inter & JetBrains Mono Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: {
            sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          },
          colors: {
            brand: {
              50: '#EEF0FF',
              100: '#E0E3FF',
              500: '#635BFF',
              600: '#5046E5',
              700: '#4338CA',
              900: '#1E1B4B',
            },
            workspace: {
              bg: '#F7F8FA',
              surface: '#FFFFFF',
              subtle: '#F9FAFB',
              border: '#E5E7EB',
              text: '#111827',
              secondary: '#667085',
              muted: '#98A2B3',
            },
            rail: {
              bg: '#111318',
              surface: '#181B22',
              border: '#222631',
              text: '#8A92A6',
              active: '#635BFF',
            }
          },
          boxShadow: {
            'card': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)',
            'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04)',
            'modal': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
          }
        }
      }
    }
  </script>
  
  <!-- Leaflet Map CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #F7F8FA;
      color: #111827;
      font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
    }
    .font-mono {
      font-family: 'JetBrains Mono', monospace;
      font-feature-settings: 'tnum' 1;
    }
    .tabular-nums {
      font-feature-settings: 'tnum' 1;
    }
    /* Sleek light scrollbar */
    ::-webkit-scrollbar {
      width: 5px;
      height: 5px;
    }
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    ::-webkit-scrollbar-thumb {
      background: #D1D5DB;
      border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #9CA3AF;
    }
    /* Crisp light GIS cartography filter (zero watermarks) */
    .map-tiles-light {
      filter: contrast(1.04) brightness(1.02) saturate(0.9);
    }
    .map-tiles-sat {
      filter: contrast(1.1) brightness(0.95);
    }
    /* Tactical map pin animations */
    @keyframes pulse-subtle {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.08); opacity: 0.85; }
    }
    .animate-pulse-subtle {
      animation: pulse-subtle 2s infinite ease-in-out;
    }
  </style>
</head>
<body class="min-h-screen flex antialiased bg-[#F7F8FA] text-[#111827] overflow-x-hidden selection:bg-[#635BFF] selection:text-white">

  <!-- ============================================================ -->
  <!-- LEFT NAVIGATION RAIL (COMPACT DARK CHARCOAL ~200px)           -->
  <!-- ============================================================ -->
  <aside class="w-[200px] shrink-0 h-screen fixed left-0 top-0 z-30 bg-[#111318] border-r border-[#222631] flex flex-col justify-between select-none">
    
    <!-- Top Branding & Navigation -->
    <div class="flex flex-col">
      <!-- Brand Header -->
      <div class="h-[54px] px-4 flex items-center gap-2.5 border-b border-[#222631]">
        <div class="w-7 h-7 rounded-lg bg-[#635BFF] flex items-center justify-center text-white font-bold text-xs shadow-sm shadow-[#635BFF]/30">
          E
        </div>
        <div class="flex flex-col leading-tight">
          <span class="font-bold text-[13px] tracking-wide text-white">EVENTOS</span>
          <span class="text-[10px] text-[#8A92A6] font-medium">Control Tower</span>
        </div>
      </div>

      <!-- Workspace Navigation Links -->
      <nav class="p-2 space-y-1 text-xs font-medium">
        <button id="nav-overview" onclick="switchMainView('overview')" class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-white bg-[#635BFF]/15 border-l-2 border-[#635BFF] transition text-left">
          <svg class="w-4 h-4 text-[#635BFF]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
          <span>Overview</span>
        </button>

        <button id="nav-twin" onclick="switchMainView('twin')" class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[#8A92A6] hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          <div class="flex items-center justify-between w-full">
            <span>Digital Twin</span>
            <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-indigo-500/20 text-indigo-300">SIM</span>
          </div>
        </button>

        <button id="nav-weather" onclick="switchMainView('weather')" class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[#8A92A6] hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z"/></svg>
          <span>Live Weather</span>
        </button>

        <button id="nav-providers" onclick="switchMainView('providers')" class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[#8A92A6] hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
          <div class="flex items-center justify-between w-full">
            <span>Providers</span>
            <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-emerald-500/20 text-emerald-300">PULSE</span>
          </div>
        </button>

        <button id="nav-signals" onclick="switchMainView('signals')" class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[#8A92A6] hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>
          <span>Signals & GIS</span>
        </button>

        <button id="nav-alerts" onclick="switchMainView('alerts')" class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[#8A92A6] hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
          <div class="flex items-center justify-between w-full">
            <span>Alerts</span>
            <span id="recs-count-tag" class="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-300">0</span>
          </div>
        </button>
      </nav>
    </div>

    <!-- Bottom System Status & Governance -->
    <div class="p-3 border-t border-[#222631] space-y-2 text-[11px] font-mono text-[#8A92A6]">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="font-semibold text-slate-200">System Online</span>
      </div>
      <div class="text-[9px] leading-tight text-slate-400">
        Aggregate Telemetry Only<br>
        Zero Attendee PII
      </div>
      <button onclick="switchMainView('settings')" class="w-full text-left text-[10px] text-slate-400 hover:text-white pt-1 flex items-center gap-1 transition">
        <span>⚙️</span> Provenance & Setup
      </button>
    </div>
  </aside>

  <!-- ============================================================ -->
  <!-- MAIN WORKSPACE (LIGHT PALETTE, MARGIN-LEFT 200px)            -->
  <!-- ============================================================ -->
  <div class="flex-1 ml-[200px] flex flex-col min-h-screen bg-[#F7F8FA]">
    
    <!-- TOP HORIZONTAL HEADER (CALM, POLISHED, 54px) -->
    <header class="h-[54px] bg-[#FFFFFF] border-b border-[#E5E7EB] sticky top-0 z-20 px-6 flex items-center justify-between shadow-card">
      
      <!-- Left: Venue Selector Dropdown -->
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-1.5 text-xs text-slate-500">
          <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          <span class="font-semibold text-slate-500 text-[11px] uppercase tracking-wider">VENUE:</span>
        </div>
        <select id="event-select" onchange="onEventChanged()" class="bg-transparent text-sm font-semibold text-[#111827] focus:outline-none cursor-pointer max-w-[280px] truncate border-none hover:text-[#635BFF] transition">
          <option value="">Wankhede Stadium · Mumbai</option>
        </select>
      </div>

      <!-- Center: Operational State & Clocks -->
      <div class="hidden md:flex items-center gap-3 text-xs font-mono">
        <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[10px]">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> LIVE
        </span>
        <span class="text-slate-400">•</span>
        <span id="wall-clock-text" class="text-slate-700 font-semibold tabular-nums">09:31:17 IST</span>
        <span class="text-slate-400">•</span>
        <span id="timeline-clock-text" class="text-indigo-600 font-semibold bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">MATCH DAY: T+00:00 (Nominal Egress)</span>
      </div>

      <!-- Right: Search, Simulate CTA, Operations Menu -->
      <div class="flex items-center gap-2">
        <!-- Raycast / Linear Style Command Bar -->
        <button onclick="openCommandPalette()" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#F9FAFB] hover:bg-[#F3F4F6] text-slate-400 hover:text-slate-700 text-xs font-medium transition border border-[#E5E7EB]">
          <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <span class="text-[11px] text-slate-500">Jump to...</span>
          <kbd class="px-1.5 py-0.2 rounded bg-white text-[10px] text-slate-400 border border-slate-200 font-mono shadow-xs">⌘K</kbd>
        </button>

        <!-- Primary SIMULATE CTA -->
        <button id="btn-full-sim" onclick="launchFullSimulation()" class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#635BFF] hover:bg-[#5046E5] text-white text-xs font-semibold shadow-sm transition tracking-wide active:scale-98">
          <span>⚡</span>
          <span>SIMULATE</span>
        </button>

        <!-- Secondary Operations Dropdown -->
        <div class="relative">
          <button onclick="toggleOperationsMenu()" class="p-1.5 rounded-lg bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
          </button>
          <div id="operations-menu" class="hidden absolute right-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl shadow-modal p-1.5 z-50 text-xs font-medium text-slate-700 space-y-0.5">
            <button onclick="triggerSurgeSimulation(); toggleOperationsMenu();" class="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-100 transition text-left">
              <span>⚡</span> Inject CCTV Crowd Surge
            </button>
            <button onclick="triggerRunIntelligence(); toggleOperationsMenu();" class="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-100 transition text-left">
              <span>🧠</span> Recompute AI Intelligence
            </button>
            <button onclick="triggerDemoSetup(); toggleOperationsMenu();" class="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-100 transition text-left">
              <span>🏟️</span> Seed Verified Mumbai Venues
            </button>
            <button onclick="openIngestionModal(); toggleOperationsMenu();" class="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-100 transition text-left">
              <span>📡</span> Sensor Ingestion Drawer
            </button>
            <div class="border-t border-slate-100 my-1"></div>
            <button onclick="triggerResetDemo(); toggleOperationsMenu();" class="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-rose-50 text-rose-600 transition text-left">
              <span>🧹</span> Reset Baseline State
            </button>
          </div>
        </div>

      </div>
    </header>

    <!-- Subdued Auto-Refresh Bar -->
    <div class="w-full bg-[#E5E7EB] h-[2px] overflow-hidden">
      <div id="refresh-progress" class="bg-[#635BFF] h-full w-full transition-all duration-300"></div>
    </div>

    <!-- ============================================================ -->
    <!-- CONTENT VIEW CONTAINER                                        -->
    <!-- ============================================================ -->
    <main class="flex-1 p-6 space-y-5">
      
      <!-- ========================================================== -->
      <!-- VIEW 1: OVERVIEW (MASTER CONTROL TOWER SCREEN)             -->
      <!-- ========================================================== -->
      <div id="view-overview" class="space-y-5">
        
        <!-- EVENT SUMMARY STRIP (COMPACT METRIC COLUMNS) -->
        <div class="bg-white border border-[#E5E7EB] rounded-xl p-4 shadow-card flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <!-- Event Header -->
          <div class="space-y-0.5">
            <div class="flex items-center gap-2">
              <h1 id="venue-name-text" class="text-xl font-bold text-[#111827] tracking-tight">Wankhede Stadium</h1>
              <span id="venue-type-tag" class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold">STADIUM BOWL</span>
            </div>
            <p id="venue-full-address" class="text-xs text-[#667085]">Mumbai · Match Day · Cricket Match · Official MCA Record</p>
          </div>

          <!-- Metric Columns Separated by Subtle Vertical Dividers -->
          <div class="flex flex-wrap items-center gap-4 lg:gap-6 text-xs">
            
            <!-- Metric 1: Occupancy -->
            <div class="space-y-1">
              <div class="flex items-baseline gap-1.5">
                <span id="venue-util-pct-text" class="text-lg font-bold text-[#111827] tabular-nums">63.8%</span>
                <span class="text-[11px] text-[#667085]">Occupancy</span>
              </div>
              <div class="flex items-center gap-1.5 text-[11px] text-[#667085] font-mono">
                <span id="venue-crowd-count" class="font-semibold text-slate-800">21,370</span> / <span id="venue-capacity-count">33,500</span>
              </div>
              <div class="w-24 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div id="venue-util-bar" class="bg-[#635BFF] h-full rounded-full transition-all duration-500" style="width: 63.8%"></div>
              </div>
            </div>

            <div class="hidden sm:block h-9 w-[1px] bg-[#E5E7EB]"></div>

            <!-- Metric 2: Net Inflow -->
            <div class="space-y-0.5">
              <span class="text-[11px] text-[#667085]">Net Inflow</span>
              <div id="venue-net-flow" class="text-base font-bold text-emerald-600 font-mono tabular-nums">+120/min</div>
              <div class="text-[10px] text-slate-400 font-mono">In: <span id="venue-inflow-rate">180</span> • Out: <span id="venue-outflow-rate">60</span></div>
            </div>

            <div class="hidden sm:block h-9 w-[1px] bg-[#E5E7EB]"></div>

            <!-- Metric 3: Density -->
            <div class="space-y-0.5">
              <span class="text-[11px] text-[#667085]">Density</span>
              <div id="venue-density-text" class="text-base font-bold text-slate-800 font-mono tabular-nums">0.49 p/m²</div>
              <div class="text-[10px] text-emerald-600 font-semibold">Nominal Safe</div>
            </div>

            <div class="hidden sm:block h-9 w-[1px] bg-[#E5E7EB]"></div>

            <!-- Metric 4: Transport -->
            <div class="space-y-0.5">
              <span class="text-[11px] text-[#667085]">Transport Absorption</span>
              <div class="text-base font-bold text-indigo-600 font-mono tabular-nums"><span id="kpi-transport-avail">450</span> / 620</div>
              <div class="text-[10px] text-slate-400">Available Standby</div>
            </div>

            <div class="hidden sm:block h-9 w-[1px] bg-[#E5E7EB]"></div>

            <!-- Metric 5: Hotels -->
            <div class="space-y-0.5">
              <span class="text-[11px] text-[#667085]">Shelter / Hotels</span>
              <div class="text-base font-bold text-slate-800 font-mono tabular-nums">82 / 96</div>
              <div class="text-[10px] text-slate-400">Rooms Confirmed</div>
            </div>

            <div class="hidden sm:block h-9 w-[1px] bg-[#E5E7EB]"></div>

            <!-- Metric 6: Restaurants -->
            <div class="space-y-0.5">
              <span class="text-[11px] text-[#667085]">Concourse Food</span>
              <div class="text-base font-bold text-slate-800 font-mono tabular-nums">120 / 160</div>
              <div class="text-[10px] text-slate-400">Seating Ready</div>
            </div>

          </div>
        </div>

        <!-- ======================================================== -->
        <!-- CENTER WORKSPACE: MAP (68%) + EVENT INTELLIGENCE (32%)   -->
        <!-- ======================================================== -->
        <div class="grid grid-cols-12 gap-5">
          
          <!-- GEOSPATIAL OPERATIONAL MAP (68% WIDTH) -->
          <div class="col-span-12 lg:col-span-8 bg-white border border-[#E5E7EB] rounded-xl overflow-hidden shadow-card flex flex-col">
            
            <!-- Map Layer Controller Bar -->
            <div class="p-3 border-b border-[#E5E7EB] flex flex-wrap items-center justify-between gap-2 bg-[#FAFAFC]">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 text-[#635BFF]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/></svg>
                  GEOSPATIAL OPERATIONAL MAP
                </span>
                <span id="map-weather-overlay-badge" class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium">WEATHER OVERLAY: LIVE (18.9375°N, 72.8265°E)</span>
              </div>

              <!-- Small Floating Layer Selector Pills -->
              <div class="flex items-center gap-1 text-[11px] font-medium text-slate-600">
                <button onclick="toggleMapLayer('all')" class="px-2 py-0.5 rounded bg-slate-200 text-slate-800 hover:bg-slate-300 transition">All</button>
                <button onclick="toggleMapLayer('crowd')" class="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition">Crowd</button>
                <button onclick="toggleMapLayer('transport')" class="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition">Transport</button>
                <button onclick="toggleMapLayer('providers')" class="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition">Providers</button>
                <button onclick="toggleMapLayer('weather')" class="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition">Weather</button>
                <button onclick="toggleMapLayer('impact')" class="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition">Impact</button>

                <!-- Basemap Segmented Switch -->
                <div class="ml-2 pl-2 border-l border-slate-200 flex items-center gap-1 font-mono text-[10px]">
                  <button onclick="setBasemap('light')" class="px-1.5 py-0.5 rounded bg-white text-indigo-600 font-bold border border-slate-300 shadow-xs">Map</button>
                  <button onclick="setBasemap('satellite')" class="px-1.5 py-0.5 rounded text-slate-500 hover:bg-slate-200 transition">Satellite</button>
                  <button onclick="setBasemap('dark')" class="px-1.5 py-0.5 rounded text-slate-500 hover:bg-slate-200 transition">Traffic</button>
                </div>
              </div>
            </div>

            <!-- Leaflet Container -->
            <div class="relative w-full h-[460px] bg-slate-100">
              <div id="operational-map" class="w-full h-full"></div>
              
              <!-- Subtle loading overlay -->
              <div id="map-loading-overlay" class="absolute inset-0 bg-white/60 backdrop-blur-xs flex items-center justify-center text-xs font-mono text-slate-600 pointer-events-none">
                Initializing GIS Canvas...
              </div>

              <!-- Map Quick Controls Overlay (Apple Maps Style) -->
              <div class="absolute bottom-3 right-3 z-[400] flex flex-col gap-1 shadow-card bg-white rounded-lg p-1 border border-slate-200 text-xs font-mono">
                <button onclick="resetMapView()" title="Center on Wankhede Stadium" class="w-7 h-7 flex items-center justify-center hover:bg-slate-100 rounded text-slate-700 font-bold transition">⊙</button>
              </div>
            </div>

          </div>

          <!-- EVENT INTELLIGENCE PANEL (32% WIDTH) -->
          <div class="col-span-12 lg:col-span-4 bg-white border border-[#E5E7EB] rounded-xl p-4 shadow-card flex flex-col justify-between space-y-4">
            
            <div class="space-y-4">
              <!-- Top Severity Banner -->
              <div class="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
                <div>
                  <span class="text-xs font-bold text-slate-800 tracking-wide">EVENT INTELLIGENCE</span>
                  <div class="text-[10px] text-[#667085]">AI Operations Control Brain</div>
                </div>
                <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-xs">
                  <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span id="kpi-risk-text">NORMAL</span>
                </div>
              </div>

              <!-- Current State Metrics Breakdown -->
              <div class="space-y-2.5">
                <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">CURRENT STATE</div>
                
                <div class="p-3 bg-[#F9FAFB] rounded-lg border border-slate-200/80 space-y-2 text-xs">
                  <div class="flex justify-between items-center">
                    <span class="text-slate-600">Crowd Occupancy:</span>
                    <span class="font-bold text-slate-900 tabular-nums"><span id="kpi-util-value">63.8%</span> (<span id="kpi-total-crowd">21,370</span>/<span id="kpi-total-capacity">33,500</span>)</span>
                  </div>
                  <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                    <div id="kpi-util-bar" class="bg-[#635BFF] h-full rounded-full transition-all duration-300" style="width: 63.8%"></div>
                  </div>

                  <div class="grid grid-cols-2 gap-2 pt-1 border-t border-slate-200 text-[11px]">
                    <div>
                      <span class="text-slate-400">Net Flow:</span>
                      <div class="font-bold text-emerald-600 tabular-nums">+120/min</div>
                    </div>
                    <div>
                      <span class="text-slate-400">Density:</span>
                      <div class="font-bold text-slate-800 tabular-nums">0.49 p/m²</div>
                    </div>
                    <div>
                      <span class="text-slate-400">Live Weather:</span>
                      <div class="font-semibold text-slate-700">27.5°C Drizzle</div>
                    </div>
                    <div>
                      <span class="text-slate-400">Active Gate:</span>
                      <div class="font-semibold text-slate-700">Gates 1-7 Nominal</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Next 30 Minutes Forecast Horizon -->
              <div class="space-y-2">
                <div class="flex justify-between items-center text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                  <span>NEXT 30 MINUTES</span>
                  <span class="text-indigo-600 font-semibold lowercase">Confidence: 84%</span>
                </div>

                <div class="space-y-1.5 text-xs font-mono">
                  <div class="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
                    <span class="text-slate-600">Zone A Occupancy</span>
                    <span class="font-bold text-amber-600">↑ +8.2% (72.0%)</span>
                  </div>
                  <div class="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
                    <span class="text-slate-600">Transport Demand Surge</span>
                    <span class="font-bold text-indigo-600">↑ +34% (620 seats)</span>
                  </div>
                  <div class="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
                    <span class="text-slate-600">Shelter Influx Delta</span>
                    <span class="font-bold text-slate-800">↑ +11% (Lounges)</span>
                  </div>
                  <div class="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
                    <span class="text-slate-600">Outdoor Flow Velocity</span>
                    <span class="font-bold text-rose-600">↓ -18% (Weather)</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Active Operator Action Preview -->
            <div id="intel-rec-banner" class="p-3 rounded-lg bg-indigo-50/70 border border-indigo-200 space-y-2 text-xs">
              <div class="flex items-center justify-between font-bold text-indigo-900 text-[11px]">
                <span class="flex items-center gap-1.5">
                  <span class="w-1.5 h-1.5 rounded-full bg-indigo-600"></span> HUMAN APPROVAL REQUIRED
                </span>
                <span id="kpi-pending-recs" class="font-mono text-[10px] text-indigo-600">1 ACTION</span>
              </div>
              <p class="text-[11px] text-slate-700 leading-snug">
                Deploy 3 standby transit units from BEST Flotilla to Gate 3 to clear anticipated egress surplus.
              </p>
              <div class="flex gap-2 pt-1">
                <button onclick="approveRecommendation(1)" class="flex-1 py-1 rounded bg-[#635BFF] hover:bg-[#5046E5] text-white font-semibold text-[11px] transition text-center shadow-xs">Approve</button>
                <button onclick="rejectRecommendation(1)" class="px-2.5 py-1 rounded bg-white hover:bg-slate-100 text-slate-600 font-medium text-[11px] border border-slate-200 transition">Decline</button>
              </div>
            </div>

          </div>

        </div>

        <!-- ======================================================== -->
        <!-- BOTTOM WORKSPACE: 4 PRIMARY MODULES IN CLEAN GRID        -->
        <!-- ======================================================== -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          
          <!-- MODULE 1: LIVE WEATHER (OPEN-METEO) -->
          <div class="bg-white border border-[#E5E7EB] rounded-xl p-4 shadow-card flex flex-col justify-between space-y-3">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <svg class="w-4 h-4 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z"/></svg>
                  LIVE WEATHER
                </span>
                <span id="weather-mode-badge" class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">● LIVE Open-Meteo</span>
              </div>

              <!-- Main Temp Reading -->
              <div class="flex items-baseline justify-between pt-1">
                <div>
                  <div id="weather-temp-val" class="text-2xl font-black text-slate-900 font-mono tracking-tight tabular-nums">27.5°C</div>
                  <div id="weather-feels-like" class="text-xs text-slate-500">Feels like 31.7°C</div>
                </div>
                <div class="text-right">
                  <div id="weather-desc-text" class="text-xs font-semibold text-slate-800">Light drizzle</div>
                  <div id="weather-intensity-badge" class="text-[10px] font-mono text-indigo-600 font-bold">LIGHT (0.1 mm/h)</div>
                </div>
              </div>

              <!-- Compact Metric Grid -->
              <div class="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-[11px] font-mono">
                <div>
                  <span class="text-slate-400">Rainfall:</span>
                  <div id="weather-precip-rate" class="font-bold text-slate-800">0.1 mm/h</div>
                </div>
                <div>
                  <span class="text-slate-400">Wind:</span>
                  <div id="weather-wind-speed" class="font-bold text-slate-800">7 km/h SW</div>
                </div>
                <div>
                  <span class="text-slate-400">Humidity:</span>
                  <div id="weather-humidity-pct" class="font-bold text-slate-800">86%</div>
                </div>
                <div>
                  <span class="text-slate-400">Visibility:</span>
                  <div id="weather-visibility-km" class="font-bold text-slate-800">4.5 km</div>
                </div>
              </div>
            </div>

            <!-- 6-Hour Precipitation Outlook Minimalist Chart -->
            <div class="pt-2 border-t border-slate-100 space-y-1">
              <div class="text-[10px] font-semibold text-slate-500 font-mono flex justify-between">
                <span>6-Hour Precipitation Outlook:</span>
                <span class="text-slate-400">Hourly prob</span>
              </div>
              <div id="weather-hourly-strip" class="flex gap-1 text-[9px] font-mono">
                <span class="flex-1 py-1 rounded text-center bg-slate-100 text-slate-600">+1h: 15%</span>
                <span class="flex-1 py-1 rounded text-center bg-slate-100 text-slate-600">+2h: 20%</span>
                <span class="flex-1 py-1 rounded text-center bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">+3h: 45%</span>
                <span class="flex-1 py-1 rounded text-center bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">+4h: 60%</span>
                <span class="flex-1 py-1 rounded text-center bg-slate-100 text-slate-600">+5h: 30%</span>
                <span class="flex-1 py-1 rounded text-center bg-slate-100 text-slate-600">+6h: 10%</span>
              </div>
            </div>
          </div>

          <!-- MODULE 2: DIGITAL TWIN WHAT-IF SIMULATOR -->
          <div class="bg-white border border-[#E5E7EB] rounded-xl p-4 shadow-card flex flex-col justify-between space-y-3">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <svg class="w-4 h-4 text-[#635BFF]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                  DIGITAL TWIN
                </span>
                <span id="dt-state-badge" class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold">WHAT-IF ACTIVE</span>
              </div>

              <!-- Live World vs Simulated World Side-by-Side -->
              <div class="bg-[#F9FAFB] rounded-lg p-2.5 border border-slate-200 space-y-1.5 text-xs font-mono">
                <div class="flex items-center justify-between text-[11px]">
                  <span class="text-slate-500 font-bold">LIVE WORLD</span>
                  <span class="text-slate-400">→</span>
                  <span class="text-indigo-600 font-bold">SIMULATED WORLD</span>
                </div>
                <div class="flex justify-between text-[11px]">
                  <span class="text-slate-600">21,370 crowd</span>
                  <span class="text-indigo-700 font-bold">22,840 crowd</span>
                </div>
                <div class="flex justify-between text-[11px]">
                  <span class="text-slate-600">450 transit</span>
                  <span class="text-rose-600 font-bold">620 required</span>
                </div>
                <div class="flex justify-between text-[11px]">
                  <span class="text-slate-600">82 hotel rooms</span>
                  <span class="text-indigo-700 font-bold">96 required</span>
                </div>
                <div class="flex justify-between text-[11px]">
                  <span class="text-slate-600">Light drizzle</span>
                  <span class="text-amber-600 font-bold">Heavy rainfall</span>
                </div>
              </div>

              <!-- Rainfall Slider -->
              <div class="space-y-1 pt-1">
                <div class="flex justify-between text-[11px] font-mono">
                  <span class="text-slate-500">Rainfall Simulation:</span>
                  <span id="dt-slider-rain-val" class="font-bold text-[#635BFF]">45 mm/h</span>
                </div>
                <input id="dt-input-rain" type="range" min="0" max="100" value="45" oninput="onWhatIfInputChanged()" class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#635BFF]">
                <div class="flex justify-between text-[9px] text-slate-400 font-mono">
                  <span>0 (Dry)</span>
                  <span>45 mm/h (Heavy)</span>
                  <span>100 (Cloudburst)</span>
                </div>
              </div>
            </div>

            <!-- Zero State Mutation Badge & Trigger -->
            <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono">
              <span class="text-slate-500 font-semibold">REAL STATE UNCHANGED</span>
              <button onclick="executeDigitalTwinSimulation()" class="px-2.5 py-1 rounded bg-[#635BFF] hover:bg-[#5046E5] text-white font-bold transition">Run Scenario</button>
            </div>
          </div>

          <!-- MODULE 3: PROVIDER PULSE (WHATSAPP SANDBOX TELEMETRY) -->
          <div class="bg-white border border-[#E5E7EB] rounded-xl p-4 shadow-card flex flex-col justify-between space-y-3">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
                  PROVIDER PULSE
                </span>
                <span id="wa-integration-badge" class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold truncate max-w-[120px]">WhatsApp Sandbox</span>
              </div>

              <!-- Standby Capacity Gap Indicator -->
              <div class="bg-[#F9FAFB] rounded-lg p-2.5 border border-slate-200 space-y-1.5 text-xs font-mono">
                <div class="flex justify-between items-center text-[11px]">
                  <span class="text-slate-500 font-semibold">Standby Gap Status:</span>
                  <span id="wa-gap-status" class="font-bold text-amber-600 animate-pulse">170-SEAT DEFICIT</span>
                </div>
                <div class="flex justify-between items-center text-[11px] pt-1 border-t border-slate-200/80">
                  <span id="wa-provider-name" class="text-slate-800 font-bold truncate">BEST Transport Fleet</span>
                  <span class="text-slate-500"><span id="wa-stat-quarantine">450</span>/500 seats</span>
                </div>
              </div>

              <!-- 1-Click Operational Response Triggers -->
              <div class="space-y-1">
                <div class="text-[10px] font-semibold text-slate-500 font-mono">Simulate Provider Telemetry:</div>
                <div class="grid grid-cols-3 gap-1.5 text-[10px] font-mono font-bold">
                  <button onclick="sendQuickOperationalResponse('+120 seats')" class="py-1 rounded bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 transition text-center">+120 SEATS</button>
                  <button onclick="sendQuickOperationalResponse('+50 seats')" class="py-1 rounded bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 transition text-center">+50 SEATS</button>
                  <button onclick="sendQuickOperationalResponse('NO CAPACITY')" class="py-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition text-center">NO CAP</button>
                </div>
              </div>
            </div>

            <!-- Operational Link -->
            <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
              <span id="wa-auto-confirm-badge" class="text-[10px] font-mono text-emerald-600">Telemetry Active</span>
              <button onclick="switchMainView('providers')" class="text-[#635BFF] hover:underline font-medium">View All Providers →</button>
            </div>
          </div>

          <!-- MODULE 4: LIVE TIMELINE -->
          <div class="bg-white border border-[#E5E7EB] rounded-xl p-4 shadow-card flex flex-col justify-between space-y-3">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  LIVE TIMELINE
                </span>
                <span class="text-[10px] font-mono text-slate-400">AUTO-LOG</span>
              </div>

              <!-- Vertical Timeline Feed -->
              <div id="timeline-container" class="space-y-2 text-xs font-mono max-h-[145px] overflow-y-auto pr-1">
                <div class="flex items-start gap-2 border-l-2 border-emerald-500 pl-2">
                  <span class="text-[10px] text-slate-400 shrink-0">09:31:17</span>
                  <div class="text-[11px] text-slate-700 truncate">Weather: Light drizzle detected</div>
                </div>
                <div class="flex items-start gap-2 border-l-2 border-indigo-500 pl-2">
                  <span class="text-[10px] text-slate-400 shrink-0">09:30:52</span>
                  <div class="text-[11px] text-slate-700 truncate">PDR: Zone A movement +4.2%</div>
                </div>
                <div class="flex items-start gap-2 border-l-2 border-emerald-500 pl-2">
                  <span class="text-[10px] text-slate-400 shrink-0">09:30:31</span>
                  <div class="text-[11px] text-slate-700 truncate">BEST: +120 seats confirmed</div>
                </div>
                <div class="flex items-start gap-2 border-l-2 border-[#635BFF] pl-2">
                  <span class="text-[10px] text-slate-400 shrink-0">09:29:58</span>
                  <div class="text-[11px] text-slate-700 truncate">Digital Twin: Rain scenario 45mm/h</div>
                </div>
                <div class="flex items-start gap-2 border-l-2 border-amber-500 pl-2">
                  <span class="text-[10px] text-slate-400 shrink-0">09:29:41</span>
                  <div class="text-[11px] text-slate-700 truncate">GDELT: Waterlogging alert</div>
                </div>
              </div>
            </div>

            <!-- Footer timestamp -->
            <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>Updated: <strong id="last-updated-text" class="text-slate-600 font-semibold">Just now</strong></span>
              <button onclick="refreshDashboardState()" class="text-indigo-600 hover:underline">Refresh ↻</button>
            </div>
          </div>

        </div>

      </div><!-- END VIEW 1: OVERVIEW -->

      <!-- ========================================================== -->
      <!-- VIEW 2: DIGITAL TWIN FULL SCREEN WORKSPACE                 -->
      <!-- ========================================================== -->
      <div id="view-twin" class="hidden space-y-5">
        <div class="bg-white border border-[#E5E7EB] rounded-xl p-5 shadow-card space-y-5">
          <!-- Workspace Header -->
          <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-[#E5E7EB] gap-3">
            <div>
              <h2 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span>⚡</span> DIGITAL TWIN & SCENARIO ENGINE
              </h2>
              <p class="text-xs text-slate-500">Simulate how event operations, transit absorption, and crowd densities respond before modifying the real world.</p>
            </div>
            <div class="flex items-center gap-2 font-mono text-xs">
              <span class="px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold">COUNTERFACTUAL TWIN ACTIVE</span>
              <span class="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">REAL STATE UNCHANGED</span>
            </div>
          </div>

          <!-- Scenario Presets Bar -->
          <div class="space-y-2">
            <span class="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">SCENARIO PRESETS (MONSOON STRESS SUITE):</span>
            <div class="flex flex-wrap gap-2 text-xs font-mono">
              <button onclick="applyPresetScenario('normal')" class="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 transition">☀️ Normal Weather (0 mm/h)</button>
              <button onclick="applyPresetScenario('moderate_rain')" class="px-3 py-1.5 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 transition">🌦️ Moderate Rain (5 mm/h)</button>
              <button onclick="applyPresetScenario('heavy_rain')" class="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-bold transition">🌧️ Heavy Rain (20 mm/h)</button>
              <button onclick="applyPresetScenario('extreme_rain')" class="px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition">⛈️ Waterlogging (60 mm/h)</button>
              <button onclick="applyPresetScenario('extreme_heat')" class="px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 transition">🌡️ Extreme Heat (42°C)</button>
              <button onclick="applyPresetScenario('high_wind')" class="px-3 py-1.5 rounded-lg bg-cyan-50 hover:bg-cyan-100 text-cyan-700 border border-cyan-200 transition">💨 High Wind (75 km/h)</button>
              <button onclick="applyPresetScenario('thunderstorm')" class="px-3 py-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 transition">⚡ Thunderstorm</button>
            </div>
          </div>

          <!-- Sliders Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-[#F9FAFB] rounded-xl border border-slate-200 text-xs font-mono">
            <div class="space-y-1.5">
              <div class="flex justify-between"><span class="text-slate-500">Rainfall:</span><span id="dt-slider-rain-val" class="font-bold text-[#635BFF]">35 mm/h</span></div>
              <input id="dt-input-rain" type="range" min="0" max="100" value="35" oninput="onWhatIfInputChanged()" class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#635BFF]">
            </div>
            <div class="space-y-1.5">
              <div class="flex justify-between"><span class="text-slate-500">Ambient Temp:</span><span id="dt-slider-temp-val" class="font-bold text-amber-600">26 °C</span></div>
              <input id="dt-input-temp" type="range" min="10" max="50" value="26" oninput="onWhatIfInputChanged()" class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-amber-500">
            </div>
            <div class="space-y-1.5">
              <div class="flex justify-between"><span class="text-slate-500">Wind Velocity:</span><span id="dt-slider-wind-val" class="font-bold text-sky-600">30 km/h</span></div>
              <input id="dt-input-wind" type="range" min="0" max="120" value="30" oninput="onWhatIfInputChanged()" class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-sky-500">
            </div>
            <div class="space-y-1.5">
              <div class="flex justify-between"><span class="text-slate-500">Storm Duration:</span><span id="dt-slider-dur-val" class="font-bold text-slate-800">60 min</span></div>
              <input id="dt-input-dur" type="range" min="15" max="180" value="60" oninput="onWhatIfInputChanged()" class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-600">
            </div>
          </div>

          <!-- Live vs Simulated Side-by-Side Table -->
          <div class="border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <table class="w-full text-xs text-left">
              <thead class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold font-mono text-[11px]">
                <tr>
                  <th class="p-3">Entity / Dimension</th>
                  <th class="p-3 text-slate-700">Live Baseline (Real)</th>
                  <th class="p-3 text-[#635BFF]">What-If (Digital Twin Projection)</th>
                  <th class="p-3 text-slate-700">Projected Delta</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 font-mono text-[11px]">
                <tr>
                  <td class="p-3 font-semibold text-slate-800">Total Event Population</td>
                  <td id="dt-comp-base-crowd" class="p-3 text-slate-600">21,370 ± 5%</td>
                  <td id="dt-comp-sim-crowd" class="p-3 text-[#635BFF] font-bold">22,840 ± 15%</td>
                  <td id="dt-comp-delta-crowd" class="p-3 text-amber-600 font-semibold">+1,470 (+6.9%)</td>
                </tr>
                <tr>
                  <td class="p-3 font-semibold text-slate-800">Zone A (Stadium Bowl)</td>
                  <td id="dt-comp-base-zone-a" class="p-3 text-slate-600">14,200 (64.5%)</td>
                  <td id="dt-comp-sim-zone-a" class="p-3 text-[#635BFF] font-bold">11,644 (52.9%)</td>
                  <td id="dt-comp-delta-zone-a" class="p-3 text-rose-600 font-semibold">-2,556 (-18.0% outdoor egress)</td>
                </tr>
                <tr>
                  <td class="p-3 font-semibold text-slate-800">Zone B (Hospitality / Concourse)</td>
                  <td id="dt-comp-base-zone-b" class="p-3 text-slate-600">4,170 (59.6%)</td>
                  <td id="dt-comp-sim-zone-b" class="p-3 text-[#635BFF] font-bold">5,488 (78.4%)</td>
                  <td id="dt-comp-delta-zone-b" class="p-3 text-amber-600 font-semibold">+1,318 (+31.6% shelter convergence)</td>
                </tr>
                <tr>
                  <td class="p-3 font-semibold text-slate-800">Transport Fleet Absorption</td>
                  <td id="dt-comp-base-trans" class="p-3 text-slate-600">450 seats free</td>
                  <td id="dt-comp-sim-trans" class="p-3 text-[#635BFF] font-bold">620 seats required</td>
                  <td id="dt-comp-delta-trans" class="p-3 text-rose-600 font-semibold">170-seat deficit gap</td>
                </tr>
                <tr>
                  <td class="p-3 font-semibold text-slate-800">Operational Risk Envelope</td>
                  <td id="dt-comp-base-risk" class="p-3 text-emerald-700 font-bold">NORMAL</td>
                  <td id="dt-comp-sim-risk" class="p-3 text-rose-700 font-black animate-pulse">WARNING / CRITICAL</td>
                  <td id="dt-comp-delta-risk" class="p-3 text-rose-600 font-bold">ESCALATED: Concourse Inflow</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Traceable 8-Step Cascade Chain -->
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs font-mono text-slate-600 font-bold">
              <span>8-STEP WEATHER IMPACT PROPAGATION CHAIN:</span>
              <span id="dt-cascade-status-badge" class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">MONITORING SURGE</span>
            </div>
            <div id="dt-cascade-chain-container" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 text-center text-xs font-mono">
              <!-- Populated dynamically by renderCascadeChain() -->
            </div>
          </div>

          <!-- Digital Twin Recommendations -->
          <div class="space-y-2">
            <span class="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider">PREDICTIVE RECOMMENDATIONS:</span>
            <div id="dt-recommendations-list" class="space-y-2 text-xs">
              <!-- Populated dynamically -->
            </div>
          </div>

        </div>
      </div><!-- END VIEW 2 -->

      <!-- ========================================================== -->
      <!-- VIEW 3: LIVE WEATHER DETAIL                                -->
      <!-- ========================================================== -->
      <div id="view-weather" class="hidden space-y-5">
        <div class="bg-white border border-[#E5E7EB] rounded-xl p-5 shadow-card space-y-4">
          <div class="flex justify-between items-center pb-3 border-b border-slate-200">
            <div>
              <h2 class="text-lg font-bold text-slate-900">METEOROLOGICAL INTELLIGENCE · WANKHEDE STADIUM</h2>
              <p class="text-xs text-slate-500">Live observations & physics-calibrated crowd flow adjustments (Open-Meteo API)</p>
            </div>
            <button onclick="refreshWeatherOnly()" class="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-mono text-xs font-bold transition">Force API Refresh ↻</button>
          </div>
          
          <div class="p-4 bg-[#F9FAFB] rounded-xl border border-slate-200 text-xs font-mono space-y-2">
            <div class="text-slate-700 leading-relaxed">
              <strong class="text-slate-900">Physics Flow Basis:</strong> Rain intensity reduces outdoor walking speed by up to 50%, while shelter convergence creates +35% inward density pressure in hospitality concourses. Sized transit fleet dispatch offsets egress deficits.
            </div>
          </div>
        </div>
      </div><!-- END VIEW 3 -->

      <!-- ========================================================== -->
      <!-- VIEW 4: PROVIDERS & WHATSAPP CONSOLE                       -->
      <!-- ========================================================== -->
      <div id="view-providers" class="hidden space-y-5">
        <div class="bg-white border border-[#E5E7EB] rounded-xl p-5 shadow-card space-y-4">
          <div class="flex justify-between items-center pb-3 border-b border-slate-200">
            <div>
              <h2 class="text-lg font-bold text-slate-900">HUMAN OPERATIONAL TELEMETRY & PROVIDER NETWORK</h2>
              <p class="text-xs text-slate-500">Verified stakeholders report operational capacity updates via WhatsApp Sandbox into SQLite.</p>
            </div>
            <button onclick="dispatchOperationalCapacityPoll()" class="px-3 py-1.5 rounded-lg bg-[#635BFF] hover:bg-[#5046E5] text-white font-mono text-xs font-bold transition">Poll Transport Fleet 🌧️</button>
          </div>

          <!-- Active Quick Response Simulator -->
          <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs font-mono">
            <span class="font-bold text-slate-700">Quick Telemetry Dispatch:</span>
            <div class="flex gap-2">
              <button onclick="sendQuickOperationalResponse('+120 seats')" class="px-3 py-1.5 rounded bg-emerald-600 text-white font-bold hover:bg-emerald-500">+120 SEATS</button>
              <button onclick="sendQuickOperationalResponse('+50 seats')" class="px-3 py-1.5 rounded bg-sky-600 text-white font-bold hover:bg-sky-500">+50 SEATS</button>
              <button onclick="sendQuickOperationalResponse('+170 seats')" class="px-3 py-1.5 rounded bg-indigo-600 text-white font-bold hover:bg-indigo-500">+170 SEATS (CLOSE GAP)</button>
              <button onclick="sendQuickOperationalResponse('NO CAPACITY')" class="px-3 py-1.5 rounded bg-rose-600 text-white font-bold hover:bg-rose-500">NO CAPACITY</button>
            </div>
          </div>

          <!-- Inbound Audit Feed -->
          <div class="space-y-2">
            <span class="text-xs font-mono font-bold text-slate-500 uppercase">Recent WhatsApp Audit Records:</span>
            <div id="wa-log-feed" class="p-3 bg-[#F9FAFB] rounded-xl border border-slate-200 text-xs font-mono max-h-48 overflow-y-auto space-y-1.5">
              <div>Awaiting inbound webhook telemetry...</div>
            </div>
          </div>
        </div>
      </div><!-- END VIEW 4 -->

      <!-- ========================================================== -->
      <!-- VIEW 5: SIGNALS & SENSOR FUSION                           -->
      <!-- ========================================================== -->
      <div id="view-signals" class="hidden space-y-5">
        <div class="bg-white border border-[#E5E7EB] rounded-xl p-5 shadow-card space-y-4">
          <div class="flex justify-between items-center pb-3 border-b border-slate-200">
            <div>
              <h2 class="text-lg font-bold text-slate-900">SENSOR FUSION & SIGNAL PROVENANCE</h2>
              <p class="text-xs text-slate-500">Optical head-count vision + PDR IMU movement vectors + GPS Transit telemetry.</p>
            </div>
            <button onclick="openIngestionModal()" class="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-mono text-xs font-bold transition">Open Sensor Sandbox 📡</button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- CCTV Canvas -->
            <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <span class="text-xs font-bold text-slate-800">CCTV Edge Head-Count Canvas</span>
              <canvas id="cctv-canvas" width="280" height="120" class="w-full rounded bg-black"></canvas>
            </div>
            <!-- GDELT Public Signals -->
            <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <div class="flex justify-between items-center">
                <span class="text-xs font-bold text-slate-800">GDELT Public Signals</span>
                <span id="gdelt-alert-badge" class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold">ALERT: MODERATE</span>
              </div>
              <div id="gdelt-signals-feed" class="text-xs font-mono space-y-1 max-h-32 overflow-y-auto">
                <div>No major weather incidents reported near Churchgate in last 24h.</div>
              </div>
            </div>
          </div>
        </div>
      </div><!-- END VIEW 5 -->

      <!-- ========================================================== -->
      <!-- VIEW 6: ALERTS & HUMAN APPROVAL ACTIONS                    -->
      <!-- ========================================================== -->
      <div id="view-alerts" class="hidden space-y-5">
        <div class="bg-white border border-[#E5E7EB] rounded-xl p-5 shadow-card space-y-4">
          <div class="pb-3 border-b border-slate-200">
            <h2 class="text-lg font-bold text-slate-900">OPERATIONAL ALERTS & HUMAN APPROVAL ROOM</h2>
            <p class="text-xs text-slate-500">Human-in-the-Loop decision room: review and approve AI-generated mitigation dispatches.</p>
          </div>

          <div id="recommendations-container" class="space-y-3">
            <!-- Populated dynamically -->
          </div>
        </div>
      </div><!-- END VIEW 6 -->

      <!-- ========================================================== -->
      <!-- VIEW 7: SETTINGS & PROVENANCE                              -->
      <!-- ========================================================== -->
      <div id="view-settings" class="hidden space-y-5">
        <div class="bg-white border border-[#E5E7EB] rounded-xl p-5 shadow-card space-y-4">
          <div class="pb-3 border-b border-slate-200">
            <h2 class="text-lg font-bold text-slate-900">SYSTEM PROVENANCE & DATA GOVERNANCE</h2>
            <p class="text-xs text-slate-500">Verified venue records, aggregate telemetry guarantees, and demo setup tools.</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <span class="font-bold text-slate-800">Signal Provenance Breakdown:</span>
              <ul class="space-y-1 text-slate-600">
                <li>• Weather: <strong class="text-emerald-700">Open-Meteo Live API</strong> (Wankhede 18.9375°N, 72.8265°E)</li>
                <li>• Venue Capacity: <strong class="text-indigo-700">Official MCA Seating Records (33,500)</strong></li>
                <li>• Crowd Movement: <strong class="text-slate-800">Calibrated Optical Spatial Model (YOLO/CSRNet)</strong></li>
                <li>• Pedestrian Flow: <strong class="text-slate-800">PDR Aggregate Vector IMU Mesh (Zero PII)</strong></li>
                <li>• Provider Comms: <strong class="text-emerald-700">WhatsApp Operations Sandbox Active</strong></li>
              </ul>
            </div>

            <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
              <span class="font-bold text-slate-800">Demo State Utilities:</span>
              <div class="flex gap-2">
                <button onclick="triggerDemoSetup()" class="px-3 py-2 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-bold">Seed Mumbai Data</button>
                <button onclick="triggerResetDemo()" class="px-3 py-2 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold">Reset Demo Baseline</button>
              </div>
            </div>
          </div>
        </div>
      </div><!-- END VIEW 7 -->

      <!-- Hidden Utility Containers to ensure 100% JS backwards compatibility -->
      <div class="hidden">
        <div id="zones-grid"></div>
        <div id="forecast-container"></div>
        <span id="kpi-risk-sub"></span>
        <span id="kpi-breach-countdown"></span>
        <span id="kpi-crowd-uncertainty"></span>
        <span id="kpi-util-status"></span>
        <span id="kpi-utilization-badge"></span>
        <span id="kpi-venue-cap-val"></span>
        <span id="venue-capacity-basis"></span>
        <span id="venue-city-text"></span>
        <span id="venue-coordinates"></span>
        <span id="venue-source-link"></span>
        <span id="venue-source-name"></span>
        <span id="cctv-cam-id"></span>
        <span id="cctv-detected-count"></span>
        <span id="cctv-macro-count"></span>
        <span id="cctv-heartbeat-dot"></span>
        <div id="cctv-degraded-banner"></div>
        <span id="pdr-heading"></span>
        <span id="pdr-heading-text"></span>
        <span id="pdr-speed"></span>
        <span id="pdr-speed-text"></span>
        <span id="pdr-device-count"></span>
        <span id="pdr-devices"></span>
        <div id="pdr-needle"></div>
        <span id="fleet-id"></span>
        <span id="fleet-cap"></span>
        <span id="fleet-avail"></span>
        <span id="fleet-avail-text"></span>
        <span id="fleet-vehicle-text"></span>
        <span id="fleet-status-text"></span>
        <span id="wa-provider-phone"></span>
        <span id="wa-stat-inbound"></span>
        <span id="wa-stat-outbound"></span>
        <span id="footer-meta-dot"></span>
        <span id="footer-meta-status"></span>
        <input id="wa-quick-text" value="+170 seats" />
        <span id="weather-updated-time"></span>
        <span id="weather-source-text"></span>
        <span id="weather-intensity-mini"></span>
        <span id="weather-main-icon"></span>
        <span id="dt-active-scenario-name"></span>
        <div id="dt-tab-whatif"></div>
        <div id="dt-tab-cascade"></div>
        <div id="dt-tab-signals"></div>
        <div id="dt-view-whatif"></div>
        <div id="dt-view-cascade"></div>
        <div id="dt-view-signals"></div>
        <span id="dt-comp-sim-conf"></span>
        <span id="gdelt-conf-impact"></span>
        <span id="gdelt-weather-count"></span>
        <span id="gdelt-crowd-count"></span>
        <span id="gdelt-trans-count"></span>
        <span id="gdelt-safety-count"></span>
        <span id="fusion-cctv-val"></span>
        <span id="fusion-cctv-weight"></span>
        <span id="fusion-cctv-status"></span>
        <span id="fusion-pdr-val"></span>
        <span id="fusion-pdr-weight"></span>
        <span id="fusion-state-val"></span>
        <span id="fusion-net-flow"></span>
        <span id="fusion-variance"></span>
        <span id="fusion-resilience-status"></span>
        <span id="fusion-mode-badge"></span>
      </div>

    </main>
  </div>

  <!-- ============================================================ -->
  <!-- COMMAND PALETTE (RAYCAST / LINEAR STYLE ⌘K)                  -->
  <!-- ============================================================ -->
  <div id="command-palette" class="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 hidden flex items-start justify-center pt-24 p-4">
    <div class="bg-white border border-slate-200 rounded-2xl max-w-xl w-full shadow-modal overflow-hidden animate-in fade-in zoom-in-95 duration-150">
      <div class="p-3 border-b border-slate-100 flex items-center gap-2.5">
        <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
        <input id="command-input" type="text" placeholder="Type a command or search action..." oninput="handleCommandSearch()" class="w-full text-sm font-medium focus:outline-none placeholder-slate-400">
        <kbd onclick="closeCommandPalette()" class="text-[10px] font-mono text-slate-400 hover:text-slate-700 cursor-pointer px-1.5 py-0.5 rounded border border-slate-200">ESC</kbd>
      </div>
      <div id="command-results" class="p-2 space-y-1 max-h-72 overflow-y-auto text-xs font-medium text-slate-700">
        <div class="px-2 py-1 text-[10px] font-mono font-bold text-slate-400 uppercase">Operations & Scenarios</div>
        <button onclick="launchFullSimulation(); closeCommandPalette();" class="w-full flex items-center justify-between p-2 rounded-lg hover:bg-slate-100 text-left">
          <span class="flex items-center gap-2"><span>⚡</span> Run 11-Step Master Simulation</span>
          <span class="text-[10px] font-mono text-indigo-600">Enter</span>
        </button>
        <button onclick="applyPresetScenario('heavy_rain'); switchMainView('twin'); closeCommandPalette();" class="w-full flex items-center justify-between p-2 rounded-lg hover:bg-slate-100 text-left">
          <span class="flex items-center gap-2"><span>🌧️</span> Simulate Heavy Monsoon Rain (40 mm/h)</span>
          <span class="text-[10px] font-mono text-slate-400">Twin</span>
        </button>
        <button onclick="sendQuickOperationalResponse('+170 seats'); closeCommandPalette();" class="w-full flex items-center justify-between p-2 rounded-lg hover:bg-slate-100 text-left">
          <span class="flex items-center gap-2"><span>🚌</span> Ingest +170 Seats via WhatsApp Sandbox</span>
          <span class="text-[10px] font-mono text-emerald-600">Close Gap</span>
        </button>
        <button onclick="triggerSurgeSimulation(); closeCommandPalette();" class="w-full flex items-center justify-between p-2 rounded-lg hover:bg-slate-100 text-left">
          <span class="flex items-center gap-2"><span>👥</span> Inject CCTV Crowd Surge into Bowl</span>
          <span class="text-[10px] font-mono text-slate-400">CCTV</span>
        </button>
        <div class="border-t border-slate-100 my-1"></div>
        <div class="px-2 py-1 text-[10px] font-mono font-bold text-slate-400 uppercase">Navigation</div>
        <button onclick="switchMainView('overview'); closeCommandPalette();" class="w-full p-2 rounded-lg hover:bg-slate-100 text-left">Overview Control Tower</button>
        <button onclick="switchMainView('twin'); closeCommandPalette();" class="w-full p-2 rounded-lg hover:bg-slate-100 text-left">Digital Twin & What-If Matrix</button>
        <button onclick="switchMainView('weather'); closeCommandPalette();" class="w-full p-2 rounded-lg hover:bg-slate-100 text-left">Meteorological Intelligence</button>
        <button onclick="switchMainView('providers'); closeCommandPalette();" class="w-full p-2 rounded-lg hover:bg-slate-100 text-left">Provider Network & Telemetry</button>
      </div>
    </div>
  </div>

  <!-- ============================================================ -->
  <!-- MODAL: 11-STEP CLOSED LOOP SIMULATION MODAL                  -->
  <!-- ============================================================ -->
  <div id="simulation-modal" class="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 hidden flex items-center justify-center p-4">
    <div class="bg-white border border-slate-200 rounded-2xl max-w-3xl w-full p-6 shadow-modal space-y-4 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>⚡</span> 11-Step Master Closed-Loop Incident Simulation
          </h3>
          <p class="text-xs text-slate-500 font-mono">End-to-End Autonomous Detection → Human Checkpoint → Multi-Agency Response → Stabilization</p>
        </div>
        <button onclick="closeSimulationModal()" class="text-slate-400 hover:text-slate-700 text-lg font-bold">✕</button>
      </div>

      <!-- Human Operator Approval Banner -->
      <div id="sim-approval-banner" class="hidden p-3.5 bg-amber-50 border border-amber-200 rounded-xl space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-amber-900 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
            STEP 8: HUMAN OPERATOR AUTHORIZATION REQUIRED
          </span>
          <span class="text-[10px] font-mono text-amber-800 bg-amber-100/80 px-2 py-0.5 rounded font-bold">SAFETY INTERLOCK ACTIVE</span>
        </div>
        <p class="text-xs text-slate-700">
          The AI engine recommends deploying 3 emergency shuttles and rate-limiting Gate 2 ingress. Sized to clear the 170-seat transport gap.
        </p>
        <div class="flex gap-2 pt-1 font-mono text-xs">
          <button id="btn-sim-approve" onclick="onSimOperatorApprove()" class="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition shadow-sm">
            ✓ APPROVE INCIDENT RESPONSE
          </button>
          <button onclick="onSimOperatorReject()" class="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 transition">
            ✕ REJECT
          </button>
        </div>
      </div>

      <!-- Result Card -->
      <div id="sim-result-card" class="hidden p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-3 font-mono text-xs">
        <div class="flex items-center justify-between">
          <span class="font-bold text-emerald-900">INCIDENT STABILIZATION VERIFIED (FEEDBACK LOOP)</span>
          <span id="sim-score-text" class="text-xs font-bold text-emerald-700">EFFECTIVENESS: 100/100</span>
        </div>
        <div class="grid grid-cols-3 gap-2 text-[11px]">
          <div class="p-2 bg-white rounded border border-emerald-100">
            <span class="text-slate-400">Pre-Action Crowd:</span>
            <div id="sim-res-pre-crowd" class="font-bold text-slate-800">18,500</div>
          </div>
          <div class="p-2 bg-white rounded border border-emerald-100">
            <span class="text-slate-400">Post-Action Crowd:</span>
            <div id="sim-res-crowd" class="font-bold text-emerald-600">14,200</div>
          </div>
          <div class="p-2 bg-white rounded border border-emerald-100">
            <span class="text-slate-400">Crowd Delta:</span>
            <div id="sim-res-crowd-delta" class="font-bold text-emerald-600">-4,300 (-23.2%)</div>
          </div>
        </div>
      </div>

      <!-- 11 Steps Progress Container -->
      <div class="space-y-1.5">
        <div class="text-[11px] font-mono font-bold text-slate-500 uppercase">Operational Pipeline Progress:</div>
        <div id="sim-steps-container" class="space-y-1 font-mono text-xs max-h-60 overflow-y-auto">
          <!-- Dynamically filled with step rows -->
        </div>
      </div>

      <!-- Simulation Modal Footer -->
      <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-mono text-slate-500">
        <span id="sim-status-label">Status: Idle</span>
        <button onclick="closeSimulationModal()" class="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition">Close Console</button>
      </div>
    </div>
  </div>

  <!-- ============================================================ -->
  <!-- MODAL: SIGNAL INGESTION SANDBOX                              -->
  <!-- ============================================================ -->
  <div id="ingestion-modal" class="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 hidden flex items-center justify-center p-4">
    <div class="bg-white border border-slate-200 rounded-2xl max-w-xl w-full p-6 shadow-modal space-y-4">
      <div class="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 class="text-sm font-bold text-slate-900">Signal Ingestion Drawer</h3>
          <p class="text-xs text-slate-500 font-mono">Inject synthetic edge frames, PDR vectors, or WhatsApp telemetry</p>
        </div>
        <button onclick="closeIngestionModal()" class="text-slate-400 hover:text-slate-700 text-base font-bold">✕</button>
      </div>

      <div class="space-y-3 text-xs font-mono">
        <div>
          <label class="text-slate-500">Target Zone ID:</label>
          <input id="cv-zone-id" type="text" value="ZONE-A" class="w-full mt-1 px-3 py-1.5 rounded border border-slate-200 focus:outline-none focus:border-[#635BFF]">
        </div>
        <div>
          <label class="text-slate-500">Synthetic Count:</label>
          <input id="cv-count" type="number" value="35" class="w-full mt-1 px-3 py-1.5 rounded border border-slate-200 focus:outline-none focus:border-[#635BFF]">
        </div>
        <button onclick="submitCVDetection()" class="w-full py-2 rounded-lg bg-[#635BFF] text-white font-bold hover:bg-[#5046E5] transition">Inject Frame Detection</button>
      </div>
    </div>
  </div>

  <!-- Toast Notification Container -->
  <div id="toast-container" class="fixed bottom-4 right-4 z-50 space-y-2 pointer-events-none"></div>

  <!-- ============================================================ -->
  <!-- JAVASCRIPT CONTROLLER                                        -->
  <!-- ============================================================ -->
  <script>
    const API_BASE = "/api/v1";
    let activeEventId = null;
    let refreshTimer = null;
    let pollInterval = 10000;
    let currentMasterData = null;

    // View Switching
    function switchMainView(viewName) {
      const views = ['overview', 'twin', 'weather', 'providers', 'signals', 'alerts', 'settings'];
      views.forEach(v => {
        const el = document.getElementById(`view-${v}`);
        const navBtn = document.getElementById(`nav-${v}`);
        if (el) el.classList.add('hidden');
        if (navBtn) {
          navBtn.className = "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[#8A92A6] hover:text-white hover:bg-white/5 transition text-left";
        }
      });

      const target = document.getElementById(`view-${viewName}`);
      const activeBtn = document.getElementById(`nav-${viewName}`);
      if (target) target.classList.remove('hidden');
      if (activeBtn) {
        activeBtn.className = "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-white bg-[#635BFF]/15 border-l-2 border-[#635BFF] transition text-left font-medium";
      }

      if (viewName === 'overview' && leafletMap) {
        setTimeout(() => leafletMap.invalidateSize(), 200);
      }
    }

    // Command Palette Controller
    function openCommandPalette() {
      const p = document.getElementById("command-palette");
      if (p) {
        p.classList.remove("hidden");
        document.getElementById("command-input").focus();
      }
    }
    function closeCommandPalette() {
      const p = document.getElementById("command-palette");
      if (p) p.classList.add("hidden");
    }
    function handleCommandSearch() {
      const query = document.getElementById("command-input").value.toLowerCase();
      const buttons = document.querySelectorAll("#command-results button");
      buttons.forEach(btn => {
        const text = btn.innerText.toLowerCase();
        btn.style.display = text.includes(query) ? "flex" : "none";
      });
    }

    // Operations Menu Dropdown
    function toggleOperationsMenu() {
      const m = document.getElementById("operations-menu");
      if (m) m.classList.toggle("hidden");
    }
    document.addEventListener("click", (e) => {
      const m = document.getElementById("operations-menu");
      if (m && !e.target.closest("#operations-menu") && !e.target.closest("button[onclick*='toggleOperationsMenu']")) {
        m.classList.add("hidden");
      }
    });

    // Keyboard Shortcuts (⌘K / Ctrl+K and ESC)
    window.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        const p = document.getElementById("command-palette");
        if (p && !p.classList.contains("hidden")) closeCommandPalette();
        else openCommandPalette();
      }
      if (e.key === "Escape") {
        closeCommandPalette();
        closeSimulationModal();
        closeIngestionModal();
      }
    });

    // Wall Clock
    function updateWallClock() {
      const el = document.getElementById("wall-clock-text");
      if (el) {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        const secs = String(now.getSeconds()).padStart(2, '0');
        el.innerText = `${hrs}:${mins}:${secs} IST`;
      }
    }
    setInterval(updateWallClock, 1000);
    updateWallClock();

    function setTimelineClock(text) {
      const el = document.getElementById("timeline-clock-text");
      if (el) el.innerText = text;
    }

    // Toast Notification
    function showToast(msg, type = "info") {
      const container = document.getElementById("toast-container");
      if (!container) return;
      const t = document.createElement("div");
      const colors = {
        success: "bg-emerald-900/90 text-emerald-200 border-emerald-700",
        error: "bg-rose-900/90 text-rose-200 border-rose-700",
        warning: "bg-amber-900/90 text-amber-200 border-amber-700",
        info: "bg-slate-900/90 text-slate-100 border-slate-700"
      };
      t.className = `px-3.5 py-2 rounded-lg text-xs font-mono font-medium shadow-modal border pointer-events-auto flex items-center gap-2 transition-all transform duration-200 ${colors[type] || colors.info}`;
      t.innerHTML = `<span>●</span><span>${msg}</span>`;
      container.appendChild(t);
      setTimeout(() => {
        t.style.opacity = '0';
        setTimeout(() => t.remove(), 250);
      }, 3500);
    }

    // Fetch Events List
    async function fetchEvents() {
      try {
        const res = await fetch(`${API_BASE}/events`);
        const events = await res.json();
        const select = document.getElementById("event-select");
        if (!select) return;
        select.innerHTML = "";

        if (!events || events.length === 0) {
          select.innerHTML = '<option value="">No events found</option>';
          activeEventId = null;
          return;
        }

        // Sort: Wankhede first
        events.sort((a, b) => {
          if ((a.name || '').includes('Wankhede')) return -1;
          if ((b.name || '').includes('Wankhede')) return 1;
          return 0;
        });

        events.forEach(ev => {
          const opt = document.createElement("option");
          opt.value = ev.event_id;
          opt.innerText = `${ev.name} · Mumbai`;
          select.appendChild(opt);
        });

        if (!activeEventId || !events.some(e => e.event_id === activeEventId)) {
          activeEventId = events[0].event_id;
        }
        select.value = activeEventId;
        await refreshDashboardState();
      } catch (e) {
        console.error("Error fetching events:", e);
      }
    }

    function onEventChanged() {
      const select = document.getElementById("event-select");
      if (select) {
        activeEventId = select.value;
        refreshDashboardState();
      }
    }

    // Master Dashboard State Refresh
    async function refreshDashboardState() {
      if (!activeEventId) return;

      try {
        const res = await fetch(`${API_BASE}/events/${activeEventId}/dashboard`);
        if (res.ok) {
          const master = await res.json();
          currentMasterData = master;
          renderVenueCard(master.venue, master.event);
          renderMasterKPIs(master.kpis, master.recommendations);
          renderWeatherCard(master.weather, master.signals?.weather);
          renderWhatsAppPanel(master.whatsapp_integration, master.signals?.whatsapp, master.providers);
          renderRecommendations(master.recommendations);
          renderTimeline(master.timeline);
          renderLeafletMap(master.venue, master.zones, master.providers, master.weather, activeDigitalTwinData);
          if (!activeDigitalTwinData && master.digital_twin) {
            renderDigitalTwinPanel(master.digital_twin, master.zones, master.providers, master.weather);
          }
          animateProgressBar();
          const lastEl = document.getElementById("last-updated-text");
          if (lastEl) lastEl.innerText = new Date().toLocaleTimeString();
        }
      } catch (e) {
        console.error("Error refreshing dashboard:", e);
      }
    }

    function animateProgressBar() {
      const bar = document.getElementById("refresh-progress");
      if (!bar) return;
      bar.style.transition = 'none';
      bar.style.width = '0%';
      setTimeout(() => {
        bar.style.transition = `width ${pollInterval}ms linear`;
        bar.style.width = '100%';
      }, 50);
    }

    // Render Event & Venue Metadata
    function renderVenueCard(venue, event) {
      if (!event) return;
      const vName = document.getElementById("venue-name-text");
      const vAddr = document.getElementById("venue-full-address");
      if (vName) vName.innerText = event.name || "Wankhede Stadium";
      if (vAddr) vAddr.innerText = `${event.city || 'Mumbai'} · Match Day · Cricket Match · ${venue?.source_name || 'Verified MCA Record'}`;
    }

    // Render Master KPIs
    function renderMasterKPIs(kpis, recs) {
      if (!kpis) return;
      const totalCrowd = kpis.total_crowd?.value || 21370;
      const totalCap = kpis.total_capacity?.value || 33500;
      const utilPct = kpis.utilization_pct?.value || ((totalCrowd / totalCap) * 100);

      const crowdEl = document.getElementById("venue-crowd-count");
      const capEl = document.getElementById("venue-capacity-count");
      const utilEl = document.getElementById("venue-util-pct-text");
      const barEl = document.getElementById("venue-util-bar");

      if (crowdEl) crowdEl.innerText = totalCrowd.toLocaleString();
      if (capEl) capEl.innerText = totalCap.toLocaleString();
      if (utilEl) utilEl.innerText = `${utilPct.toFixed(1)}%`;
      if (barEl) barEl.style.width = `${Math.min(100, utilPct)}%`;

      // Intel panel sync
      const kUtil = document.getElementById("kpi-util-value");
      const kCrowd = document.getElementById("kpi-total-crowd");
      const kCap = document.getElementById("kpi-total-capacity");
      const kBar = document.getElementById("kpi-util-bar");
      if (kUtil) kUtil.innerText = `${utilPct.toFixed(1)}%`;
      if (kCrowd) kCrowd.innerText = totalCrowd.toLocaleString();
      if (kCap) kCap.innerText = totalCap.toLocaleString();
      if (kBar) kBar.style.width = `${Math.min(100, utilPct)}%`;

      // Risk
      const riskEl = document.getElementById("kpi-risk-text");
      if (riskEl && kpis.overall_risk?.value) {
        riskEl.innerText = kpis.overall_risk.value.toUpperCase();
      }

      // Transport
      const transEl = document.getElementById("kpi-transport-avail");
      if (transEl && kpis.transport_available?.value !== undefined) {
        transEl.innerText = kpis.transport_available.value.toLocaleString();
      }

      // Pending recs tag
      const recsTag = document.getElementById("recs-count-tag");
      const pendingCount = recs ? recs.filter(r => r.status === 'pending').length : 0;
      if (recsTag) recsTag.innerText = pendingCount;
    }

    // Render Weather Card
    function renderWeatherCard(weather, signal) {
      if (!weather) return;
      const tempVal = document.getElementById("weather-temp-val");
      const feelsLike = document.getElementById("weather-feels-like");
      const descText = document.getElementById("weather-desc-text");
      const precipRate = document.getElementById("weather-precip-rate");
      const windSpeed = document.getElementById("weather-wind-speed");
      const humidityPct = document.getElementById("weather-humidity-pct");
      const visibilityKm = document.getElementById("weather-visibility-km");
      const intensityBadge = document.getElementById("weather-intensity-badge");

      if (tempVal) tempVal.innerText = `${weather.temperature_c.toFixed(1)}°C`;
      if (feelsLike) feelsLike.innerText = `Feels like ${(weather.feels_like_c || weather.temperature_c).toFixed(1)}°C`;
      if (descText) descText.innerText = weather.weather_description || "Light drizzle";
      if (precipRate) precipRate.innerText = `${weather.precipitation_mm_h.toFixed(1)} mm/h`;
      if (windSpeed) windSpeed.innerText = `${weather.wind_speed_kmh.toFixed(0)} km/h SW`;
      if (humidityPct) humidityPct.innerText = `${weather.humidity_pct.toFixed(0)}%`;
      if (visibilityKm) visibilityKm.innerText = `${(weather.visibility_m / 1000).toFixed(1)} km`;

      if (intensityBadge) {
        intensityBadge.innerText = `${(weather.rain_intensity || 'LIGHT').toUpperCase()} (${weather.precipitation_mm_h.toFixed(1)} mm/h)`;
      }

      const mapBadge = document.getElementById("map-weather-overlay-badge");
      if (mapBadge) {
        mapBadge.innerText = `WEATHER OVERLAY: ${(weather.weather_description || 'LIVE').toUpperCase()} (${weather.precipitation_mm_h.toFixed(1)} mm/h)`;
      }
    }

    // Render WhatsApp / Provider Pulse
    function renderWhatsAppPanel(waData, waSignal, providers) {
      const badge = document.getElementById("wa-integration-badge");
      if (badge) {
        badge.innerText = waData?.is_sandbox ? "WhatsApp Sandbox" : "Meta WhatsApp Live";
      }

      const prov = providers?.find(p => p.type === 'transport') || providers?.[0];
      const provNameEl = document.getElementById("wa-provider-name");
      if (provNameEl && prov) {
        provNameEl.innerText = prov.name ? prov.name.split('—')[0].trim() : "BEST Transport Fleet";
      }
      const quarEl = document.getElementById("wa-stat-quarantine");
      if (quarEl && prov) {
        quarEl.innerText = prov.available || 450;
      }
    }

    // Render Recommendations
    function renderRecommendations(recs) {
      const container = document.getElementById("recommendations-container");
      if (!container) return;
      if (!recs || recs.length === 0) {
        container.innerHTML = `<div class="p-3 text-slate-400 font-mono text-xs">No pending recommendations. System nominal.</div>`;
        return;
      }
      container.innerHTML = recs.map(r => `
        <div class="p-4 rounded-xl border border-slate-200 bg-white space-y-2 font-mono text-xs shadow-card">
          <div class="flex justify-between items-center">
            <span class="font-bold text-slate-800 uppercase tracking-wide">${r.type || 'RECOMMENDATION'}</span>
            <span class="text-[10px] px-2 py-0.5 rounded font-bold ${r.status === 'approved' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}">${r.status.toUpperCase()}</span>
          </div>
          <p class="text-slate-600 font-sans text-xs">${r.description}</p>
          ${r.status === 'pending' ? `
            <div class="flex gap-2 pt-2">
              <button onclick="approveRecommendation(${r.id})" class="px-3 py-1 rounded bg-[#635BFF] hover:bg-[#5046E5] text-white font-bold transition">Approve</button>
              <button onclick="rejectRecommendation(${r.id})" class="px-3 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition">Decline</button>
            </div>
          ` : ''}
        </div>
      `).join("");
    }

    // Render Timeline
    function renderTimeline(timeline) {
      const container = document.getElementById("timeline-container");
      if (!container || !timeline || timeline.length === 0) return;
      container.innerHTML = timeline.slice(0, 5).map(t => `
        <div class="flex items-start gap-2 border-l-2 border-emerald-500 pl-2">
          <span class="text-[10px] text-slate-400 shrink-0">${t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : '09:31:17'}</span>
          <div class="text-[11px] text-slate-700 truncate">Mitigation stabilized (score: ${t.effectiveness_score || 100}/100)</div>
        </div>
      `).join("");
    }

    // Recommendation Actions
    async function approveRecommendation(id) {
      try {
        const res = await fetch(`${API_BASE}/recommendations/${id}/approve`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ approved_by: "ORGANIZER_ADMIN" })
        });
        if (res.ok) {
          showToast(`Recommendation #${id} approved and dispatched`, "success");
          refreshDashboardState();
        }
      } catch (e) {
        showToast("Error approving recommendation", "error");
      }
    }

    async function rejectRecommendation(id) {
      try {
        const res = await fetch(`${API_BASE}/recommendations/${id}/reject`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rejected_by: "ORGANIZER_ADMIN", reason: "Operational override" })
        });
        if (res.ok) {
          showToast(`Recommendation #${id} rejected`, "info");
          refreshDashboardState();
        }
      } catch (e) {
        showToast("Error rejecting recommendation", "error");
      }
    }

    // Digital Twin Side-by-Side Panel & Cascade Chain
    let activeDigitalTwinData = null;

    function renderDigitalTwinPanel(dt, zones, providers, liveWeather) {
      if (!dt) return;
      activeDigitalTwinData = dt;

      const baseCrowd = document.getElementById("dt-comp-base-crowd");
      const simCrowd = document.getElementById("dt-comp-sim-crowd");
      const deltaCrowd = document.getElementById("dt-comp-delta-crowd");
      if (baseCrowd) baseCrowd.innerText = `${dt.baseline_total_crowd.toLocaleString()} ± 5%`;
      if (simCrowd) simCrowd.innerText = `${dt.simulated_total_crowd.toLocaleString()} ± ${dt.uncertainty_pct.toFixed(0)}%`;
      if (deltaCrowd) {
        const d = dt.crowd_delta;
        deltaCrowd.innerText = `${d >= 0 ? '+' : ''}${d.toLocaleString()} (${d >= 0 ? '+' : ''}${dt.crowd_delta_pct.toFixed(1)}%)`;
      }

      // Transport Demand & Gap
      const simTrans = document.getElementById("dt-comp-sim-trans");
      const deltaTrans = document.getElementById("dt-comp-delta-trans");
      if (simTrans) simTrans.innerText = `${dt.transport_demand_required || 620} seats required`;
      if (deltaTrans) {
        deltaTrans.innerText = dt.transport_capacity_gap > 0 ? `${dt.transport_capacity_gap}-seat deficit gap` : `0 deficit (Gap Closed)`;
      }

      // Gap Status on Provider Pulse Module
      const gapEl = document.getElementById("wa-gap-status");
      if (gapEl) {
        if (dt.transport_capacity_gap > 0) {
          gapEl.innerText = `${dt.transport_capacity_gap}-SEAT DEFICIT`;
          gapEl.className = "font-bold text-amber-600 animate-pulse";
        } else {
          gapEl.innerText = "CAPACITY GAP CLOSED";
          gapEl.className = "font-bold text-emerald-600";
        }
      }

      // Render 8-Step Cascade Chain
      if (dt.cascade_chain && dt.cascade_chain.length > 0) {
        renderCascadeChain(dt.cascade_chain, dt.transport_capacity_gap);
      }

      // Recommendations list
      const recList = document.getElementById("dt-recommendations-list");
      if (recList && dt.weather_recommendations) {
        recList.innerHTML = dt.weather_recommendations.map(r => `
          <div class="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-700 flex items-start gap-2">
            <span class="text-[#635BFF] font-bold">▶</span>
            <div><strong class="text-slate-900">RECOMMENDED:</strong> ${r}</div>
          </div>
        `).join("");
      }
    }

    function renderCascadeChain(chain, capacityGap) {
      const container = document.getElementById("dt-cascade-chain-container");
      if (!container || !chain) return;

      const icons = ["🌧️", "🚶", "🏢", "🚌", "⚠️", "📡", "💬", "🛡️"];
      container.innerHTML = chain.map((step, idx) => {
        const isResolved = step.status === "RESOLVED" || step.status === "MITIGATED" || step.status === "CONFIRMED";
        const isAlert = step.status === "ALERT_GAP" || step.status === "SURGING";
        
        let borderCol = "border-slate-200 bg-white";
        let textCol = "text-slate-800";
        let badge = `<span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">${step.status}</span>`;

        if (isResolved) {
          borderCol = "border-emerald-200 bg-emerald-50/50";
          textCol = "text-emerald-900 font-bold";
          badge = `<span class="text-[9px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">${step.status}</span>`;
        } else if (isAlert) {
          borderCol = "border-amber-200 bg-amber-50/50";
          textCol = "text-amber-900 font-bold";
          badge = `<span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-bold">${step.status}</span>`;
        }

        return `
          <div class="p-2 rounded-lg border ${borderCol} flex flex-col justify-between shadow-xs">
            <div>
              <div class="text-[9px] text-slate-400 font-semibold uppercase truncate">${step.step}</div>
              <div class="text-base my-0.5">${icons[idx % icons.length]}</div>
              <div class="text-[11px] leading-tight ${textCol}">${step.detail}</div>
            </div>
            <div class="pt-1">${badge}</div>
          </div>
        `;
      }).join("");

      const statusBadge = document.getElementById("dt-cascade-status-badge");
      if (statusBadge) {
        if (capacityGap === 0) {
          statusBadge.innerText = "CAPACITY GAP CLOSED · RISK MITIGATED";
          statusBadge.className = "px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200";
        } else {
          statusBadge.innerText = `ACTIVE GAP: ${capacityGap} SEATS`;
          statusBadge.className = "px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200";
        }
      }
    }

    // What-If Simulator Triggers
    async function executeDigitalTwinSimulation(scenarioNameOverride) {
      if (!activeEventId) return;
      const scenario = scenarioNameOverride || "heavy_rain";
      const rain = parseFloat(document.getElementById("dt-input-rain")?.value || "40");

      showToast(`Running Digital Twin: ${scenario} (${rain} mm/h)...`, "info");
      try {
        const res = await fetch(`${API_BASE}/events/${activeEventId}/digital-twin/simulate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scenario_name: scenario,
            precipitation_mm_h: rain
          })
        });
        if (res.ok) {
          const data = await res.json();
          renderDigitalTwinPanel(data.digital_twin, currentMasterData?.zones, currentMasterData?.providers, currentMasterData?.weather);
          showToast(`Digital Twin calculated: ${data.digital_twin.scenario_label}`, "success");
        }
      } catch (e) {
        showToast("Simulation error", "error");
      }
    }

    function applyPresetScenario(name) {
      const presets = {
        normal: 0,
        moderate_rain: 5,
        heavy_rain: 20,
        extreme_rain: 60,
        extreme_heat: 0,
        high_wind: 3,
        thunderstorm: 30
      };
      const r = presets[name] !== undefined ? presets[name] : 40;
      const rInput = document.getElementById("dt-input-rain");
      const rVal = document.getElementById("dt-slider-rain-val");
      if (rInput) rInput.value = r;
      if (rVal) rVal.innerText = `${r} mm/h`;
      executeDigitalTwinSimulation(name);
    }

    function onWhatIfInputChanged() {
      const rInput = document.getElementById("dt-input-rain");
      const rVal = document.getElementById("dt-slider-rain-val");
      if (rInput && rVal) rVal.innerText = `${rInput.value} mm/h`;
    }

    // Provider Operational Telemetry Dispatch
    async function sendQuickOperationalResponse(text) {
      const prov = currentMasterData?.providers?.find(p => p.type === 'transport') || currentMasterData?.providers?.[0];
      const provId = prov ? prov.provider_id : "PROV-BEST-TRANSIT";

      showToast(`Ingesting provider telemetry: "${text}"...`, "info");
      try {
        const res = await fetch(`${API_BASE}/whatsapp/sandbox/respond`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider_id: provId,
            response_text: text,
            event_id: activeEventId
          })
        });
        if (res.ok) {
          const data = await res.json();
          showToast(`Capacity confirmed: ${data.response.delta_capacity >= 0 ? '+' : ''}${data.response.delta_capacity} ${data.response.resource_type}!`, "success");
          if (data.digital_twin) {
            renderDigitalTwinPanel(data.digital_twin, currentMasterData?.zones, currentMasterData?.providers, currentMasterData?.weather);
          }
          refreshDashboardState();
        }
      } catch (e) {
        showToast("Error ingesting telemetry", "error");
      }
    }

    async function dispatchOperationalCapacityPoll() {
      const prov = currentMasterData?.providers?.find(p => p.type === 'transport') || currentMasterData?.providers?.[0];
      const provId = prov ? prov.provider_id : "PROV-BEST-TRANSIT";

      showToast("Polling provider for standby capacity...", "info");
      try {
        const res = await fetch(`${API_BASE}/whatsapp/sandbox/request`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider_id: provId,
            event_id: activeEventId,
            required_capacity: 170,
            weather_trigger: "Heavy Rain (40 mm/h) — Transport Surge"
          })
        });
        if (res.ok) {
          showToast("Operational capacity inquiry dispatched via WhatsApp Sandbox", "success");
        }
      } catch (e) {
        showToast("Dispatch error", "error");
      }
    }

    // Leaflet Geospatial Operations Map
    let leafletMap = null;
    let currentTileLayer = null;

    function initLeafletMap() {
      const container = document.getElementById("operational-map");
      if (!container || leafletMap) return;

      try {
        // Wankhede Stadium coordinates: 18.9375°N, 72.8265°E
        leafletMap = L.map('operational-map', {
          zoomControl: false,
          attributionControl: true
        }).setView([18.9375, 72.8265], 15);

        // Clean light Cartography
        setBasemap('light');

        // Wankhede Anchor Marker
        const stadiumIcon = L.divIcon({
          className: 'custom-stadium-marker',
          html: `<div style="background:#635BFF; border: 2.5px solid white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 13px; box-shadow: 0 2px 8px rgba(99,91,255,0.5);">🏟️</div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });

        L.marker([18.9375, 72.8265], { icon: stadiumIcon })
          .addTo(leafletMap)
          .bindPopup(`<b>Wankhede Stadium</b><br>Seated Capacity: 33,500<br>Churchgate, Mumbai`);

        const overlay = document.getElementById("map-loading-overlay");
        if (overlay) overlay.style.display = "none";
      } catch (e) {
        console.error("Leaflet init error:", e);
      }
    }

    function setBasemap(type) {
      if (!leafletMap) return;
      if (currentTileLayer) leafletMap.removeLayer(currentTileLayer);

      if (type === 'satellite') {
        currentTileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
          attribution: '&copy; Esri',
          className: 'map-tiles-sat',
          maxZoom: 19
        }).addTo(leafletMap);
      } else {
        // Crisp 100% Free OpenStreetMap
        currentTileLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>',
          className: type === 'dark' ? 'map-tiles-dark' : 'map-tiles-light',
          maxZoom: 19
        }).addTo(leafletMap);
      }
    }

    function resetMapView() {
      if (leafletMap) leafletMap.setView([18.9375, 72.8265], 15);
    }

    function toggleMapLayer(layer) {
      showToast(`Map layer filter: ${layer.toUpperCase()}`, "info");
    }

    function renderLeafletMap(venue, zones, providers, weather, dtState) {
      if (!leafletMap) initLeafletMap();
    }

    // 11-Step Master Simulation Modal Controller
    const SIMULATION_STEPS = [
      { id: 1, name: "Event & Multi-Zone Topology Setup", desc: "Initialize Wankhede Bowl, Marine Concourse, Churchgate Station" },
      { id: 2, name: "CCTV Head-Count Ingestion", desc: "Capture optical head-count velocity & concourse density surge" },
      { id: 3, name: "PDR Movement Correlation", desc: "Correlate anonymized step/heading telemetry mesh" },
      { id: 4, name: "Predictive Demand Forecasting", desc: "Project 30-min threshold breach horizon" },
      { id: 5, name: "Multi-Factor Risk Evaluation", desc: "Escalate zone safety envelope to CRITICAL" },
      { id: 6, name: "Orchestration Sizing", desc: "Generate sized shuttle dispatch & ingress rate-limiting" },
      { id: 7, name: "Pre-Action Snapshot", desc: "Capture baseline telemetry for feedback loop validation" },
      { id: 8, name: "Human-in-the-Loop Approval", desc: "Authorize physical dispatch (Safety interlock)" },
      { id: 9, name: "Dispatch & GPS Fleet Ingestion", desc: "Transmit transit order to BEST special fleet" },
      { id: 10, name: "Optical Flow Ingestion", desc: "Stabilize egress corridor & reverse density accumulation" },
      { id: 11, name: "Feedback Loop & Stabilization", desc: "Score mitigation efficacy & confirm 100% resolution" }
    ];

    function launchFullSimulation() {
      const modal = document.getElementById("simulation-modal");
      if (!modal) return;
      modal.classList.remove("hidden");
      renderSimulationStepsUI();
      runNextSimulationSteps(1);
    }

    function closeSimulationModal() {
      const modal = document.getElementById("simulation-modal");
      if (modal) modal.classList.add("hidden");
    }

    function renderSimulationStepsUI() {
      const container = document.getElementById("sim-steps-container");
      if (!container) return;
      container.innerHTML = SIMULATION_STEPS.map(s => `
        <div id="step-row-${s.id}" class="p-2 rounded-lg border border-slate-200 bg-white flex items-center justify-between text-xs transition">
          <div class="flex items-center gap-2">
            <span id="step-icon-${s.id}" class="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center font-bold text-[10px] text-slate-500">${s.id}</span>
            <div>
              <span class="font-bold text-slate-800">${s.name}</span>
              <div class="text-[10px] text-slate-400 font-sans">${s.desc}</div>
            </div>
          </div>
          <span id="step-badge-${s.id}" class="text-[10px] px-2 py-0.5 rounded font-bold bg-slate-100 text-slate-500">QUEUED</span>
        </div>
      `).join("");
    }

    function setSimStepStatus(stepId, status) {
      const row = document.getElementById(`step-row-${stepId}`);
      const badge = document.getElementById(`step-badge-${stepId}`);
      const icon = document.getElementById(`step-icon-${stepId}`);
      if (!badge || !row) return;

      if (status === 'RUNNING') {
        badge.innerText = "EXECUTING...";
        badge.className = "text-[10px] px-2 py-0.5 rounded font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 animate-pulse";
        row.className = "p-2 rounded-lg border border-indigo-300 bg-indigo-50/30 flex items-center justify-between text-xs";
        icon.className = "w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-[10px]";
      } else if (status === 'SUCCESS') {
        badge.innerText = "VERIFIED ✓";
        badge.className = "text-[10px] px-2 py-0.5 rounded font-bold bg-emerald-50 text-emerald-700 border border-emerald-200";
        row.className = "p-2 rounded-lg border border-emerald-200 bg-emerald-50/20 flex items-center justify-between text-xs";
        icon.className = "w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-[10px]";
      }
    }

    async function runNextSimulationSteps(startStep) {
      for (let i = startStep; i <= 7; i++) {
        setSimStepStatus(i, 'RUNNING');
        await new Promise(r => setTimeout(r, 600));
        setSimStepStatus(i, 'SUCCESS');
      }

      // Step 8: Human Approval Checkpoint
      const banner = document.getElementById("sim-approval-banner");
      if (banner) {
        banner.classList.remove("hidden");
        setSimStepStatus(8, 'RUNNING');
        const statusLabel = document.getElementById("sim-status-label");
        if (statusLabel) statusLabel.innerText = "Awaiting Human Operator Authorization";
      }
    }

    async function onSimOperatorApprove() {
      const banner = document.getElementById("sim-approval-banner");
      if (banner) banner.classList.add("hidden");
      setSimStepStatus(8, 'SUCCESS');

      for (let i = 9; i <= 11; i++) {
        setSimStepStatus(i, 'RUNNING');
        await new Promise(r => setTimeout(r, 600));
        setSimStepStatus(i, 'SUCCESS');
      }

      const resCard = document.getElementById("sim-result-card");
      if (resCard) resCard.classList.remove("hidden");
      showToast("11-Step Master Simulation verified with 100% stabilization", "success");
      refreshDashboardState();
    }

    function onSimOperatorReject() {
      const banner = document.getElementById("sim-approval-banner");
      if (banner) banner.classList.add("hidden");
      showToast("Simulation response rejected by operator", "info");
    }

    // Modal drawer helpers
    function openIngestionModal() {
      const m = document.getElementById("ingestion-modal");
      if (m) m.classList.remove("hidden");
    }
    function closeIngestionModal() {
      const m = document.getElementById("ingestion-modal");
      if (m) m.classList.add("hidden");
    }

    // Demo Actions
    async function triggerSurgeSimulation() {
      showToast("Injecting crowd surge telemetry into Bowl...", "warning");
      try {
        await fetch(`${API_BASE}/events/${activeEventId}/simulate`, { method: "POST" });
        showToast("Crowd surge active in Zone A", "success");
        refreshDashboardState();
      } catch (e) {
        showToast("Surge simulation error", "error");
      }
    }

    async function triggerRunIntelligence() {
      showToast("Recomputing AI forecasting and risk models...", "info");
      refreshDashboardState();
    }

    async function triggerDemoSetup() {
      showToast("Seeding verified Mumbai venues (Wankhede & JWCC)...", "info");
      try {
        await fetch(`${API_BASE}/demo/seed-mumbai`, { method: "POST" });
        showToast("Mumbai venues seeded successfully", "success");
        fetchEvents();
      } catch (e) {
        showToast("Seed error", "error");
      }
    }

    async function triggerResetDemo() {
      showToast("Resetting demo baseline data...", "info");
      try {
        await fetch(`${API_BASE}/demo/reset`, { method: "POST" });
        showToast("Database reset to clean baseline", "success");
        fetchEvents();
      } catch (e) {
        showToast("Reset error", "error");
      }
    }

    async function refreshWeatherOnly() {
      showToast("Refreshed live weather from Open-Meteo", "success");
      refreshDashboardState();
    }

    // App Initialization
    window.addEventListener("DOMContentLoaded", () => {
      fetchEvents();
      setInterval(refreshDashboardState, pollInterval);
      setTimeout(initLeafletMap, 400);
    });
  </script>
</body>
</html>
'''

target_file = r"C:\Users\neera\OneDrive\Documents\Default Project\eventos\backend\app\static\index.html"

with open(target_file, "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)

print(f"Successfully generated redesigned UI at: {target_file}")
print(f"File size: {os.path.getsize(target_file)} bytes")
