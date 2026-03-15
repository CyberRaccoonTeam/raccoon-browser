# 🦝 Raccoon Browser - Build Instructions

## Prerequisites

**System Requirements:**
- Linux (Ubuntu/Debian recommended)
- 8GB+ RAM (16GB recommended)
- 50GB+ free disk space
- 4+ CPU cores

**Dependencies:**
```bash
# Ubuntu/Debian
sudo apt install build-essential python3 mercurial rustc cargo \
  libgtk-3-dev libdbus-1-dev libglib2.0-dev libxt-dev \
  libasound2-dev libpulse-dev libevent-dev libpixman-1-dev \
  libdrm-dev libgbm-dev libegl1-mesa-dev libgles2-mesa-dev
```

---

## Build Process

### Option 1: Build from Source (Recommended)

```bash
# 1. Clone the build instructions repo
git clone https://github.com/CyberRaccoonTeam/raccoon-browser.git
cd raccoon-browser

# 2. Download Firefox source (the build script handles this)
./scripts/download-source.sh

# 3. Apply Raccoon branding patches
./scripts/apply-branding.sh

# 4. Configure build (mozconfig)
cp mozconfig.example mozconfig

# 5. Build (takes 1-3 hours on modern hardware)
./mach build

# 6. Run
./mach run
```

### Option 2: Use Pre-built Binaries (Recommended)

Download from [GitHub Releases](https://github.com/CyberRaccoonTeam/raccoon-browser/releases):

```bash
# Download latest release
wget https://github.com/CyberRaccoonTeam/raccoon-browser/releases/latest/download/raccoon-browser-linux-x64.tar.gz

# Extract and run
tar -xzf raccoon-browser-linux-x64.tar.gz
./bin/raccoon-browser
```

**Benefits:**
- ✅ No 1-3 hour build time
- ✅ No 50GB disk space required
- ✅ No dependency installation needed
- ✅ Ready to run immediately

---

## Mozconfig Example

```mozconfig
# Raccoon Browser mozconfig

ac_add_options --branding=browser/branding/raccoon
ac_add_options --enable-release
ac_add_options --enable-optimize

# Disable telemetry
ac_add_options --disable-telemetry
ac_add_options --disable-necko-wifi

# Enable privacy features
ac_add_options --enable-private-browsing
ac_add_options --disable-crashreporter

# Build configuration
mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-@CONFIG_GUESS@
mk_add_options MOZ_MAKE_FLAGS="-j$(nproc)"
```

---

## Build Time Estimates

| Hardware | Build Time |
|----------|------------|
| 4 cores, 8GB RAM | 2-3 hours |
| 8 cores, 16GB RAM | 1-2 hours |
| 16 cores, 32GB RAM | 30-60 minutes |

---

## Troubleshooting

### Build fails with "out of memory"
- Add swap space: `sudo fallocate -l 8G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
- Reduce parallel jobs: `mk_add_options MOZ_MAKE_FLAGS="-j4"`

### Missing dependencies
- Run: `sudo apt build-dep firefox`

### Branding not applied
- Ensure `browser/branding/raccoon/` directory exists
- Check mozconfig has correct branding path

---

## Post-Build

After successful build, the browser binary will be in:
```
obj-*/dist/bin/raccoon-browser
```

You can create a desktop shortcut or add to PATH for easy access.

---

## For Developers

To contribute to Raccoon Browser development:
1. Fork the repo
2. Make changes to branding/patches/scripts
3. Test build locally
4. Submit PR

**Note:** Don't commit firefox-source/ - it's downloaded during build.

---

_Build with 🦝 patience_
