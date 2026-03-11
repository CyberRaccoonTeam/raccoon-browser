"""
🦝 Raccoon Browser - Flask Backend API
Privacy-focused search and navigation services

"Digging through the web so you don't have to."
"""

import os
import random
import hashlib
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Allow Electron renderer to communicate

# Configuration
SEARXNG_INSTANCES = [
    'https://search.bus-hit.me',
    'https://search.projectsegfau.lt',
    'https://search.privacyredirect.com',
    'https://searx.be',
    'https://search.sapti.me',
]

# Tracker domains to block
TRACKER_DOMAINS = [
    'google-analytics.com',
    'googletagmanager.com',
    'doubleclick.net',
    'facebook.net',
    'facebook.com/tr',
    'connect.facebook.net',
    'adservice.google.com',
    'ads.twitter.com',
    'analytics.twitter.com',
    'pixel.facebook.com',
    'scorecardresearch.com',
    'quantserve.com',
    'newrelic.com',
]

# Privacy-respecting domains (bonus in ranking)
PRIVACY_DOMAINS = [
    'wikipedia.org',
    'mozilla.org',
    'eff.org',
    'privacytools.io',
    'protonmail.com',
    'duckduckgo.com',
    'github.com',
]


def get_user_agent():
    """Generate privacy-focused user agent"""
    version = "0.1.0"
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Raccoon/{version}"


def pick_searxng_instance():
    """Randomly select a SearXNG instance for load distribution"""
    return random.choice(SEARXNG_INSTANCES)


def apply_raccoon_ranking(results, query):
    """
    Custom ranking algorithm for search results.
    Prioritizes privacy-friendly sites and relevance.
    """
    ranked = []
    
    for result in results:
        score = 100  # Base score
        url = result.get('url', '')
        title = result.get('title', '')
        
        # Privacy bonus: HTTPS
        if url.startswith('https://'):
            score += 15
        
        # Privacy bonus: Known privacy-respecting domains
        for domain in PRIVACY_DOMAINS:
            if domain in url:
                score += 25
                break
        
        # Privacy penalty: Tracker-heavy domains
        for domain in ['facebook.com', 'google.com', 'twitter.com', 'tiktok.com', 'instagram.com']:
            if domain in url:
                score -= 20
                break
        
        # Relevance: Title match
        if query.lower() in title.lower():
            score += 10
        
        # Relevance: URL contains query terms
        query_terms = query.lower().split()
        for term in query_terms:
            if term in url.lower():
                score += 5
        
        ranked.append({
            **result,
            'raccoon_score': score,
        })
    
    # Sort by score descending
    return sorted(ranked, key=lambda x: x.get('raccoon_score', 0), reverse=True)


# ============================================================================
# API Routes
# ============================================================================

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Raccoon Browser Backend',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/search', methods=['POST'])
def search():
    """
    Perform a search using SearXNG or DuckDuckGo fallback.
    Zero-tracking, anonymous meta-search.
    """
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'No query provided'
        }), 400
    
    # Try SearXNG first
    try:
        instance = pick_searxng_instance()
        
        search_url = f"{instance}/search"
        params = {
            'q': query,
            'format': 'json',
        }
        headers = {
            'User-Agent': get_user_agent(),
            'Accept': 'application/json',
        }
        
        response = requests.get(
            search_url,
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                results = json_data.get('results', [])
                
                if results:
                    ranked_results = apply_raccoon_ranking(results, query)
                    return jsonify({
                        'success': True,
                        'query': query,
                        'instance': instance,
                        'total': len(ranked_results),
                        'results': ranked_results[:20],
                    })
            except:
                pass  # Fall through to DuckDuckGo
    except:
        pass  # Fall through to DuckDuckGo
    
    # Fallback: DuckDuckGo HTML search (more reliable)
    try:
        results = duckduckgo_search(query)
        ranked_results = apply_raccoon_ranking(results, query)
        
        return jsonify({
            'success': True,
            'query': query,
            'instance': 'DuckDuckGo',
            'total': len(ranked_results),
            'results': ranked_results[:20],
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500


def duckduckgo_search(query):
    """Fallback search using DuckDuckGo Instant Answer API + HTML scrape"""
    from urllib.parse import unquote, urlparse, parse_qs, quote
    
    results = []
    
    # Method 1: DuckDuckGo Instant Answer API (reliable)
    try:
        api_url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1"
        headers = {'User-Agent': get_user_agent()}
        
        response = requests.get(api_url, headers=headers, timeout=10)
        data = response.json()
        
        # Get related topics
        for topic in data.get('RelatedTopics', [])[:10]:
            if isinstance(topic, dict) and 'FirstURL' in topic:
                results.append({
                    'title': topic.get('Text', '').split(' - ')[0][:100],
                    'url': topic.get('FirstURL', ''),
                    'content': topic.get('Text', '')[:200],
                })
    except Exception as e:
        print(f"DDG API error: {e}")
    
    # Method 2: If API doesn't give enough, try Brave Search (no auth needed)
    if len(results) < 5:
        try:
            brave_results = brave_search(query)
            results.extend(brave_results)
        except Exception as e:
            print(f"Brave search error: {e}")
    
    # Method 3: Wikipedia search as final fallback
    if len(results) < 3:
        try:
            wiki_results = wikipedia_search(query)
            results.extend(wiki_results)
        except Exception as e:
            print(f"Wikipedia search error: {e}")
    
    return results[:15]


def brave_search(query):
    """Search using Brave Search (no API key required for basic use)"""
    from urllib.parse import quote
    
    url = f"https://search.brave.com/search?q={quote(query)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html',
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    for item in soup.select('div.snippet')[:10]:
        title_elem = item.select_one('a')
        desc_elem = item.select_one('p')
        
        if title_elem:
            results.append({
                'title': title_elem.get_text(strip=True)[:100],
                'url': title_elem.get('href', ''),
                'content': desc_elem.get_text(strip=True)[:200] if desc_elem else '',
            })
    
    return results


def wikipedia_search(query):
    """Search Wikipedia API (very reliable, no auth)"""
    from urllib.parse import quote
    import json
    
    url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote(query)}&limit=5&format=json"
    headers = {'User-Agent': get_user_agent()}
    
    response = requests.get(url, headers=headers, timeout=10)
    data = response.json()
    
    results = []
    if len(data) >= 4:
        titles = data[1]
        urls = data[3]
        
        for title, url in zip(titles, urls):
            results.append({
                'title': title,
                'url': url,
                'content': f'Wikipedia article about {title}',
            })
    
    return results


@app.route('/api/check-trackers', methods=['POST'])
def check_trackers():
    """
    Check a URL for known trackers.
    Returns list of blocked tracker domains.
    """
    data = request.get_json()
    url = data.get('url', '')
    
    blocked = []
    for domain in TRACKER_DOMAINS:
        if domain in url:
            blocked.append(domain)
    
    return jsonify({
        'success': True,
        'url': url,
        'trackers_found': len(blocked),
        'blocked_domains': blocked,
        'is_safe': len(blocked) == 0
    })


@app.route('/api/check-privacy', methods=['POST'])
def check_privacy():
    """
    Get privacy score for a URL.
    """
    data = request.get_json()
    url = data.get('url', '')
    
    score = 100
    
    # HTTPS bonus
    if url.startswith('https://'):
        score += 10
    
    # Tracker penalty
    for domain in TRACKER_DOMAINS:
        if domain in url:
            score -= 5
    
    # Privacy domain bonus
    for domain in PRIVACY_DOMAINS:
        if domain in url:
            score += 15
            break
    
    # Clamp score
    score = max(0, min(100, score))
    
    return jsonify({
        'success': True,
        'url': url,
        'privacy_score': score,
        'rating': 'excellent' if score >= 80 else 'good' if score >= 60 else 'moderate' if score >= 40 else 'poor'
    })


@app.route('/api/fetch-page', methods=['POST'])
def fetch_page():
    """
    Fetch and extract content from a URL.
    Returns clean text for reading mode.
    """
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({
            'success': False,
            'error': 'No URL provided'
        }), 400
    
    try:
        headers = {
            'User-Agent': get_user_agent(),
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript']):
            tag.decompose()
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else ''
        
        # Extract main content
        main = soup.find('main') or soup.find('article') or soup.find('body')
        content = main.get_text(separator='\n', strip=True) if main else ''
        
        # Truncate
        max_chars = 5000
        if len(content) > max_chars:
            content = content[:max_chars] + '\n\n[... truncated ...]'
        
        return jsonify({
            'success': True,
            'url': url,
            'title': title_text,
            'content': content,
            'length': len(content)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/suggestions', methods=['GET'])
def suggestions():
    """
    Get search suggestions for autocomplete.
    Uses DuckDuckGo suggestions API (no tracking).
    """
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'suggestions': []})
    
    try:
        # DuckDuckGo suggestions (privacy-friendly)
        url = f"https://duckduckgo.com/ac/?q={query}&type=list"
        headers = {'User-Agent': get_user_agent()}
        
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        suggestions = data[1] if len(data) > 1 else []
        
        return jsonify({
            'success': True,
            'query': query,
            'suggestions': suggestions[:8]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'suggestions': []
        })


# ============================================================================
# Run Server
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('RACCOON_PORT', 5555))
    print(f"🦝 Raccoon Browser Backend starting on port {port}")
    app.run(host='127.0.0.1', port=port, debug=True)