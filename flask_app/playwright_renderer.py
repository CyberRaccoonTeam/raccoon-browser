"""
🦝 Raccoon Browser - Playwright Renderer
Full browser rendering for JS-heavy sites
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import re


# Sites known to be JS-heavy (React SPAs, etc.)
JS_HEAVY_SITES = [
    'github.com',
    'twitter.com', 'x.com',
    'facebook.com',
    'instagram.com',
    'linkedin.com',
    'reddit.com',
    'youtube.com',
    'gmail.com',
    'sheets.google.com',
    'docs.google.com',
    'notion.so',
    'figma.com',
    'canva.com',
    'airtable.com',
]


def is_js_heavy_site(url):
    """Detect if a site is likely JS-heavy (SPA)"""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    
    # Check against known JS-heavy sites
    for site in JS_HEAVY_SITES:
        if site in domain:
            return True
    
    return False


def render_with_playwright(url, timeout=15000):
    """
    Render a full page using Playwright (headless Chromium)
    Returns: (html, success, error_message)
    """
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                ]
            )
            
            # Create context with privacy settings
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Raccoon/0.2.0",
                java_script_enabled=True,
            )
            
            page = context.new_page()
            
            # Block trackers
            page.route("**/*", lambda route: route.abort() if _is_tracker(route.request.url) else route.continue_())
            
            # Navigate and wait for network idle
            try:
                page.goto(url, wait_until='networkidle', timeout=timeout)
            except PlaywrightTimeout:
                # If networkidle times out, just wait for load
                page.goto(url, wait_until='load', timeout=timeout)
            
            # Wait a bit for any final JS to execute
            page.wait_for_timeout(2000)
            
            # Get the fully rendered HTML
            html = page.content()
            
            # Get page title
            title = page.title()
            
            browser.close()
            
            return html, True, None
            
    except Exception as e:
        error_msg = str(e)
        return None, False, error_msg


def _is_tracker(url):
    """Check if URL is a known tracker"""
    tracker_patterns = [
        'google-analytics', 'googletagmanager', 'doubleclick',
        'facebook.net/tr', 'facebook.com/tr',
        'adservice.google', 'ads.twitter', 'analytics.twitter',
        'hotjar', 'crazyegg', 'mouseflow', 'clicktale',
        'fullstory', 'mixpanel', 'amplitude', 'segment',
        'heap.io', 'optimizely', 'newrelic', 'pingdom',
        'taboola', 'outbrain', 'criteo', 'adnxs',
    ]
    
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in tracker_patterns)


def get_site_info(url):
    """Get compatibility info for a site"""
    from urllib.parse import urlparse
    
    domain = urlparse(url).netloc.lower()
    is_js_heavy = is_js_heavy_site(url)
    
    info = {
        'url': url,
        'domain': domain,
        'is_js_heavy': is_js_heavy,
        'rendering_mode': 'playwright' if is_js_heavy else 'proxy',
        'warnings': [],
        'tips': [],
    }
    
    if is_js_heavy:
        info['warnings'].append('This is a JavaScript-heavy site (React/Angular/Vue SPA)')
        info['warnings'].append('Some features may not work in proxy mode')
        info['tips'].append('Use "Full Render" button for best experience')
        info['tips'].append('Or click "Open in Browser" for native browsing')
    
    if 'github.com' in domain:
        info['tips'].append('GitHub works best with Full Render mode')
    
    return info
