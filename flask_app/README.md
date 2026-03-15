# 🦝 Raccoon Browser - Web Edition

> *Digging through the web so you don't have to.*

A privacy-focused web browser built with Flask. No Electron - pure Python.

## Features

- 🔍 **Private Search** - SearXNG meta-search + DuckDuckGo HTML (real web results)
- 🎭 **Full Render Mode** - Playwright-powered rendering for JavaScript-heavy sites (GitHub, Twitter, etc.)
- ⚠️ **Site Compatibility Detection** - Auto-detects React/Angular/Vue SPAs and warns users
- 🦝 **Proxy Browsing** - URL rewriting for inline browsing with privacy
- 🛡️ **Tracker Blocking** - Blocks analytics, ads, and social trackers
- 📑 **Session Management** - Persistent sessions with cookies and history (optional)
- 💉 **JavaScript Injection** - Custom JS for enhanced functionality
- 🌙 **Dark Theme** - Matrix-style, raccoon-approved

## Quick Start

```bash
# Install dependencies
pip install -r requirements_advanced.txt

# Install Playwright browsers
playwright install chromium

# Run the browser
python3 app.py

# Access at http://localhost:5555
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/api/health` | GET | Health check |
| `/api/search` | POST | Search query |
| `/api/site-info` | POST | Get site compatibility info |
| `/api/full-render` | POST | Full Playwright rendering |
| `/browse` | GET | Proxy browse a URL |
| `/api/check-trackers` | POST | Check URL for trackers |
| `/api/suggestions` | GET | Search suggestions |

## Site Compatibility

The browser automatically detects JavaScript-heavy sites and shows a compatibility warning:

**JS-Heavy Sites Detected:**
- github.com
- twitter.com / x.com
- facebook.com
- instagram.com
- linkedin.com
- reddit.com
- youtube.com
- gmail.com
- docs.google.com
- notion.so
- figma.com

**For these sites, you have 3 options:**
1. **Full Render** - Uses Playwright for complete JavaScript support (recommended)
2. **Proxy Mode** - Basic HTML/CSS only (may not work properly)
3. **Open in Browser** - Launch in your native browser

## Tech Stack

- **Flask** - Web framework
- **Playwright** - Headless browser automation
- **BeautifulSoup4** - HTML parsing
- **Requests** - HTTP client
- **SQLite** - Session storage (optional)

## Configuration

Edit `app.py` to customize:
- `SEARXNG_INSTANCES` - Meta-search engines
- `TRACKER_DOMAINS` - Blocked tracker domains
- `AD_DOMAINS` - Blocked ad networks
- `JS_HEAVY_SITES` - Sites requiring full render mode

## Privacy Features

- No telemetry
- Blocks Google Analytics, Facebook Pixel, etc.
- Blocks ad networks (Taboola, Outbrain, etc.)
- Blocks social trackers
- Prioritizes privacy-friendly sites in search results

## Files

```
flask_app/
├── app.py                    # Main Flask application
├── playwright_renderer.py    # Playwright full rendering
├── session_manager.py        # Session/cookie management
├── js_injector.py            # JavaScript injection
├── browser_engine.py         # Legacy browser engine
├── requirements_advanced.txt # Python dependencies
├── static/
│   ├── css/style.css        # Dark theme styles
│   └── js/app.js            # Frontend logic
└── templates/
    └── index.html           # Main UI
```

## License

MIT - Built by 🦝 for the CyberRaccoonTeam
