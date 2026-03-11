"""
🦝 Raccoon Browser - JavaScript Injection Engine
Handles dynamic content and page manipulation
"""

import re
import json
from typing import Dict, List, Any, Optional


class JSInjector:
    """Manages JavaScript injection for pages"""
    
    def __init__(self):
        self.scripts = {}
        self.injected_patterns = []
    
    def register_script(self, name: str, script: str, inject_on: str = 'load'):
        """
        Register a script for injection
        
        Args:
            name: Script identifier
            script: JavaScript code
            inject_on: When to inject ('load', 'domcontentloaded', 'idle')
        """
        self.scripts[name] = {
            'script': script,
            'inject_on': inject_on,
            'enabled': True,
        }
    
    def get_script(self, name: str) -> Optional[Dict]:
        """Get registered script by name"""
        return self.scripts.get(name)
    
    def enable_script(self, name: str, enabled: bool = True):
        """Enable or disable a script"""
        if name in self.scripts:
            self.scripts[name]['enabled'] = enabled
    
    def get_injection_code(self, include_disabled: bool = False) -> str:
        """Get all enabled scripts as single injection block"""
        scripts = []
        for name, data in self.scripts.items():
            if include_disabled or data['enabled']:
                scripts.append(f"// === {name} ===\n{data['script']}")
        return '\n\n'.join(scripts)
    
    def inject_into_html(self, html: str) -> str:
        """Inject scripts into HTML document"""
        injection = self.get_injection_code()
        if not injection:
            return html
        
        script_tag = f'<script type="text/javascript">\n{injection}\n</script>'
        
        # Inject before </head> or </body>
        if '</head>' in html:
            return html.replace('</head>', f'{script_tag}\n</head>')
        elif '</body>' in html:
            return html.replace('</body>', f'{script_tag}\n</body>')
        else:
            return html + script_tag


# ============================================================================
# Built-in Scripts
# ============================================================================

TRACKER_BLOCKER_JS = """
(function() {
    // Raccoon Tracker Blocker
    const blockedDomains = [
        'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
        'facebook.net', 'facebook.com/tr', 'adservice.google.com',
        'ads.twitter.com', 'analytics.twitter.com', 'pixel.facebook.com',
        'scorecardresearch.com', 'quantserve.com', 'newrelic.com',
    ];
    
    let blockedCount = 0;
    
    // Block script requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        const urlStr = url.toString();
        if (blockedDomains.some(d => urlStr.includes(d))) {
            console.log('🦝 Blocked fetch:', urlStr);
            blockedCount++;
            return Promise.resolve(new Response('', { status: 200 }));
        }
        return originalFetch.apply(this, arguments);
    };
    
    // Block XHR
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        if (blockedDomains.some(d => url.includes(d))) {
            console.log('🦝 Blocked XHR:', url);
            blockedCount++;
            return;
        }
        return originalOpen.apply(this, arguments);
    };
    
    // Remove existing tracker scripts
    document.querySelectorAll('script[src]').forEach(script => {
        if (blockedDomains.some(d => script.src.includes(d))) {
            script.remove();
            blockedCount++;
        }
    });
    
    console.log('🦝 Raccoon Tracker Blocker active. Blocked:', blockedCount);
    window.raccoonBlockedCount = blockedCount;
})();
"""

COOKIE_MANAGER_JS = """
(function() {
    // Raccoon Cookie Manager
    window.raccoonCookies = {
        getAll: function() {
            return document.cookie.split('; ').reduce((acc, cookie) => {
                const [key, value] = cookie.split('=');
                acc[key] = value;
                return acc;
            }, {});
        },
        
        get: function(name) {
            const cookies = this.getAll();
            return cookies[name];
        },
        
        set: function(name, value, days = 30) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            document.cookie = `${name}=${value};expires=${date.toUTCString()};path=/`;
        },
        
        delete: function(name) {
            document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
        },
        
        clear: function() {
            document.cookie.split('; ').forEach(cookie => {
                const name = cookie.split('=')[0];
                this.delete(name);
            });
        }
    };
    
    console.log('🦝 Raccoon Cookie Manager loaded');
})();
"""

BRIDGE_JS = """
(function() {
    // Raccoon Browser Bridge
    window.raccoonBridge = {
        version: '0.2.0',
        
        // Get page info
        getPageInfo: function() {
            return {
                title: document.title,
                url: window.location.href,
                domain: window.location.hostname,
                readyState: document.readyState,
            };
        },
        
        // Get page content
        getContent: function(selector = 'body') {
            const el = document.querySelector(selector);
            return el ? el.innerText : '';
        },
        
        // Get all links
        getLinks: function() {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: a.innerText.trim(),
                href: a.href,
            }));
        },
        
        // Get all images
        getImages: function() {
            return Array.from(document.querySelectorAll('img[src]')).map(img => ({
                alt: img.alt,
                src: img.src,
            }));
        },
        
        // Execute custom JS
        exec: function(code) {
            try {
                return { success: true, result: eval(code) };
            } catch(e) {
                return { success: false, error: e.message };
            }
        },
        
        // Inject CSS
        injectCSS: function(css) {
            const style = document.createElement('style');
            style.textContent = css;
            document.head.appendChild(style);
            return true;
        },
        
        // Remove element
        remove: function(selector) {
            const count = document.querySelectorAll(selector).length;
            document.querySelectorAll(selector).forEach(el => el.remove());
            return count;
        },
        
        // Click element
        click: function(selector) {
            const el = document.querySelector(selector);
            if (el) {
                el.click();
                return true;
            }
            return false;
        },
        
        // Type into input
        type: function(selector, text) {
            const el = document.querySelector(selector);
            if (el) {
                el.value = text;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                return true;
            }
            return false;
        },
        
        // Scroll to element
        scrollTo: function(selector) {
            const el = document.querySelector(selector);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth' });
                return true;
            }
            return false;
        },
        
        // Take screenshot (requires backend support)
        screenshot: function() {
            return { message: 'Screenshot requires PyQt backend' };
        },
    };
    
    console.log('🦝 Raccoon Bridge v' + window.raccoonBridge.version + ' loaded');
})();
"""


# Global injector instance
js_injector = JSInjector()

# Register built-in scripts
js_injector.register_script('tracker_blocker', TRACKER_BLOCKER_JS, 'domcontentloaded')
js_injector.register_script('cookie_manager', COOKIE_MANAGER_JS, 'load')
js_injector.register_script('bridge', BRIDGE_JS, 'load')


def get_injection_html() -> str:
    """Get injection scripts as HTML script tag"""
    code = js_injector.get_injection_code()
    return f'<script type="text/javascript">\n{code}\n</script>'