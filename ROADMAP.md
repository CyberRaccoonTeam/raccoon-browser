# 🦝 Raccoon Browser - Project Roadmap

**Mission:** Build a privacy-focused, sleek browser with its own non-tracking search engine.

**Core Values:** Speed • Privacy • Sovereignty • Wit

---

## Phase 1: Foundation (Week 1-2)

### 1.1 Core Browser Shell
- [ ] Electron.js setup with security hardening
- [ ] Basic browser window with navigation
- [ ] Tab management system
- [ ] URL bar with smart suggestions

### 1.2 Search Engine Integration
- [ ] Meta-search backend (SearXNG API wrapper)
- [ ] Custom ranking algorithm
- [ ] Result caching with "trash can" metaphor
- [ ] Zero-tracking search queries

### 1.3 UI Framework
- [ ] Dark theme foundation
- [ ] Raccoon-inspired design system
- [ ] Icon set and branding
- [ ] Responsive layout components

---

## Phase 2: Privacy Features (Week 3-4)

### 2.1 Tracking Protection
- [ ] Built-in ad blocker (uBlock Origin integration)
- [ ] Tracker prevention (Disconnect list)
- [ ] Fingerprinting protection
- [ ] HTTPS-only mode

### 2.2 Data Sovereignty
- [ ] Local-only bookmarks and history
- [ ] Encrypted profile storage
- [ ] "Incognito+" mode (no disk writes)
- [ ] Cookie jar management

---

## Phase 3: Unique Features (Week 5-6)

### 3.1 "Trash Can" Cache System
- [ ] Visual cache management with trash metaphor
- [ ] One-click cache dump
- [ ] Scheduled auto-cleaning
- [ ] Per-site cache control

### 3.2 Raccoon Assistant
- [ ] Built-in AI assistant (local Ollama integration)
- [ ] Page summarization
- [ ] Privacy score for visited sites
- [ ] Smart content extraction

### 3.3 Developer Tools
- [ ] Built-in network inspector
- [ ] Privacy audit panel
- [ ] Request blocker visualizer

---

## Phase 4: Polish & Distribution (Week 7-8)

### 4.1 Performance
- [ ] Memory optimization
- [ ] Cold start < 2 seconds
- [ ] Smooth scrolling and animations

### 4.2 Distribution
- [ ] Windows installer
- [ ] macOS DMG
- [ ] Linux AppImage/deb
- [ ] Auto-update mechanism

### 4.3 Branding
- [ ] Custom protocol (raccoon://)
- [ ] Welcome page with onboarding
- [ ] About page with raccoon personality

---

## Tech Stack Decision

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Desktop Framework** | Electron.js | Cross-platform, mature ecosystem |
| **Search Backend** | SearXNG API | Meta-search, no tracking, self-hostable |
| **UI Framework** | React + TypeScript | Type safety, component reusability |
| **Styling** | Tailwind CSS + Custom dark theme | Rapid development, consistent design |
| **State Management** | Zustand | Lightweight, no boilerplate |
| **Storage** | SQLite (better-sqlite3) | Local, fast, encrypted option |
| **AI Integration** | Ollama (local) | Privacy-first, no external calls |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Raccoon Browser                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Browser   │  │   Search    │  │  Assistant  │     │
│  │   Shell     │  │   Engine    │  │   (AI)      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │              Privacy Layer                       │   │
│  │  • Ad Blocker • Tracker Prevention • HTTPS      │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │              Storage Layer                       │   │
│  │  • SQLite DB • Encrypted Profiles • Cache       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Search Engine Logic: Raccoon Search

### Query Flow (Zero-Tracking)

```
User Query → Local Cache Check → SearXNG API → Custom Ranking → Results
                    ↓                                      ↓
              Return cached                          No logs
              (instant)                              No tracking
                                                      Anonymous proxy
```

### Custom Ranking Algorithm

```javascript
function raccoonRank(results, query) {
  return results.map(result => {
    let score = 0;
    
    // Privacy bonus (HTTPS, no trackers)
    score += result.https ? 10 : 0;
    score += result.trackerCount === 0 ? 15 : -result.trackerCount * 2;
    
    // Relevance signals
    score += result.titleMatch * 5;
    score += result.domainAuthority * 0.5;
    
    // User preferences (local only)
    score += getLocalPreference(result.domain);
    
    return { ...result, raccoonScore: score };
  }).sort((a, b) => b.raccoonScore - a.raccoonScore);
}
```

---

## First Milestone Target

**Goal:** Basic browser window with URL bar and Raccoon Search working.

**Success Criteria:**
1. Window opens and loads pages
2. URL bar shows current URL
3. Search query returns results from SearXNG
4. Zero external tracking calls

---

*Let's dig through the trash and find the good stuff. 🦝*