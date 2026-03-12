# 🦝 Raccoon Browser - Web Version

> Use Raccoon Browser from any device. No installation required.

## What Is This?

A web-based version of Raccoon Browser. Privacy-focused search and browsing without installing anything.

**Differences from Desktop Version:**
- Runs in your browser (no Electron)
- Accessible from any device
- Simplified feature set
- No local storage (except bookmarks)

## Features

- 🔍 **Private Search** — DuckDuckGo + SearXNG meta-search
- 🛡️ **Tracker Blocking** — Blocks known trackers
- 📑 **Bookmarks** — Save your favorite sites
- 🌙 **Dark Theme** — Raccoon-approved
- 📱 **Mobile Friendly** — Works on any device

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Access at: http://localhost:5558

## Tech Stack

- Flask (Python)
- SQLite (bookmarks, history)
- Vanilla JS (no frameworks)
- Dark CSS theme

## Project Structure

```
web-version/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/style.css   # Dark theme
│   └── js/app.js       # Frontend logic
├── templates/
│   └── index.html      # Main UI
└── utils/
    ├── search.py       # Search engine
    └── blockers.py     # Tracker blocking
```

## Why Web Version?

Some users can't install Python or Electron. This version runs on a server and anyone can use it through their browser.

---

Built by 🦝 Raccoon