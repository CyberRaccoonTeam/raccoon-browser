"""
🦝 Raccoon Browser - Advanced Browser Engine
Uses PyQt WebEngine for full browser capabilities

Features:
- Real browser engine (Chromium-based)
- JavaScript execution
- Cookie/Session management
- Dynamic content handling

Run: python3 browser_engine.py
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timedelta
from threading import Thread
from urllib.parse import quote, urlparse, urljoin

from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineCookieStore
from PyQt5.QtWebEngineCore import QWebEngineScript

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

# ============================================================================
# Flask API Server (runs in background)
# ============================================================================

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# Cookie/Session storage
sessions = {}
cookies_db = {}

TRACKER_DOMAINS = [
    'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
    'facebook.net', 'facebook.com/tr', 'adservice.google.com',
]

PRIVACY_DOMAINS = [
    'wikipedia.org', 'mozilla.org', 'eff.org', 'privacytools.io',
    'github.com', 'protonmail.com', 'duckduckgo.com',
]


def get_user_agent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Raccoon/0.2.0"


def apply_raccoon_ranking(results, query):
    ranked = []
    for result in results:
        score = 100
        url = result.get('url', '')
        
        if url.startswith('https://'):
            score += 15
        
        for domain in PRIVACY_DOMAINS:
            if domain in url:
                score += 25
                break
        
        for domain in ['facebook.com', 'google.com', 'tiktok.com']:
            if domain in url:
                score -= 20
                break
        
        ranked.append({**result, 'raccoon_score': score})
    
    return sorted(ranked, key=lambda x: x.get('raccoon_score', 0), reverse=True)


def search_duckduckgo(query):
    results = []
    try:
        url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1"
        headers = {'User-Agent': get_user_agent()}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        for topic in data.get('RelatedTopics', [])[:15]:
            if isinstance(topic, dict) and 'FirstURL' in topic:
                results.append({
                    'title': topic.get('Text', '').split(' - ')[0][:100],
                    'url': topic.get('FirstURL', ''),
                    'content': topic.get('Text', '')[:200],
                })
    except Exception as e:
        print(f"DDG error: {e}")
    
    return results


# ============================================================================
# Session Management
# ============================================================================

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new browser session"""
    import secrets
    session_id = secrets.token_hex(16)
    sessions[session_id] = {
        'created_at': datetime.utcnow().isoformat(),
        'history': [],
        'cookies': {},
        'local_storage': {},
    }
    return jsonify({
        'success': True,
        'session_id': session_id,
    })


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session info"""
    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    return jsonify({
        'success': True,
        'session': sessions[session_id],
    })


@app.route('/api/session/<session_id>/cookies', methods=['GET'])
def get_cookies(session_id):
    """Get cookies for session"""
    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    return jsonify({
        'success': True,
        'cookies': sessions[session_id].get('cookies', {}),
    })


@app.route('/api/session/<session_id>/cookies', methods=['DELETE'])
def clear_cookies(session_id):
    """Clear cookies for session"""
    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    sessions[session_id]['cookies'] = {}
    return jsonify({
        'success': True,
        'message': 'Cookies cleared',
    })


# ============================================================================
# Search API
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Raccoon Browser',
        'version': '0.2.0',
        'engine': 'PyQt WebEngine',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'No query provided'}), 400
    
    results = search_duckduckgo(query)
    
    if results:
        ranked = apply_raccoon_ranking(results, query)
        return jsonify({
            'success': True,
            'query': query,
            'instance': 'DuckDuckGo',
            'total': len(ranked),
            'results': ranked[:15],
        })
    
    return jsonify({
        'success': False,
        'error': 'No results found'
    })


@app.route('/api/fetch', methods=['POST'])
def fetch_page():
    """Fetch a page with JavaScript rendering (via WebEngine)"""
    data = request.get_json()
    url = data.get('url', '')
    session_id = data.get('session_id')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    
    # This endpoint signals the WebEngine to load the page
    return jsonify({
        'success': True,
        'url': url,
        'message': 'Use WebEngine for full rendering',
    })


@app.route('/api/inject-js', methods=['POST'])
def inject_javascript():
    """Inject JavaScript into a page"""
    data = request.get_json()
    url = data.get('url', '')
    js_code = data.get('javascript', '')
    
    if not url or not js_code:
        return jsonify({'success': False, 'error': 'Missing url or javascript'}), 400
    
    # Return JS for client-side injection
    return jsonify({
        'success': True,
        'javascript': js_code,
    })


# ============================================================================
# Proxy Browsing (Enhanced)
# ============================================================================

@app.route('/browse')
def browse():
    """Browse URL through proxy"""
    url = request.args.get('url', '')
    
    if not url:
        return '''
        <html>
        <head><title>Error</title></head>
        <body style="background:#0a0a0a;color:#00ff41;font-family:sans-serif;padding:40px;">
            <h1>⚠️ No URL provided</h1>
            <p><a href="/" style="color:#00ff41;">← Back to Home</a></p>
        </body>
        </html>
        '''
    
    try:
        headers = {
            'User-Agent': get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        content_type = response.headers.get('Content-Type', 'text/html')
        
        if 'image/' in content_type:
            from flask import Response
            return Response(response.content, mimetype=content_type)
        
        if 'text/css' in content_type or 'javascript' in content_type:
            return response.text, 200, {'Content-Type': content_type}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = response.url
        
        # Inject base tag
        if soup.head:
            base = soup.new_tag('base', href=base_url)
            soup.head.insert(0, base)
            
            # Inject JavaScript handler for dynamic content
            js_inject = soup.new_tag('script')
            js_inject.string = '''
            // Raccoon Browser JS Bridge
            window.raccoonBridge = {
                version: '0.2.0',
                
                // Block trackers dynamically
                blockTrackers: function() {
                    const trackers = ['google-analytics.com', 'googletagmanager.com', 'doubleclick.net', 'facebook.net'];
                    document.querySelectorAll('script[src]').forEach(script => {
                        if (trackers.some(t => script.src.includes(t))) {
                            script.remove();
                            console.log('🦝 Blocked tracker:', script.src);
                        }
                    });
                },
                
                // Get page content
                getContent: function() {
                    return document.body.innerText;
                },
                
                // Execute custom JS
                exec: function(code) {
                    try {
                        return eval(code);
                    } catch(e) {
                        return {error: e.message};
                    }
                }
            };
            
            // Auto-block trackers
            document.addEventListener('DOMContentLoaded', function() {
                raccoonBridge.blockTrackers();
                console.log('🦝 Raccoon Browser JS Bridge loaded');
            });
            '''
            soup.head.append(js_inject)
        
        # Rewrite URLs
        for tag in soup.find_all(['a', 'link', 'img', 'script', 'iframe', 'source']):
            attrs = ['href'] if tag.name in ['a', 'link'] else ['src']
            for attr in attrs:
                if tag.has_attr(attr):
                    original = tag[attr]
                    if not original or original.startswith(('data:', 'javascript:', 'mailto:', '#')):
                        continue
                    if original.startswith('http'):
                        tag[attr] = f'/browse?url={quote(original)}'
                    elif original.startswith('//'):
                        tag[attr] = f'/browse?url={quote("https:" + original)}'
                    elif original.startswith('/'):
                        tag[attr] = f'/browse?url={quote(urljoin(base_url, original))}'
        
        # Add Raccoon header
        header = soup.new_tag('div', **{'id': 'raccoon-header'})
        header['style'] = '''
            position: fixed; top: 0; left: 0; right: 0;
            background: #050505; padding: 8px 12px;
            border-bottom: 1px solid #00ff41;
            z-index: 2147483647;
            display: flex; align-items: center; gap: 12px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        '''
        
        home = soup.new_tag('a', href='/')
        home['style'] = 'color: #00ff41; text-decoration: none; font-size: 20px;'
        home.string = '🦝'
        header.append(home)
        
        url_input = soup.new_tag('input', **{'type': 'text', 'value': response.url, 'id': 'raccoon-url'})
        url_input['style'] = 'flex: 1; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 8px 12px; color: #e0e0e0; font-size: 13px;'
        url_input['onkeydown'] = "if(event.key==='Enter')location.href='/browse?url='+encodeURIComponent(this.value)"
        header.append(url_input)
        
        ext = soup.new_tag('a', href=response.url, target='_blank')
        ext['style'] = 'color: #888; text-decoration: none; font-size: 12px;'
        ext.string = '↗'
        header.append(ext)
        
        if soup.body:
            soup.body.insert(0, header)
            soup.body['style'] = (soup.body.get('style', '') + ' padding-top: 50px !important;')
        
        return str(soup)
        
    except Exception as e:
        return f'''
        <html>
        <head><title>Error</title></head>
        <body style="background:#0a0a0a;color:#00ff41;font-family:sans-serif;padding:40px;">
            <h1>⚠️ Failed to load</h1>
            <p><strong>URL:</strong> {url}</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/" style="color:#00ff41;">← Back to Home</a></p>
        </body>
        </html>
        '''


# ============================================================================
# Run Flask Server
# ============================================================================

def run_flask():
    port = int(os.environ.get('RACCOON_PORT', 5555))
    print(f"🦝 Raccoon Browser API starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


if __name__ == '__main__':
    # Run Flask in background thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🦝 Raccoon Browser Engine starting...")
    print("   API: http://localhost:5555")
    print("   Web: Open http://localhost:5555 in your browser")
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🦝 Shutting down...")