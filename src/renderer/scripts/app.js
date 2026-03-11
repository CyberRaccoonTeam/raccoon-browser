/**
 * 🦝 Raccoon Browser - Renderer Application
 * Handles UI interactions and communication with Flask backend
 */

// Configuration
const BACKEND_URL = 'http://127.0.0.1:5555';

// DOM Elements
const elements = {
  urlInput: document.getElementById('url-input'),
  searchInput: document.getElementById('search-input'),
  searchBtn: document.getElementById('search-btn'),
  btnBack: document.getElementById('btn-back'),
  btnForward: document.getElementById('btn-forward'),
  btnRefresh: document.getElementById('btn-refresh'),
  btnHome: document.getElementById('btn-home'),
  btnTrash: document.getElementById('btn-trash'),
  btnMenu: document.getElementById('btn-menu'),
  welcomePage: document.getElementById('welcome-page'),
  webContent: document.getElementById('web-content'),
  statusText: document.getElementById('status-text'),
  privacyStatus: document.getElementById('privacy-status'),
  tabTitle: document.querySelector('.tab-title'),
};

// State
const state = {
  currentUrl: '',
  history: [],
  historyIndex: -1,
  isLoading: false,
};

/**
 * Initialize the browser
 */
function init() {
  setupEventListeners();
  updateNavigationButtons();
  checkBackendHealth();
  console.log('🦝 Raccoon Browser ready');
}

/**
 * Check if Flask backend is running
 */
async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`);
    const data = await response.json();
    console.log('🦝 Backend connected:', data.service);
    elements.statusText.textContent = 'Connected';
  } catch (error) {
    console.warn('🦝 Backend not available:', error.message);
    elements.statusText.textContent = 'Backend offline';
  }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // URL bar navigation
  elements.urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      navigateTo(elements.urlInput.value);
    }
  });

  // URL bar autocomplete
  elements.urlInput.addEventListener('input', debounce(async (e) => {
    const query = e.target.value;
    if (query.length > 2) {
      const suggestions = await getSuggestions(query);
      // TODO: Show suggestions dropdown
    }
  }, 300));

  // Search box
  elements.searchBtn.addEventListener('click', performSearch);
  elements.searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  });

  // Navigation buttons
  elements.btnBack.addEventListener('click', goBack);
  elements.btnForward.addEventListener('click', goForward);
  elements.btnRefresh.addEventListener('click', refresh);
  elements.btnHome.addEventListener('click', goHome);

  // Trash button (clear cache)
  elements.btnTrash.addEventListener('click', clearCache);

  // Quick links
  document.querySelectorAll('.quick-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(link.dataset.url);
    });
  });

  // Webview events
  elements.webContent.addEventListener('did-start-loading', () => {
    state.isLoading = true;
    elements.statusText.textContent = 'Loading...';
  });

  elements.webContent.addEventListener('did-stop-loading', () => {
    state.isLoading = false;
    elements.statusText.textContent = 'Done';
    checkPagePrivacy();
  });

  elements.webContent.addEventListener('page-title-updated', (e) => {
    elements.tabTitle.textContent = e.title;
    document.title = `${e.title} - Raccoon Browser`;
  });
}

/**
 * Get search suggestions from Flask backend
 */
async function getSuggestions(query) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/suggestions?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    return data.suggestions || [];
  } catch (error) {
    return [];
  }
}

/**
 * Navigate to URL
 */
async function navigateTo(input) {
  if (!input.trim()) return;

  let url = input.trim();

  // Check if it's a search query
  if (!url.includes('.') || url.includes(' ')) {
    await performSearch(url);
    return;
  }

  // Add protocol if missing
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url;
  }

  try {
    elements.statusText.textContent = 'Loading...';
    elements.welcomePage.style.display = 'none';
    elements.webContent.style.display = 'flex';
    
    // Use webview to load URL
    elements.webContent.src = url;
    elements.urlInput.value = url;
    
    // Update history
    state.history = state.history.slice(0, state.historyIndex + 1);
    state.history.push(url);
    state.historyIndex = state.history.length - 1;
    
    updateNavigationButtons();
    state.currentUrl = url;
    
    // Check for trackers
    await checkTrackers(url);
    
    console.log('🦝 Navigated to:', url);
  } catch (error) {
    console.error('Navigation error:', error);
    elements.statusText.textContent = 'Error loading page';
  }
}

/**
 * Perform search using Flask backend (Raccoon Search)
 */
async function performSearch(query) {
  if (!query) {
    query = elements.searchInput.value || elements.urlInput.value;
  }
  
  if (!query.trim()) return;

  elements.statusText.textContent = 'Searching...';
  
  try {
    // Call Flask backend for search
    const response = await fetch(`${BACKEND_URL}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
    const result = await response.json();
    
    if (result.success && result.results.length > 0) {
      // For now, navigate to first result
      // TODO: Show search results page
      const topResult = result.results[0];
      navigateTo(topResult.url);
      
      console.log('🦝 Search results:', result.total);
      console.log('🦝 Using instance:', result.instance);
    } else {
      elements.statusText.textContent = 'No results found';
    }
  } catch (error) {
    console.error('Search error:', error);
    elements.statusText.textContent = 'Search failed';
  }
}

/**
 * Check for trackers on current page
 */
async function checkTrackers(url) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/check-trackers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    
    const data = await response.json();
    
    if (data.trackers_found > 0) {
      elements.privacyStatus.textContent = `🛡️ Blocked ${data.trackers_found} tracker${data.trackers_found > 1 ? 's' : ''}`;
    } else {
      elements.privacyStatus.textContent = '🔒 Protected';
    }
  } catch (error) {
    console.error('Tracker check error:', error);
  }
}

/**
 * Check privacy score of current page
 */
async function checkPagePrivacy() {
  if (!state.currentUrl) return;
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/check-privacy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: state.currentUrl })
    });
    
    const data = await response.json();
    
    if (data.success) {
      const emoji = data.privacy_score >= 80 ? '🔒' : data.privacy_score >= 60 ? '🛡️' : '⚠️';
      elements.privacyStatus.textContent = `${emoji} Privacy: ${data.privacy_score}%`;
    }
  } catch (error) {
    console.error('Privacy check error:', error);
  }
}

/**
 * Go back in history
 */
function goBack() {
  if (state.historyIndex > 0) {
    state.historyIndex--;
    const url = state.history[state.historyIndex];
    elements.webContent.src = url;
    elements.urlInput.value = url;
    state.currentUrl = url;
    updateNavigationButtons();
  }
}

/**
 * Go forward in history
 */
function goForward() {
  if (state.historyIndex < state.history.length - 1) {
    state.historyIndex++;
    const url = state.history[state.historyIndex];
    elements.webContent.src = url;
    elements.urlInput.value = url;
    state.currentUrl = url;
    updateNavigationButtons();
  }
}

/**
 * Refresh current page
 */
function refresh() {
  if (elements.webContent.style.display !== 'none') {
    elements.webContent.reload();
    elements.statusText.textContent = 'Refreshing...';
  }
}

/**
 * Go to home page
 */
function goHome() {
  elements.welcomePage.style.display = 'flex';
  elements.webContent.style.display = 'none';
  elements.urlInput.value = '';
  elements.statusText.textContent = 'Ready';
  elements.tabTitle.textContent = 'New Tab';
  elements.privacyStatus.textContent = '🔒 Protected';
}

/**
 * Clear cache (trash can feature)
 */
async function clearCache() {
  try {
    // Clear webview cache
    elements.webContent.clearHistory();
    
    // Animate trash button
    elements.btnTrash.style.transform = 'scale(1.2) rotate(-15deg)';
    setTimeout(() => {
      elements.btnTrash.style.transform = '';
    }, 300);
    
    elements.statusText.textContent = '🗑️ Trash emptied!';
    console.log('🦝 Cache cleared');
    
    setTimeout(() => {
      elements.statusText.textContent = 'Ready';
    }, 2000);
  } catch (error) {
    console.error('Clear cache error:', error);
  }
}

/**
 * Update navigation button states
 */
function updateNavigationButtons() {
  elements.btnBack.disabled = state.historyIndex <= 0;
  elements.btnForward.disabled = state.historyIndex >= state.history.length - 1;
}

/**
 * Debounce utility
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);