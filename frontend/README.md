# EVENTOS — Netlify Frontend Deployment Package

This package contains the complete, production-ready static build of the **EVENTOS Event Operations Control Tower** dashboard configured for instant deployment to [Netlify](https://www.netlify.com/).

---

## 🚀 Quick Deployment Options

### Method 1: Netlify Drop (Zero Configuration — Drag & Drop)
1. Go to **[app.netlify.com/drop](https://app.netlify.com/drop)** in your web browser.
2. Drag and drop the `eventos-netlify-deploy.zip` file directly into the drop zone.
3. Your control tower dashboard is deployed live on a public Netlify URL within seconds!

### Method 2: Netlify CLI
If you have `netlify-cli` installed:
```bash
cd frontend
netlify deploy --prod --dir=.
```

---

## 🔗 Connecting to your FastAPI Backend

Once deployed on Netlify, the dashboard can communicate with your EventOS backend server in two ways:

### Option A: In-Dashboard Config (Recommended & Instant)
1. Open your deployed Netlify website in the browser.
2. In the top navigation bar, click the **`API`** badge (or open the top-right menu `⋮` and select **`Backend API Host`**).
3. Enter your backend URL:
   - Example: `https://your-backend.onrender.com`
   - Example: `https://eventos-api.up.railway.app`
   - Example (local dev testing): `https://your-tunnel.ngrok-free.app`
4. Click **`Test Ping`** to verify connectivity, then click **`Save & Reload`**.
5. Your target backend URL is saved in `localStorage` and will persist across sessions.

### Option B: Netlify Reverse Proxy (`_redirects` / `netlify.toml`)
If you want Netlify to route all `/api/*` traffic transparently:
1. Open `_redirects` or `netlify.toml` in this folder before zipping or deploying.
2. Uncomment the proxy rule and update it with your backend URL:
   ```text
   /api/*  https://your-eventos-backend.onrender.com/api/:splat  200!
   ```
3. Re-deploy. All API requests made to `/api/v1/...` will now be forwarded by Netlify to your live backend.

---

## 📦 What's Included in This Package
- `index.html`: Complete high-fidelity control tower dashboard with Leaflet GIS cartography, CCTV playback, Digital Twin visualization, NuGen AI orchestrator, and real-time telemetry.
- `_redirects`: Netlify routing rules and API proxy configuration.
- `netlify.toml`: Header policies, caching strategies, and SPA redirect rules.
- `cctv/`: Recorded surveillance camera feeds (`cam01_entrance.mp4`, `cam02_concourse.mp4`, `cam03_gate.mp4`) used for computer vision testing.
