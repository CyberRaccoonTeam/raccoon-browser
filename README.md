# 🦝 Raccoon Browser

> *Digging through the web so you don't have to.*

A privacy-focused, sleek browser with its own non-tracking search engine.

## Features

- 🦝 **Privacy First** - Built-in tracker blocking, no telemetry
- 🔍 **Raccoon Search** - Meta-search via SearXNG with custom ranking
- 🗑️ **Trash Can Cache** - Visual cache management with one-click clearing
- ⚡ **Fast** - Minimal footprint, quick startup
- 🌙 **Dark Theme** - Easy on the eyes, raccoon-approved

## Quick Start

```bash
# Install dependencies
npm install

# Run in development
npm run dev

# Build for production
npm run build
```

## Tech Stack

- **Electron.js** - Cross-platform desktop framework
- **SearXNG** - Meta-search engine (no tracking)
- **SQLite** - Local-only data storage
- **Tailwind CSS** - Styling (coming soon)

## Project Structure

```
raccoon-browser/
├── src/
│   ├── main/           # Electron main process
│   │   ├── main.js     # Entry point
│   │   └── preload.js  # Secure bridge
│   ├── renderer/       # UI (HTML/CSS/JS)
│   │   ├── index.html
│   │   ├── styles/
│   │   └── scripts/
│   └── search/         # Search engine logic (coming)
├── assets/             # Icons, images
└── tests/              # Test files
```

## Privacy Features

- ✅ Built-in tracker blocking
- ✅ HTTPS-only mode
- ✅ Local-only bookmarks & history
- ✅ No telemetry or data collection
- ✅ Anonymous search (via SearXNG)

## License

MIT - Use it, fork it, make it yours.

---

*Built with 🦝 by Cyber & Raccoon*