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
    """Search using DuckDuckGo"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    # Log to history
    conn = get_db()
    conn.execute(
        'INSERT INTO history (title, url, visited_at) VALUES (?, ?, ?)',
        (f'Search: {query}', f'/search?q={query}', datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    
    # Use DuckDuckGo HTML version for privacy
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


# ============ HELPERS ============

def perform_search(query):
    """Search DuckDuckGo and return results"""
    try:
        # Use DuckDuckGo HTML version
        url = f'https://html.duckduckgo.com/html/?q={quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove trackers
    for script in soup.find_all('script', src=True):
        src = script.get('src', '')
        if any(tracker in src for tracker in TRACKER_DOMAINS):
            script.decompose()
    
    for img in soup.find_all('img', src=True):
        src = img.get('src', '')
        if any(tracker in src for tracker in TRACKER_DOMAINS):
            img.decompose()
    
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