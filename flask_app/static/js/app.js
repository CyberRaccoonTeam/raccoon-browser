/**
 * 🦝 Raccoon Browser - Flask Frontend
 * Pure Flask backend, no Electron
 * Phase 1: Tab Management + Search Suggestions
 */

// State
const state = {
    tabs: [],
    activeTabId: null,
    tabCounter: 0,
};

// DOM Elements
const elements = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Cache elements
    elements.tabsContainer = document.querySelector('.tabs');
    elements.newTabBtn = document.getElementById('new-tab');
    elements.urlInput = document.getElementById('url-input');
    elements.searchInput = document.getElementById('search-input');
    elements.searchBtn = document.getElementById('search-btn');
    elements.btnBack = document.getElementById('btn-back');
    elements.btnForward = document.getElementById('btn-forward');
    elements.btnRefresh = document.getElementById('btn-refresh');
    elements.btnHome = document.getElementById('btn-home');
    elements.btnTrash = document.getElementById('btn-trash');
    elements.welcomePage = document.getElementById('welcome-page');
    elements.resultsPage = document.getElementById('results-page');
    elements.loadingPage = document.getElementById('loading-page');
    elements.resultsList = document.getElementById('results-list');
    elements.resultsTitle = document.getElementById('results-title');
    elements.resultsCount = document.getElementById('results-count');
    elements.statusText = document.getElementById('status-text');
    elements.privacyBadge = document.getElementById('privacy-badge');
    
    // Create suggestions dropdown
    createSuggestionsDropdown();
    
    // Create initial tab
    createTab();
    
    setupEventListeners();
    setupKeyboardShortcuts();
    console.log('🦝 Raccoon Browser ready - Phase 1.2');
});

function setupEventListeners() {
    // Tab management
    elements.newTabBtn.addEventListener('click', createTab);
    
    // Search
    elements.searchBtn.addEventListener('click', () => performSearch());
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            hideSuggestions();
            performSearch();
        }
    });
    
    // Search suggestions
    elements.searchInput.addEventListener('input', debounce(fetchSuggestions, 200));
    elements.searchInput.addEventListener('focus', () => {
        if (elements.searchInput.value.length > 1) fetchSuggestions();
    });
    
    // URL bar with suggestions
    elements.urlInput.addEventListener('input', debounce(fetchSuggestions, 200));
    elements.urlInput.addEventListener('focus', () => {
        if (elements.urlInput.value.length > 1) fetchSuggestions();
    });
    elements.urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            hideSuggestions();
            handleUrlInput();
        }
    });
    
    // Navigation
    elements.btnBack.addEventListener('click', goBack);
    elements.btnForward.addEventListener('click', goForward);
    elements.btnRefresh.addEventListener('click', refresh);
    elements.btnHome.addEventListener('click', goHome);
    elements.btnTrash.addEventListener('click', clearHistory);
    
    // Quick links - browse within Raccoon
    document.querySelectorAll('.quick-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const url = link.dataset.url;
            navigateTo(url);
        });
    });
    
    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.url-bar') && !e.target.closest('.search-box') && !e.target.closest('.suggestions-dropdown')) {
            hideSuggestions();
        }
    });
    
    // Bookmarks
    const btnBookmark = document.getElementById('btn-bookmark');
    const btnBookmarks = document.getElementById('btn-bookmarks');
    if (btnBookmark) btnBookmark.addEventListener('click', toggleBookmark);
    if (btnBookmarks) btnBookmarks.addEventListener('click', toggleBookmarksPanel);
    
    // Privacy badge
    elements.privacyBadge.addEventListener('click', togglePrivacyPanel);
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const isInputFocused = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);
        
        // Ctrl/Cmd + T: New Tab
        if ((e.ctrlKey || e.metaKey) && e.key === 't') {
            e.preventDefault();
            createTab();
            elements.searchInput.focus();
        }
        
        // Ctrl/Cmd + W: Close Tab
        if ((e.ctrlKey || e.metaKey) && e.key === 'w') {
            e.preventDefault();
            closeTab(state.activeTabId);
        }
        
        // Ctrl/Cmd + L: Focus URL Bar
        if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
            e.preventDefault();
            elements.urlInput.focus();
            elements.urlInput.select();
        }
        
        // Ctrl/Cmd + R / F5: Refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r' || e.key === 'F5') {
            e.preventDefault();
            refresh();
        }
        
        // Alt + Home: Go Home
        if (e.altKey && e.key === 'Home') {
            e.preventDefault();
            goHome();
        }
        
        // Alt + Left: Back
        if (e.altKey && e.key === 'ArrowLeft') {
            e.preventDefault();
            goBack();
        }
        
        // Alt + Right: Forward
        if (e.altKey && e.key === 'ArrowRight') {
            e.preventDefault();
            goForward();
        }
        
        // Escape: Close suggestions / modal / Go home
        if (e.key === 'Escape') {
            const modal = document.getElementById('shortcuts-modal');
            if (modal?.classList.contains('active')) {
                closeShortcutsModal();
                return;
            }
            hideSuggestions();
            if (!isInputFocused) {
                goHome();
            }
        }
        
        // Ctrl/Cmd + Tab: Next Tab
        if ((e.ctrlKey || e.metaKey) && e.key === 'Tab') {
            e.preventDefault();
            cycleTab(e.shiftKey ? -1 : 1);
        }
        
        // Ctrl/Cmd + 1-9: Switch to tab by index
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '9') {
            e.preventDefault();
            const index = parseInt(e.key) - 1;
            if (state.tabs[index]) {
                switchToTab(state.tabs[index].id);
            }
        }
        
        // Ctrl/Cmd + /: Show shortcuts
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            openShortcutsModal();
        }
    });
}

function cycleTab(direction) {
    const currentIndex = state.tabs.findIndex(t => t.id === state.activeTabId);
    let newIndex = currentIndex + direction;
    
    if (newIndex < 0) newIndex = state.tabs.length - 1;
    if (newIndex >= state.tabs.length) newIndex = 0;
    
    switchToTab(state.tabs[newIndex].id);
}

// ============================================================================
// Tab Management
// ============================================================================

function createTab(url = null, title = 'New Tab') {
    const tabId = ++state.tabCounter;
    const tab = {
        id: tabId,
        title: title,
        url: url,
        history: [],
        historyIndex: -1,
        searchResults: [],
    };
    
    state.tabs.push(tab);
    renderTabs();
    switchToTab(tabId);
    
    if (url) {
        navigateTo(url);
    }
    
    return tabId;
}

function switchToTab(tabId) {
    state.activeTabId = tabId;
    renderTabs();
    
    const tab = getActiveTab();
    if (tab) {
        elements.urlInput.value = tab.url || '';
        
        if (tab.searchResults.length > 0) {
            displayResults({ 
                query: tab.title, 
                results: tab.searchResults, 
                total: tab.searchResults.length, 
                instance: 'Cache' 
            });
        } else if (tab.url) {
            showPage('loading');
        } else {
            showPage('welcome');
        }
    }
}

function closeTab(tabId, event) {
    if (event) event.stopPropagation();
    
    const index = state.tabs.findIndex(t => t.id === tabId);
    if (index === -1) return;
    
    state.tabs.splice(index, 1);
    
    if (state.tabs.length === 0) {
        createTab();
    } else if (state.activeTabId === tabId) {
        const newIndex = Math.min(index, state.tabs.length - 1);
        switchToTab(state.tabs[newIndex].id);
    }
    
    renderTabs();
}

function getActiveTab() {
    return state.tabs.find(t => t.id === state.activeTabId);
}

function renderTabs() {
    elements.tabsContainer.innerHTML = state.tabs.map(tab => `
        <div class="tab ${tab.id === state.activeTabId ? 'active' : ''}" data-tab-id="${tab.id}">
            <span class="tab-icon">🦝</span>
            <span class="tab-title">${escapeHtml(tab.title)}</span>
            ${state.tabs.length > 1 ? '<button class="tab-close" onclick="closeTab(' + tab.id + ', event)">×</button>' : ''}
        </div>
    `).join('');
    
    // Add click handlers
    document.querySelectorAll('.tab').forEach(tabEl => {
        tabEl.addEventListener('click', () => {
            const tabId = parseInt(tabEl.dataset.tabId);
            switchToTab(tabId);
        });
    });
}

function updateActiveTab(updates) {
    const tab = getActiveTab();
    if (tab) {
        Object.assign(tab, updates);
        renderTabs();
    }
}

// ============================================================================
// Search Suggestions
// ============================================================================

function createSuggestionsDropdown() {
    const dropdown = document.createElement('div');
    dropdown.className = 'suggestions-dropdown';
    dropdown.id = 'suggestions-dropdown';
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--raccoon-gray);
        border: 1px solid #333;
        border-radius: 8px;
        margin-top: 4px;
        max-height: 300px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
    `;
    
    // Add to both url-bar and search-box containers
    const urlBar = document.querySelector('.url-bar');
    urlBar.style.position = 'relative';
    urlBar.appendChild(dropdown.cloneNode(true));
    
    const searchBox = document.querySelector('.search-box');
    if (searchBox) {
        searchBox.style.position = 'relative';
        searchBox.appendChild(dropdown.cloneNode(true));
    }
}

async function fetchSuggestions() {
    const query = elements.searchInput.value || elements.urlInput.value;
    if (query.length < 2) {
        hideSuggestions();
        return;
    }
    
    try {
        const response = await fetch(`/api/suggestions?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.suggestions && data.suggestions.length > 0) {
            showSuggestions(data.suggestions);
        } else {
            hideSuggestions();
        }
    } catch (error) {
        console.error('Suggestions error:', error);
    }
}

function showSuggestions(suggestions) {
    const activeInput = document.activeElement;
    const container = activeInput.closest('.url-bar') || activeInput.closest('.search-box');
    const dropdown = container?.querySelector('.suggestions-dropdown');
    
    if (!dropdown) return;
    
    dropdown.innerHTML = suggestions.map((s, i) => `
        <div class="suggestion-item" data-index="${i}">
            <span class="suggestion-icon">🔍</span>
            <span class="suggestion-text">${escapeHtml(s)}</span>
        </div>
    `).join('');
    
    dropdown.style.display = 'block';
    
    // Add click handlers
    dropdown.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            const text = item.querySelector('.suggestion-text').textContent;
            elements.searchInput.value = text;
            elements.urlInput.value = text;
            hideSuggestions();
            performSearch(text);
        });
    });
}

function hideSuggestions() {
    document.querySelectorAll('.suggestions-dropdown').forEach(d => {
        d.style.display = 'none';
    });
}

// ============================================================================
// Navigation
// ============================================================================

function navigateTo(url) {
    window.location.href = '/browse?url=' + encodeURIComponent(url);
}

function showPage(pageName) {
    elements.welcomePage.classList.remove('active');
    elements.resultsPage.classList.remove('active');
    elements.loadingPage.classList.remove('active');
    
    if (pageName === 'welcome') {
        elements.welcomePage.classList.add('active');
    } else if (pageName === 'results') {
        elements.resultsPage.classList.add('active');
    } else if (pageName === 'loading') {
        elements.loadingPage.classList.add('active');
    }
}

async function performSearch(query) {
    query = query || elements.searchInput.value.trim();
    
    if (!query) {
        query = elements.urlInput.value.trim();
    }
    
    if (!query) return;
    
    // Check if it's a URL
    if (query.includes('.') && !query.includes(' ')) {
        navigateTo(query.startsWith('http') ? query : 'https://' + query);
        return;
    }
    
    showPage('loading');
    elements.statusText.textContent = 'Searching...';
    elements.urlInput.value = query;
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.success && data.results.length > 0) {
            // Update active tab
            updateActiveTab({
                title: query,
                url: null,
                searchResults: data.results,
            });
            
            const tab = getActiveTab();
            tab.history.push({ type: 'search', query, results: data.results });
            tab.historyIndex = tab.history.length - 1;
            
            displayResults(data);
        } else {
            showError('No results found');
        }
    } catch (error) {
        showError('Search failed: ' + error.message);
    }
}

function displayResults(data) {
    document.getElementById('results-title').textContent = `Results for "${data.query}"`;
    document.getElementById('results-count').textContent = `${data.total} results via ${data.instance}`;
    
    elements.resultsList.innerHTML = data.results.map((result, index) => `
        <div class="result-item" data-url="${escapeHtml(result.url)}">
            <div class="result-number">${index + 1}</div>
            <div class="result-content">
                <a href="/browse?url=${encodeURIComponent(result.url)}" class="result-title">
                    ${escapeHtml(result.title)}
                </a>
                <p class="result-url">${escapeHtml(result.url)}</p>
                <p class="result-snippet">${escapeHtml(result.content || '')}</p>
                <div class="result-meta">
                    <span class="privacy-score" data-score="${result.raccoon_score}">
                        ${result.raccoon_score >= 140 ? '🔒 Great' : result.raccoon_score >= 120 ? '🛡️ Good' : '⚠️ Caution'}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
    
    // Add click handlers - navigate within Raccoon
    document.querySelectorAll('.result-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.tagName !== 'A') {
                const url = item.dataset.url;
                navigateTo(url);
            }
        });
    });
    
    showPage('results');
    elements.statusText.textContent = `${data.total} results`;
}

function handleUrlInput() {
    const input = elements.urlInput.value.trim();
    
    if (!input) return;
    
    // Search or navigate
    if (input.includes('.') && !input.includes(' ')) {
        // URL - browse within Raccoon
        const url = input.startsWith('http') ? input : 'https://' + input;
        updateActiveTab({ title: url, url: url });
        navigateTo(url);
    } else {
        // Search
        performSearch(input);
    }
}

function goBack() {
    const tab = getActiveTab();
    if (!tab || tab.historyIndex <= 0) return;
    
    tab.historyIndex--;
    const item = tab.history[tab.historyIndex];
    if (item.type === 'search') {
        displayResults({ query: item.query, results: item.results, total: item.results.length, instance: 'History' });
    }
}

function goForward() {
    const tab = getActiveTab();
    if (!tab || tab.historyIndex >= tab.history.length - 1) return;
    
    tab.historyIndex++;
    const item = tab.history[tab.historyIndex];
    if (item.type === 'search') {
        displayResults({ query: item.query, results: item.results, total: item.results.length, instance: 'History' });
    }
}

function refresh() {
    const tab = getActiveTab();
    if (!tab) return;
    
    const item = tab.history[tab.historyIndex];
    if (item && item.type === 'search') {
        performSearch(item.query);
    }
}

function goHome() {
    showPage('welcome');
    elements.urlInput.value = '';
    elements.searchInput.value = '';
    updateActiveTab({ title: 'New Tab', url: null, searchResults: [] });
    elements.statusText.textContent = 'Ready';
}

function clearHistory() {
    const tab = getActiveTab();
    if (tab) {
        tab.history = [];
        tab.historyIndex = -1;
    }
    
    // Animate
    elements.btnTrash.style.transform = 'scale(1.2) rotate(-15deg)';
    setTimeout(() => {
        elements.btnTrash.style.transform = '';
    }, 300);
    
    elements.statusText.textContent = '🗑️ History cleared!';
    setTimeout(() => {
        elements.statusText.textContent = 'Ready';
    }, 2000);
}

function showError(message) {
    showPage('results');
    elements.resultsTitle.textContent = 'Error';
    elements.resultsCount.textContent = '';
    elements.resultsList.innerHTML = `
        <div class="error-message">
            <span class="error-icon">⚠️</span>
            <p>${escapeHtml(message)}</p>
            <button onclick="goHome()" class="btn">Go Home</button>
        </div>
    `;
    elements.statusText.textContent = 'Error';
}

// ============================================================================
// Shortcuts Modal
// ============================================================================

function openShortcutsModal() {
    document.getElementById('shortcuts-modal').classList.add('active');
}

function closeShortcutsModal() {
    document.getElementById('shortcuts-modal').classList.remove('active');
}

// Add event listener for shortcuts button
document.addEventListener('DOMContentLoaded', () => {
    const shortcutsBtn = document.getElementById('btn-shortcuts');
    if (shortcutsBtn) {
        shortcutsBtn.addEventListener('click', openShortcutsModal);
    }
    
    // Close modal on outside click
    document.getElementById('shortcuts-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'shortcuts-modal') {
            closeShortcutsModal();
        }
    });
    
    // Privacy badge click
    elements.privacyBadge?.addEventListener('click', togglePrivacyPanel);
    
    // Close privacy panel on outside click
    document.addEventListener('click', (e) => {
        const panel = document.getElementById('privacy-panel');
        if (panel?.classList.contains('active') && 
            !e.target.closest('.privacy-panel') && 
            !e.target.closest('#privacy-badge')) {
            closePrivacyPanel();
        }
    });
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Privacy Panel
// ============================================================================

function togglePrivacyPanel() {
    const panel = document.getElementById('privacy-panel');
    panel?.classList.toggle('active');
}

function closePrivacyPanel() {
    document.getElementById('privacy-panel')?.classList.remove('active');
}

async function checkPagePrivacy(url) {
    if (!url) return;
    
    try {
        const response = await fetch('/api/check-trackers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (data.success) {
            updatePrivacyUI(data);
        }
    } catch (error) {
        console.error('Privacy check error:', error);
    }
}

function updatePrivacyUI(data) {
    const score = data.privacy_score;
    const badge = elements.privacyBadge;
    
    // Update badge
    badge.className = 'privacy-badge';
    if (score >= 80) {
        badge.textContent = '🔒 Protected';
        badge.classList.add('good');
    } else if (score >= 50) {
        badge.textContent = '⚠️ Some Trackers';
        badge.classList.add('warning');
    } else {
        badge.textContent = '🚨 Trackers Detected';
        badge.classList.add('danger');
    }
    
    // Update panel
    document.getElementById('privacy-score-value').textContent = score;
    document.getElementById('stat-trackers').textContent = data.blocked_trackers.length;
    document.getElementById('stat-ads').textContent = data.blocked_ads.length;
    document.getElementById('stat-social').textContent = data.blocked_social.length;
    document.getElementById('stat-https').textContent = data.https ? 'HTTPS ✓' : 'HTTP ⚠️';
    
    // Update score circle color
    const circle = document.getElementById('privacy-score-circle');
    const degrees = (score / 100) * 360;
    const color = score >= 80 ? '#00ff41' : score >= 50 ? '#ffaa00' : '#ff4444';
    circle.style.background = `conic-gradient(${color} ${degrees}deg, #2a2a2a ${degrees}deg)`;
    
    // Update blocked domains list
    const blockedList = document.getElementById('blocked-list');
    const allBlocked = [...data.blocked_trackers, ...data.blocked_ads, ...data.blocked_social];
    
    if (allBlocked.length > 0) {
        blockedList.innerHTML = allBlocked.map(domain => 
            `<li>🚫 ${escapeHtml(domain)}</li>`
        ).join('');
        document.getElementById('blocked-domains').style.display = 'block';
    } else {
        blockedList.innerHTML = '<li style="color: var(--raccoon-primary);">✓ No trackers detected</li>';
    }
}

// ============================================================================
// Privacy Panel
// ============================================================================

function togglePrivacyPanel() {
    const panel = document.getElementById('privacy-panel');
    panel?.classList.toggle('active');
}

function closePrivacyPanel() {
    document.getElementById('privacy-panel')?.classList.remove('active');
}

async function checkPagePrivacy(url) {
    if (!url) return;
    
    try {
        const response = await fetch('/api/check-trackers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (data.success) {
            updatePrivacyUI(data);
        }
    } catch (error) {
        console.error('Privacy check error:', error);
    }
}

function updatePrivacyUI(data) {
    const score = data.privacy_score;
    const badge = elements.privacyBadge;
    
    // Update badge
    badge.className = 'privacy-badge';
    if (score >= 80) {
        badge.textContent = '🔒 Protected';
        badge.classList.add('good');
    } else if (score >= 50) {
        badge.textContent = '⚠️ Some Trackers';
        badge.classList.add('warning');
    } else {
        badge.textContent = '🚨 Trackers Detected';
        badge.classList.add('danger');
    }
    
    // Update panel
    document.getElementById('privacy-score-value').textContent = score;
    document.getElementById('stat-trackers').textContent = data.blocked_trackers.length;
    document.getElementById('stat-ads').textContent = data.blocked_ads.length;
    document.getElementById('stat-social').textContent = data.blocked_social.length;
    document.getElementById('stat-https').textContent = data.https ? 'HTTPS ✓' : 'HTTP ⚠️';
    
    // Update score circle color
    const circle = document.getElementById('privacy-score-circle');
    const degrees = (score / 100) * 360;
    const color = score >= 80 ? '#00ff41' : score >= 50 ? '#ffaa00' : '#ff4444';
    circle.style.background = `conic-gradient(${color} ${degrees}deg, #2a2a2a ${degrees}deg)`;
    
    // Update blocked domains list
    const blockedList = document.getElementById('blocked-list');
    const allBlocked = [...data.blocked_trackers, ...data.blocked_ads, ...data.blocked_social];
    
    if (allBlocked.length > 0) {
        blockedList.innerHTML = allBlocked.map(domain => 
            `<li>🚫 ${escapeHtml(domain)}</li>`
        ).join('');
        document.getElementById('blocked-domains').style.display = 'block';
    } else {
        blockedList.innerHTML = '<li style="color: var(--raccoon-primary);">✓ No trackers detected</li>';
    }
}
// ============================================================================
// Bookmarks System
// ============================================================================

const BOOKMARKS_KEY = 'raccoon_bookmarks';

function getBookmarks() {
    try {
        return JSON.parse(localStorage.getItem(BOOKMARKS_KEY) || '[]');
    } catch {
        return [];
    }
}

function saveBookmarks(bookmarks) {
    localStorage.setItem(BOOKMARKS_KEY, JSON.stringify(bookmarks));
}

function addBookmark(url, title) {
    const bookmarks = getBookmarks();
    if (bookmarks.some(b => b.url === url)) {
        updateStatus('Already bookmarked');
        return false;
    }
    const bookmark = {
        id: Date.now(),
        url: url,
        title: title || url,
        created: new Date().toISOString()
    };
    bookmarks.unshift(bookmark);
    saveBookmarks(bookmarks);
    updateBookmarkButton(url);
    updateStatus('📑 Bookmark added');
    return true;
}

function removeBookmark(id) {
    const bookmarks = getBookmarks();
    const filtered = bookmarks.filter(b => b.id !== id);
    saveBookmarks(filtered);
    renderBookmarks();
    updateStatus('Bookmark removed');
}

function isBookmarked(url) {
    return getBookmarks().some(b => b.url === url);
}

function updateBookmarkButton(url) {
    const btn = document.getElementById('btn-bookmark');
    if (!btn) return;
    if (isBookmarked(url)) {
        btn.textContent = '★';
        btn.classList.add('bookmarked');
        btn.title = 'Remove bookmark';
    } else {
        btn.textContent = '☆';
        btn.classList.remove('bookmarked');
        btn.title = 'Bookmark this page';
    }
}

function toggleBookmark() {
    const url = state.currentUrl || state.currentTab?.url;
    const title = state.currentTab?.title || document.getElementById('tab-title')?.textContent || url;
    if (!url || url === 'about:blank') {
        updateStatus('Cannot bookmark this page');
        return;
    }
    const bookmarks = getBookmarks();
    const existing = bookmarks.find(b => b.url === url);
    if (existing) {
        removeBookmark(existing.id);
    } else {
        addBookmark(url, title);
    }
}

function renderBookmarks() {
    const container = document.getElementById('bookmarks-list');
    if (!container) return;
    const bookmarks = getBookmarks();
    if (bookmarks.length === 0) {
        container.innerHTML = '<div class="bookmarks-empty"><p>📭 No bookmarks yet</p><p style="font-size: 12px; margin-top: 8px;">Click ☆ to bookmark a page</p></div>';
        return;
    }
    container.innerHTML = bookmarks.map(b => `
        <div class="bookmark-item" onclick="navigateToBookmark('${escapeHtml(b.url)}')">
            <span class="bookmark-icon">📄</span>
            <div class="bookmark-info">
                <div class="bookmark-title">${escapeHtml(b.title)}</div>
                <div class="bookmark-url">${escapeHtml(b.url)}</div>
            </div>
            <button class="bookmark-delete" onclick="event.stopPropagation(); removeBookmark(${b.id})" title="Remove">×</button>
        </div>
    `).join('');
}

function navigateToBookmark(url) {
    closeBookmarksPanel();
    navigateToUrl(url);
}

function toggleBookmarksPanel() {
    const panel = document.getElementById('bookmarks-panel');
    if (panel?.classList.contains('active')) {
        closeBookmarksPanel();
    } else {
        closePrivacyPanel();
        renderBookmarks();
        panel?.classList.add('active');
    }
}

function closeBookmarksPanel() {
    document.getElementById('bookmarks-panel')?.classList.remove('active');
}

function exportBookmarks() {
    const bookmarks = getBookmarks();
    const json = JSON.stringify(bookmarks, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'raccoon-bookmarks-' + new Date().toISOString().split('T')[0] + '.json';
    a.click();
    URL.revokeObjectURL(url);
    updateStatus('📤 Bookmarks exported');
}

function clearBookmarks() {
    if (confirm('Clear all bookmarks?')) {
        saveBookmarks([]);
        renderBookmarks();
        updateStatus('🗑️ Bookmarks cleared');
    }
}
