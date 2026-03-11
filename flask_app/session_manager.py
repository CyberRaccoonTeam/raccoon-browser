"""
🦝 Raccoon Browser - Cookie & Session Manager
Handles cookies, sessions, and local storage
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path

class SessionManager:
    """Manages browser sessions with cookies and storage"""
    
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir or '/tmp/raccoon_sessions')
        self.data_dir.mkdir(exist_ok=True)
        self.sessions_file = self.data_dir / 'sessions.json'
        self.sessions = self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from disk"""
        if self.sessions_file.exists():
            try:
                return json.loads(self.sessions_file.read_text())
            except:
                return {}
        return {}
    
    def _save_sessions(self):
        """Save sessions to disk"""
        self.sessions_file.write_text(json.dumps(self.sessions, indent=2))
    
    def create_session(self, name=None):
        """Create a new browser session"""
        session_id = secrets.token_hex(16)
        self.sessions[session_id] = {
            'id': session_id,
            'name': name or f'Session {len(self.sessions) + 1}',
            'created_at': datetime.utcnow().isoformat(),
            'last_used': datetime.utcnow().isoformat(),
            'cookies': {},
            'local_storage': {},
            'history': [],
            'bookmarks': [],
        }
        self._save_sessions()
        return self.sessions[session_id]
    
    def get_session(self, session_id):
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def get_all_sessions(self):
        """Get all sessions"""
        return list(self.sessions.values())
    
    def delete_session(self, session_id):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            return True
        return False
    
    def add_cookie(self, session_id, domain, cookie_data):
        """Add a cookie to session"""
        if session_id not in self.sessions:
            return False
        
        if domain not in self.sessions[session_id]['cookies']:
            self.sessions[session_id]['cookies'][domain] = []
        
        self.sessions[session_id]['cookies'][domain].append({
            **cookie_data,
            'created_at': datetime.utcnow().isoformat(),
        })
        self._save_sessions()
        return True
    
    def get_cookies(self, session_id, domain=None):
        """Get cookies for session, optionally filtered by domain"""
        if session_id not in self.sessions:
            return {}
        
        cookies = self.sessions[session_id]['cookies']
        if domain:
            return cookies.get(domain, [])
        return cookies
    
    def clear_cookies(self, session_id, domain=None):
        """Clear cookies for session"""
        if session_id not in self.sessions:
            return False
        
        if domain:
            self.sessions[session_id]['cookies'].pop(domain, None)
        else:
            self.sessions[session_id]['cookies'] = {}
        
        self._save_sessions()
        return True
    
    def add_history(self, session_id, url, title=None):
        """Add URL to session history"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]['history'].append({
            'url': url,
            'title': title or url,
            'visited_at': datetime.utcnow().isoformat(),
        })
        
        # Keep last 100 history items
        self.sessions[session_id]['history'] = self.sessions[session_id]['history'][-100:]
        self._save_sessions()
        return True
    
    def get_history(self, session_id, limit=50):
        """Get browsing history for session"""
        if session_id not in self.sessions:
            return []
        return self.sessions[session_id]['history'][-limit:]
    
    def clear_history(self, session_id):
        """Clear browsing history"""
        if session_id not in self.sessions:
            return False
        self.sessions[session_id]['history'] = []
        self._save_sessions()
        return True
    
    def set_local_storage(self, session_id, origin, key, value):
        """Set local storage item"""
        if session_id not in self.sessions:
            return False
        
        if origin not in self.sessions[session_id]['local_storage']:
            self.sessions[session_id]['local_storage'][origin] = {}
        
        self.sessions[session_id]['local_storage'][origin][key] = {
            'value': value,
            'set_at': datetime.utcnow().isoformat(),
        }
        self._save_sessions()
        return True
    
    def get_local_storage(self, session_id, origin=None, key=None):
        """Get local storage items"""
        if session_id not in self.sessions:
            return {}
        
        storage = self.sessions[session_id]['local_storage']
        
        if origin and key:
            return storage.get(origin, {}).get(key, {}).get('value')
        elif origin:
            return {k: v['value'] for k, v in storage.get(origin, {}).items()}
        return storage


# Global session manager instance
session_manager = SessionManager()