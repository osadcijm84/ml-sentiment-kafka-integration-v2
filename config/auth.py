import os
import jwt
import hashlib
import secrets
import yaml
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any

class AuthConfig:
    """Authentication and authorization configuration"""
    
    def __init__(self):
        # Load secrets from secrets.yml (decrypted by Ansible Vault)
        try:
            with open("secrets.yml", "r") as f:
                secrets_data = yaml.safe_load(f)
        except FileNotFoundError:
            current_app.logger.error("secrets.yml not found. Ensure Ansible Vault has decrypted it.")
            secrets_data = {}

        self.secret_key = secrets_data.get("secret_key", os.getenv("SECRET_KEY", self._generate_secret_key()))
        self.token_expiration_hours = int(os.getenv("TOKEN_EXPIRATION_HOURS", "24"))
        self.api_key_header = "X-API-Key"
        
        # In production, these should be stored in a secure database
        self.api_keys = {
            secrets_data.get("api_key", os.getenv("API_KEY_1", self._generate_api_key())): "ml-client-1",
            os.getenv("API_KEY_2", self._generate_api_key()): "ml-client-2" # Keep this for now, can be moved to vault later
        }
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    def generate_token(self, user_id: str, client_name: str) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_id,
            "client_name": client_name,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiration_hours),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return client name"""
        return self.api_keys.get(api_key)
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

# Global auth configuration instance
auth_config = AuthConfig()

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get(auth_config.api_key_header)
        
        if not api_key:
            return jsonify({
                "error": "API key required",
                "message": f"Please provide API key in {auth_config.api_key_header} header"
            }), 401
        
        client_name = auth_config.verify_api_key(api_key)
        if not client_name:
            return jsonify({
                "error": "Invalid API key",
                "message": "The provided API key is not valid"
            }), 401
        
        # Add client info to request context
        request.client_name = client_name
        return f(*args, **kwargs)
    
    return decorated_function

def require_token(f):
    """Decorator to require JWT token authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                pass
        
        if not token:
            return jsonify({
                "error": "Token required",
                "message": "Please provide a valid JWT token in Authorization header"
            }), 401
        
        payload = auth_config.verify_token(token)
        if not payload:
            return jsonify({
                "error": "Invalid or expired token",
                "message": "The provided token is invalid or has expired"
            }), 401
        
        # Add user info to request context
        request.user_id = payload["user_id"]
        request.client_name = payload["client_name"]
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """Decorator for optional authentication (logs requests but doesn't block)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try API key first
        api_key = request.headers.get(auth_config.api_key_header)
        if api_key:
            client_name = auth_config.verify_api_key(api_key)
            if client_name:
                request.client_name = client_name
                request.authenticated = True
                return f(*args, **kwargs)
        
        # Try JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
                payload = auth_config.verify_token(token)
                if payload:
                    request.user_id = payload["user_id"]
                    request.client_name = payload["client_name"]
                    request.authenticated = True
                    return f(*args, **kwargs)
            except (IndexError, AttributeError):
                pass
        
        # No authentication provided
        request.authenticated = False
        request.client_name = "anonymous"
        return f(*args, **kwargs)
    
    return decorated_function



