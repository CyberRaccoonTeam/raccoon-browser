/* 🦝 Raccoon Browser - Web Version JS */

document.addEventListener('DOMContentLoaded', () => {
    loadQuickLinks();
    setupModals();
});

// Quick Links
const defaultLinks = [
    { title: 'DuckDuckGo', url: 'https://duckduckgo.com' },
    { title: 'GitHub', url: 'https://github.com' },
    { title: 'Hacker News', url: 'https://news.ycombinator.com' },
    { title: 'Reddit', url: 'https://reddit.com' },
    { title: 'Wikipedia', url: 'https://wikipedia.org' },
    { title: 'YouTube', url: 'https://youtube.com' },
];

async function loadQuickLinks() {
    const container = document.getElementById('quickLinks');
    if (!container) return;

    // Try to load bookmarks, fall back to defaults
    let links = defaultLinks;
    
    try {
        const res = await fetch('/api/bookmarks');
        const bookmarks = await res.json();
        if (bookmarks.length > 0) {
            links = bookmarks.slice(0, 6);
        }
    } catch (e) {
        console.log('Using default links');
    }

    container.innerHTML = links.map(link => `
        <div class="link-item" onclick="visitLink('${link.url}')">
            <a href="${link.url}">${link.title}</a>
        </div>
    `).join('');
}

function visitLink(url) {
    window.location.href = `/browse?url=${encodeURIComponent(url)}`;
}

// Modals
function setupModals() {
    const bookmarksBtn = document.getElementById('bookmarksBtn');
    const historyBtn = document.getElementById('historyBtn');
    const closeBookmarks = document.getElementById('closeBookmarks');
    const closeHistory = document.getElementById('closeHistory');
    const bookmarksModal = document.getElementById('bookmarksModal');
    const historyModal = document.getElementById('historyModal');

    if (bookmarksBtn) {
        bookmarksBtn.addEventListener('click', (e) => {
            e.preventDefault();
            loadBookmarks();
            bookmarksModal.classList.add('active');
        });
    }

    if (historyBtn) {
        historyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            loadHistory();
            historyModal.classList.add('active');
        });
    }

    if (closeBookmarks) {
        closeBookmarks.addEventListener('click', () => {
            bookmarksModal.classList.remove('active');
        });
    }

    if (closeHistory) {
        closeHistory.addEventListener('click', () => {
            historyModal.classList.remove('active');
        });
    }

    // Close modal on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

async function loadBookmarks() {
    const container = document.getElementById('bookmarksList');
    if (!container) return;

    try {
        const res = await fetch('/api/bookmarks');
        const bookmarks = await res.json();

        if (bookmarks.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted)">No bookmarks yet. Save pages as you browse!</p>';
            return;
        }

        container.innerHTML = bookmarks.map(b => `
            <div class="bookmark-item">
                <a href="/browse?url=${encodeURIComponent(b.url)}">${escapeHtml(b.title)}</a>
                <p>${escapeHtml(b.url)}</p>
                <button onclick="deleteBookmark(${b.id})" style="background: var(--error); color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; margin-top: 0.5rem;">Delete</button>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p style="color: var(--error)">Failed to load bookmarks</p>';
    }
}

async function loadHistory() {
    const container = document.getElementById('historyList');
    if (!container) return;

    try {
        const res = await fetch('/api/history?limit=20');
        const history = await res.json();

        if (history.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted)">No history yet</p>';
            return;
        }

        container.innerHTML = history.map(h => `
            <div class="history-item">
                <a href="${h.url}">${escapeHtml(h.title || h.url)}</a>
                <p>${new Date(h.visited_at).toLocaleString()}</p>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p style="color: var(--error)">Failed to load history</p>';
    }
}

async function deleteBookmark(id) {
    if (!confirm('Delete this bookmark?')) return;

    try {
        await fetch(`/api/bookmarks/${id}`, { method: 'DELETE' });
        loadBookmarks();
    } catch (e) {
        alert('Failed to delete bookmark');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}