"""
🦝 Raccoon Browser - Web Version
Privacy-focused search and browsing from any device

Run: python app.py
Access: http://localhost:5558
"""

import os
import requests
from flask import Flask, render_template, jsonify, request, redirect, url_for
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote, urlparse, urljoin
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'raccoon_web.db')

# Port configuration
PORT = int(os.environ.get('PORT', 5558))

# Tracker domains to block
TRACKER_DOMAINS = {
    'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
    'facebook.net', 'facebook.com/tr', 'adservice.google.com',
    'ads.twitter.com', 'hotjar.com', 'crazyegg.com', 'mouseflow.com',
    'mixpanel.com', 'amplitude.com', 'segment.io', 'optimizely.com',
}

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            created_at TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT NOT NULL,
            visited_at TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            search_engine TEXT DEFAULT 'duckduckgo',
            safe_search INTEGER DEFAULT 0,
            block_trackers INTEGER DEFAULT 1,
            https_only INTEGER DEFAULT 1,
            save_history INTEGER DEFAULT 1,
            theme TEXT DEFAULT 'dark',
            show_quick_links INTEGER DEFAULT 1,
            trackers_blocked INTEGER DEFAULT 0
        )
    ''')
    # Insert default settings if not exists
    conn.execute('''
        INSERT OR IGNORE INTO settings (id) VALUES (1)
    ''')
    conn.commit()
    conn.close()

init_db()


# ============ ROUTES ============

@app.route('/')
def index():
    """Main page with search"""
    return render_template('index.html')


@app.route('/search')
def search():
    """Search using configured search engine"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    # Log to history if enabled
    settings = get_user_settings()
    if settings.get('save_history', 1):
        conn = get_db()
        conn.execute(
            'INSERT INTO history (title, url, visited_at) VALUES (?, ?, ?)',
            (f'Search: {query}', f'/search?q={query}', datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
    
    results = perform_search(query)
    
    return render_template('results.html', query=query, results=results)


@app.route('/browse')
def browse():
    """Browse a URL through our proxy"""
    url = request.args.get('url', '')
    if not url:
        return redirect(url_for('index'))
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        content = fetch_and_clean(url)
        return render_template('browse.html', content=content, url=url)
    except Exception as e:
        return render_template('error.html', error=str(e), url=url)


# ============ API ============

@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    results = perform_search(query)
    return jsonify({'query': query, 'results': results})


@app.route('/api/bookmarks', methods=['GET'])
def get_bookmarks():
    """Get all bookmarks"""
    conn = get_db()
    bookmarks = conn.execute(
        'SELECT * FROM bookmarks ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    
    return jsonify([dict(b) for b in bookmarks])


@app.route('/api/bookmarks', methods=['POST'])
def add_bookmark():
    """Add a bookmark"""
    data = request.get_json()
    title = data.get('title', 'Untitled')
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO bookmarks (title, url, created_at) VALUES (?, ?, ?)',
            (title, url, datetime.utcnow().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already bookmarked'}), 409
    finally:
        conn.close()
    
    return jsonify({'message': 'Bookmarked!', 'title': title, 'url': url}), 201


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    """Delete a bookmark"""
    conn = get_db()
    conn.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Bookmark deleted'})


@app.route('/api/history')
def get_history():
    """Get browsing history"""
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db()
    history = conn.execute(
        'SELECT * FROM history ORDER BY visited_at DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(h) for h in history])


@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear all history"""
    conn = get_db()
    conn.execute('DELETE FROM history')
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'History cleared'})


@app.route('/api/bookmarks/all', methods=['DELETE'])
def clear_all_bookmarks():
    """Clear all bookmarks"""
    conn = get_db()
    conn.execute('DELETE FROM bookmarks')
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'All bookmarks cleared'})


# ============ SETTINGS API ============

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get user settings"""
    conn = get_db()
    settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    conn.close()
    
    if settings:
        return jsonify({
            'search_engine': settings['search_engine'],
            'safe_search': bool(settings['safe_search']),
            'block_trackers': bool(settings['block_trackers']),
            'https_only': bool(settings['https_only']),
            'save_history': bool(settings['save_history']),
            'theme': settings['theme'],
            'show_quick_links': bool(settings['show_quick_links']),
            'trackers_blocked': settings['trackers_blocked']
        })
    return jsonify({})


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save user settings"""
    data = request.get_json()
    
    conn = get_db()
    conn.execute('''
        UPDATE settings SET
            search_engine = ?,
            safe_search = ?,
            block_trackers = ?,
            https_only = ?,
            save_history = ?,
            theme = ?,
            show_quick_links = ?
        WHERE id = 1
    ''', (
        data.get('search_engine', 'duckduckgo'),
        1 if data.get('safe_search') else 0,
        1 if data.get('block_trackers', True) else 0,
        1 if data.get('https_only', True) else 0,
        1 if data.get('save_history', True) else 0,
        data.get('theme', 'dark'),
        1 if data.get('show_quick_links', True) else 0
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Settings saved'})


@app.route('/settings')
def settings_page():
    """Settings page"""
    return render_template('settings.html')


# ============ HELPERS ============

def get_user_settings():
    """Get user settings from DB"""
    conn = get_db()
    settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    conn.close()
    return dict(settings) if settings else {}


def increment_trackers_blocked(count=1):
    """Increment trackers blocked counter"""
    conn = get_db()
    conn.execute('UPDATE settings SET trackers_blocked = trackers_blocked + ?', (count,))
    conn.commit()
    conn.close()


def perform_search(query):
    """Search using configured search engine"""
    settings = get_user_settings()
    engine = settings.get('search_engine', 'duckduckgo')
    safe = settings.get('safe_search', 0)
    
    try:
        if engine == 'searxng':
            # Use a public SearXNG instance
            url = f'https://search.bus-hit.me/search?q={quote(query)}&format=json'
            if safe:
                url += '&safesearch=1'
            response = requests.get(url, timeout=10)
            data = response.json()
            return [{
                'title': r.get('title', 'No title'),
                'url': r.get('url', ''),
                'snippet': r.get('content', '')
            } for r in data.get('results', [])[:10]]
        
        elif engine == 'brave':
            # Brave Search HTML version
            url = f'https://search.brave.com/search?q={quote(query)}'
            if safe:
                url += '&safe=strict'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.select('.snippet')[:10]:
                title_elem = result.select_one('.snippet-title')
                url_elem = result.select_one('a')
                desc_elem = result.select_one('.snippet-description')
                if title_elem and url_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': url_elem.get('href', ''),
                        'snippet': desc_elem.get_text(strip=True) if desc_elem else ''
                    })
            return results
        
        elif engine == 'google':
            # Google (not recommended - for users who insist)
            url = f'https://www.google.com/search?q={quote(query)}'
            if safe:
                url += '&safe=active'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.select('.g')[:10]:
                title_elem = result.select_one('h3')
                link_elem = result.select_one('a')
                snippet_elem = result.select_one('.VwiC3b')
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
            return results
        
        else:  # DuckDuckGo (default)
            url = f'https://html.duckduckgo.com/html/?q={quote(query)}'
            if safe:
                url += '&kp=1'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.select('.result')[:10]:
                title_elem = result.select_one('.result__title')
                snippet_elem = result.select_one('.result__snippet')
                if title_elem:
                    link = title_elem.select_one('a')
                    if link:
                        results.append({
                            'title': link.get_text(strip=True),
                            'url': link.get('href', ''),
                            'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                        })
            return results
    except Exception as e:
        print(f"Search error: {e}")
        return []


def fetch_and_clean(url):
    """Fetch URL and clean the content"""
    settings = get_user_settings()
    block_trackers = settings.get('block_trackers', 1)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Track and remove trackers
    trackers_found = 0
    if block_trackers:
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            if any(tracker in src for tracker in TRACKER_DOMAINS):
                script.decompose()
                trackers_found += 1
        
        for img in soup.find_all('img', src=True):
            src = img.get('src', '')
            if any(tracker in src for tracker in TRACKER_DOMAINS):
                img.decompose()
                trackers_found += 1
        
        for iframe in soup.find_all('iframe', src=True):
            src = iframe.get('src', '')
            if any(tracker in src for tracker in TRACKER_DOMAINS):
                iframe.decompose()
                trackers_found += 1
    
    # Increment counter if trackers were blocked
    if trackers_found > 0:
        increment_trackers_blocked(trackers_found)
    
    # Remove scripts and styles
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    
    # Rewrite links to go through our proxy
    for a in soup.find_all('a', href=True):
        href = a.get('href')
        if href and not href.startswith(('#', 'javascript:', 'mailto:')):
            if href.startswith('/'):
                a['href'] = f'/browse?url={quote(urljoin(url, href))}'
            elif href.startswith('http'):
                a['href'] = f'/browse?url={quote(href)}'
    
    return str(soup)


if __name__ == '__main__':
    print(f"🦝 Raccoon Browser Web Version starting on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)