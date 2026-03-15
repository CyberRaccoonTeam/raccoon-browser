"""
🦝 Raccoon Browser - Pure Flask Application
No Electron - Flask handles everything

Features:
- Search with DuckDuckGo + Wikipedia
- Proxy browsing with URL rewriting
- JavaScript injection for dynamic content
- Cookie/Session management
- Tracker blocking

Run: python3 app.py
Access: http://localhost:5555
"""

import os
import random
import requests
from flask import Flask, render_template, jsonify, request
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote, urlparse, parse_qs, urljoin
from datetime import datetime, timezone

# Import advanced modules
try:
    from session_manager import session_manager
    from js_injector import js_injector, get_injection_html
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False
    print("⚠️ Advanced features not available - install requirements_advanced.txt")

# Import Playwright renderer
try:
    from playwright_renderer import render_with_playwright, is_js_heavy_site, get_site_info
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright renderer not available")

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Configuration
SEARXNG_INSTANCES = [
    'https://searx.be',
    'https://searx.org',
    'https://search.bus-hit.me',
    'https://searx.info',
    'https://opensearch.org',
]

TRACKER_DOMAINS = [
    'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
    'facebook.net', 'facebook.com/tr', 'adservice.google.com',
    'ads.twitter.com', 'analytics.twitter.com', 'pixel.facebook.com',
    'hotjar.com', 'crazyegg.com', 'mouseflow.com', 'clicktale.net',
    'fullstory.com', 'mixpanel.com', 'amplitude.com', 'segment.io',
    'heap.io', 'optimizely.com', 'newrelic.com', 'pingdom.net',
]

AD_DOMAINS = [
    'ads.google.com', 'ads.youtube.com', 'ads.facebook.com',
    'taboola.com', 'outbrain.com', 'criteo.com', 'adnxs.com',
    'pubmatic.com', 'openx.net', 'rubiconproject.com',
]

SOCIAL_TRACKERS = [
    'facebook.com/plugins', 'platform.twitter.com', 'platform.linkedin.com',
    'assets.pinterest.com', 'widgets.wp.com', 'sharethis.com',
]

PRIVACY_DOMAINS = [
    'wikipedia.org', 'mozilla.org', 'eff.org', 'privacytools.io',
    'github.com', 'protonmail.com', 'duckduckgo.com',
]


def get_user_agent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Raccoon/0.1.0"


def apply_raccoon_ranking(results, query):
    """Custom ranking: prioritize privacy-friendly sites"""
    ranked = []
    for result in results:
        score = 100
        url = result.get('url', '')
        title = result.get('title', '')
        
        if url.startswith('https://'):
            score += 15
        
        for domain in PRIVACY_DOMAINS:
            if domain in url:
                score += 25
                break
        
        for domain in ['facebook.com', 'google.com', 'tiktok.com', 'instagram.com']:
            if domain in url:
                score -= 20
                break
        
        if query.lower() in title.lower():
            score += 10
        
        ranked.append({**result, 'raccoon_score': score})
    
    return sorted(ranked, key=lambda x: x.get('raccoon_score', 0), reverse=True)


def search_searxng(query):
    """SearXNG meta-search - more reliable results"""
    results = []
    for instance in SEARXNG_INSTANCES:
        try:
            url = f"{instance}/search?q={quote(query)}&format=json"
            headers = {'User-Agent': get_user_agent()}
            
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            for result in data.get('results', [])[:10]:
                results.append({
                    'title': result.get('title', 'Untitled'),
                    'url': result.get('url', ''),
                    'content': result.get('content', '')[:200],
                })
            
            if results:
                return results
        except Exception as e:
            print(f"SearXNG {instance} error: {e}")
            continue
    
    return results


def search_duckduckgo_html(query):
    """DuckDuckGo HTML search - scrapes real results"""
    results = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        headers = {'User-Agent': get_user_agent()}
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for result in soup.select('.result')[:15]:
            title_tag = result.select_one('.result__title')
            url_tag = result.select_one('.result__url')
            snippet_tag = result.select_one('.result__snippet')
            
            if title_tag and url_tag:
                title = title_tag.get_text(strip=True)
                url = url_tag.get('href', '')
                
                # DuckDuckGo uses redirect URLs, extract real URL
                if 'uddg=' in url:
                    from urllib.parse import parse_qs
                    parsed = parse_qs(urlparse(url).query)
                    if 'uddg' in parsed:
                        url = parsed['uddg'][0]
                
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                
                results.append({
                    'title': title,
                    'url': url,
                    'content': snippet[:200],
                })
    except Exception as e:
        print(f"DDG HTML error: {e}")
    
    return results


def search_wikipedia(query):
    """Wikipedia API - very reliable"""
    results = []
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote(query)}&limit=5&format=json"
        headers = {'User-Agent': get_user_agent()}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if len(data) >= 4:
            for title, url in zip(data[1], data[3]):
                results.append({
                    'title': title,
                    'url': url,
                    'content': f'Wikipedia article about {title}',
                })
    except Exception as e:
        print(f"Wikipedia error: {e}")
    
    return results


# ============================================================================
# Routes
# ============================================================================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Raccoon Browser',
        'version': '0.3.0',
        'features': {
            'session_management': ADVANCED_FEATURES,
            'js_injection': ADVANCED_FEATURES,
            'proxy_browsing': True,
            'tracker_blocking': True,
            'playwright_rendering': PLAYWRIGHT_AVAILABLE,
            'site_compatibility_detection': True,
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# ============================================================================
# Session Management API
# ============================================================================

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new browser session"""
    if not ADVANCED_FEATURES:
        return jsonify({'success': False, 'error': 'Session management not available'}), 501
    
    data = request.get_json() or {}
    name = data.get('name')
    session = session_manager.create_session(name)
    return jsonify({'success': True, 'session': session})


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session info"""
    if not ADVANCED_FEATURES:
        return jsonify({'success': False, 'error': 'Session management not available'}), 501
    
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    return jsonify({'success': True, 'session': session})


@app.route('/api/session/<session_id>/cookies', methods=['GET'])
def get_session_cookies(session_id):
    """Get cookies for session"""
    if not ADVANCED_FEATURES:
        return jsonify({'success': False, 'error': 'Session management not available'}), 501
    
    domain = request.args.get('domain')
    cookies = session_manager.get_cookies(session_id, domain)
    return jsonify({'success': True, 'cookies': cookies})


@app.route('/api/session/<session_id>/cookies', methods=['DELETE'])
def clear_session_cookies(session_id):
    """Clear cookies for session"""
    if not ADVANCED_FEATURES:
        return jsonify({'success': False, 'error': 'Session management not available'}), 501
    
    domain = request.args.get('domain')
    session_manager.clear_cookies(session_id, domain)
    return jsonify({'success': True, 'message': 'Cookies cleared'})


@app.route('/api/session/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """Get browsing history"""
    if not ADVANCED_FEATURES:
        return jsonify({'success': False, 'error': 'Session management not available'}), 501
    
    limit = request.args.get('limit', 50, type=int)
    history = session_manager.get_history(session_id, limit)
    return jsonify({'success': True, 'history': history})


@app.route('/api/search', methods=['POST'])
def search():
    """Perform search"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'No query provided'}), 400
    
    # Try SearXNG first (meta-search, real web results)
    results = search_searxng(query)
    instance = 'SearXNG'
    
    # Fallback to DuckDuckGo HTML search (real results, not just Wikipedia)
    if not results:
        results = search_duckduckgo_html(query)
        instance = 'DuckDuckGo'
    
    # Final fallback: Wikipedia only if nothing else works
    if not results:
        results = search_wikipedia(query)
        instance = 'Wikipedia'
    
    if results:
        ranked = apply_raccoon_ranking(results, query)
        return jsonify({
            'success': True,
            'query': query,
            'instance': instance,
            'total': len(ranked),
            'results': ranked[:15],
        })
    
    return jsonify({
        'success': False,
        'error': 'No results found'
    })


@app.route('/api/site-info', methods=['POST'])
def site_info():
    """Get site compatibility information"""
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    
    info = get_site_info(url)
    info['playwright_available'] = PLAYWRIGHT_AVAILABLE
    
    return jsonify({
        'success': True,
        'info': info,
    })


@app.route('/api/full-render', methods=['POST'])
def full_render():
    """Render a page with full JavaScript support using Playwright"""
    if not PLAYWRIGHT_AVAILABLE:
        return jsonify({'success': False, 'error': 'Playwright not available'}), 503
    
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    
    # Check if site is JS-heavy
    info = get_site_info(url)
    
    # Render with Playwright
    html, success, error = render_with_playwright(url)
    
    if not success:
        return jsonify({
            'success': False,
            'error': error,
            'fallback_hint': 'Try opening in native browser',
        }), 500
    
    # Parse and rewrite HTML (same as proxy mode)
    soup = BeautifulSoup(html, 'html.parser')
    base_url = url
    
    # Remove CSP
    for meta in soup.find_all('meta', {'http-equiv': 'Content-Security-Policy'}):
        meta.decompose()
    
    # Rewrite URLs
    from urllib.parse import urljoin
    for tag in soup.find_all(['link', 'script', 'img', 'iframe', 'source', 'video', 'audio', 'a']):
        if tag.name == 'link':
            href = tag.get('href', '')
            if href and not href.startswith(('data:', 'javascript:')):
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = urljoin(base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                tag['href'] = f'/browse?url={quote(href)}'
        elif tag.name == 'script':
            src = tag.get('src', '')
            if src and not src.startswith(('data:', 'javascript:')):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                tag['src'] = f'/browse?url={quote(src)}'
        elif tag.name in ['img', 'iframe', 'source', 'video', 'audio']:
            src = tag.get('src', '')
            if src and not src.startswith(('data:', 'javascript:', 'mailto:')):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                tag['src'] = f'/browse?url={quote(src)}'
        elif tag.name == 'a':
            href = tag.get('href', '')
            if href and not href.startswith(('data:', 'javascript:', 'mailto:', '#', 'tel:')):
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = urljoin(base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                tag['href'] = f'/browse?url={quote(href)}'
    
    # Add Raccoon header with compatibility notice
    header = soup.new_tag('div', id='raccoon-header')
    header['style'] = '''
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #050505;
        padding: 8px 12px;
        border-bottom: 1px solid #00ff41;
        z-index: 2147483647;
        display: flex;
        align-items: center;
        gap: 12px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    '''
    
    # Home link
    home_link = soup.new_tag('a', href='/')
    home_link['style'] = 'color: #00ff41; text-decoration: none; font-size: 20px;'
    home_link.string = '🦝'
    header.append(home_link)
    
    # URL bar
    url_input = soup.new_tag('input', type='text', id='raccoon-url', value=url)
    url_input['style'] = '''
        flex: 1;
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 8px 12px;
        color: #e0e0e0;
        font-size: 13px;
        outline: none;
    '''
    url_input['onkeydown'] = "if(event.key==='Enter'){window.location.href='/browse?url='+encodeURIComponent(this.value);}"
    header.append(url_input)
    
    # Compatibility badge
    if info['is_js_heavy']:
        badge = soup.new_tag('span')
        badge['style'] = 'color: #ff9800; font-size: 12px; padding: 4px 8px; background: rgba(255, 152, 0, 0.2); border-radius: 4px;'
        badge.string = '⚠️ Full Render Mode (JS-Heavy Site)'
        header.append(badge)
    
    # External link
    ext_link = soup.new_tag('a', href=url, target='_blank')
    ext_link['style'] = 'color: #888; text-decoration: none; font-size: 12px;'
    ext_link.string = '↗ Open in Browser'
    header.append(ext_link)
    
    # Inject header
    if soup.body:
        soup.body.insert(0, header)
        soup.body['style'] = 'padding-top: 50px !important;'
    
    return str(soup), 200, {'Content-Type': 'text/html'}


@app.route('/api/check-trackers', methods=['POST'])
def check_trackers():
    """Check URL for trackers and calculate privacy score"""
    data = request.get_json()
    url = data.get('url', '')
    
    blocked_trackers = []
    blocked_ads = []
    blocked_social = []
    
    for domain in TRACKER_DOMAINS:
        if domain in url:
            blocked_trackers.append(domain)
    
    for domain in AD_DOMAINS:
        if domain in url:
            blocked_ads.append(domain)
    
    for domain in SOCIAL_TRACKERS:
        if domain in url:
            blocked_social.append(domain)
    
    total_blocked = len(blocked_trackers) + len(blocked_ads) + len(blocked_social)
    
    # Calculate privacy score (0-100)
    privacy_score = 100
    privacy_score -= len(blocked_trackers) * 15  # Trackers are worst
    privacy_score -= len(blocked_ads) * 10       # Ads are bad
    privacy_score -= len(blocked_social) * 8     # Social trackers are moderate
    privacy_score = max(0, privacy_score)
    
    # Check for HTTPS
    if not url.startswith('https://'):
        privacy_score -= 10
    
    return jsonify({
        'success': True,
        'url': url,
        'trackers_found': total_blocked,
        'blocked_trackers': blocked_trackers,
        'blocked_ads': blocked_ads,
        'blocked_social': blocked_social,
        'is_safe': total_blocked == 0,
        'privacy_score': privacy_score,
        'https': url.startswith('https://'),
    })


@app.route('/api/suggestions')
def suggestions():
    """Search suggestions"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'suggestions': []})
    
    try:
        url = f"https://duckduckgo.com/ac/?q={quote(query)}&type=list"
        headers = {'User-Agent': get_user_agent()}
        
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        suggestions = data[1] if len(data) > 1 else []
        
        return jsonify({
            'success': True,
            'suggestions': suggestions[:8]
        })
    except:
        return jsonify({'suggestions': []})


@app.route('/browse')
def browse():
    """Browse URL through proxy - displays page inline"""
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
            'Accept-Encoding': 'gzip, deflate, br',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        content_type = response.headers.get('Content-Type', 'text/html')
        
        # Handle different content types
        if 'image/' in content_type:
            from flask import Response
            return Response(response.content, mimetype=content_type)
        
        if 'text/css' in content_type:
            # Rewrite CSS URLs to go through proxy
            css = response.text
            import re
            
            def replace_css_url(match):
                url_val = match.group(1) or match.group(2) or match.group(3)
                if not url_val or url_val.startswith('data:'):
                    return match.group(0)
                if url_val.startswith('//'):
                    url_val = 'https:' + url_val
                elif url_val.startswith('/'):
                    url_val = urljoin(url, url_val)
                elif not url_val.startswith(('http://', 'https://')):
                    url_val = urljoin(url, url_val)
                return f'url(/browse?url={quote(url_val)})'
            
            css = re.sub(r'url\(\s*["\']([^"\')\s]+)["\']\s*\)', replace_css_url, css)
            css = re.sub(r'url\(\s*([^"\')\s]+)\s*\)', replace_css_url, css)
            return css, 200, {'Content-Type': 'text/css'}
        
        if 'application/javascript' in content_type or 'text/javascript' in content_type:
            return response.text, 200, {'Content-Type': 'application/javascript'}
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get base URL for resolving relative URLs
        from urllib.parse import urljoin
        base_url = response.url
        
        # Remove CSP meta tags (they block proxy resources)
        for meta in soup.find_all('meta', {'http-equiv': 'Content-Security-Policy'}):
            meta.decompose()
        for meta in soup.find_all('meta', {'http-equiv': 'Content-Security-Policy-Report-Only'}):
            meta.decompose()
        
        # Don't inject base tag - it breaks relative URL resolution
        # Instead, rewrite all URLs explicitly
        
        # Rewrite all resource URLs to go through proxy
        for tag in soup.find_all(['link', 'script', 'img', 'iframe', 'source', 'video', 'audio', 'a']):
            if tag.name == 'link':
                href = tag.get('href', '')
                if href and not href.startswith(('data:', 'javascript:')):
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = urljoin(base_url, href)
                    elif not href.startswith(('http://', 'https://')):
                        href = urljoin(base_url, href)
                    tag['href'] = f'/browse?url={quote(href)}'
            
            elif tag.name == 'script':
                src = tag.get('src', '')
                if src and not src.startswith(('data:', 'javascript:')):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(base_url, src)
                    elif not src.startswith(('http://', 'https://')):
                        src = urljoin(base_url, src)
                    tag['src'] = f'/browse?url={quote(src)}'
            
            elif tag.name in ['img', 'iframe', 'source', 'video', 'audio']:
                src = tag.get('src', '')
                if src and not src.startswith(('data:', 'javascript:', 'mailto:')):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(base_url, src)
                    elif not src.startswith(('http://', 'https://')):
                        src = urljoin(base_url, src)
                    tag['src'] = f'/browse?url={quote(src)}'
            
            elif tag.name == 'a':
                href = tag.get('href', '')
                if href and not href.startswith(('data:', 'javascript:', 'mailto:', '#', 'tel:')):
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = urljoin(base_url, href)
                    elif not href.startswith(('http://', 'https://')):
                        href = urljoin(base_url, href)
                    tag['href'] = f'/browse?url={quote(href)}'
        
        # Rewrite inline styles with url()
        import re
        for tag in soup.find_all(style=True):
            style = tag['style']
            
            def replace_style_url(match):
                url_val = match.group(1) or match.group(2)
                if not url_val or url_val.startswith('data:'):
                    return match.group(0)
                if url_val.startswith('//'):
                    url_val = 'https:' + url_val
                elif url_val.startswith('/'):
                    url_val = urljoin(base_url, url_val)
                elif not url_val.startswith(('http://', 'https://')):
                    url_val = urljoin(base_url, url_val)
                return f'url(/browse?url={quote(url_val)})'
            
            style = re.sub(r'url\(\s*["\']([^"\')\s]+)["\']\s*\)', replace_style_url, style)
            style = re.sub(r'url\(\s*([^"\')\s]+)\s*\)', replace_style_url, style)
            tag['style'] = style
        
        # Rewrite style blocks
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                style_css = style_tag.string
                
                def replace_block_url(match):
                    url_val = match.group(1) or match.group(2)
                    if not url_val or url_val.startswith('data:'):
                        return match.group(0)
                    if url_val.startswith('//'):
                        url_val = 'https:' + url_val
                    elif url_val.startswith('/'):
                        url_val = urljoin(base_url, url_val)
                    elif not url_val.startswith(('http://', 'https://')):
                        url_val = urljoin(base_url, url_val)
                    return f'url(/browse?url={quote(url_val)})'
                
                style_css = re.sub(r'url\(\s*["\']([^"\')\s]+)["\']\s*\)', replace_block_url, style_css)
                style_css = re.sub(r'url\(\s*([^"\')\s]+)\s*\)', replace_block_url, style_css)
                style_tag.string = style_css
        
        # Inject JavaScript bridge and tracker blocker
            if ADVANCED_FEATURES:
                injection_html = get_injection_html()
                injection_script = soup.new_tag('script')
                injection_script.string = injection_html.replace('<script type="text/javascript">', '').replace('</script>', '')
                soup.head.append(injection_script)
            
            # Add Raccoon header bar
        header = soup.new_tag('div', **{'id': 'raccoon-header'})
        header['style'] = '''
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #050505;
            padding: 8px 12px;
            border-bottom: 1px solid #00ff41;
            z-index: 2147483647;
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        '''
        
        # Home link
        home_link = soup.new_tag('a', href='/')
        home_link['style'] = 'color: #00ff41; text-decoration: none; font-size: 20px;'
        home_link.string = '🦝'
        header.append(home_link)
        
        # URL bar
        url_input = soup.new_tag('input', **{'type': 'text', 'id': 'raccoon-url', 'value': response.url})
        url_input['style'] = '''
            flex: 1;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 8px 12px;
            color: #e0e0e0;
            font-size: 13px;
            outline: none;
        '''
        url_input['onkeydown'] = "if(event.key==='Enter'){window.location.href='/browse?url='+encodeURIComponent(this.value);}"
        header.append(url_input)
        
        # External link
        ext_link = soup.new_tag('a', href=response.url, target='_blank')
        ext_link['style'] = 'color: #888; text-decoration: none; font-size: 12px;'
        ext_link.string = '↗ Open in Browser'
        header.append(ext_link)
        
        # Inject header
        if soup.body:
            soup.body.insert(0, header)
            # Add padding to body
            existing_style = soup.body.get('style', '')
            soup.body['style'] = existing_style + ' padding-top: 50px !important;'
        
        return str(soup)
        
    except Exception as e:
        return f'''
        <html>
        <head>
            <title>Error - Raccoon Browser</title>
            <style>
                body {{ background: #0a0a0a; color: #00ff41; font-family: sans-serif; padding: 40px; }}
                a {{ color: #00ff41; }}
                .error {{ background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>⚠️ Failed to load page</h1>
            <div class="error">
                <p><strong>URL:</strong> {escape_html(url)}</p>
                <p><strong>Error:</strong> {escape_html(str(e))}</p>
            </div>
            <p><a href="/">← Back to Home</a></p>
        </body>
        </html>
        '''


def escape_html(text):
    """Escape HTML special characters"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


if __name__ == '__main__':
    port = int(os.environ.get('RACCOON_PORT', 5555))
    print(f"🦝 Raccoon Browser starting at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)