"""
🦝 Raccoon Browser - Fixed CSS/JS Handling
Properly rewrites all resource URLs for proxy browsing
"""

import os
import random
import requests
from flask import Flask, render_template, jsonify, request, Response
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote, urlparse, parse_qs, urljoin
from datetime import datetime, timezone
import re

# Import advanced modules
try:
    from session_manager import session_manager
    from js_injector import js_injector, get_injection_html
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Configuration
SEARXNG_INSTANCES = [
    'https://searx.be',
    'https://searx.org',
    'https://search.bus-hit.me',
]

def get_user_agent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"


def rewrite_css_urls(css_content, base_url):
    """Rewrite all url() references in CSS to go through proxy"""
    def replace_url(match):
        full_match = match.group(0)
        url = match.group(1) or match.group(2) or match.group(3)
        
        if not url:
            return full_match
        
        # Skip data URLs
        if url.startswith('data:'):
            return full_match
        
        # Make absolute URL
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = urljoin(base_url, url)
        elif not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        return f'url(/browse?url={quote(url)})'
    
    # Match url("..."), url('...'), or url(...)
    css_content = re.sub(r'url\(\s*["\']([^"\')\s]+)["\']\s*\)', replace_url, css_content)
    css_content = re.sub(r'url\(\s*([^"\')\s]+)\s*\)', replace_url, css_content)
    
    return css_content


def rewrite_html_resources(soup, base_url):
    """Rewrite all resource URLs in HTML to go through proxy"""
    
    # Remove CSP meta tags
    for meta in soup.find_all('meta', {'http-equiv': 'Content-Security-Policy'}):
        meta.decompose()
    for meta in soup.find_all('meta', {'http-equiv': 'Content-Security-Policy-Report-Only'}):
        meta.decompose()
    
    # Remove CSP headers would be ideal but we can't modify response headers from external sites
    
    # Rewrite all resource tags
    for tag in soup.find_all(['link', 'script', 'img', 'iframe', 'source', 'video', 'audio', 'track', 'embed', 'object']):
        if tag.name == 'link':
            # CSS stylesheets
            if tag.get('rel') == ['stylesheet'] or tag.get('type') == 'text/css':
                href = tag.get('href')
                if href and not href.startswith(('data:', 'javascript:')):
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = urljoin(base_url, href)
                    elif not href.startswith(('http://', 'https://')):
                        href = urljoin(base_url, href)
                    tag['href'] = f'/browse?url={quote(href)}'
        
        elif tag.name == 'script':
            src = tag.get('src')
            if src and not src.startswith(('data:', 'javascript:')):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                tag['src'] = f'/browse?url={quote(src)}'
        
        elif tag.name in ['img', 'iframe', 'source', 'video', 'audio', 'track', 'embed']:
            attr = 'src' if tag.name != 'a' else 'href'
            src = tag.get(attr)
            if src and not src.startswith(('data:', 'javascript:', 'mailto:')):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                tag[attr] = f'/browse?url={quote(src)}'
        
        elif tag.name == 'object':
            data = tag.get('data')
            if data and not data.startswith(('data:', 'javascript:')):
                if data.startswith('//'):
                    data = 'https:' + data
                elif data.startswith('/'):
                    data = urljoin(base_url, data)
                elif not data.startswith(('http://', 'https://')):
                    data = urljoin(base_url, data)
                tag['data'] = f'/browse?url={quote(data)}'
    
    # Rewrite anchor links
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href and not href.startswith(('data:', 'javascript:', 'mailto:', '#', 'tel:')):
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = urljoin(base_url, href)
            elif not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            a['href'] = f'/browse?url={quote(href)}'
    
    # Rewrite inline styles
    for tag in soup.find_all(style=True):
        style = tag['style']
        style = rewrite_css_urls(style, base_url)
        tag['style'] = style
    
    # Rewrite style blocks
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            style_tag.string = rewrite_css_urls(style_tag.string, base_url)
    
    return soup


@app.route('/browse')
def browse():
    """Browse URL through proxy with proper CSS/JS handling"""
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        headers = {
            'User-Agent': get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        content_type = response.headers.get('Content-Type', 'text/html')
        base_url = response.url
        
        # Handle images
        if 'image/' in content_type:
            return Response(response.content, mimetype=content_type)
        
        # Handle CSS - rewrite all URLs
        if 'text/css' in content_type:
            css = response.text
            css = rewrite_css_urls(css, base_url)
            return Response(css, mimetype='text/css')
        
        # Handle JavaScript - pass through as-is
        if 'javascript' in content_type:
            return Response(response.text, mimetype='application/javascript')
        
        # Handle HTML
        if 'text/html' not in content_type:
            return Response(response.content)
        
        # Parse and rewrite HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove CSP meta tags
        for meta in soup.find_all('meta', {'http-equiv': 'Content-Security-Policy'}):
            meta.decompose()
        for meta in soup.find_all('meta', {'http-equiv': 'Content-Security-Policy-Report-Only'}):
            meta.decompose()
        
        # Rewrite all resources
        soup = rewrite_html_resources(soup, base_url)
        
        # Add Raccoon header
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
        url_input = soup.new_tag('input', type='text', id='raccoon-url', value=response.url)
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
            soup.body['style'] = 'padding-top: 50px !important;'
        
        return Response(str(soup), mimetype='text/html')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'Raccoon Browser'})


if __name__ == '__main__':
    port = int(os.environ.get('RACCOON_PORT', 5555))
    print(f"🦝 Raccoon Browser starting at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
