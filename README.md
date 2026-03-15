# 🦝 Raccoon Browser

> *Digging through the web so you don't have to.*

A privacy-focused browser built on Firefox - a real browser fork with full Firefox engine power.

## Features

- 🦝 **Privacy First** - Firefox-based with enhanced privacy defaults
- 🔍 **Raccoon Search** - Meta-search via SearXNG with custom ranking
- 🗑️ **Trash Can Cache** - Visual cache management with one-click clearing
- ⚡ **Fast** - Full Firefox engine performance
- 🌙 **Dark Theme** - Easy on the eyes, raccoon-approved
- 🔒 **Real Browser** - Not a web wrapper - actual Firefox fork with full rendering engine

## Quick Start

### Option 1: Pre-built Binary (Recommended)

Download the latest release from [GitHub Releases](https://github.com/CyberRaccoonTeam/raccoon-browser/releases):

```bash
# Download latest release (replace VERSION with actual version)
wget https://github.com/CyberRaccoonTeam/raccoon-browser/releases/latest/download/raccoon-browser-linux-x64.tar.gz

# Extract
tar -xzf raccoon-browser-linux-x64.tar.gz

# Run
./bin/raccoon-browser
```

**System Requirements:**
- Linux (Ubuntu/Debian recommended)
- 8GB+ RAM
- GTK3 dependencies: `sudo apt install libgtk-3-dev libdbus-1-dev libglib2.0-dev`

### Option 2: Build from Source

For developers and advanced users:

```bash
# 1. Clone repository
git clone https://github.com/CyberRaccoonTeam/raccoon-browser.git
cd raccoon-browser

# 2. Download Firefox source
./scripts/download-source.sh

# 3. Apply Raccoon branding
./scripts/apply-branding.sh

# 4. Configure build
cp mozconfig.example mozconfig

# 5. Build (takes 1-3 hours)
cd firefox-source
./mach build

# 6. Run
./mach run
```

See [BUILD.md](BUILD.md) for detailed build instructions.

## Tech Stack

- **Firefox** - Full browser engine (not Electron!)
- **SearXNG** - Meta-search engine (no tracking)
- **SQLite** - Local-only data storage
- **mozconfig** - Custom Firefox build configuration

## Project Structure

```
raccoon-browser/
├── firefox-source/       # Firefox browser fork source code
│   ├── browser/          # Browser-specific code
│   ├── dom/              # DOM implementation
│   ├── layout/           # Rendering engine
│   ├── js/               # JavaScript engine
│   └── mozconfig         # Build configuration
├── .git/                 # Version control
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── ROADMAP.md            # Development roadmap
```

## Privacy Features

- ✅ Firefox privacy defaults (no telemetry)
- ✅ Built-in tracker blocking
- ✅ HTTPS-only mode
- ✅ Local-only bookmarks & history
- ✅ No data collection
- ✅ Anonymous search (via SearXNG)

## Why Firefox Fork?

The old Electron/web version was **not a real browser** - just a Flask web app wrapper. This is now a **genuine Firefox fork** with:

- Full rendering engine
- Complete web standards support
- Real browser security model
- Extension compatibility
- Better performance

## License

MIT - Use it, fork it, make it yours.

---

*Built with 🦝 by Cyber & Raccoon*
