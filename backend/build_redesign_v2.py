"""
EVENTOS Control Tower - Production Grade Redesign Builder (v2)
Typography & Layout Polish:
- Plus Jakarta Sans + Inter for ultra-crisp, crystal-clear typography
- Tabular figures for solid, beautiful numbers (no faint/slashed mono zeroes)
- Header layout collision fix: prevent wrapping and text collisions
- Clean zone distribution cards with high-contrast text and vibrant indicators
- 100% preservation of all 56 DOM IDs and 50 JS functions
"""

import os
import sys

HTML_CONTENT = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EVENTOS — Event Operations Control Tower</title>
  
  <!-- High-Clarity Modern Typography: Plus Jakarta Sans & Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- Leaflet GIS Cartography -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>

  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: {
            sans: ['"Plus Jakarta Sans"', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
            num: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
          },
          colors: {
            brand: {
              50: '#EEF2FF',
              100: '#E0E7FF',
              500: '#6366F1',
              600: '#4F46E5',
              700: '#4338CA',
            },
            surface: {
              DEFAULT: '#FFFFFF',
              ground: '#F8FAFC',
              sidebar: '#0F172A',
              border: '#E2E8F0',
              hover: '#F1F5F9',
            }
          }
        }
      }
    }
  </script>

  <style>
    * {
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      text-rendering: optimizeLegibility;
    }
    body, button, input, select, textarea {
      font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Clean custom scrollbar */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: #F1F5F9;
    }
    ::-webkit-scrollbar-thumb {
      background: #CBD5E1;
      border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #94A3B8;
    }

    /* Crisp Apple Maps light cartography filter */
    .map-tiles-light {
      filter: contrast(1.03) brightness(1.02) saturate(0.92);
    }
    .map-tiles-sat {
      filter: contrast(1.08) brightness(0.96);
    }

    /* Crisp Tabular Numerals (Solid, Beautiful, Non-jagged) */
    .tabular-nums, .font-num {
      font-variant-numeric: tabular-nums;
      font-feature-settings: "tnum" 1;
      letter-spacing: -0.015em;
    }

    /* Subtle operational pulse */
    @keyframes pulse-dot {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.15); opacity: 0.75; }
    }
    .animate-pulse-dot {
      animation: pulse-dot 2.2s infinite ease-in-out;
    }

    /* Range slider styling */
    input[type=range] {
      -webkit-appearance: none;
      background: #E2E8F0;
      border-radius: 9999px;
      height: 6px;
    }
    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none;
      height: 16px;
      width: 16px;
      border-radius: 50%;
      background: #4F46E5;
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
      transition: transform 0.1s ease;
    }
    input[type=range]::-webkit-slider-thumb:hover {
      transform: scale(1.15);
    }

    /* ============================================================ */
    /* LIQUID GLASS DESIGN SYSTEM (Apple Maps + Linear + Raycast)    */
    /* ============================================================ */
    /* LIQUID GLASS DESIGN SYSTEM (Apple Maps + Linear + Raycast)    */
    /* ============================================================ */

    .glass-float {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.50) 0%, rgba(255, 255, 255, 0.32) 100%);
      backdrop-filter: blur(28px) saturate(220%) contrast(106%);
      -webkit-backdrop-filter: blur(28px) saturate(220%) contrast(106%);
      border: 1px solid rgba(255, 255, 255, 0.75);
      box-shadow: 
        0 16px 38px -6px rgba(15, 23, 42, 0.12), 
        0 4px 14px -2px rgba(15, 23, 42, 0.05), 
        inset 0 1.5px 1px rgba(255, 255, 255, 0.98),
        inset 0 -1px 1px rgba(0, 0, 0, 0.05),
        inset 1px 0 1px rgba(255, 255, 255, 0.5);
      border-radius: 14px;
      position: relative;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1), background 0.2s ease;
    }

    .glass-pill {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.58) 0%, rgba(255, 255, 255, 0.38) 100%);
      backdrop-filter: blur(22px) saturate(210%) contrast(105%);
      -webkit-backdrop-filter: blur(22px) saturate(210%) contrast(105%);
      border: 1px solid rgba(255, 255, 255, 0.82);
      box-shadow: 
        0 6px 20px -2px rgba(15, 23, 42, 0.07), 
        inset 0 1.5px 1px rgba(255, 255, 255, 0.98),
        inset 0 -1px 1px rgba(0, 0, 0, 0.04);
      border-radius: 9999px;
      position: relative;
      transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .glass-panel {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.68) 0%, rgba(255, 255, 255, 0.46) 100%);
      backdrop-filter: blur(32px) saturate(220%) contrast(106%);
      -webkit-backdrop-filter: blur(32px) saturate(220%) contrast(106%);
      border: 1px solid rgba(255, 255, 255, 0.85);
      box-shadow: 
        0 24px 56px -10px rgba(15, 23, 42, 0.15), 
        0 8px 24px -4px rgba(15, 23, 42, 0.07), 
        inset 0 1.5px 1.5px rgba(255, 255, 255, 1),
        inset 0 -1px 1px rgba(0, 0, 0, 0.05);
      border-radius: 18px;
      position: relative;
      transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .glass-control {
      background: rgba(255, 255, 255, 0.55);
      border: 1px solid rgba(255, 255, 255, 0.65);
      border-radius: 8px;
      transition: all 0.15s ease-out;
      color: #334155;
    }
    .glass-control:hover {
      background: rgba(255, 255, 255, 0.95);
      color: #0F172A;
      box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
    }
    .glass-control:active {
      transform: scale(0.97);
    }
    .glass-control.active {
      background: #4F46E5;
      color: #FFFFFF;
      border-color: #4338CA;
      box-shadow: 0 2px 6px rgba(79, 70, 229, 0.25);
    }

    .glass-popover {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.78) 0%, rgba(255, 255, 255, 0.58) 100%);
      backdrop-filter: blur(28px) saturate(220%);
      -webkit-backdrop-filter: blur(28px) saturate(220%);
      border: 1px solid rgba(255, 255, 255, 0.88);
      box-shadow: 
        0 24px 52px -12px rgba(15, 23, 42, 0.16), 
        0 8px 24px -4px rgba(15, 23, 42, 0.08), 
        inset 0 1.5px 1px rgba(255, 255, 255, 1);
      border-radius: 16px;
      position: relative;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .glass-command {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.80) 0%, rgba(255, 255, 255, 0.60) 100%);
      backdrop-filter: blur(32px) saturate(220%);
      -webkit-backdrop-filter: blur(32px) saturate(220%);
      border: 1px solid rgba(255, 255, 255, 0.88);
      box-shadow: 
        0 32px 72px -16px rgba(15, 23, 42, 0.25), 
        0 12px 32px -8px rgba(15, 23, 42, 0.12), 
        inset 0 1.5px 1px rgba(255, 255, 255, 1);
      border-radius: 20px;
      position: relative;
    }

    .glass-simulation {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.54) 0%, rgba(255, 255, 255, 0.36) 100%);
      backdrop-filter: blur(30px) saturate(220%) contrast(106%);
      -webkit-backdrop-filter: blur(30px) saturate(220%) contrast(106%);
      border: 1px solid rgba(255, 255, 255, 0.80);
      box-shadow: 
        0 20px 48px -12px rgba(15, 23, 42, 0.14), 
        0 6px 18px -4px rgba(15, 23, 42, 0.06), 
        inset 0 1.5px 1px rgba(255, 255, 255, 0.98),
        inset 0 -1px 1px rgba(0, 0, 0, 0.05);
      border-radius: 18px;
      position: relative;
    }

    .glass-marker {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.75) 0%, rgba(255, 255, 255, 0.55) 100%);
      backdrop-filter: blur(16px) saturate(200%);
      -webkit-backdrop-filter: blur(16px) saturate(200%);
      border: 1px solid rgba(255, 255, 255, 0.8);
      box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.12), inset 0 1px 0.5px rgba(255, 255, 255, 0.9);
      border-radius: 12px;
    }

    .glass-canvas-layer {
      position: absolute;
      inset: 0;
      pointer-events: none;
      border-radius: inherit;
      z-index: 0;
    }

    /* Dynamic Refractive Glint / Specular highlight */
    .glass-float::after, .glass-panel::after, .glass-pill::after, .glass-popover::after, .glass-simulation::after {
      content: '';
      position: absolute;
      inset: 0;
      border-radius: inherit;
      pointer-events: none;
      background: radial-gradient(circle at var(--glass-x, 50%) var(--glass-y, 50%), rgba(255, 255, 255, 0.45) 0%, rgba(255, 255, 255, 0) 65%);
      opacity: var(--glass-specular-opacity, 0);
      transition: opacity 0.25s ease;
      z-index: 1;
    }

    /* Fallback for environments lacking backdrop-filter */
    .glass-fallback-active {
      background: rgba(255, 255, 255, 0.98) !important;
      backdrop-filter: none !important;
      -webkit-backdrop-filter: none !important;
      box-shadow: 0 10px 25px rgba(15, 23, 42, 0.12) !important;
    }

    /* Fallback and Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .glass-float, .glass-pill, .glass-panel, .glass-control, .glass-popover, .glass-command, .glass-simulation {
        transition: none !important;
        animation: none !important;
      }
    }
  </style>
</head>

<body class="min-h-screen flex antialiased bg-[#F8FAFC] text-[#0F172A] overflow-x-hidden selection:bg-indigo-600 selection:text-white">

  <!-- ============================================================ -->
  <!-- LEFT NAVIGATION RAIL (SLATE-900 ~210px)                      -->
  <!-- ============================================================ -->
  <aside class="w-[210px] shrink-0 h-screen fixed left-0 top-0 z-30 bg-[#0F172A] border-r border-slate-800 flex flex-col justify-between select-none">
    
    <!-- Top Branding & Navigation Items -->
    <div class="flex flex-col">
      <!-- Brand Header -->
      <div class="h-[56px] px-4 flex items-center gap-2.5 border-b border-slate-800">
        <div class="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-xs shadow-sm shadow-indigo-600/30">
          E
        </div>
        <div class="flex flex-col leading-tight">
          <span class="font-bold text-[13px] tracking-tight text-white">EVENTOS</span>
          <span class="text-[10px] text-slate-400 font-medium">Control Tower</span>
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="p-2 space-y-1 text-xs font-semibold">
        <button id="nav-overview" onclick="switchMainView('overview')" class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-white bg-indigo-600/20 border-l-2 border-indigo-500 transition text-left">
          <svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
          <span>Operations Cockpit</span>
        </button>

        <button id="nav-zones" onclick="switchMainView('zones')" class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
          <div class="flex items-center justify-between w-full">
            <span>Zone Distribution</span>
            <span id="nav-zone-count-badge" class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">3</span>
          </div>
        </button>

        <button id="nav-providers" onclick="switchMainView('providers')" class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4 text-sky-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.121l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.196 1.006.128.832.922z"/></svg>
          <div class="flex items-center justify-between w-full">
            <span>Provider Pulse</span>
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400">TELEGRAM</span>
          </div>
        </button>

        <button id="nav-twin" onclick="switchMainView('twin')" class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          <div class="flex items-center justify-between w-full">
            <span>Digital Twin</span>
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300">SIM</span>
          </div>
        </button>

        <button id="nav-weather" onclick="switchMainView('weather')" class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z"/></svg>
          <span>Weather Radar</span>
        </button>

        <button id="nav-signals" onclick="switchMainView('signals')" class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>
          <span>CCTV & Signals</span>
        </button>

        <button id="nav-alerts" onclick="switchMainView('alerts')" class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition text-left">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
          <div class="flex items-center justify-between w-full">
            <span>Action Audit</span>
            <span id="recs-count-tag" class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300">0</span>
          </div>
        </button>
      </nav>
    </div>

    <!-- Bottom System Status & Config -->
    <div class="p-3.5 border-t border-slate-800 space-y-2">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-dot"></span>
        <span class="text-xs font-semibold text-slate-300">Meta Cloud API v20.0</span>
      </div>
      <div class="text-[11px] text-slate-400 font-medium leading-tight">
        <span>Webhook Active • SQLite DB</span>
      </div>
      <button onclick="triggerResetDemo()" class="w-full text-left text-[11px] font-medium text-slate-400 hover:text-white pt-1 flex items-center gap-1.5 transition">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        <span>Reset Demo Telemetry</span>
      </button>
    </div>
  </aside>

  <!-- ============================================================ -->
  <!-- MAIN WORKSPACE SURFACE (OFFSET 210px)                         -->
  <!-- ============================================================ -->
  <main class="ml-[210px] flex-1 flex flex-col min-w-0 bg-[#F8FAFC]">

    <!-- Top Command Strip (Fixed, Zero Collision) -->
    <header class="h-[58px] bg-white border-b border-slate-200 px-5 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      
      <!-- Left: Venue Selector & Status -->
      <div class="flex items-center gap-2.5 min-w-0">
        <div class="flex items-center gap-1.5 shrink-0">
          <span class="text-[11px] font-bold text-slate-600 uppercase tracking-wider">Venue:</span>
          <select id="event-select" onchange="onEventChanged()" class="bg-slate-50 border border-slate-200 hover:border-slate-300 text-slate-900 text-xs font-semibold rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 cursor-pointer max-w-[240px] truncate"></select>
        </div>

        <span class="glass-pill inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-emerald-800 shrink-0">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse-dot"></span>
          Live Egress
        </span>

        <!-- Hidden on medium screens to prevent any overlap -->
        <span id="venue-full-address" class="text-xs text-slate-500 font-medium hidden 2xl:inline truncate max-w-[280px]">
          Wankhede Stadium • MCA Verified Record
        </span>
      </div>

      <!-- Right: Macro Metrics & Quick Actions -->
      <div class="flex items-center gap-3 shrink-0">
        
        <!-- Live Clock -->
        <div class="flex items-center gap-1 text-xs text-slate-800 font-bold font-num bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
          <span id="wall-clock-text">--:--:--</span>
          <span class="text-[10px] text-slate-500 font-semibold">IST</span>
        </div>

        <!-- Ingestion Status Indicators (Subtle Glass Pills) -->
        <div class="hidden lg:flex items-center gap-2 text-xs font-semibold text-slate-700 border-l border-slate-200 pl-3">
          <span class="glass-pill inline-flex items-center gap-1.5 px-2.5 py-1 text-slate-800"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-xs"></span>CCTV</span>
          <span class="glass-pill inline-flex items-center gap-1.5 px-2.5 py-1 text-slate-800"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-xs"></span>PDR</span>
          <span class="glass-pill inline-flex items-center gap-1.5 px-2.5 py-1 text-slate-800"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-xs"></span>GPS</span>
          <button onclick="toggleProviderPulsePopover()" class="glass-pill inline-flex items-center gap-1.5 px-2.5 py-1 text-indigo-700 hover:text-indigo-900 cursor-pointer shadow-xs transition" title="View Provider Network Pulse">
            <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span>
            <span>Pulse</span>
          </button>
        </div>

        <!-- Command Palette Trigger -->
        <button onclick="openCommandPalette()" class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition">
          <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <span>Jump to...</span>
          <kbd class="text-[10px] font-bold px-1.5 py-0.5 bg-white rounded border border-slate-200 text-slate-500">⌘K</kbd>
        </button>

        <!-- Pitch Demo Extreme Scenario Trigger -->
        <button onclick="runCombinedExtremeDemo()" class="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-indigo-600 to-rose-600 hover:from-indigo-700 hover:to-rose-700 rounded-lg shadow-sm transition animate-pulse" title="Run 3-minute pitch demo story across all sensors">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          <span>⚡ Run Combined Extreme Scenario (Pitch Demo)</span>
        </button>

        <!-- Dropdown Menu -->
        <div class="relative">
          <button onclick="toggleOperationsMenu()" class="p-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>
          </button>
          <div id="operations-menu" class="hidden absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 z-30 text-xs text-slate-700">
            <button onclick="triggerDemoSetup()" class="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
              <span>Seed Wankhede Data</span>
            </button>
            <button onclick="openIngestionModal()" class="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              <span>Manual Telemetry Ingest</span>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Top Loading Progress Bar -->
    <div class="h-0.5 w-full bg-slate-100 overflow-hidden">
      <div id="refresh-progress" class="h-full bg-indigo-600 transition-all duration-300 w-0"></div>
    </div>

    <!-- ============================================================ -->
    <!-- VIEW CONTAINER: OPERATIONS COCKPIT (DEFAULT)                 -->
    <!-- ============================================================ -->
    <div id="view-overview" class="p-5 space-y-4">
      
      <!-- SECTION: ZONE DISTRIBUTION BAR (PROMINENT AT TOP) -->
      <section class="space-y-2.5">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xs font-bold uppercase tracking-wider text-slate-800">Stadium Zone Distribution & Capacity Balance</h2>
            <p class="text-xs text-slate-500 font-medium mt-0.5">Calibrated real-time sensor fusion: CCTV OpenCV spatial counts + PDR movement vectors</p>
          </div>
          <button onclick="switchMainView('zones')" class="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
            <span>Detailed Zone Analytics</span>
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
          </button>
        </div>

        <!-- Dynamic Zone Distribution Cards Container -->
        <div id="zone-distribution-cards" class="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          <!-- Populated dynamically by renderZoneDistribution() -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 animate-pulse">
            <div class="h-4 bg-slate-200 rounded w-1/2 mb-2"></div>
            <div class="h-6 bg-slate-200 rounded w-3/4 mb-3"></div>
            <div class="h-2 bg-slate-100 rounded w-full"></div>
          </div>
          <div class="bg-white rounded-xl border border-slate-200 p-4 animate-pulse">
            <div class="h-4 bg-slate-200 rounded w-1/2 mb-2"></div>
            <div class="h-6 bg-slate-200 rounded w-3/4 mb-3"></div>
            <div class="h-2 bg-slate-100 rounded w-full"></div>
          </div>
          <div class="bg-white rounded-xl border border-slate-200 p-4 animate-pulse">
            <div class="h-4 bg-slate-200 rounded w-1/2 mb-2"></div>
            <div class="h-6 bg-slate-200 rounded w-3/4 mb-3"></div>
            <div class="h-2 bg-slate-100 rounded w-full"></div>
          </div>
        </div>
      </section>

      <!-- SECTION: MAIN OPERATIONAL SPLIT (MAP 68% + AI INTELLIGENCE 32%) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        <!-- Left: Geospatial Map Canvas (8 Columns) -->
        <div class="lg:col-span-8 flex flex-col gap-3">
          <div class="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col relative h-[560px]">
            
            <!-- A. FLOATING MAP CONTROLS (Liquid Glass System) -->
            <div id="map-floating-controls" class="glass-float glass-pill absolute top-3 left-3 z-[1000] flex items-center gap-1 p-1 text-xs font-semibold select-none">
              <button id="btn-map-canvas" onclick="setBasemap('light')" class="glass-control active px-2.5 py-1 text-xs font-bold rounded-lg transition">Canvas</button>
              <button id="btn-map-sat" onclick="setBasemap('satellite')" class="glass-control px-2.5 py-1 text-xs font-semibold rounded-lg transition">Satellite</button>
              <div class="w-px h-3.5 bg-slate-300/70 my-auto"></div>
              <button id="btn-map-zones" onclick="toggleMapLayer('zones')" class="glass-control px-2.5 py-1 text-xs font-semibold rounded-lg transition">Zones</button>
              <button id="btn-map-transit" onclick="toggleMapLayer('transit')" class="glass-control px-2.5 py-1 text-xs font-semibold rounded-lg transition">Transit</button>
              <button id="btn-map-cameras" onclick="toggleMapLayer('cameras')" class="glass-control px-2.5 py-1 text-xs font-semibold rounded-lg transition">CCTV</button>
              <button onclick="resetMapView()" class="glass-control p-1 text-slate-600 hover:text-slate-900 rounded-lg transition" title="Reset Map View">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
              </button>
            </div>

            <!-- B. WEATHER GLASS PILL ON MAP (Click to Expand Weather Intelligence) -->
            <div id="map-weather-pill" onclick="toggleWeatherGlassPanel()" class="glass-pill cursor-pointer hover:scale-102 active:scale-98 transition absolute top-3 right-3 z-[1000] flex items-center gap-2 px-3 py-1.5 shadow-sm text-xs select-none" title="Click to view full weather radar intelligence">
              <span class="text-sm">☁</span>
              <span id="map-weather-overlay-badge" class="font-bold font-num text-slate-800">27°C • Rain 62% • 14 km/h</span>
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            </div>

            <!-- FLOATING ZOOM CONTROLS (Right Margin) -->
            <div id="map-floating-zoom" class="glass-float absolute top-12 right-3 z-[1000] flex flex-col items-center p-1 gap-1 text-xs shadow-sm">
              <button onclick="leafletMap && leafletMap.zoomIn()" class="glass-control w-7 h-7 flex items-center justify-center font-bold text-sm" title="Zoom In">+</button>
              <button onclick="leafletMap && leafletMap.zoomOut()" class="glass-control w-7 h-7 flex items-center justify-center font-bold text-sm" title="Zoom Out">−</button>
              <div class="w-4 h-px bg-slate-300/60 my-0.5"></div>
              <button onclick="resetMapView()" class="glass-control w-7 h-7 flex items-center justify-center text-xs text-slate-700" title="Center Stadium">◎</button>
            </div>

            <!-- C. EXPANDABLE WEATHER INTELLIGENCE GLASS OVERLAY PANEL -->
            <div id="map-weather-expanded-panel" class="hidden glass-panel absolute top-12 right-3 z-[1002] w-80 p-4 space-y-3">
              <div class="flex items-center justify-between border-b border-white/60 pb-2">
                <div class="flex items-center gap-2">
                  <span class="text-base">🌧</span>
                  <span class="font-bold text-xs text-slate-900 tracking-tight">WEATHER INTELLIGENCE</span>
                </div>
                <button onclick="toggleWeatherGlassPanel(false)" class="text-slate-400 hover:text-slate-700 text-xs font-bold p-1">✕</button>
              </div>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div class="p-2 rounded-lg bg-white/50 border border-white/60">
                  <div class="text-[10px] text-slate-500 font-bold uppercase">Temperature</div>
                  <div class="text-base font-bold font-num text-slate-900" id="gw-temp">27.4°C</div>
                  <div class="text-[10px] text-slate-400">Feels like 29.1°C</div>
                </div>
                <div class="p-2 rounded-lg bg-white/50 border border-white/60">
                  <div class="text-[10px] text-slate-500 font-bold uppercase">Rain Probability</div>
                  <div class="text-base font-bold font-num text-indigo-600" id="gw-rain-prob">62%</div>
                  <div class="text-[10px] text-slate-400">Moderate Showers</div>
                </div>
                <div class="p-2 rounded-lg bg-white/50 border border-white/60">
                  <div class="text-[10px] text-slate-500 font-bold uppercase">Wind Speed</div>
                  <div class="text-base font-bold font-num text-slate-900" id="gw-wind">14 km/h</div>
                  <div class="text-[10px] text-slate-400">Heading 278° W</div>
                </div>
                <div class="p-2 rounded-lg bg-white/50 border border-white/60">
                  <div class="text-[10px] text-slate-500 font-bold uppercase">Precipitation</div>
                  <div class="text-base font-bold font-num text-slate-900" id="gw-precip">4.2 mm/h</div>
                  <div class="text-[10px] text-slate-400">Open-Meteo Sensor</div>
                </div>
              </div>
              <div class="pt-1">
                <div class="text-[10px] font-bold uppercase text-slate-500 tracking-wider mb-1.5">3-Hour Hourly Forecast</div>
                <div class="grid grid-cols-3 gap-1.5 text-center text-xs font-num">
                  <div class="p-1.5 rounded-lg bg-white/40 border border-white/50">
                    <div class="text-[10px] text-slate-500">12:00</div>
                    <div class="font-bold text-slate-800">28°C</div>
                    <div class="text-[10px] text-indigo-600 font-semibold">42% Rain</div>
                  </div>
                  <div class="p-1.5 rounded-lg bg-white/40 border border-white/50">
                    <div class="text-[10px] text-slate-500">13:00</div>
                    <div class="font-bold text-slate-800">27°C</div>
                    <div class="text-[10px] text-indigo-600 font-semibold">61% Rain</div>
                  </div>
                  <div class="p-1.5 rounded-lg bg-white/40 border border-white/50">
                    <div class="text-[10px] text-slate-500">14:00</div>
                    <div class="font-bold text-slate-800">26°C</div>
                    <div class="text-[10px] text-indigo-600 font-semibold">78% Rain</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- D. SELECTED MAP OBJECT CONTEXTUAL FLOATING GLASS PANEL -->
            <div id="map-selected-object-panel" class="hidden glass-panel absolute top-14 left-3 z-[1001] max-w-sm w-full p-4 space-y-2.5">
              <div class="flex items-center justify-between border-b border-white/60 pb-2">
                <div class="flex items-center gap-2">
                  <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                  <span id="sel-obj-title" class="font-bold text-xs text-slate-900 tracking-tight">ZONE A · STADIUM BOWL</span>
                </div>
                <button onclick="closeSelectedObjectPanel()" class="text-slate-400 hover:text-slate-700 text-xs font-bold p-1">✕</button>
              </div>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div class="p-2 rounded-lg bg-white/50 border border-white/60">
                  <div class="text-[10px] text-slate-500 font-bold uppercase">Occupancy</div>
                  <div id="sel-obj-occ" class="text-sm font-bold font-num text-slate-900">18,420 / 26,000</div>
                  <div id="sel-obj-util" class="text-[10px] text-slate-500">70.8% capacity</div>
                </div>
                <div class="p-2 rounded-lg bg-white/50 border border-white/60">
                  <div class="text-[10px] text-slate-500 font-bold uppercase">Flow Vectors</div>
                  <div id="sel-obj-flow" class="text-sm font-bold font-num text-indigo-600">+120/m in • -30/m out</div>
                  <div class="text-[10px] text-slate-500">Net Flow: +90/m</div>
                </div>
              </div>
              <div class="flex items-center justify-between text-xs pt-1">
                <span class="text-slate-500 font-medium">Forecast: <strong id="sel-obj-forecast" class="text-amber-600 font-bold">WATCH</strong></span>
                <button id="sel-obj-action-btn" onclick="switchMainView('zones')" class="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-[11px] shadow-xs transition">
                  Open Zone Intelligence →
                </button>
              </div>
            </div>

            <!-- E. DIGITAL TWIN FLOATING SIMULATION TRAY (Bottom-Center) -->
            <div id="map-simulation-tray" class="glass-simulation absolute bottom-3 left-1/2 -translate-x-1/2 z-[1000] w-[94%] max-w-xl px-4 py-2.5 transition-all duration-300">
              <div class="flex items-center justify-between mb-1.5">
                <div class="flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-indigo-600 animate-pulse"></span>
                  <span class="font-bold text-xs text-slate-900 uppercase tracking-wider">Digital Twin · What-If</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">COUNTERFACTUAL</span>
                </div>
                <button onclick="toggleSimulationTray()" class="text-slate-500 hover:text-slate-800 text-[11px] font-semibold flex items-center gap-1" id="sim-tray-toggle-btn">
                  <span>Collapse</span>
                  <span>▼</span>
                </button>
              </div>
              <div id="sim-tray-content" class="space-y-2">
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
                  <div>
                    <div class="flex justify-between text-[11px] font-semibold text-slate-700 mb-0.5">
                      <span>Rainfall:</span>
                      <span id="tray-rain-val" class="font-bold font-num text-indigo-600">18 mm/h</span>
                    </div>
                    <input type="range" id="tray-rain-input" min="0" max="60" value="18" oninput="onTraySliderChange()" class="w-full">
                  </div>
                  <div>
                    <div class="flex justify-between text-[11px] font-semibold text-slate-700 mb-0.5">
                      <span>Wind:</span>
                      <span id="tray-wind-val" class="font-bold font-num text-indigo-600">24 km/h</span>
                    </div>
                    <input type="range" id="tray-wind-input" min="0" max="80" value="24" oninput="onTraySliderChange()" class="w-full">
                  </div>
                  <div>
                    <div class="flex justify-between text-[11px] font-semibold text-slate-700 mb-0.5">
                      <span>Duration:</span>
                      <span id="tray-dur-val" class="font-bold font-num text-indigo-600">60 min</span>
                    </div>
                    <input type="range" id="tray-dur-input" min="15" max="180" step="15" value="60" oninput="onTraySliderChange()" class="w-full">
                  </div>
                </div>
                <div class="flex items-center justify-between pt-1 flex-wrap gap-2">
                  <div class="flex items-center gap-1.5">
                    <button onclick="setTrayPreset('Heavy Rain', 25, 30, 60)" class="px-2 py-0.5 rounded text-[11px] font-semibold bg-white/70 hover:bg-white text-slate-700 border border-white/60">Heavy Rain</button>
                    <button onclick="setTrayPreset('Severe Gale', 10, 55, 45)" class="px-2 py-0.5 rounded text-[11px] font-semibold bg-white/70 hover:bg-white text-slate-700 border border-white/60">Gale</button>
                    <button onclick="setTrayPreset('Flash Surge', 40, 20, 90)" class="px-2 py-0.5 rounded text-[11px] font-semibold bg-white/70 hover:bg-white text-slate-700 border border-white/60">Flash Flood</button>
                  </div>
                  <div class="flex items-center gap-2">
                    <button onclick="resetTraySimulation()" class="px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white/70 border border-white/60 transition">
                      Reset
                    </button>
                    <button onclick="runTraySimulation()" class="px-3 py-1 rounded-lg text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition flex items-center gap-1.5">
                      <span>Run Counterfactual</span>
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- F. DIGITAL TWIN RESULT FLOATING GLASS PANEL -->
            <div id="map-dt-result-panel" class="hidden glass-panel absolute bottom-16 left-1/2 -translate-x-1/2 z-[1002] w-[94%] max-w-lg p-4 space-y-3">
              <!-- Dynamically populated by renderTraySimulationResult() -->
            </div>

            <!-- Map Viewport -->
            <div id="operational-map" class="w-full h-full z-0"></div>

            <!-- Map Loading Overlay -->
            <div id="map-loading-overlay" class="hidden absolute inset-0 bg-white/70 backdrop-blur-2xs flex items-center justify-center z-[1001]">
              <div class="flex items-center gap-2 text-xs font-semibold text-slate-700 bg-white px-3 py-2 rounded-lg shadow-sm border border-slate-200">
                <svg class="w-4 h-4 animate-spin text-indigo-600" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <span>Synchronizing Geospatial Layer...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: AI Recommendations & Operator Sign-off (4 Columns) -->
        <div class="lg:col-span-4 flex flex-col gap-3">
          
          <!-- Venue Rollup Card -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-600">Total Venue Attendance</span>
              <span id="venue-util-pct-text" class="text-xs font-bold font-num text-slate-800">63.8%</span>
            </div>
            <div class="flex items-baseline gap-2 mb-2.5">
              <span id="venue-crowd-count" class="text-3xl font-extrabold font-num text-slate-900 tracking-tight">21,370</span>
              <span class="text-xs text-slate-400 font-medium">/</span>
              <span id="venue-capacity-count" class="text-xs font-semibold font-num text-slate-500">33,500</span>
              <span class="text-xs text-slate-400 font-medium ml-auto">Verified Capacity</span>
            </div>
            <div class="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div id="venue-util-bar" class="h-full bg-emerald-500 rounded-full transition-all duration-500" style="width: 63.8%"></div>
            </div>
            <div class="mt-3.5 pt-3 border-t border-slate-100 grid grid-cols-2 gap-3 text-xs">
              <div>
                <span class="text-slate-500 block text-[11px] font-medium mb-1">Event Risk Status:</span>
                <span id="kpi-risk-text" class="inline-block px-2 py-0.5 rounded text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">WATCH</span>
              </div>
              <div>
                <span class="text-slate-500 block text-[11px] font-medium mb-1">Transit Seats Vacant:</span>
                <span id="kpi-transport-avail" class="inline-block text-xs font-bold text-indigo-700 font-num">700 Vacant</span>
              </div>
            </div>
          </div>

          <!-- AI Recommendation Panel -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex-1 flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-indigo-600"></span>
                  <h3 class="text-xs font-bold uppercase tracking-wider text-slate-800">AI Operations Copilot</h3>
                </div>
                <span class="text-[11px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">Human-in-Loop</span>
              </div>

              <!-- Recommendation Cards Container -->
              <div id="recommendations-container" class="space-y-2.5">
                <!-- If no recommendations, friendly calm prompt -->
                <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 text-center space-y-2">
                  <p class="font-medium">All sectors operating within baseline limits. No active intervention requested.</p>
                  <button onclick="triggerSurgeSimulation()" class="px-3 py-1.5 bg-white border border-slate-200 text-slate-800 font-bold rounded-lg shadow-2xs hover:bg-slate-50 transition">
                    Test Concourse Surge Scenario
                  </button>
                </div>
              </div>
            </div>

            <!-- Recent Action Execution Log -->
            <div class="mt-4 pt-3 border-t border-slate-100">
              <div class="flex items-center justify-between text-[11px] font-bold text-slate-600 uppercase mb-2">
                <span>Recent Actions Dispatched</span>
                <span id="last-updated-text" class="font-num text-slate-500">--:--:--</span>
              </div>
              <div id="timeline-container" class="space-y-1.5 text-xs text-slate-600 max-h-[110px] overflow-y-auto">
                <div class="flex items-center gap-2 text-[11px]">
                  <span class="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
                  <span class="font-num text-slate-500 font-semibold">09:50</span>
                  <span class="truncate font-medium text-slate-700">Nominal match egress commenced</span>
                </div>
              </div>
            </div>

          </div>

        </div>

      </div>

    </div>

    <!-- ============================================================ -->
    <!-- VIEW CONTAINER: ZONE DISTRIBUTION & DETAILED TELEMETRY       -->
    <!-- ============================================================ -->
    <div id="view-zones" class="hidden p-5 space-y-4">
      <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Stadium Sector Telemetry & Flow Distribution</h2>
            <p class="text-xs text-slate-500 font-medium">Live per-zone ingress, egress velocity, density (ppl/m²), and sensor confidence.</p>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="refreshDashboardState()" class="px-3 py-1.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100">
              Refresh Telemetry
            </button>
          </div>
        </div>

        <!-- Detailed Zone Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 text-slate-600 font-bold border-y border-slate-200">
              <tr>
                <th class="py-2.5 px-3">Zone / Sector Name</th>
                <th class="py-2.5 px-3">Current Crowd</th>
                <th class="py-2.5 px-3">Capacity</th>
                <th class="py-2.5 px-3">Occupancy</th>
                <th class="py-2.5 px-3">Flow Rate (In/Out)</th>
                <th class="py-2.5 px-3">Density (ppl/m²)</th>
                <th class="py-2.5 px-3">Status</th>
                <th class="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody id="zones-detailed-table-body" class="divide-y divide-slate-100">
              <!-- Populated dynamically -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- VIEW CONTAINER: TELEGRAM PROVIDER PULSE & OPERATIONS GATEWAY   -->
    <!-- ============================================================ -->
    <div id="view-providers" class="hidden p-5 space-y-4">
      
      <!-- Telegram & Multi-Gateway Live Operations Status Banner -->
      <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-600 flex items-center justify-center font-bold">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.121l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.196 1.006.128.832.922z"/></svg>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-sm font-bold text-slate-900">EVENTOS Operations Network (Two-Bot Architecture)</h2>
              <span id="wa-integration-badge" class="text-[11px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">● LIVE POLLING</span>
            </div>
            <p class="text-xs text-slate-500 font-medium">Coordinated network connecting Visitors, Hotels, Transport, and Staff into the EVENTOS Digital Twin.</p>
          </div>
        </div>

        <div class="flex items-center gap-3 text-xs font-semibold flex-wrap">
          <div>
            <span class="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Staff / Ops Bot:</span>
            <a id="telegram-channel-link" href="https://t.me/hckathn_bot" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 font-num text-sky-700 hover:text-sky-800 text-[11px] bg-sky-50 hover:bg-sky-100 px-2 py-0.5 rounded border border-sky-200 transition">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span id="telegram-channel-handle">@hckathn_bot</span>
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
            </a>
          </div>
          <div>
            <span class="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Visitor Bot:</span>
            <a id="visitor-channel-link" href="https://t.me/eventos_visitor_bot" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 font-num text-indigo-700 hover:text-indigo-800 text-[11px] bg-indigo-50 hover:bg-indigo-100 px-2 py-0.5 rounded border border-indigo-200 transition">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
              <span>@eventos_visitor_bot</span>
              <span class="text-[9px] px-1 bg-indigo-100 rounded text-indigo-800">SANDBOX</span>
            </a>
          </div>
          <div>
            <span class="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Network Gap:</span>
            <span id="wa-gap-status" class="font-bold text-emerald-600">BALANCED</span>
          </div>
          <div class="flex items-center gap-1.5">
            <button onclick="dispatchTelegramOperationalPoll()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white font-bold rounded-lg shadow-sm transition">
              Broadcast Fleet Poll
            </button>
            <button onclick="runSimulatedCrowdAlert()" class="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-lg shadow-sm transition flex items-center gap-1.5" title="Test Digital Twin crowd breach alert dispatch, staff diversion action, and risk stabilization">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              <span>Crowd Alert Loop</span>
            </button>
            <button onclick="runSimulatedHotelRequest()" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg shadow-sm transition flex items-center gap-1.5" title="Test Visitor hotel request match, staff bot hotel approval, and confirmation">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
              <span>Hotel Request Loop</span>
            </button>
            <button onclick="runClosedLoopDemo()" class="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white font-bold rounded-lg shadow-sm transition flex items-center gap-1.5" title="Demonstrate 10-step shock, poll, response, and gap recalculation">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/></svg>
              <span>Transport Loop</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Two-Column Layout: Fleet Roster (Left) + Telegram Chat & Dispatch (Right) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        <!-- Left: Registered Fleet Providers (5 Cols) -->
        <div class="lg:col-span-5 space-y-3">
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-800">Verified Stakeholder Network</h3>
              <span class="text-xs text-slate-500 font-semibold" id="wa-providers-count">4 Providers</span>
            </div>

            <div id="wa-providers-list" class="space-y-2.5">
              <!-- Provider 1: BEST -->
              <div class="p-3 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition">
                <div class="flex items-center justify-between">
                  <span class="font-bold text-xs text-slate-900">BEST Transit — South Zone</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">TELEGRAM CONNECTED</span>
                </div>
                <div class="mt-1 flex items-center justify-between text-xs text-slate-500 font-medium">
                  <span class="font-num font-semibold text-sky-700">@best_mumbai_bot</span>
                  <span class="font-bold text-slate-800">120 seats available</span>
                </div>
              </div>

              <!-- Provider 2: Western Railway -->
              <div class="p-3 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition">
                <div class="flex items-center justify-between">
                  <span class="font-bold text-xs text-slate-900">Western Railway Churchgate Desk</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700">STANDBY</span>
                </div>
                <div class="mt-1 flex items-center justify-between text-xs text-slate-500 font-medium">
                  <span class="font-num font-semibold text-sky-700">@wr_churchgate_ops</span>
                  <span class="font-bold text-slate-800">Special Fast EMU ready</span>
                </div>
              </div>

              <!-- Provider 3: Mumbai Police -->
              <div class="p-3 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition">
                <div class="flex items-center justify-between">
                  <span class="font-bold text-xs text-slate-900">Mumbai Traffic Police South</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">ENFORCED</span>
                </div>
                <div class="mt-1 flex items-center justify-between text-xs text-slate-500 font-medium">
                  <span class="font-num font-semibold text-sky-700">@traffic_mumbai_south</span>
                  <span class="font-bold text-slate-800">Marine Drive Diversions</span>
                </div>
              </div>

              <!-- Provider 4: Medical -->
              <div class="p-3 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition">
                <div class="flex items-center justify-between">
                  <span class="font-bold text-xs text-slate-900">108 Emergency Medical Command</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">STATIONED</span>
                </div>
                <div class="mt-1 flex items-center justify-between text-xs text-slate-500 font-medium">
                  <span class="font-num font-semibold text-sky-700">@medical_108_ops</span>
                  <span class="font-bold text-slate-800">4 Ambulances (Gate 2 & 7)</span>
                </div>
              </div>
            </div>

            <!-- Provider name legacy ID placeholder -->
            <div id="wa-provider-name" class="hidden"></div>
            <div id="wa-stat-quarantine" class="hidden">0</div>
          </div>
        </div>

        <!-- Right: Live Telegram Operational Chat & Dispatcher (7 Cols) -->
        <div class="lg:col-span-7 space-y-3">
          
          <!-- Live Telemetry Stream -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col h-[340px]">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-sky-500"></span>
                <span class="text-xs font-bold uppercase tracking-wider text-slate-800">Live Telemetry & Telegram Message Audit</span>
              </div>
              <button onclick="refreshDashboardState()" class="text-xs text-indigo-600 hover:text-indigo-800 font-bold">Refresh</button>
            </div>

            <!-- Messages Stream -->
            <div id="wa-messages-feed" class="flex-1 overflow-y-auto py-3 space-y-2.5 pr-1">
              <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                <div class="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                  <span>From: @best_mumbai_bot (BEST Transit Desk)</span>
                  <span class="font-num">Live Telegram Update</span>
                </div>
                <div class="mt-1 font-bold text-slate-800">
                  "+100 seats confirmed available at Depot 4 for Wankhede Gate 3"
                </div>
                <div class="mt-1 flex items-center gap-1.5">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">PARSED: 100 SEATS</span>
                  <span class="text-[10px] font-semibold px-2 py-0.5 rounded bg-sky-100 text-sky-700">TELEGRAM CONFIRMED ✓✓</span>
                </div>
              </div>
            </div>

            <!-- Quick Inbound Provider Response Simulators -->
            <div class="pt-3 border-t border-slate-100 space-y-1.5">
              <span class="text-[11px] font-bold text-slate-600 block">Simulate Deterministic Provider Text Messages:</span>
              <div class="flex flex-wrap gap-1.5">
                <button onclick="sendTelegramOperationalResponse('+100 seats')" class="px-2.5 py-1 text-xs font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-md border border-emerald-200 transition">
                  +100 Seats
                </button>
                <button onclick="sendTelegramOperationalResponse('+50 seats')" class="px-2.5 py-1 text-xs font-bold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-md border border-indigo-200 transition">
                  +50 Seats
                </button>
                <button onclick="sendTelegramOperationalResponse('82 rooms available')" class="px-2.5 py-1 text-xs font-bold bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-md border border-purple-200 transition">
                  82 Rooms Available
                </button>
                <button onclick="sendTelegramOperationalResponse('delay 20 minutes')" class="px-2.5 py-1 text-xs font-bold bg-amber-50 hover:bg-amber-100 text-amber-700 rounded-md border border-amber-200 transition">
                  Delay 20 Min
                </button>
                <button onclick="sendTelegramOperationalResponse('NO CAPACITY')" class="px-2.5 py-1 text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-md border border-rose-200 transition">
                  NO CAPACITY
                </button>
              </div>

              <!-- Interactive Telegram Inline Keyboard Simulation -->
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block pt-1">Simulate Telegram Inline Keyboards:</span>
              <div class="flex flex-wrap gap-1.5">
                <button onclick="sendTelegramOperationalResponse('+50 seats')" class="px-2 py-0.5 text-[11px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-800 rounded border border-slate-300 transition">
                  [+50 seats]
                </button>
                <button onclick="sendTelegramOperationalResponse('+100 seats')" class="px-2 py-0.5 text-[11px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-800 rounded border border-slate-300 transition">
                  [+100 seats]
                </button>
                <button onclick="sendTelegramOperationalResponse('+120 seats')" class="px-2 py-0.5 text-[11px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-800 rounded border border-slate-300 transition">
                  [+120 seats]
                </button>
                <button onclick="sendTelegramOperationalResponse('Accept')" class="px-2 py-0.5 text-[11px] font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded border border-emerald-300 transition">
                  [Accept]
                </button>
                <button onclick="sendTelegramOperationalResponse('Decline')" class="px-2 py-0.5 text-[11px] font-bold bg-rose-50 hover:bg-rose-100 text-rose-800 rounded border border-rose-300 transition">
                  [Decline]
                </button>
                <button onclick="sendTelegramOperationalResponse('Available')" class="px-2 py-0.5 text-[11px] font-bold bg-sky-50 hover:bg-sky-100 text-sky-800 rounded border border-sky-300 transition">
                  [Available]
                </button>
              </div>
            </div>
          </div>

          <!-- Outbound Telegram Dispatcher -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-800 block mb-2">Send Operational Dispatch to Telegram Bot / Fleet</span>
            <div class="flex gap-2">
              <input id="wa-custom-input" type="text" placeholder="e.g. URGENT: Deploy 8 buses to Gate 3 Churchgate Link immediately..." class="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500">
              <button onclick="sendCustomWhatsAppMessage()" class="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-lg transition shadow-2xs">
                Dispatch Telegram
              </button>
            </div>
          </div>

        </div>

      </div>

    </div>

    <!-- ============================================================ -->
    <!-- VIEW CONTAINER: DIGITAL TWIN & SIMULATION LAB                -->
    <!-- ============================================================ -->
    <div id="view-twin" class="hidden p-5 space-y-4">
      
      <!-- Top Operational Provenance & Scenario Header -->
      <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600 animate-pulse"></span>
            <h2 class="text-sm font-bold text-slate-900 tracking-tight">EVENTOS Scenario Engine & What-If Simulation Lab</h2>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">PHYSICS-BASED COUNTERFACTUAL</span>
          </div>
          <p class="text-xs text-slate-500 font-medium mt-0.5">Perturb real sensor streams (CCTV, PDR, GPS, Weather) into the Digital Twin without mutating production ground truth.</p>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <button onclick="runCombinedExtremeDemo()" class="px-3.5 py-1.5 bg-gradient-to-r from-indigo-600 to-rose-600 hover:from-indigo-700 hover:to-rose-700 text-white font-bold text-xs rounded-lg shadow-sm transition flex items-center gap-1.5 animate-pulse" title="Run full 3-minute pitch demo story">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            <span>⚡ Run Combined Extreme Scenario (Pitch Demo)</span>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        <!-- Controls & Sensor Simulators Column (5 Cols) -->
        <div class="lg:col-span-5 space-y-3">
          
          <!-- Scenario Selector Card -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-800">Operational Scenarios</span>
              <span id="active-scenario-tag" class="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">6 AVAILABLE</span>
            </div>

            <!-- 6 Deterministic Scenarios Grid -->
            <div class="grid grid-cols-2 gap-2">
              <button onclick="executeNamedScenario('CROWD_SURGE')" class="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-indigo-50/60 hover:border-indigo-200 text-left transition space-y-1">
                <div class="font-bold text-xs text-slate-900 flex items-center justify-between">
                  <span>1. Crowd Surge</span>
                  <span class="text-[9px] px-1 bg-amber-100 text-amber-800 rounded">CROWD</span>
                </div>
                <p class="text-[10px] text-slate-500 font-medium">Zone A inflow +150/min, threshold breach in 8m</p>
              </button>

              <button onclick="executeNamedScenario('HEAVY_RAIN')" class="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-indigo-50/60 hover:border-indigo-200 text-left transition space-y-1">
                <div class="font-bold text-xs text-slate-900 flex items-center justify-between">
                  <span>2. Heavy Rain</span>
                  <span class="text-[9px] px-1 bg-sky-100 text-sky-800 rounded">WEATHER</span>
                </div>
                <p class="text-[10px] text-slate-500 font-medium">25 mm/h rain, concourse indoor load +35%</p>
              </button>

              <button onclick="executeNamedScenario('GATE_CLOSURE')" class="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-indigo-50/60 hover:border-indigo-200 text-left transition space-y-1">
                <div class="font-bold text-xs text-slate-900 flex items-center justify-between">
                  <span>3. Gate Closure</span>
                  <span class="text-[9px] px-1 bg-rose-100 text-rose-800 rounded">INGRESS</span>
                </div>
                <p class="text-[10px] text-slate-500 font-medium">Gate A locked, 180 ppl/min diverted to Gate B</p>
              </button>

              <button onclick="executeNamedScenario('TRANSPORT_FAILURE')" class="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-indigo-50/60 hover:border-indigo-200 text-left transition space-y-1">
                <div class="font-bold text-xs text-slate-900 flex items-center justify-between">
                  <span>4. Transit Outage</span>
                  <span class="text-[9px] px-1 bg-purple-100 text-purple-800 rounded">FLEET</span>
                </div>
                <p class="text-[10px] text-slate-500 font-medium">3 buses breakdown, transit gap deficit</p>
              </button>

              <button onclick="executeNamedScenario('HOSPITALITY_SHOCK')" class="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-indigo-50/60 hover:border-indigo-200 text-left transition space-y-1">
                <div class="font-bold text-xs text-slate-900 flex items-center justify-between">
                  <span>5. Hotel Shock</span>
                  <span class="text-[9px] px-1 bg-emerald-100 text-emerald-800 rounded">HOTELS</span>
                </div>
                <p class="text-[10px] text-slate-500 font-medium">100 hotel rooms offline, Telegram auto-query</p>
              </button>

              <button onclick="executeNamedScenario('COMBINED_EXTREME_EVENT')" class="p-2.5 rounded-lg border border-indigo-300 bg-indigo-50/80 hover:bg-indigo-100 text-left transition space-y-1">
                <div class="font-bold text-xs text-indigo-950 flex items-center justify-between">
                  <span>6. Combined Event</span>
                  <span class="text-[9px] px-1 bg-rose-600 text-white rounded font-bold">PITCH DEMO</span>
                </div>
                <p class="text-[10px] text-indigo-700 font-medium">Surge + Rain + Fleet failure multi-sector crisis</p>
              </button>
            </div>
          </div>

          <!-- GPS Fleet Live Simulator Card -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-2.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span class="text-xs font-bold uppercase tracking-wider text-slate-800">GPS Fleet Trajectory Engine</span>
              </div>
              <span id="gps-fleet-status-badge" class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">● 4 BUSES EN ROUTE</span>
            </div>

            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <span class="text-slate-500 text-[10px] block font-semibold">Available Fleet Seats</span>
                <span id="gps-avail-seats" class="text-base font-bold font-num text-slate-900">230 Seats</span>
              </div>
              <div class="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <span class="text-slate-500 text-[10px] block font-semibold">Transit Gap Status</span>
                <span id="gps-gap-status" class="text-base font-bold text-emerald-600 font-num">BALANCED</span>
              </div>
            </div>

            <div class="flex items-center gap-2 pt-1">
              <button onclick="simulateFleetFailure()" class="flex-1 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-[11px] rounded-lg transition">
                ⚠️ Break Down 3 Buses
              </button>
              <button onclick="resetFleetSimulator()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] rounded-lg transition">
                Reset Fleet
              </button>
            </div>
          </div>

          <!-- PDR Replay Mobility Card -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-sky-500"></span>
                <span class="text-xs font-bold uppercase tracking-wider text-slate-800">PDR Mobility Stream Replay</span>
              </div>
              <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-sky-50 text-sky-700">● REPLAY ACTIVE</span>
            </div>
            <div class="grid grid-cols-3 gap-2 text-xs text-center">
              <div class="p-2 bg-slate-50 rounded border border-slate-200">
                <span class="text-slate-500 text-[10px] block">Devices</span>
                <span id="pdr-stat-devices" class="font-bold font-num text-slate-900">390</span>
              </div>
              <div class="p-2 bg-slate-50 rounded border border-slate-200">
                <span class="text-slate-500 text-[10px] block">Mean Speed</span>
                <span id="pdr-stat-speed" class="font-bold font-num text-slate-900">1.10 m/s</span>
              </div>
              <div class="p-2 bg-slate-50 rounded border border-slate-200">
                <span class="text-slate-500 text-[10px] block">Flow Rate</span>
                <span id="pdr-stat-flow" class="font-bold font-num text-indigo-600">+180/m</span>
              </div>
            </div>
          </div>

        </div>

        <!-- Right: Baseline vs What-If Comparison Matrix + Replay Timeline (7 Cols) -->
        <div class="lg:col-span-7 space-y-3">
          
          <!-- Baseline vs What-If Matrix Card -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
              <div>
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-800" id="matrix-scenario-title">Baseline vs. What-If Counterfactual Matrix</h3>
                <p class="text-[11px] text-slate-500 font-medium" id="matrix-scenario-desc">Comparing operational equilibrium against simulated perturbation.</p>
              </div>
              <span id="matrix-scenario-severity" class="text-xs font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">CRITICAL</span>
            </div>

            <!-- Comparison Table -->
            <div class="overflow-x-auto">
              <table class="w-full text-xs text-left">
                <thead class="bg-slate-50 text-slate-500 font-bold uppercase text-[10px]">
                  <tr>
                    <th class="py-2 px-2.5 rounded-l">Metric</th>
                    <th class="py-2 px-2.5">Baseline</th>
                    <th class="py-2 px-2.5">What-If Projection</th>
                    <th class="py-2 px-2.5">Delta</th>
                    <th class="py-2 px-2.5 rounded-r">Status</th>
                  </tr>
                </thead>
                <tbody id="matrix-comparison-tbody" class="divide-y divide-slate-100 font-medium">
                  <!-- Dynamically populated via executeNamedScenario -->
                </tbody>
              </table>
            </div>
          </div>

          <!-- Chronological Cause-and-Effect Event Timeline -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-800">Operational Replay Timeline (Cause & Effect)</h3>
              </div>
              <span class="text-[10px] font-bold text-slate-500 font-num">00:00 ──▶ 01:00</span>
            </div>

            <!-- Timeline Items Container -->
            <div id="timeline-chronology-container" class="space-y-2 max-h-56 overflow-y-auto pr-1">
              <!-- Dynamically populated via fetchTimelineEvents -->
            </div>
          </div>

        </div>

      </div>
    </div>

    <!-- ============================================================ -->
    <!-- VIEW CONTAINER: LIVE WEATHER RADAR                           -->
    <!-- ============================================================ -->
    <div id="view-weather" class="hidden p-5 space-y-4">
      <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-sm font-bold text-slate-900">Marine Drive & Stadium Coastal Microclimate</h3>
            <p class="text-xs text-slate-500 font-medium">Live meteorological observations calibrated with Doppler radar feeds.</p>
          </div>
          <button onclick="refreshWeatherOnly()" class="px-3.5 py-1.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100">
            Refresh Weather Feed
          </button>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
            <span class="text-[11px] font-bold text-slate-500 block">Temperature:</span>
            <span id="weather-temp-val" class="text-2xl font-bold font-num text-slate-900">29°C</span>
            <span id="weather-feels-like" class="text-[11px] font-medium text-slate-500 block mt-0.5">Feels 32°C</span>
          </div>
          <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
            <span class="text-[11px] font-bold text-slate-500 block">Precipitation:</span>
            <span id="weather-precip-rate" class="text-2xl font-bold font-num text-slate-900">0.0 mm/h</span>
            <span id="weather-intensity-badge" class="text-xs font-bold text-emerald-600 block mt-0.5">NONE</span>
          </div>
          <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
            <span class="text-[11px] font-bold text-slate-500 block">Relative Humidity:</span>
            <span id="weather-humidity-pct" class="text-2xl font-bold font-num text-slate-900">82%</span>
            <span class="text-[11px] font-medium text-slate-500 block mt-0.5">Coastal Marine</span>
          </div>
          <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
            <span class="text-[11px] font-bold text-slate-500 block">Wind Velocity:</span>
            <span id="weather-wind-speed" class="text-2xl font-bold font-num text-slate-900">18 km/h</span>
            <span class="text-[11px] font-medium text-slate-500 block mt-0.5">WSW Breeze</span>
          </div>
          <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
            <span class="text-[11px] font-bold text-slate-500 block">Visibility:</span>
            <span id="weather-visibility-km" class="text-2xl font-bold font-num text-slate-900">10.0 km</span>
            <span class="text-[11px] font-medium text-slate-500 block mt-0.5">Nominal</span>
          </div>
          <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
            <span class="text-[11px] font-bold text-slate-500 block">Condition:</span>
            <span id="weather-desc-text" class="text-xs font-bold text-slate-900 mt-1 block">Partly Cloudy</span>
            <span class="text-[11px] font-medium text-slate-500 block mt-0.5">Doppler Clear</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- VIEW CONTAINER: SIGNALS, CCTV & SENSOR FUSION EVIDENCE       -->
    <!-- ============================================================ -->
    <div id="view-signals" class="hidden p-5 space-y-5">
      <!-- Section Header with Operational Provenance Badges -->
      <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <h2 class="text-base font-bold text-slate-900 tracking-tight">CCTV Computer Vision & Multi-Sensor Fusion Evidence Panel</h2>
          </div>
          <p class="text-xs text-slate-500 font-medium mt-1">
            Real-time edge pedestrian detection, centroid multi-tracking, and virtual line-crossing corroborating aggregate movement vectors.
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
            <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
            SIMULATED CCTV REPLAY
          </span>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            COMPUTER VISION ACTIVE
          </span>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold bg-indigo-50 text-indigo-800 border border-indigo-200">
            4 FEEDS CONNECTED
          </span>
        </div>
      </div>

      <!-- Camera Selector Switcher Tabs -->
      <div class="flex flex-wrap items-center gap-2 p-1.5 bg-slate-100/80 rounded-xl border border-slate-200/80">
        <button id="tab-cam-CAM-01" onclick="selectCctvCamera('CAM-01')" class="px-3 py-2 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-xs transition flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>CAM-01 · Gate A Main Entrance</span>
          <span class="text-[10px] font-semibold bg-white/20 px-1.5 py-0.5 rounded">Zone A Bowl</span>
        </button>
        <button id="tab-cam-CAM-02" onclick="selectCctvCamera('CAM-02')" class="px-3 py-2 rounded-lg text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 transition flex items-center gap-1.5 border border-transparent hover:border-slate-200">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>CAM-02 · North Concourse Ramp</span>
          <span class="text-[10px] font-semibold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">Zone B North</span>
        </button>
        <button id="tab-cam-CAM-03" onclick="selectCctvCamera('CAM-03')" class="px-3 py-2 rounded-lg text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 transition flex items-center gap-1.5 border border-transparent hover:border-slate-200">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>CAM-03 · Gate 3 Queue</span>
          <span class="text-[10px] font-semibold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">Zone C Marine</span>
        </button>
        <button id="tab-cam-CAM-04" onclick="selectCctvCamera('CAM-04')" class="px-3 py-2 rounded-lg text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 transition flex items-center gap-1.5 border border-transparent hover:border-slate-200">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>CAM-04 · Gate B Pavilion Link</span>
          <span class="text-[10px] font-semibold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">Gate B Upper</span>
        </button>
      </div>

      <!-- Main Evidence Grid: Video & Telemetry (Left) + Sensor Corroboration & Macro Aggregation (Right) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <!-- LEFT: Live Video Stream & Metrics Bar (7 Cols) -->
        <div class="lg:col-span-7 space-y-4">
          <!-- Video Card -->
          <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <!-- Feed Control Bar -->
            <div class="px-4 py-3 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
              <div class="flex items-center gap-2.5">
                <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
                <span id="cctv-hud-cam-name" class="font-bold text-xs font-num text-white">CAM-01: Stadium Main Entrance</span>
                <span id="cctv-hud-zone" class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 border border-indigo-500/30">Zone A · Turnstiles</span>
              </div>
              <div class="flex items-center gap-3 text-slate-400 text-[11px] font-num">
                <span>FPS: <strong id="cctv-stat-fps" class="text-emerald-400">14.2</strong></span>
                <span>RES: <strong class="text-slate-200">1280x720</strong></span>
                <span class="hidden sm:inline">CODEC: <strong class="text-slate-200">MJPEG/RAW</strong></span>
              </div>
            </div>

            <!-- Video Player Stream -->
            <div class="relative w-full aspect-video bg-slate-950 flex items-center justify-center overflow-hidden">
              <img id="cctv-stream-player" src="/api/v1/cv/stream/CAM-01" alt="CCTV Computer Vision Stream" class="w-full h-full object-cover">
              
              <!-- Tactical HUD Overlay Top-Right -->
              <div class="absolute top-2.5 right-2.5 bg-slate-900/85 backdrop-blur-2xs border border-white/10 px-2.5 py-1 rounded text-[10px] font-num text-emerald-400 font-bold flex items-center gap-1.5 shadow-sm">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>VIRTUAL COUNTING LINE: Y=180px</span>
              </div>
            </div>

            <!-- Tactical Legend / Explanation Bar -->
            <div class="px-4 py-2 bg-slate-900/95 border-t border-slate-800 text-slate-300 text-[11px] font-medium flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-3 flex-wrap">
                <span class="flex items-center gap-1">
                  <span class="w-2.5 h-2.5 rounded-xs border border-emerald-400 bg-emerald-500/20"></span>
                  <span class="text-slate-300">Tracked Pedestrian</span>
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-yellow-400"></span>
                  <span class="text-slate-300">Centroid</span>
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-3 h-0.5 bg-cyan-400"></span>
                  <span class="text-slate-300">Motion Trail</span>
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-3 h-0.5 bg-emerald-400"></span>
                  <span class="text-slate-300">Inflow Line (IN)</span>
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-3 h-0.5 bg-rose-400"></span>
                  <span class="text-slate-300">Outflow Line (OUT)</span>
                </span>
              </div>
              <span class="text-[10px] text-slate-400">Multi-Object Centroid Tracker (v5.0)</span>
            </div>
          </div>

          <!-- Real-Time Metrics Strip (5 Metric Cards) -->
          <div class="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
            <div class="bg-white rounded-xl border border-slate-200 p-3 shadow-xs">
              <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Currently Visible</div>
              <div id="cctv-stat-visible" class="text-xl font-bold font-num text-slate-900">37</div>
              <div class="text-[10px] text-slate-400 font-medium mt-0.5">Bounding Boxes</div>
            </div>
            <div class="bg-white rounded-xl border border-slate-200 p-3 shadow-xs">
              <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Line Inflow (IN)</div>
              <div id="cctv-stat-in" class="text-xl font-bold font-num text-emerald-600">+18</div>
              <div class="text-[10px] text-slate-400 font-medium mt-0.5">Crossed Down</div>
            </div>
            <div class="bg-white rounded-xl border border-slate-200 p-3 shadow-xs">
              <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Line Outflow (OUT)</div>
              <div id="cctv-stat-out" class="text-xl font-bold font-num text-rose-600">-12</div>
              <div class="text-[10px] text-slate-400 font-medium mt-0.5">Crossed Up</div>
            </div>
            <div class="bg-white rounded-xl border border-slate-200 p-3 shadow-xs">
              <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Net Flow Rate</div>
              <div id="cctv-stat-net" class="text-xl font-bold font-num text-indigo-600">+6/min</div>
              <div class="text-[10px] text-slate-400 font-medium mt-0.5">IN minus OUT</div>
            </div>
            <div class="bg-white rounded-xl border border-slate-200 p-3 shadow-xs col-span-2 sm:col-span-1">
              <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Model Confidence</div>
              <div id="cctv-stat-conf" class="text-xl font-bold font-num text-slate-800">91.4%</div>
              <div class="text-[10px] text-slate-400 font-medium mt-0.5">HOG-SVM Calibrated</div>
            </div>
          </div>
        </div>

        <!-- RIGHT: Cross-Sensor Validation & Macro Aggregation (5 Cols) -->
        <div class="lg:col-span-5 space-y-4">
          <!-- Card 1: Multi-Sensor Cross-Validation (CCTV ⨉ PDR) -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-indigo-600"></span>
                <h3 class="text-xs font-bold text-slate-900 uppercase tracking-wider">Multi-Sensor Cross-Validation</h3>
              </div>
              <span id="cctv-pdr-agree" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                HIGH (94.8% AGREEMENT)
              </span>
            </div>
            <p class="text-[11px] text-slate-500 font-medium leading-relaxed">
              Optical line-crossings corroborate Pedestrian Dead Reckoning (PDR) aggregate phone movement vectors, eliminating single-sensor false alarms.
            </p>

            <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2.5">
              <div class="flex items-center justify-between text-xs">
                <span class="text-slate-600 font-medium">CCTV Optical Flow Rate:</span>
                <span id="cctv-pdr-optical" class="font-bold font-num text-slate-900">+6.0 / min</span>
              </div>
              <div class="flex items-center justify-between text-xs">
                <span class="text-slate-600 font-medium">PDR Aggregate Drift Vector:</span>
                <span id="cctv-pdr-vector" class="font-bold font-num text-slate-900">+5.4 / min (SIMULATED)</span>
              </div>
              <div class="h-px bg-slate-200"></div>
              <div class="flex items-center justify-between text-xs pt-0.5">
                <span class="font-bold text-indigo-700">Fused Flow Rate:</span>
                <span id="cctv-pdr-fused" class="font-bold font-num text-indigo-700 text-sm">+5.7 / min</span>
              </div>
            </div>

            <div class="text-[11px] text-slate-500 bg-indigo-50/60 border border-indigo-100 rounded-lg p-2.5 flex items-start gap-2">
              <svg class="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <span><strong>Cross-Validation Principle:</strong> CCTV observes physical turnstile gates directly. PDR models user movement without PII. When both agree within 8%, system confidence reaches 87%+.</span>
            </div>
          </div>

          <!-- Card 2: Macro Aggregation & Stadium Scaling -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-slate-800"></span>
                <h3 class="text-xs font-bold text-slate-900 uppercase tracking-wider">Macro Aggregation & Stadium Scaling</h3>
              </div>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600">SPATIAL SYNTHESIS</span>
            </div>

            <div class="space-y-2 text-xs">
              <div class="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <span class="text-slate-600 font-medium">Local Camera Field of View:</span>
                <span id="cctv-macro-local" class="font-bold font-num text-slate-900">37 in FOV</span>
              </div>
              <div class="flex items-center justify-between p-2.5 bg-indigo-50/60 rounded-lg border border-indigo-100">
                <span class="text-indigo-900 font-medium">Zone A (Stadium Bowl) Total:</span>
                <span id="cctv-macro-zone" class="font-bold font-num text-indigo-700">18,420 / 26,000 (70.8%)</span>
              </div>
              <div class="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <span class="text-slate-600 font-medium">Venue Total Crowd Occupancy:</span>
                <span id="cctv-macro-venue" class="font-bold font-num text-slate-900">21,370 / 33,500 (63.8%)</span>
              </div>
            </div>

            <p class="text-[11px] text-slate-500 font-medium leading-relaxed">
              <strong>Scale Boundary:</strong> A single camera does not claim to see the entire stadium. Local line-crossing deltas feed into sector crowd states, aggregated across all venue gates for total venue occupancy.
            </p>
          </div>

          <!-- Card 3: Governance & Data Privacy -->
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-2">
            <h3 class="text-xs font-bold text-slate-900 uppercase tracking-wider">AI Ethics & DPDP Compliance</h3>
            <ul class="text-[11px] text-slate-600 space-y-1.5 list-disc list-inside">
              <li><strong>Zero Facial Recognition:</strong> Only anonymous centroid bounding boxes are processed.</li>
              <li><strong>Edge Inference:</strong> Real-time OpenCV video inference runs locally without external cloud telemetry upload.</li>
              <li><strong>Traceable Provenance:</strong> Benchmark replay clearly marked to distinguish physical hardware from simulated data streams.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- VIEW CONTAINER: ALERTS & AUDIT TRAIL                         -->
    <!-- ============================================================ -->
    <div id="view-alerts" class="hidden p-5 space-y-4">
      <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 class="text-sm font-bold text-slate-900 mb-1">Operational Action & Execution Audit Trail</h3>
        <p class="text-xs text-slate-500 font-medium mb-4">Complete audit record of automated risk assessments, operator dispatches, and provider confirmations.</p>

        <div id="audit-trail-full-list" class="space-y-2 text-xs">
          <!-- Dynamically populated -->
          <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-indigo-600"></span>
              <span class="font-bold text-slate-800">Operational Capacity Poll Dispatched</span>
              <span class="text-slate-500 font-medium">— Broadcast to all registered transit providers</span>
            </div>
            <span class="font-num text-xs font-semibold text-slate-500">Today, 09:51:00</span>
          </div>
        </div>
      </div>
    </div>

  </main>

  <!-- ============================================================ -->
  <!-- MODAL: MANUAL INGESTION                                      -->
  <!-- ============================================================ -->
  <div id="ingestion-modal" class="hidden fixed inset-0 bg-slate-900/40 backdrop-blur-2xs z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-5 shadow-xl space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-slate-900">Manual Telemetry Ingest</h3>
        <button onclick="closeIngestionModal()" class="text-slate-400 hover:text-slate-700">✕</button>
      </div>
      <p class="text-xs text-slate-500 font-medium">Inject calibrated crowd counts or environmental signals directly into SQLite.</p>
      <div class="space-y-3">
        <div>
          <label class="text-xs font-bold text-slate-700 block mb-1">Zone Selection:</label>
          <select id="ingest-zone-select" class="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-semibold"></select>
        </div>
        <div>
          <label class="text-xs font-bold text-slate-700 block mb-1">Current Crowd Count:</label>
          <input id="ingest-crowd-count" type="number" class="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-num" placeholder="e.g. 18500">
        </div>
      </div>
      <div class="flex justify-end gap-2 pt-2">
        <button onclick="closeIngestionModal()" class="px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-lg">Cancel</button>
        <button onclick="submitManualIngestion()" class="px-3 py-1.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm">Ingest Telemetry</button>
      </div>
    </div>
  </div>

  <!-- ============================================================ -->
  <!-- MODAL: SIMULATION ORCHESTRATION BANNER                       -->
  <!-- ============================================================ -->
  <div id="simulation-modal" class="hidden fixed inset-0 bg-slate-900/40 backdrop-blur-2xs z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 shadow-xl space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-slate-900">Closed-Loop Incident Simulation</h3>
        <button onclick="closeSimulationModal()" class="text-slate-400 hover:text-slate-700">✕</button>
      </div>
      <div id="sim-status-label" class="text-xs text-slate-600 font-semibold">Running scenario steps...</div>
      
      <!-- Stepper container -->
      <div id="sim-steps-container" class="space-y-2"></div>

      <!-- Result Card -->
      <div id="sim-result-card" class="hidden p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
        <span class="font-bold text-slate-900">Incident Resolution Verified</span>
        <p class="text-slate-600 font-medium">Simulated capacity gap closed via provider dispatch approval.</p>
      </div>

      <!-- Operator Sign-off Banner -->
      <div id="sim-approval-banner" class="hidden p-3 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center justify-between">
        <span class="text-xs font-bold text-indigo-900">Human Approval Required to Dispatch Fleets</span>
        <div class="flex gap-2">
          <button onclick="onSimOperatorReject()" class="px-2.5 py-1 text-xs text-slate-600 hover:text-slate-900 font-bold">Dismiss</button>
          <button onclick="onSimOperatorApprove()" class="px-3 py-1 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-2xs">Authorize</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ============================================================ -->
  <!-- FLOATING PROVIDER PULSE POPOVER (Liquid Glass Layer)         -->
  <!-- ============================================================ -->
  <div id="provider-pulse-popover" class="hidden glass-popover fixed top-16 right-16 z-50 max-w-sm w-full p-4 space-y-3 select-none">
    <div class="flex items-center justify-between border-b border-white/60 pb-2">
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="font-bold text-xs text-slate-900 tracking-tight uppercase">EVENTOS PULSE · LOGISTICS</span>
      </div>
      <button onclick="toggleProviderPulsePopover(false)" class="text-slate-400 hover:text-slate-700 text-xs font-bold p-1">✕</button>
    </div>
    <div class="text-[11px] text-slate-600 font-medium">
      Verified transit and hospitality reserves synchronized via Meta Cloud WhatsApp API.
    </div>
    <div class="space-y-2 text-xs">
      <div class="p-2.5 rounded-xl bg-white/50 border border-white/60 flex items-center justify-between">
        <div>
          <div class="font-bold text-slate-800">BEST Feeder Bus Depot 4</div>
          <div class="text-[10px] text-slate-500">Route 108 • Gate 3 Standby</div>
        </div>
        <span class="font-bold font-num text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">+120 seats</span>
      </div>
      <div class="p-2.5 rounded-xl bg-white/50 border border-white/60 flex items-center justify-between">
        <div>
          <div class="font-bold text-slate-800">Hotel Vivanta Cuffe Parade</div>
          <div class="text-[10px] text-slate-500">Hospitality Partner Holding</div>
        </div>
        <span class="font-bold font-num text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">+82 rooms</span>
      </div>
    </div>
    <div class="flex items-center justify-between pt-1 border-t border-white/60">
      <span class="text-[10px] text-emerald-700 font-bold flex items-center gap-1">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
        Provider responses verified
      </span>
      <button onclick="switchMainView('providers'); toggleProviderPulsePopover(false);" class="text-[11px] font-bold text-indigo-600 hover:text-indigo-800">
        Open Fleet View →
      </button>
    </div>
  </div>

  <!-- ============================================================ -->
  <!-- COMMAND PALETTE (CMD+K) (Liquid Glass Raycast Style)        -->
  <!-- ============================================================ -->
  <div id="command-palette" class="hidden fixed inset-0 bg-slate-900/40 backdrop-blur-2xs z-50 flex items-start justify-center pt-20 p-4">
    <div id="command-palette-card" class="glass-command max-w-lg w-full overflow-hidden shadow-2xl p-1">
      <div class="p-3 border-b border-white/60 flex items-center gap-2.5">
        <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
        <input id="command-input" type="text" oninput="handleCommandSearch()" placeholder="Search EVENTOS (commands, sectors, CCTV, digital twin)..." class="w-full text-xs text-slate-900 font-semibold bg-transparent focus:outline-none placeholder-slate-400">
        <kbd onclick="closeCommandPalette()" class="text-[10px] font-bold text-slate-500 bg-white/60 px-1.5 py-0.5 rounded border border-white/70 cursor-pointer">ESC</kbd>
      </div>
      <div id="command-results" class="p-2 space-y-1 max-h-72 overflow-y-auto text-xs font-semibold">
        <button onclick="switchMainView('overview'); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>↗</span><span>Jump to Operations Cockpit</span></span>
          <span class="text-[10px] text-slate-400 font-normal">Overview</span>
        </button>
        <button onclick="switchMainView('zones'); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>↗</span><span>Jump to Zone Distribution & Capacity</span></span>
          <span class="text-[10px] text-slate-400 font-normal">Zones</span>
        </button>
        <button onclick="switchMainView('providers'); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>↗</span><span>Jump to WhatsApp Fleet Dispatch</span></span>
          <span class="text-[10px] text-slate-400 font-normal">WhatsApp</span>
        </button>
        <button onclick="switchMainView('twin'); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>↗</span><span>Run Full Weather Digital Twin</span></span>
          <span class="text-[10px] text-slate-400 font-normal">Digital Twin</span>
        </button>
        <button onclick="switchMainView('signals'); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>◉</span><span>Show CCTV Computer Vision & Evidence</span></span>
          <span class="text-[10px] text-slate-400 font-normal">CCTV CV</span>
        </button>
        <button onclick="switchMainView('weather'); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>☁</span><span>Open Weather Radar Intelligence</span></span>
          <span class="text-[10px] text-slate-400 font-normal">Weather</span>
        </button>
        <button onclick="toggleWeatherGlassPanel(true); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>🌧</span><span>Expand Map Weather Intelligence Overlay</span></span>
          <span class="text-[10px] text-indigo-600 font-normal">Glass Overlay</span>
        </button>
        <button onclick="toggleProviderPulsePopover(true); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>📡</span><span>Open Provider Pulse Status</span></span>
          <span class="text-[10px] text-emerald-600 font-normal">Pulse</span>
        </button>
        <button onclick="launchFullSimulation(); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>⚡</span><span>Simulate Egress Surge (Full Stepper)</span></span>
          <span class="text-[10px] text-indigo-600 font-normal">Sim</span>
        </button>
        <button onclick="resetMapView(); closeCommandPalette();" class="w-full text-left px-3 py-2 rounded-lg hover:bg-white/70 flex items-center justify-between text-slate-800 transition">
          <span class="flex items-center gap-2"><span>🗺</span><span>Reset Map View to Stadium Center</span></span>
          <span class="text-[10px] text-slate-400 font-normal">Map</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Toast Notification Container -->
  <div id="toast-container" class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"></div>

  <!-- ============================================================ -->
  <!-- JAVASCRIPT: MASTER CLIENT APPLICATION                        -->
  <!-- ============================================================ -->
  <script>
    // Configuration & State
    const API_BASE = "/api/v1";
    let activeEventId = null;
    let pollInterval = 8000;
    let pollTimer = null;
    let currentMasterData = null;
    let activeDigitalTwinData = null;
    let leafletMap = null;
    let mapLayers = {
      base: null,
      zones: null,
      transit: null,
      cameras: null,
      weather: null
    };
    let currentCameraId = 'CAM-01';
    let cctvTelemetryTimer = null;

    // ============================================================
    // LIQUID GLASS MATERIAL SYSTEM MANAGER (Apple Maps + Linear)
    // ============================================================
    class LiquidGlassManager {
      constructor() {
        this.surfaces = [];
        this.reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.isSupported = this.checkSupport();
      }

      checkSupport() {
        return (window.CSS && (CSS.supports('backdrop-filter', 'blur(10px)') || CSS.supports('-webkit-backdrop-filter', 'blur(10px)')));
      }

      register(el) {
        if (!el || this.surfaces.includes(el)) return;
        this.surfaces.push(el);

        if (!this.isSupported) {
          el.classList.add('glass-fallback-active');
          return;
        }

        if (!this.reducedMotion) {
          el.addEventListener('pointermove', (e) => this.handlePointerMove(e, el));
          el.addEventListener('pointerleave', () => this.handlePointerLeave(el));
        }
      }

      handlePointerMove(e, el) {
        const rect = el.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        el.style.setProperty('--glass-x', `${x.toFixed(1)}%`);
        el.style.setProperty('--glass-y', `${y.toFixed(1)}%`);
        el.style.setProperty('--glass-specular-opacity', '1');
      }

      handlePointerLeave(el) {
        el.style.removeProperty('--glass-x');
        el.style.removeProperty('--glass-y');
        el.style.removeProperty('--glass-specular-opacity');
      }

      registerAll() {
        const selectors = [
          '#map-floating-controls',
          '#map-weather-pill',
          '#map-floating-zoom',
          '#map-weather-expanded-panel',
          '#map-selected-object-panel',
          '#map-simulation-tray',
          '#map-dt-result-panel',
          '#provider-pulse-popover',
          '#command-palette > div',
          '.glass-pill',
          '.glass-float',
          '.glass-panel'
        ];
        selectors.forEach(sel => {
          document.querySelectorAll(sel).forEach(el => this.register(el));
        });
      }
    }
    const liquidGlass = new LiquidGlassManager();

    // Initialize Application
    document.addEventListener("DOMContentLoaded", () => {
      initLeafletMap();
      fetchEvents();
      updateWallClock();
      setInterval(updateWallClock, 1000);
      pollTimer = setInterval(refreshDashboardState, pollInterval);
      liquidGlass.registerAll();

      // Keyboard Shortcut ⌘K
      document.addEventListener("keydown", (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === "k") {
          e.preventDefault();
          openCommandPalette();
        } else if (e.key === "Escape") {
          closeCommandPalette();
          closeSimulationModal();
          closeIngestionModal();
          closeSelectedObjectPanel();
          toggleWeatherGlassPanel(false);
          closeTrayResultPanel();
          toggleProviderPulsePopover(false);
        }
      });
    });

    // Wall Clock (Clean Tabular Numbers)
    function updateWallClock() {
      const clockEl = document.getElementById("wall-clock-text");
      if (clockEl) {
        const now = new Date();
        clockEl.innerText = now.toLocaleTimeString('en-US', { hour12: false });
      }
    }

    // View Switching Controller
    function switchMainView(viewName) {
      const views = ['overview', 'zones', 'twin', 'weather', 'providers', 'signals', 'alerts'];
      views.forEach(v => {
        const el = document.getElementById(`view-${v}`);
        const navBtn = document.getElementById(`nav-${v}`);
        if (el) el.classList.add('hidden');
        if (navBtn) {
          navBtn.className = "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition text-left";
        }
      });

      const target = document.getElementById(`view-${viewName}`);
      const activeBtn = document.getElementById(`nav-${viewName}`);
      if (target) target.classList.remove('hidden');
      if (activeBtn) {
        activeBtn.className = "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-white bg-indigo-600/20 border-l-2 border-indigo-500 transition text-left";
      }

      if (viewName === 'overview' && leafletMap) {
        setTimeout(() => leafletMap.invalidateSize(), 200);
      }

      if (viewName === 'signals') {
        fetchCctvTelemetry();
        if (!cctvTelemetryTimer) {
          cctvTelemetryTimer = setInterval(fetchCctvTelemetry, 1500);
        }
      } else {
        if (cctvTelemetryTimer) {
          clearInterval(cctvTelemetryTimer);
          cctvTelemetryTimer = null;
        }
      }

      if (viewName === 'providers') {
        if (typeof renderWhatsAppPanel === 'function' && currentMasterData) {
          renderWhatsAppPanel(
            currentMasterData.whatsapp_integration,
            currentMasterData.signals?.whatsapp,
            currentMasterData.providers || []
          );
        }
      }
    }

    // Command Palette
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

    // Toast Manager
    function showToast(message, type = 'info') {
      const container = document.getElementById("toast-container");
      if (!container) return;
      const toast = document.createElement("div");
      toast.className = `p-3 rounded-xl border shadow-lg text-xs font-semibold flex items-center gap-2.5 transition-all transform duration-300 translate-y-2 pointer-events-auto ${
        type === 'success' ? 'bg-emerald-950 text-emerald-100 border-emerald-700' :
        type === 'danger' ? 'bg-rose-950 text-rose-100 border-rose-700' :
        type === 'warning' ? 'bg-amber-950 text-amber-100 border-amber-700' :
        'bg-slate-900 text-slate-100 border-slate-700'
      }`;
      toast.innerHTML = `<span>${message}</span>`;
      container.appendChild(toast);
      setTimeout(() => toast.classList.remove("translate-y-2"), 50);
      setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => toast.remove(), 300);
      }, 4000);
    }

    // Fetch Events & Default to Wankhede Stadium (Stable Comparator)
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

        // Deterministic Sort: Wankhede first, then events with name, then others
        events.sort((a, b) => {
          const aScore = (a.name || '').toLowerCase().includes('wankhede') ? 3 : ((a.name || '').toLowerCase().includes('mumbai') ? 2 : 1);
          const bScore = (b.name || '').toLowerCase().includes('wankhede') ? 3 : ((b.name || '').toLowerCase().includes('mumbai') ? 2 : 1);
          return bScore - aScore;
        });

        events.forEach(ev => {
          const opt = document.createElement("option");
          opt.value = ev.event_id;
          opt.innerText = `${ev.name} — Mumbai`;
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
          renderZoneDistribution(master.zones);
          renderWeatherCard(master.weather, master.signals?.weather);
          renderWhatsAppPanel(master.whatsapp_integration, master.signals?.whatsapp, master.providers);
          renderRecommendations(master.recommendations);
          renderTimeline(master.timeline);
          renderLeafletMap(master.venue, master.zones, master.providers, master.weather, activeDigitalTwinData);
          if (!activeDigitalTwinData && master.digital_twin) {
            renderDigitalTwinPanel(master.digital_twin, master.zones, master.providers, master.weather);
          }
          await fetchGpsFleet();
          await fetchPdrStream();
          await fetchTimelineEvents();
          const matrixTbody = document.getElementById("matrix-comparison-tbody");
          if (matrixTbody && matrixTbody.children.length === 0) {
            executeNamedScenario('COMBINED_EXTREME_EVENT');
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

    // Render Event & Venue Metadata (Zero wrapping collision)
    function renderVenueCard(venue, event) {
      if (!event) return;
      const vName = document.getElementById("venue-name-text");
      const vAddr = document.getElementById("venue-full-address");
      if (vName) vName.innerText = event.name || "Wankhede Stadium";
      if (vAddr) vAddr.innerText = `${event.city || 'Mumbai'} • ${venue?.source_name || 'Verified MCA Record'}`;
    }

    // Render Master KPIs (Clean Tabular Numbers)
    function renderMasterKPIs(kpis, recs) {
      if (!kpis) return;
      const totalCrowd = kpis.total_crowd?.value || 21370;
      const totalCap = kpis.total_capacity?.value || 33500;
      const utilPct = kpis.utilization_pct?.value || ((totalCrowd / totalCap) * 100);

      const crowdEl = document.getElementById("venue-crowd-count");
      const capEl = document.getElementById("venue-capacity-count");
      const utilEl = document.getElementById("venue-util-pct-text");
      const utilBar = document.getElementById("venue-util-bar");
      const riskEl = document.getElementById("kpi-risk-text");
      const transEl = document.getElementById("kpi-transport-avail");

      if (crowdEl) crowdEl.innerText = Number(totalCrowd).toLocaleString();
      if (capEl) capEl.innerText = Number(totalCap).toLocaleString();
      if (utilEl) utilEl.innerText = `${utilPct.toFixed(1)}%`;
      if (utilBar) {
        utilBar.style.width = `${Math.min(utilPct, 100)}%`;
        utilBar.className = `h-full rounded-full transition-all duration-500 ${
          utilPct > 90 ? 'bg-rose-500' : utilPct > 75 ? 'bg-amber-500' : 'bg-emerald-500'
        }`;
      }
      if (riskEl) {
        const risk = kpis.overall_risk?.value || 'NORMAL';
        riskEl.innerText = risk;
        riskEl.className = `inline-block px-2.5 py-0.5 rounded text-xs font-bold ${
          risk === 'CRITICAL' || risk === 'OVERLOAD' ? 'text-rose-700 bg-rose-50 border border-rose-200' :
          risk === 'WATCH' || risk === 'WARNING' ? 'text-amber-700 bg-amber-50 border border-amber-200' :
          'text-emerald-700 bg-emerald-50 border border-emerald-200'
        }`;
      }
      if (transEl) transEl.innerText = `${kpis.transport_available?.value || 700} Vacant`;

      // Legacy KPI IDs
      const kpiTotCrowd = document.getElementById("kpi-total-crowd");
      const kpiTotCap = document.getElementById("kpi-total-capacity");
      const kpiUtilVal = document.getElementById("kpi-util-value");
      const kpiUtilBar = document.getElementById("kpi-util-bar");
      if (kpiTotCrowd) kpiTotCrowd.innerText = Number(totalCrowd).toLocaleString();
      if (kpiTotCap) kpiTotCap.innerText = Number(totalCap).toLocaleString();
      if (kpiUtilVal) kpiUtilVal.innerText = `${utilPct.toFixed(1)}%`;
      if (kpiUtilBar) kpiUtilBar.style.width = `${Math.min(utilPct, 100)}%`;
    }

    // ============================================================
    // RENDER ZONE DISTRIBUTION (CRYSTAL-CLEAR TYPOGRAPHY)
    // ============================================================
    function renderZoneDistribution(zones) {
      const container = document.getElementById("zone-distribution-cards");
      const tableBody = document.getElementById("zones-detailed-table-body");
      const zoneBadge = document.getElementById("nav-zone-count-badge");
      
      if (!zones || zones.length === 0) {
        zones = [
          { zone_id: 'ZONE-A', name: 'Zone A - Stadium Bowl', current_crowd: 18420, capacity: 26000, risk_level: 'watch', density: 0.71, inflow_per_minute: 40, outflow_per_minute: 620 },
          { zone_id: 'ZONE-B', name: 'Zone B - North Gate & Churchgate Access', current_crowd: 2100, capacity: 4500, risk_level: 'normal', density: 0.47, inflow_per_minute: 540, outflow_per_minute: 310 },
          { zone_id: 'ZONE-C', name: 'Zone C - Marine Drive External Approach', current_crowd: 850, capacity: 3000, risk_level: 'normal', density: 0.28, inflow_per_minute: 410, outflow_per_minute: 180 }
        ];
      }

      if (zoneBadge) zoneBadge.innerText = zones.length;

      // Render Overview Zone Cards with solid high-contrast numbers
      if (container) {
        container.innerHTML = "";
        zones.forEach(z => {
          const crowd = z.current_crowd || 0;
          const cap = z.capacity || 1;
          const pct = Math.min(100, (crowd / cap) * 100);
          const risk = (z.risk_level || 'normal').toUpperCase();
          const riskBadgeStyle = risk === 'CRITICAL' ? 'text-rose-700 bg-rose-50 border border-rose-200' :
                                 risk === 'WATCH' || risk === 'WARNING' ? 'text-amber-800 bg-amber-50 border border-amber-200' :
                                 'text-emerald-700 bg-emerald-50 border border-emerald-200';
          const barColor = pct > 90 ? 'bg-rose-500' : pct > 75 ? 'bg-amber-500' : 'bg-emerald-500';

          const card = document.createElement("div");
          card.className = "bg-white rounded-xl border border-slate-200 p-4 shadow-xs hover:border-slate-300 transition flex flex-col justify-between";
          card.innerHTML = `
            <div>
              <div class="flex items-start justify-between gap-2 mb-2.5">
                <div>
                  <h3 class="font-bold text-[13px] text-slate-900 tracking-tight" title="${z.name}">${z.name}</h3>
                  <div class="flex items-center gap-2 mt-1">
                    <span class="text-[11px] font-bold px-2 py-0.5 rounded-md ${riskBadgeStyle}">${risk}</span>
                    <span class="text-xs font-semibold text-slate-500 font-num">${(z.density || (crowd/cap*1.2)).toFixed(2)} ppl/m²</span>
                  </div>
                </div>
                <button onclick="focusZoneOnMap('${z.zone_id}')" class="text-slate-400 hover:text-indigo-600 p-1.5 rounded-lg hover:bg-slate-100 transition" title="Focus Sector on Map">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                </button>
              </div>

              <div class="flex items-baseline justify-between mt-3 mb-1.5">
                <div class="flex items-baseline gap-1.5">
                  <span class="text-xl font-bold font-num text-slate-900 tracking-tight">${crowd.toLocaleString()}</span>
                  <span class="text-xs font-medium text-slate-400">/</span>
                  <span class="text-xs font-semibold font-num text-slate-500">${cap.toLocaleString()}</span>
                </div>
                <span class="text-xs font-bold font-num text-slate-700">${pct.toFixed(1)}%</span>
              </div>
              <div class="h-2 w-full bg-slate-100 rounded-full overflow-hidden mb-3">
                <div class="${barColor} h-full rounded-full transition-all duration-500" style="width: ${pct}%"></div>
              </div>
            </div>

            <div class="pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs font-semibold">
              <span class="text-emerald-700 flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
                +${z.inflow_per_minute || 120}/m
              </span>
              <span class="text-indigo-700 flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 10l7-7m0 0l7 7m-7-7v18"/></svg>
                -${z.outflow_per_minute || 340}/m
              </span>
              <span class="text-slate-500 text-[11px] font-semibold bg-slate-100 px-2 py-0.5 rounded-md">CCTV 88%</span>
            </div>
          `;
          container.appendChild(card);
        });
      }

      // Render Detailed Zone Table (in Zones Tab)
      if (tableBody) {
        tableBody.innerHTML = "";
        zones.forEach(z => {
          const crowd = z.current_crowd || 0;
          const cap = z.capacity || 1;
          const pct = Math.min(100, (crowd / cap) * 100);
          const tr = document.createElement("tr");
          tr.className = "hover:bg-slate-50/50 transition font-medium";
          tr.innerHTML = `
            <td class="py-2.5 px-3 font-bold text-slate-900">${z.name}</td>
            <td class="py-2.5 px-3 font-num font-bold text-slate-900">${crowd.toLocaleString()}</td>
            <td class="py-2.5 px-3 font-num text-slate-500">${cap.toLocaleString()}</td>
            <td class="py-2.5 px-3 font-num font-bold text-slate-900">${pct.toFixed(1)}%</td>
            <td class="py-2.5 px-3 font-num text-xs font-semibold text-slate-700">+${z.inflow_per_minute || 120} / -${z.outflow_per_minute || 340}</td>
            <td class="py-2.5 px-3 font-num font-semibold">${(z.density || 0.5).toFixed(2)}</td>
            <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[11px] font-bold ${(z.risk_level||'normal')==='normal'?'bg-emerald-50 text-emerald-700':'bg-amber-50 text-amber-700'}">${(z.risk_level||'normal').toUpperCase()}</span></td>
            <td class="py-2.5 px-3 text-right">
              <button onclick="focusZoneOnMap('${z.zone_id}')" class="px-2.5 py-1 bg-white border border-slate-200 text-slate-800 font-bold rounded-md hover:bg-slate-50 text-xs">Inspect</button>
            </td>
          `;
          tableBody.appendChild(tr);
        });
      }
    }

    // Focus Zone on Leaflet Map
    function focusZoneOnMap(zoneId) {
      if (!leafletMap) return;
      switchMainView('overview');
      if (zoneId.includes('ZONE-A') || zoneId.includes('56894058')) {
        leafletMap.flyTo([18.9389, 72.8258], 17);
      } else if (zoneId.includes('ZONE-B') || zoneId.includes('28E21710')) {
        leafletMap.flyTo([18.9398, 72.8265], 18);
      } else {
        leafletMap.flyTo([18.9378, 72.8245], 17);
      }
      showToast(`Focused map on ${zoneId}`, 'info');
    }

    // Render Weather Card (High-Contrast Solid Figures)
    function renderWeatherCard(weather, sigWeather) {
      const w = weather || sigWeather;
      if (!w) return;

      const tempEl = document.getElementById("weather-temp-val");
      const feelsEl = document.getElementById("weather-feels-like");
      const precipEl = document.getElementById("weather-precip-rate");
      const intBadge = document.getElementById("weather-intensity-badge");
      const humEl = document.getElementById("weather-humidity-pct");
      const windEl = document.getElementById("weather-wind-speed");
      const visEl = document.getElementById("weather-visibility-km");
      const descEl = document.getElementById("weather-desc-text");
      const mapBadge = document.getElementById("map-weather-overlay-badge");

      if (tempEl) tempEl.innerText = `${Math.round(w.temperature_c || 29)}°C`;
      if (feelsEl) feelsEl.innerText = `Feels ${Math.round(w.feels_like_c || 32)}°C`;
      if (precipEl) precipEl.innerText = `${(w.precipitation_mm_h || 0).toFixed(1)} mm/h`;
      if (intBadge) {
        const intensity = (w.rain_intensity || 'none').toUpperCase();
        intBadge.innerText = intensity;
        intBadge.className = `text-xs font-bold block mt-0.5 ${
          intensity === 'HEAVY' || intensity === 'TORRENTIAL' ? 'text-rose-600' :
          intensity === 'MODERATE' ? 'text-amber-600' : 'text-emerald-600'
        }`;
      }
      if (humEl) humEl.innerText = `${Math.round(w.humidity_pct || 82)}%`;
      if (windEl) windEl.innerText = `${Math.round(w.wind_speed_kmh || 18)} km/h`;
      if (visEl) visEl.innerText = `${((w.visibility_m || 10000)/1000).toFixed(1)} km`;
      if (descEl) descEl.innerText = w.weather_description || "Partly Cloudy";
      if (mapBadge) mapBadge.innerText = `${w.weather_description || 'Clear'} • ${Math.round(w.temperature_c || 29)}°C`;

      const gTemp = document.getElementById("gw-temp");
      const gRain = document.getElementById("gw-rain-prob");
      const gWind = document.getElementById("gw-wind");
      const gPrecip = document.getElementById("gw-precip");
      if (gTemp) gTemp.innerText = `${Math.round(w.temperature_c || 29)}°C`;
      if (gRain) gRain.innerText = `${Math.round(w.rain_probability || 62)}%`;
      if (gWind) gWind.innerText = `${Math.round(w.wind_speed_kmh || 18)} km/h`;
      if (gPrecip) gPrecip.innerText = `${(w.precipitation_mm_h || 0).toFixed(1)} mm/h`;
    }

    // ============================================================
    // RENDER PROVIDER PULSE / TELEGRAM PANEL & MESSAGE AUDIT
    // ============================================================
    function renderWhatsAppPanel(wa, sigWa, providers) {
      const feed = document.getElementById("wa-messages-feed");
      const gapStatus = document.getElementById("wa-gap-status");
      const badge = document.getElementById("wa-integration-badge");
      const providersCount = document.getElementById("wa-providers-count");

      if (gapStatus && currentMasterData?.digital_twin) {
        gapStatus.innerText = currentMasterData.digital_twin.capacity_gap_status || 'BALANCED';
      }

      if (providers && providersCount) {
        providersCount.innerText = `${providers.length} Providers Verified`;
      }

      const pulse = currentMasterData?.provider_pulse;
      if (badge && pulse) {
        badge.innerText = pulse.display_badge || (pulse.telegram_configured ? `TELEGRAM ONLINE (${pulse.mode.toUpperCase()})` : "SANDBOX ACTIVE");
        if (pulse.telegram_configured) {
          badge.className = "text-[11px] font-bold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200";
        }
        if (pulse.bot_username) {
          const u = pulse.bot_username;
          const handle = document.getElementById("telegram-channel-handle");
          const link = document.getElementById("telegram-channel-link");
          const hLink = document.getElementById("telegram-header-link");
          if (handle) handle.innerText = `@${u}`;
          if (link) link.href = `https://t.me/${u}`;
          if (hLink) {
            hLink.innerText = `@${u}`;
            hLink.href = `https://t.me/${u}`;
          }
        }
      }

      // Fetch Telegram messages with fallback to WhatsApp
      fetch(`${API_BASE}/telegram/messages`)
        .then(r => r.json())
        .then(msgs => {
          if (!feed) return;
          if (msgs && msgs.length > 0) {
            feed.innerHTML = "";
            msgs.slice(0, 10).forEach(m => {
              const isOut = m.direction === 'OUTBOUND';
              const msgEl = document.createElement("div");
              msgEl.className = `p-2.5 rounded-lg border text-xs ${
                isOut ? 'bg-sky-50/70 border-sky-200 ml-4' : 'bg-slate-50 border-slate-200 mr-4'
              }`;
              msgEl.innerHTML = `
                <div class="flex items-center justify-between text-[11px] text-slate-500 font-medium mb-1">
                  <span class="font-bold text-slate-700">${isOut ? 'Dispatch To' : 'From'}: @${m.telegram_username || m.provider_id || 'Transit Operator'} (${m.channel || 'Telegram'})</span>
                  <span class="font-num">${new Date(m.created_at || m.timestamp || Date.now()).toLocaleTimeString()}</span>
                </div>
                <div class="font-bold text-slate-800">${m.raw_text || 'Capacity telemetry update'}</div>
                <div class="mt-1 flex items-center gap-1.5">
                  ${m.parsed_value ? `<span class="text-[10px] font-bold font-num px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">+${m.parsed_value} ${m.parsed_resource || 'CAPACITY'}</span>` : ''}
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-white text-slate-600 border border-slate-200">${m.status || m.processing_status || 'CONFIRMED'} ✓✓</span>
                </div>
              `;
              feed.appendChild(msgEl);
            });
            return;
          }

          // Fallback to whatsapp messages
          fetch(`${API_BASE}/whatsapp/messages`)
            .then(r => r.json())
            .then(wmsgs => {
              if (!wmsgs || wmsgs.length === 0) return;
              feed.innerHTML = "";
              wmsgs.slice(0, 10).forEach(m => {
                const isOut = m.direction === 'OUTBOUND';
                const msgEl = document.createElement("div");
                msgEl.className = `p-2.5 rounded-lg border text-xs ${
                  isOut ? 'bg-indigo-50/70 border-indigo-200 ml-4' : 'bg-slate-50 border-slate-200 mr-4'
                }`;
                msgEl.innerHTML = `
                  <div class="flex items-center justify-between text-[11px] text-slate-500 font-medium mb-1">
                    <span class="font-bold text-slate-700">${isOut ? 'Dispatch To' : 'From'}: ${m.from_number_masked || m.provider_id || 'Transit Operator'}</span>
                    <span class="font-num">${new Date(m.timestamp || Date.now()).toLocaleTimeString()}</span>
                  </div>
                  <div class="font-bold text-slate-800">${m.raw_text || 'Capacity telemetry update'}</div>
                  <div class="mt-1 flex items-center gap-1.5">
                    ${m.parsed_value ? `<span class="text-[10px] font-bold font-num px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">+${m.parsed_value} SEATS</span>` : ''}
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-white text-slate-600 border border-slate-200">${m.delivery_status || m.processing_status || 'DELIVERED'} ✓✓</span>
                  </div>
                `;
                feed.appendChild(msgEl);
              });
            }).catch(e => console.error(e));
        })
        .catch(e => console.error("Error fetching messages:", e));
    }

    // Send Deterministic Telegram Operational Response into Backend
    async function sendTelegramOperationalResponse(text, providerId) {
      try {
        const provId = providerId || "prov-mumbai-best-01";
        const eventId = currentEventId || "mumbai-cricket-match-wankhede";
        const res = await fetch(`${API_BASE}/telegram/simulate-response`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider_id: provId,
            response_text: text,
            event_id: eventId
          })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(`Telegram Telemetry: ${data.message || text}`, 'success');
          await refreshDashboardState();
        } else {
          showToast(`Error: ${data.detail || 'Failed to simulate response'}`, 'danger');
        }
      } catch (e) {
        showToast(`Error: ${e.message}`, 'danger');
      }
    }

    // Dispatch Telegram Operational Capacity Poll to Fleet
    async function dispatchTelegramOperationalPoll() {
      try {
        const provId = "prov-mumbai-best-01";
        const eventId = currentEventId || "mumbai-cricket-match-wankhede";
        const res = await fetch(`${API_BASE}/telegram/poll/dispatch`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider_id: provId,
            event_id: eventId,
            required_capacity: 120,
            weather_trigger: "Heavy rain detected near Wankhede Stadium (42 mm/h)"
          })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(`Broadcast Telegram Poll: Dispatched to @best_mumbai_bot`, 'success');
          await refreshDashboardState();
        } else {
          showToast(`Error: ${data.detail || 'Failed to dispatch poll'}`, 'danger');
        }
      } catch (e) {
        showToast(`Error: ${e.message}`, 'danger');
      }
    }

    // Run 10-Step Deterministic Telegram Closed-Loop Demo
    async function runClosedLoopDemo() {
      try {
        showToast("Running 10-step Telegram closed-loop simulation...", "info");
        const eventId = currentEventId || "mumbai-cricket-match-wankhede";
        const res = await fetch(`${API_BASE}/telegram/demo/closed-loop?event_id=${eventId}`, {
          method: "POST"
        });
        const data = await res.json();
        if (res.ok) {
          showToast(`Closed Loop Complete: Shortage dropped from 120 -> 20 seats via Telegram response!`, 'success');
          await refreshDashboardState();
        } else {
          showToast(`Demo failed: ${data.detail || 'Error running demo'}`, 'danger');
        }
      } catch (e) {
        showToast(`Error: ${e.message}`, 'danger');
      }
    }

    // Run Simulated Crowd Alert Closed Loop (Digital Twin -> Staff Bot -> Diversion -> Risk Stabilized)
    async function runSimulatedCrowdAlert() {
      try {
        showToast("Dispatching simulated crowd surge alert to Staff Bot...", "info");
        const res = await fetch(`${API_BASE}/operations-network/simulate-crowd-alert`, {
          method: "POST"
        });
        const data = await res.json();
        if (res.ok && data.status === "ok") {
          showToast(`Crowd Closed-Loop Done: Alert dispatched to Zone ${data.zone_id}, diversion executed, risk stabilized to WATCH!`, 'success');
          await refreshDashboardState();
        } else {
          showToast(`Crowd Alert failed: ${data.detail || 'Error'}`, 'danger');
        }
      } catch (e) {
        showToast(`Error: ${e.message}`, 'danger');
      }
    }

    // Run Simulated Hotel Request Closed Loop (Visitor Bot -> EVENTOS -> Staff Bot -> Provider Accept)
    async function runSimulatedHotelRequest() {
      try {
        showToast("Processing simulated visitor hotel booking request...", "info");
        const res = await fetch(`${API_BASE}/operations-network/simulate-hotel-request`, {
          method: "POST"
        });
        const data = await res.json();
        if (res.ok && data.status === "ok") {
          showToast(`Hotel Closed-Loop Done: Booking ${data.request_id} accepted & confirmed to visitor!`, 'success');
          await refreshDashboardState();
        } else {
          showToast(`Hotel Request failed: ${data.detail || 'Error'}`, 'danger');
        }
      } catch (e) {
        showToast(`Error: ${e.message}`, 'danger');
      }
    }

    // Send Quick Simulated Inbound Provider Response into SQLite (Backward Compatible)
    async function sendQuickOperationalResponse(text) {
      await sendTelegramOperationalResponse(text);
    }

    // Send Custom WhatsApp / Telegram Outbound Dispatch
    async function sendCustomWhatsAppMessage() {
      const input = document.getElementById("wa-custom-input");
      if (!input || !input.value.trim()) return;
      const text = input.value.trim();

      try {
        const res = await fetch(`${API_BASE}/whatsapp/send`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            to_number: "+919820111223",
            message: text
          })
        });
        if (res.ok) {
          showToast(`Telegram / Fleet Alert Dispatched: "${text}"`, 'success');
          input.value = "";
          await refreshDashboardState();
        } else {
          showToast("Failed to dispatch alert", 'danger');
        }
      } catch (e) {
        showToast(`Error: ${e.message}`, 'danger');
      }
    }

    // Poll Transport Fleet (Backward Compatible)
    async function dispatchOperationalCapacityPoll() {
      await dispatchTelegramOperationalPoll();
    }

    // Render Recommendations
    function renderRecommendations(recs) {
      const container = document.getElementById("recommendations-container");
      const tag = document.getElementById("recs-count-tag");
      if (!container) return;

      if (!recs || recs.length === 0) {
        container.innerHTML = `
          <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 text-center space-y-2">
            <p class="font-medium">All sectors operating within baseline limits. No active intervention requested.</p>
            <button onclick="triggerSurgeSimulation()" class="px-3 py-1.5 bg-white border border-slate-200 text-slate-800 font-bold rounded-lg shadow-2xs hover:bg-slate-50 transition">
              Test Concourse Surge Scenario
            </button>
          </div>
        `;
        if (tag) tag.innerText = "0";
        return;
      }

      if (tag) tag.innerText = recs.length;
      container.innerHTML = "";

      recs.forEach(r => {
        const isApproved = r.status === 'approved' || r.status === 'dispatched';
        const card = document.createElement("div");
        card.className = `p-3 rounded-xl border text-xs space-y-2 transition ${
          isApproved ? 'bg-emerald-50/50 border-emerald-200' : 'bg-white border-slate-200 shadow-2xs'
        }`;
        card.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="font-bold text-slate-900">${r.recommendation_type || 'Operational Action'}</span>
            <span class="text-[11px] font-bold px-2 py-0.5 rounded ${
              isApproved ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
            }">${(r.status || 'PENDING').toUpperCase()}</span>
          </div>
          <p class="text-slate-600 text-[11px] font-medium leading-relaxed">${r.description || 'Proactive flow intervention'}</p>
          <div class="flex items-center justify-between pt-1">
            <span class="text-xs font-semibold text-slate-500 font-num">Target: ${r.target_zone_id || 'All Sectors'}</span>
            ${!isApproved ? `
              <div class="flex gap-1.5">
                <button onclick="rejectRecommendation('${r.id}')" class="px-2 py-1 text-xs text-slate-500 hover:text-slate-800 font-bold">Dismiss</button>
                <button onclick="approveRecommendation('${r.id}')" class="px-3 py-1 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-2xs">Approve & Dispatch</button>
              </div>
            ` : `
              <span class="text-xs font-bold text-emerald-700 flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                Dispatched to Fleet
              </span>
            `}
          </div>
        `;
        container.appendChild(card);
      });
    }

    // Approve Recommendation
    async function approveRecommendation(recId) {
      try {
        const res = await fetch(`${API_BASE}/recommendations/${recId}/approve`, {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        if (res.ok) {
          showToast(`Recommendation #${recId} approved and dispatched!`, 'success');
          await refreshDashboardState();
        }
      } catch (e) {
        showToast(`Approval failed: ${e.message}`, 'danger');
      }
    }

    // Reject Recommendation
    async function rejectRecommendation(recId) {
      try {
        const res = await fetch(`${API_BASE}/recommendations/${recId}/reject`, {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        if (res.ok) {
          showToast(`Recommendation #${recId} dismissed`, 'info');
          await refreshDashboardState();
        }
      } catch (e) {
        showToast(`Dismiss failed: ${e.message}`, 'danger');
      }
    }

    // Render Timeline Audit
    function renderTimeline(timeline) {
      const container = document.getElementById("timeline-container");
      const fullList = document.getElementById("audit-trail-full-list");
      if (!timeline || timeline.length === 0) return;

      if (container) {
        container.innerHTML = "";
        timeline.slice(0, 5).forEach(item => {
          const div = document.createElement("div");
          div.className = "flex items-center gap-2 text-[11px]";
          div.innerHTML = `
            <span class="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
            <span class="font-num font-semibold text-slate-500">${new Date(item.timestamp || Date.now()).toLocaleTimeString()}</span>
            <span class="truncate font-semibold text-slate-700">${item.event_type || item.description}</span>
          `;
          container.appendChild(div);
        });
      }

      if (fullList) {
        fullList.innerHTML = "";
        timeline.forEach(item => {
          const div = document.createElement("div");
          div.className = "p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between";
          div.innerHTML = `
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-indigo-600"></span>
              <span class="font-bold text-slate-800">${item.event_type || 'System Event'}</span>
              <span class="text-slate-500 font-medium">— ${item.description || 'Logged operation'}</span>
            </div>
            <span class="font-num text-xs font-semibold text-slate-500">${new Date(item.timestamp || Date.now()).toLocaleTimeString()}</span>
          `;
          fullList.appendChild(div);
        });
      }
    }

    // Digital Twin Panel
    function renderDigitalTwinPanel(dt, zones, providers, liveWeather) {
      if (!dt) return;
      activeDigitalTwinData = dt;

      const deltaCrowd = document.getElementById("dt-comp-delta-crowd");
      const baseCrowd = document.getElementById("dt-comp-base-crowd");
      const simCrowd = document.getElementById("dt-comp-sim-crowd");
      const deltaTrans = document.getElementById("dt-comp-delta-trans");
      const simTrans = document.getElementById("dt-comp-sim-trans");
      const statusBadge = document.getElementById("dt-cascade-status-badge");

      if (deltaCrowd) deltaCrowd.innerText = `+${Number(dt.crowd_delta || 1420).toLocaleString()}`;
      if (baseCrowd) baseCrowd.innerText = Number(dt.baseline_total_crowd || 21370).toLocaleString();
      if (simCrowd) simCrowd.innerText = Number(dt.simulated_total_crowd || 22790).toLocaleString();
      if (deltaTrans) deltaTrans.innerText = `-${Number(dt.transport_capacity_gap || 10518).toLocaleString()}`;
      if (simTrans) simTrans.innerText = Number(dt.transport_demand_required || 11218).toLocaleString();
      if (statusBadge) statusBadge.innerText = (dt.capacity_gap_status || 'EVALUATED');

      renderCascadeChain(dt.cascade_chain);
    }

    function renderCascadeChain(chain) {
      const container = document.getElementById("dt-cascade-chain-container");
      if (!container || !chain || chain.length === 0) return;
      container.innerHTML = "";
      chain.forEach((c, idx) => {
        const div = document.createElement("div");
        div.className = "p-3 rounded-lg border border-slate-200 bg-slate-50 text-xs flex items-center justify-between";
        div.innerHTML = `
          <div>
            <span class="font-bold text-slate-800">${c.step || `Step ${idx+1}`}</span>
            <span class="text-slate-600 font-medium ml-2">${c.detail || ''}</span>
          </div>
          <span class="text-[10px] font-bold px-2 py-0.5 rounded ${
            c.status === 'DETECTED' ? 'bg-amber-100 text-amber-800' :
            c.status === 'SURGING' || c.status === 'ALERT_GAP' ? 'bg-rose-100 text-rose-800' :
            'bg-slate-200 text-slate-700'
          }">${c.status || 'ACTIVE'}</span>
        `;
        container.appendChild(div);
      });
    }

    // Execute Digital Twin Simulation
    async function executeDigitalTwinSimulation() {
      if (!activeEventId) return;
      const rainVal = parseFloat(document.getElementById("dt-input-rain")?.value || 20);

      try {
        const res = await fetch(`${API_BASE}/events/${activeEventId}/digital-twin/simulate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            precipitation_mm_h: rainVal,
            wind_speed_kmh: 42.0,
            scenario_name: rainVal > 30 ? "heavy_rain" : "moderate_rain"
          })
        });
        if (res.ok) {
          const data = await res.json();
          renderDigitalTwinPanel(data.digital_twin, currentMasterData?.zones, currentMasterData?.providers, currentMasterData?.weather);
          showToast(`Digital Twin computed: ${data.digital_twin.scenario_label}`, 'success');
        }
      } catch (e) {
        showToast(`Simulation failed: ${e.message}`, 'danger');
      }
    }

    function onWhatIfInputChanged(val) {
      const label = document.getElementById("dt-slider-rain-val");
      if (label) label.innerText = `${parseFloat(val).toFixed(1)} mm/h`;
    }

    function applyPresetScenario(name) {
      const slider = document.getElementById("dt-input-rain");
      if (!slider) return;
      if (name === 'normal') slider.value = 0;
      else if (name === 'moderate_rain') slider.value = 15;
      else if (name === 'heavy_rain') slider.value = 35;
      else if (name === 'thunderstorm') slider.value = 55;
      onWhatIfInputChanged(slider.value);
      executeDigitalTwinSimulation();
    }

    // Leaflet GIS Map Implementation
    function initLeafletMap() {
      const mapEl = document.getElementById("operational-map");
      if (!mapEl) return;

      leafletMap = L.map("operational-map", {
        center: [18.9389, 72.8258],
        zoom: 16,
        zoomControl: false,
        attributionControl: false
      });

      mapLayers.base = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        className: 'map-tiles-light'
      }).addTo(leafletMap);

      L.control.zoom({ position: 'bottomright' }).addTo(leafletMap);

      mapLayers.zones = L.layerGroup().addTo(leafletMap);
      mapLayers.transit = L.layerGroup().addTo(leafletMap);
      mapLayers.cameras = L.layerGroup().addTo(leafletMap);

      addTransitMarkers();
      addCameraMarkers();
    }

    function setBasemap(type) {
      if (!leafletMap) return;
      if (mapLayers.base) leafletMap.removeLayer(mapLayers.base);

      const btnCanvas = document.getElementById("btn-map-canvas");
      const btnSat = document.getElementById("btn-map-sat");

      if (type === 'satellite') {
        mapLayers.base = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
          maxZoom: 19,
          className: 'map-tiles-sat'
        }).addTo(leafletMap);
        if (btnCanvas) btnCanvas.classList.remove('active');
        if (btnSat) btnSat.classList.add('active');
      } else {
        mapLayers.base = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          className: 'map-tiles-light'
        }).addTo(leafletMap);
        if (btnCanvas) btnCanvas.classList.add('active');
        if (btnSat) btnSat.classList.remove('active');
      }
    }

    function toggleMapLayer(layer) {
      if (!leafletMap || !mapLayers[layer]) return;
      const btn = document.getElementById(`btn-map-${layer}`);
      if (leafletMap.hasLayer(mapLayers[layer])) {
        leafletMap.removeLayer(mapLayers[layer]);
        if (btn) btn.classList.remove('active');
      } else {
        leafletMap.addLayer(mapLayers[layer]);
        if (btn) btn.classList.add('active');
      }
    }

    function resetMapView() {
      if (leafletMap) leafletMap.flyTo([18.9389, 72.8258], 16);
    }

    function addTransitMarkers() {
      if (!mapLayers.transit) return;
      mapLayers.transit.clearLayers();

      // Churchgate Railway Terminus
      const m1 = L.marker([18.9355, 72.8272], {
        icon: L.divIcon({
          className: 'custom-pin',
          html: `<div class="bg-blue-600 text-white p-1 rounded-full border-2 border-white shadow-md cursor-pointer hover:scale-110 transition"><svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2c-4 0-8 .5-8 4v9.5C4 17.43 5.57 19 7.5 19L6 20.5v.5h12v-.5L16.5 19c1.93 0 3.5-1.57 3.5-3.5V6c0-3.5-4-4-8-4z"/></svg></div>`,
          iconSize: [24, 24]
        })
      }).bindTooltip("<b>Churchgate Railway Terminus</b><br>Western Line Fast EMUs").addTo(mapLayers.transit);
      m1.on('click', () => {
        showSelectedObjectPanel({
          type: 'transit',
          name: 'Churchgate Railway Terminus',
          occ: '1,420 passengers waiting',
          util: 'Western Line EMU Terminal',
          flow: 'Dispatched every 3 min',
          forecast: 'HIGH FREQUENCY'
        });
      });

      // Marine Drive Feeder Bus Stop
      const m2 = L.marker([18.9405, 72.8235], {
        icon: L.divIcon({
          className: 'custom-pin',
          html: `<div class="bg-emerald-600 text-white p-1 rounded-full border-2 border-white shadow-md cursor-pointer hover:scale-110 transition"><svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M4 16c0 .88.39 1.67 1 2.22V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h8v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1c-.83 0-1.5-.67-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm9 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg></div>`,
          iconSize: [24, 24]
        })
      }).bindTooltip("<b>BEST Feeder Bus Depot 4</b><br>120 seats available").addTo(mapLayers.transit);
      m2.on('click', () => {
        showSelectedObjectPanel({
          type: 'transit',
          name: 'BEST Feeder Bus Depot 4',
          occ: '350 queued passengers',
          util: '120 active standby seats',
          flow: 'Buses dispatched every 5 min',
          forecast: 'VERIFIED STANDBY'
        });
      });

      // Ambulance Emergency Station
      const m3 = L.marker([18.9372, 72.8268], {
        icon: L.divIcon({
          className: 'custom-pin',
          html: `<div class="bg-rose-600 text-white p-1 rounded-full border-2 border-white shadow-md cursor-pointer hover:scale-110 transition"><svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M19 10.5V6a2 2 0 00-2-2H7a2 2 0 00-2 2v4.5C3.9 11 3 12.1 3 13.5v4c0 .8.7 1.5 1.5 1.5H5v1c0 .6.4 1 1 1h1c.6 0 1-.4 1-1v-1h8v1c0 .6.4 1 1 1h1c.6 0 1-.4 1-1v-1h.5c.8 0 1.5-.7 1.5-1.5v-4c0-1.4-.9-2.5-2-3zM13 13h-2v2H9v-2H7v-2h2V9h2v2h2v2z"/></svg></div>`,
          iconSize: [24, 24]
        })
      }).bindTooltip("<b>108 Emergency Ambulance Post</b><br>Gate 2 Standby").addTo(mapLayers.transit);
      m3.on('click', () => {
        showSelectedObjectPanel({
          type: 'transit',
          name: '108 Emergency Ambulance Post',
          occ: '2 ALS Units on Standby',
          util: 'Gate 2 Perimeter Access',
          flow: 'Zero queue · Immediate response',
          forecast: 'READY'
        });
      });
    }

    function addCameraMarkers() {
      if (!mapLayers.cameras) return;
      mapLayers.cameras.clearLayers();

      const cctvCams = [
        {
          id: "CAM-01",
          name: "CAM-01: Stadium Main Entrance",
          zone: "Zone A · Turnstiles Egress",
          coords: [18.9388, 72.8256]
        },
        {
          id: "CAM-02",
          name: "CAM-02: North Concourse & Ramp Access",
          zone: "Zone B · Upper Level Flow",
          coords: [18.9402, 72.8262]
        },
        {
          id: "CAM-03",
          name: "CAM-03: Gate 3 Queue & Outer Perimeter",
          zone: "Zone C · Outer Security Perimeter",
          coords: [18.9378, 72.8242]
        }
      ];

      cctvCams.forEach(cam => {
        const icon = L.divIcon({
          className: 'custom-cctv-pin',
          html: `<div class="relative group cursor-pointer">
            <div class="w-7 h-7 rounded-full bg-slate-900 border-2 border-indigo-400 text-indigo-300 flex items-center justify-center shadow-lg hover:scale-110 transition">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
            </div>
            <span class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full border border-white animate-pulse"></span>
          </div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });

        const popupContent = `
          <div class="p-1 font-sans" style="min-width: 220px;">
            <div class="flex items-center justify-between gap-2 mb-1.5">
              <span class="font-bold text-xs text-slate-900">${cam.name}</span>
              <span class="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">ONLINE</span>
            </div>
            <div class="text-[11px] text-slate-500 font-medium mb-2">${cam.zone}</div>
            <div class="relative rounded-lg overflow-hidden border border-slate-200 bg-slate-900 aspect-video mb-2">
              <img src="/api/v1/cv/stream/${cam.id}" alt="${cam.name}" class="w-full h-full object-cover">
              <span class="absolute top-1 left-1.5 bg-slate-900/80 backdrop-blur-2xs text-[9px] text-emerald-400 font-num font-bold px-1.5 py-0.5 rounded">
                CV ACTIVE
              </span>
            </div>
            <button onclick="selectCameraFromMap('${cam.id}')" class="w-full py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-lg transition shadow-xs flex items-center justify-center gap-1.5">
              <span>Open in CCTV Evidence Panel</span>
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
            </button>
          </div>
        `;

        const marker = L.marker(cam.coords, { icon: icon })
          .bindPopup(popupContent, { maxWidth: 260 })
          .bindTooltip(`<b>${cam.id}</b>: ${cam.name}`)
          .addTo(mapLayers.cameras);

        marker.on('click', () => {
          showSelectedObjectPanel({
            type: 'camera',
            id: cam.id,
            name: cam.name,
            occ: '14 in FOV (YOLO Track)',
            util: cam.zone,
            flow: 'Net: +6/min',
            forecast: 'COMPUTER VISION ACTIVE'
          });
        });
      });
    }

    function selectCameraFromMap(camId) {
      if (leafletMap) leafletMap.closePopup();
      switchMainView('signals');
      selectCctvCamera(camId);
    }

    function selectCctvCamera(camId) {
      currentCameraId = camId;
      const player = document.getElementById("cctv-stream-player");
      if (player) {
        player.src = `${API_BASE}/cv/stream/${camId}?t=${Date.now()}`;
      }

      ['CAM-01', 'CAM-02', 'CAM-03', 'CAM-04'].forEach(id => {
        const tab = document.getElementById(`tab-cam-${id}`);
        if (tab) {
          if (id === camId) {
            tab.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-xs transition flex items-center gap-2";
          } else {
            tab.className = "px-3.5 py-2 rounded-lg text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 transition flex items-center gap-2 border border-transparent hover:border-slate-200";
          }
        }
      });

      fetchCctvTelemetry();
    }

    // Scenario Engine & Pitch Demo Controllers
    async function executeNamedScenario(scenarioKey) {
      try {
        showToast(`Executing Operational Scenario: ${scenarioKey}...`, "info");
        const res = await fetch(`${API_BASE}/scenarios/execute`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario_key: scenarioKey })
        });
        const data = await res.json();
        if (res.ok) {
          renderScenarioMatrix(data);
          showToast(`Scenario Applied: ${data.name}. Severity: ${data.severity}`, data.severity === 'CRITICAL' ? 'danger' : 'warning');
          await fetchTimelineEvents();
        } else {
          showToast(`Scenario failed: ${data.detail || 'Error'}`, "danger");
        }
      } catch (e) {
        showToast(`Error: ${e.message}`, "danger");
      }
    }

    function renderScenarioMatrix(data) {
      if (!data) return;
      const titleEl = document.getElementById("matrix-scenario-title");
      const descEl = document.getElementById("matrix-scenario-desc");
      const sevEl = document.getElementById("matrix-scenario-severity");
      const tbody = document.getElementById("matrix-comparison-tbody");

      if (titleEl) titleEl.innerText = `${data.name} — Baseline vs What-If Matrix`;
      if (descEl) descEl.innerText = data.description || "";
      if (sevEl) {
        sevEl.innerText = data.severity;
        sevEl.className = `text-xs font-bold px-2 py-0.5 rounded ${
          data.severity === 'CRITICAL' ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
        }`;
      }

      if (tbody && data.comparison_table) {
        tbody.innerHTML = "";
        data.comparison_table.forEach(row => {
          const tr = document.createElement("tr");
          tr.className = "hover:bg-slate-50/60 transition";
          const statusBadge = row.status === 'CRITICAL' 
            ? '<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">BREACH</span>'
            : (row.status === 'WARNING'
                ? '<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">ELEVATED</span>'
                : '<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">SAFE</span>');

          tr.innerHTML = `
            <td class="py-2.5 px-2.5 font-bold text-slate-800">${row.metric_name}</td>
            <td class="py-2.5 px-2.5 text-slate-600 font-num">${row.baseline_value}</td>
            <td class="py-2.5 px-2.5 font-bold font-num text-slate-900">${row.whatif_value}</td>
            <td class="py-2.5 px-2.5 font-num font-semibold ${row.status === 'CRITICAL' ? 'text-rose-600' : 'text-slate-700'}">${row.delta}</td>
            <td class="py-2.5 px-2.5">${statusBadge}</td>
          `;
          tbody.appendChild(tr);
        });
      }
    }

    async function runCombinedExtremeDemo() {
      try {
        switchMainView('twin');
        showToast("⚡ INITIATING 3-MINUTE PITCH DEMO: Combined Surge + Rain + Transit Outage...", "warning");
        await executeNamedScenario('COMBINED_EXTREME_EVENT');
        await simulateFleetFailure();
        await fetchTimelineEvents();
        await refreshDashboardState();
        showToast("Multi-Sector Cascading Crisis Active: Nugen AI is synthesizing contingency recommendations.", "danger");
      } catch (e) {
        showToast(`Demo error: ${e.message}`, "danger");
      }
    }

    async function fetchTimelineEvents() {
      try {
        const res = await fetch(`${API_BASE}/timeline/events`);
        if (res.ok) {
          const data = await res.json();
          renderTimelineChronology(data.timeline || []);
        }
      } catch (err) {
        console.warn("Timeline fetch error:", err);
      }
    }

    function renderTimelineChronology(events) {
      const container = document.getElementById("timeline-chronology-container");
      if (!container || !events) return;
      container.innerHTML = "";

      events.forEach(ev => {
        const div = document.createElement("div");
        div.className = "p-2.5 rounded-lg border border-slate-200/80 bg-slate-50/70 hover:bg-slate-50 transition text-xs space-y-1";
        const badgeColor = ev.badge_style === 'emerald' ? 'bg-emerald-100 text-emerald-800' : (ev.badge_style === 'rose' ? 'bg-rose-100 text-rose-800' : (ev.badge_style === 'amber' ? 'bg-amber-100 text-amber-800' : 'bg-indigo-100 text-indigo-800'));

        div.innerHTML = `
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1.5">
              <span class="text-[9px] font-bold px-1.5 py-0.5 rounded ${badgeColor}">${ev.system_source}</span>
              <span class="font-bold text-slate-800">${ev.headline}</span>
            </div>
            <span class="font-num text-[10px] text-slate-400 font-semibold">${ev.timestamp}</span>
          </div>
          <p class="text-[11px] text-slate-600 font-medium">${ev.details}</p>
          ${ev.metric_delta ? `<div class="text-[10px] font-bold font-num text-indigo-700">${ev.metric_delta}</div>` : ''}
        `;
        container.appendChild(div);
      });
    }

    async function fetchGpsFleet() {
      try {
        const res = await fetch(`${API_BASE}/gps/fleet`);
        if (res.ok) {
          const data = await res.json();
          const seatsEl = document.getElementById("gps-avail-seats");
          const gapEl = document.getElementById("gps-gap-status");
          const badgeEl = document.getElementById("gps-fleet-status-badge");

          if (seatsEl) seatsEl.innerText = `${data.total_available_seats} Seats`;
          if (gapEl) {
            gapEl.innerText = data.capacity_gap_status;
            gapEl.className = `text-base font-bold font-num ${data.capacity_gap_status === 'DEFICIT' ? 'text-rose-600' : 'text-emerald-600'}`;
          }
          if (badgeEl) {
            badgeEl.innerText = `● ${data.active_vehicles} BUSES EN ROUTE (${data.offline_vehicles} OFFLINE)`;
            badgeEl.className = `text-[10px] font-bold px-1.5 py-0.5 rounded ${data.offline_vehicles > 0 ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'}`;
          }
        }
      } catch (err) {
        console.warn("GPS fleet error:", err);
      }
    }

    async function simulateFleetFailure() {
      try {
        const res = await fetch(`${API_BASE}/gps/fleet/simulate-failure`, { method: "POST" });
        if (res.ok) {
          showToast("Simulated 3 Buses Breakdown: Transit deficit injected into Digital Twin!", "danger");
          await fetchGpsFleet();
          await refreshDashboardState();
        }
      } catch (err) {
        showToast(`Failure injection failed: ${err.message}`, "danger");
      }
    }

    async function resetFleetSimulator() {
      try {
        const res = await fetch(`${API_BASE}/gps/fleet/reset`, { method: "POST" });
        if (res.ok) {
          showToast("Fleet Simulator reset to normal operations.", "success");
          await fetchGpsFleet();
          await refreshDashboardState();
        }
      } catch (err) {
        showToast(`Reset failed: ${err.message}`, "danger");
      }
    }

    async function fetchPdrStream() {
      try {
        const res = await fetch(`${API_BASE}/pdr/stream`);
        if (res.ok) {
          const data = await res.json();
          const zoneA = data["ZONE-56894058"] || Object.values(data)[0];
          if (zoneA) {
            const devEl = document.getElementById("pdr-stat-devices");
            const spdEl = document.getElementById("pdr-stat-speed");
            const flwEl = document.getElementById("pdr-stat-flow");
            if (devEl) devEl.innerText = zoneA.device_count;
            if (spdEl) spdEl.innerText = `${zoneA.mean_speed_mps} m/s`;
            if (flwEl) flwEl.innerText = `${zoneA.flow_rate_per_min > 0 ? '+' : ''}${zoneA.flow_rate_per_min}/m`;
          }
        }
      } catch (err) {
        console.warn("PDR stream error:", err);
      }
    }


    async function fetchCctvTelemetry() {
      try {
        const res = await fetch(`${API_BASE}/cv/telemetry/${currentCameraId}`);
        if (res.ok) {
          const data = await res.json();
          renderCctvTelemetryUI(data);
        }
      } catch (err) {
        console.warn("CCTV telemetry fetch error:", err);
      }
    }

    function renderCctvTelemetryUI(data) {
      if (!data) return;
      const m = data.metrics || {};
      const p = data.pdr_corroboration || {};
      const ma = data.macro_aggregation || {};

      const setT = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
      };

      setT("cctv-stat-visible", m.currently_visible ?? '--');
      setT("cctv-stat-in", `+${m.entered_count ?? 0}`);
      setT("cctv-stat-out", `-${m.exited_count ?? 0}`);
      const net = m.net_flow ?? 0;
      const netEl = document.getElementById("cctv-stat-net");
      if (netEl) {
        netEl.innerText = net >= 0 ? `+${net}/min` : `${net}/min`;
        netEl.className = `text-xl font-bold font-num ${net >= 0 ? 'text-indigo-600' : 'text-amber-600'}`;
      }
      setT("cctv-stat-fps", data.processing_fps ?? 14.2);
      setT("cctv-stat-conf", `${data.detection_confidence_pct ?? 91.4}%`);

      // PDR Corroboration
      setT("cctv-pdr-optical", p.cctv_flow_rate ?? '+6.0/min');
      setT("cctv-pdr-vector", p.pdr_flow_rate ?? '+5.4/min (SIMULATED)');
      setT("cctv-pdr-fused", p.fused_flow_rate ?? '+5.7/min');
      setT("cctv-pdr-agree", p.sensor_agreement ?? 'HIGH (94.8% AGREEMENT)');

      // Macro Aggregation
      setT("cctv-macro-local", `${ma.local_camera_observation ?? m.currently_visible} in FOV`);
      setT("cctv-macro-zone", `${Number(ma.zone_crowd_estimate ?? 18420).toLocaleString()} / 26,000 (70.8%)`);
      setT("cctv-macro-venue", `${Number(ma.venue_occupancy_estimate ?? 21370).toLocaleString()} / 33,500 (63.8%)`);

      // HUD elements
      setT("cctv-hud-cam-name", `${data.camera_id}: ${data.camera_name}`);
      setT("cctv-hud-zone", data.zone_name || 'Zone A');
    }

    function renderLeafletMap(venue, zones, providers, weather, dtState) {
      if (!leafletMap || !mapLayers.zones) return;
      mapLayers.zones.clearLayers();

      const zonePolygons = [
        {
          name: "Zone A - Stadium Bowl",
          color: "#4F46E5",
          coords: [
            [18.9395, 72.8250],
            [18.9395, 72.8268],
            [18.9380, 72.8268],
            [18.9380, 72.8250]
          ],
          crowd: "18,420 / 26,000"
        },
        {
          name: "Zone B - North Gate & Churchgate Access",
          color: "#059669",
          coords: [
            [18.9405, 72.8252],
            [18.9405, 72.8275],
            [18.9396, 72.8275],
            [18.9396, 72.8252]
          ],
          crowd: "2,100 / 4,500"
        },
        {
          name: "Zone C - Marine Drive External Approach",
          color: "#D97706",
          coords: [
            [18.9398, 72.8235],
            [18.9398, 72.8249],
            [18.9372, 72.8249],
            [18.9372, 72.8235]
          ],
          crowd: "850 / 3,000"
        }
      ];

      zonePolygons.forEach(z => {
        const poly = L.polygon(z.coords, {
          color: z.color,
          weight: 2,
          fillOpacity: 0.18
        }).bindTooltip(`<b>${z.name}</b><br>Crowd: ${z.crowd}`).addTo(mapLayers.zones);

        poly.on('click', () => {
          showSelectedObjectPanel({
            type: 'zone',
            name: z.name,
            occ: z.crowd,
            util: 'Calibrated Sector Occupancy',
            flow: '+540/m in • -310/m out',
            forecast: 'WATCH'
          });
        });
      });
    }

    // ============================================================
    // LIQUID GLASS INTERACTIVE PANELS CONTROLLER
    // ============================================================

    // Weather Intelligence Glass Panel
    function toggleWeatherGlassPanel(forceState) {
      const panel = document.getElementById("map-weather-expanded-panel");
      if (!panel) return;
      if (typeof forceState === 'boolean') {
        if (forceState) panel.classList.remove('hidden');
        else panel.classList.add('hidden');
      } else {
        panel.classList.toggle('hidden');
      }

      if (!panel.classList.contains('hidden') && currentMasterData) {
        const w = currentMasterData.weather || currentMasterData.signals?.weather;
        if (w) {
          const t = document.getElementById("gw-temp");
          const r = document.getElementById("gw-rain-prob");
          const wi = document.getElementById("gw-wind");
          const p = document.getElementById("gw-precip");
          if (t) t.innerText = `${Math.round(w.temperature_c || 27.4)}°C`;
          if (r) r.innerText = `${Math.round(w.rain_probability || 62)}%`;
          if (wi) wi.innerText = `${Math.round(w.wind_speed_kmh || 14)} km/h`;
          if (p) p.innerText = `${(w.precipitation_mm_h || 4.2).toFixed(1)} mm/h`;
        }
      }
    }

    // Selected Map Object Contextual Glass Panel
    function showSelectedObjectPanel(data) {
      const panel = document.getElementById("map-selected-object-panel");
      if (!panel || !data) return;
      const titleEl = document.getElementById("sel-obj-title");
      const occEl = document.getElementById("sel-obj-occ");
      const utilEl = document.getElementById("sel-obj-util");
      const flowEl = document.getElementById("sel-obj-flow");
      const forecastEl = document.getElementById("sel-obj-forecast");
      const btnEl = document.getElementById("sel-obj-action-btn");

      if (titleEl) titleEl.innerText = (data.name || 'Object Details').toUpperCase();
      if (occEl) occEl.innerText = data.occ || '--';
      if (utilEl) utilEl.innerText = data.util || 'Active Telemetry';
      if (flowEl) flowEl.innerText = data.flow || 'Normal Inflow / Outflow';
      if (forecastEl) forecastEl.innerText = data.forecast || 'STABLE';
      if (btnEl) {
        if (data.type === 'camera') {
          btnEl.innerText = "Open CCTV Camera →";
          btnEl.onclick = () => selectCameraFromMap(data.id || 'CAM-01');
        } else if (data.type === 'transit') {
          btnEl.innerText = "Open Fleet Providers →";
          btnEl.onclick = () => switchMainView('providers');
        } else {
          btnEl.innerText = "Open Zone Intelligence →";
          btnEl.onclick = () => switchMainView('zones');
        }
      }
      panel.classList.remove('hidden');
    }

    function closeSelectedObjectPanel() {
      const panel = document.getElementById("map-selected-object-panel");
      if (panel) panel.classList.add('hidden');
    }

    // Floating Digital Twin Simulation Tray
    function toggleSimulationTray() {
      const content = document.getElementById("sim-tray-content");
      const btn = document.getElementById("sim-tray-toggle-btn");
      if (!content) return;
      const isHidden = content.classList.toggle('hidden');
      if (btn) {
        btn.innerHTML = isHidden ? '<span>Expand</span><span>▲</span>' : '<span>Collapse</span><span>▼</span>';
      }
    }

    function onTraySliderChange() {
      const rain = document.getElementById("tray-rain-input")?.value || 18;
      const wind = document.getElementById("tray-wind-input")?.value || 24;
      const dur = document.getElementById("tray-dur-input")?.value || 60;

      const rVal = document.getElementById("tray-rain-val");
      const wVal = document.getElementById("tray-wind-val");
      const dVal = document.getElementById("tray-dur-val");

      if (rVal) rVal.innerText = `${rain} mm/h`;
      if (wVal) wVal.innerText = `${wind} km/h`;
      if (dVal) dVal.innerText = `${dur} min`;
    }

    function setTrayPreset(label, rain, wind, dur) {
      const rInput = document.getElementById("tray-rain-input");
      const wInput = document.getElementById("tray-wind-input");
      const dInput = document.getElementById("tray-dur-input");
      if (rInput) rInput.value = rain;
      if (wInput) wInput.value = wind;
      if (dInput) dInput.value = dur;
      onTraySliderChange();
      showToast(`Counterfactual Preset: ${label} applied`, 'info');
    }

    function resetTraySimulation() {
      setTrayPreset('Baseline', 18, 24, 60);
      closeTrayResultPanel();
    }

    async function runTraySimulation() {
      if (!activeEventId) return;
      const rain = parseFloat(document.getElementById("tray-rain-input")?.value || 18);
      const wind = parseFloat(document.getElementById("tray-wind-input")?.value || 24);
      const dur = parseInt(document.getElementById("tray-dur-input")?.value || 60);

      try {
        const res = await fetch(`${API_BASE}/events/${activeEventId}/digital-twin/simulate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            precipitation_mm_h: rain,
            wind_speed_kmh: wind,
            scenario_name: rain > 30 ? "heavy_rain" : "moderate_rain"
          })
        });
        if (res.ok) {
          const data = await res.json();
          renderTraySimulationResult(data.digital_twin, rain, wind, dur);
          showToast(`Counterfactual Twin computed: ${data.digital_twin?.scenario_label || 'Scenario'}`, 'success');
        }
      } catch (err) {
        showToast(`Simulation error: ${err.message}`, 'danger');
      }
    }

    function renderTraySimulationResult(dt, rain, wind, dur) {
      const panel = document.getElementById("map-dt-result-panel");
      if (!panel || !dt) return;

      const deltaCrowd = dt.crowd_delta || 1420;
      const simCrowd = dt.simulated_total_crowd || 22790;
      const baseCrowd = dt.baseline_total_crowd || 21370;
      const gap = dt.transport_capacity_gap || 10518;
      const label = dt.scenario_label || `Rainfall ${rain} mm/h · Wind ${wind} km/h`;

      panel.innerHTML = `
        <div class="flex items-center justify-between border-b border-white/60 pb-2">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600 animate-pulse"></span>
            <span class="font-bold text-xs text-slate-900 tracking-tight uppercase">${label}</span>
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">COUNTERFACTUAL</span>
          </div>
          <button onclick="closeTrayResultPanel()" class="text-slate-400 hover:text-slate-700 text-xs font-bold p-1">✕</button>
        </div>
        <div class="grid grid-cols-3 gap-2 text-xs">
          <div class="p-2 rounded-lg bg-white/50 border border-white/60">
            <div class="text-[10px] text-slate-500 font-bold uppercase">Delta Crowd</div>
            <div class="text-base font-bold font-num text-amber-700">+${Number(deltaCrowd).toLocaleString()}</div>
            <div class="text-[10px] text-slate-500">${Number(baseCrowd).toLocaleString()} → ${Number(simCrowd).toLocaleString()}</div>
          </div>
          <div class="p-2 rounded-lg bg-white/50 border border-white/60">
            <div class="text-[10px] text-slate-500 font-bold uppercase">Transit Gap</div>
            <div class="text-base font-bold font-num text-rose-700">-${Number(gap).toLocaleString()}</div>
            <div class="text-[10px] text-slate-500">${dt.capacity_gap_status || 'CAPACITY DEFICIT'}</div>
          </div>
          <div class="p-2 rounded-lg bg-white/50 border border-white/60">
            <div class="text-[10px] text-slate-500 font-bold uppercase">Sim Duration</div>
            <div class="text-base font-bold font-num text-slate-900">${dur} min</div>
            <div class="text-[10px] text-slate-500">Continuous Stress</div>
          </div>
        </div>
        <div class="p-2 rounded-lg bg-white/40 border border-white/50 space-y-1">
          <div class="text-[10px] font-bold uppercase text-slate-600">Cascade Chain Evaluation</div>
          ${(dt.cascade_chain || []).slice(0, 3).map(c => `
            <div class="flex items-center justify-between text-[11px]">
              <span class="font-medium text-slate-700">${c.step}: ${c.detail}</span>
              <span class="text-[9px] font-bold px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700">${c.status}</span>
            </div>
          `).join('')}
        </div>
        <div class="flex items-center justify-between pt-1">
          <button onclick="closeTrayResultPanel()" class="px-2.5 py-1 text-xs text-slate-500 hover:text-slate-800 font-semibold">Dismiss</button>
          <button onclick="switchMainView('twin'); closeTrayResultPanel();" class="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-xs transition">
            Open Full Digital Twin View →
          </button>
        </div>
      `;
      panel.classList.remove('hidden');
    }

    function closeTrayResultPanel() {
      const panel = document.getElementById("map-dt-result-panel");
      if (panel) panel.classList.add('hidden');
    }

    // Provider Pulse Popover
    function toggleProviderPulsePopover(forceState) {
      const popover = document.getElementById("provider-pulse-popover");
      if (!popover) return;
      if (typeof forceState === 'boolean') {
        if (forceState) popover.classList.remove('hidden');
        else popover.classList.add('hidden');
      } else {
        popover.classList.toggle('hidden');
      }
    }

    // Closed-Loop Incident Simulation Modal Stepper
    let simSteps = [
      { id: 1, title: "1. Detect Concourse Inflow Surge", status: "pending" },
      { id: 2, title: "2. Evaluate Egress Bottleneck Risk", status: "pending" },
      { id: 3, title: "3. Propose Transit Bus Reallocation", status: "pending" },
      { id: 4, title: "4. Human Operator Sign-off", status: "pending" },
      { id: 5, title: "5. Dispatch via Meta WhatsApp Cloud API", status: "pending" },
      { id: 6, title: "6. Provider Confirmation (+120 Seats)", status: "pending" }
    ];

    function launchFullSimulation() {
      const modal = document.getElementById("simulation-modal");
      if (!modal) return;
      modal.classList.remove("hidden");
      renderSimulationStepsUI();
      runNextSimulationSteps();
    }

    function closeSimulationModal() {
      const modal = document.getElementById("simulation-modal");
      if (modal) modal.classList.add("hidden");
    }

    function renderSimulationStepsUI() {
      const container = document.getElementById("sim-steps-container");
      if (!container) return;
      container.innerHTML = "";
      simSteps.forEach(s => {
        const div = document.createElement("div");
        div.className = `p-2.5 rounded-lg border text-xs flex items-center justify-between ${
          s.status === 'done' ? 'bg-emerald-50 border-emerald-200 text-emerald-900 font-bold' :
          s.status === 'running' ? 'bg-indigo-50 border-indigo-200 text-indigo-900 font-bold animate-pulse' :
          'bg-slate-50 border-slate-200 text-slate-500 font-semibold'
        }`;
        div.innerHTML = `
          <span class="font-bold">${s.title}</span>
          <span class="text-[10px] font-bold uppercase">${s.status}</span>
        `;
        container.appendChild(div);
      });
    }

    function setSimStepStatus(id, status) {
      const s = simSteps.find(x => x.id === id);
      if (s) s.status = status;
      renderSimulationStepsUI();
    }

    async function runNextSimulationSteps() {
      setSimStepStatus(1, 'running');
      await new Promise(r => setTimeout(r, 700));
      setSimStepStatus(1, 'done');

      setSimStepStatus(2, 'running');
      await new Promise(r => setTimeout(r, 700));
      setSimStepStatus(2, 'done');

      setSimStepStatus(3, 'running');
      await new Promise(r => setTimeout(r, 700));
      setSimStepStatus(3, 'done');

      setSimStepStatus(4, 'running');
      const banner = document.getElementById("sim-approval-banner");
      if (banner) banner.classList.remove("hidden");
    }

    async function onSimOperatorApprove() {
      const banner = document.getElementById("sim-approval-banner");
      if (banner) banner.classList.add("hidden");
      setSimStepStatus(4, 'done');

      setSimStepStatus(5, 'running');
      await dispatchOperationalCapacityPoll();
      setSimStepStatus(5, 'done');

      setSimStepStatus(6, 'running');
      await new Promise(r => setTimeout(r, 900));
      await sendQuickOperationalResponse("+120 seats");
      setSimStepStatus(6, 'done');

      const card = document.getElementById("sim-result-card");
      if (card) card.classList.remove("hidden");
      showToast("Full closed-loop incident simulation complete: 100% verified!", "success");
    }

    function onSimOperatorReject() {
      closeSimulationModal();
      showToast("Simulation dismissed by operator", "info");
    }

    // Modal Helpers
    function openIngestionModal() {
      const m = document.getElementById("ingestion-modal");
      if (m) m.classList.remove("hidden");
    }
    function closeIngestionModal() {
      const m = document.getElementById("ingestion-modal");
      if (m) m.classList.add("hidden");
    }
    function toggleOperationsMenu() {
      const menu = document.getElementById("operations-menu");
      if (menu) menu.classList.toggle("hidden");
    }
    function refreshWeatherOnly() {
      refreshDashboardState();
      showToast("Weather telemetry refreshed", "info");
    }
    function setTimelineClock(clock) {}

    // Seed Demo
    async function triggerDemoSetup() {
      toggleOperationsMenu();
      try {
        const res = await fetch(`${API_BASE}/demo/seed-mumbai`, { method: "POST" });
        if (res.ok) {
          showToast("Wankhede Stadium Mumbai venue dataset seeded successfully!", "success");
          await fetchEvents();
        }
      } catch (e) {
        showToast(`Setup error: ${e.message}`, "danger");
      }
    }

    async function triggerResetDemo() {
      try {
        const res = await fetch(`${API_BASE}/demo/reset`, { method: "POST" });
        if (res.ok) {
          showToast("Demo telemetry reset to baseline", "info");
          await fetchEvents();
        }
      } catch (e) {
        showToast(`Reset error: ${e.message}`, "danger");
      }
    }

    async function triggerSurgeSimulation() {
      await launchFullSimulation();
    }
    async function triggerRunIntelligence() {
      await refreshDashboardState();
    }
  </script>
</body>
</html>
'''

def build():
  target_path = os.path.join(os.path.dirname(__file__), "app", "static", "index.html")
  with open(target_path, "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)
  print(f"Successfully generated redesigned UI at: {target_path}")
  print(f"File size: {len(HTML_CONTENT)} bytes")

if __name__ == "__main__":
  build()
