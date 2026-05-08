"""
Security module for Short Chain Commerce API.

Provides:
- JWT authentication
- API key validation
- Rate limiting
- Request validation
- Security headers
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import jwt
import redis
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
API_KEYS_FILE = Path(os.getenv("API_KEYS_FILE", "data/api_keys.json"))

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

security = HTTPBearer(auto_error=False)


def generate_jwt_token(user_id: str, roles: list = None) -> str:
    """
    Generate JWT access token.

    Args:
        user_id: User identifier
        roles: User roles

    Returns:
        JWT token string
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "roles": roles or ["user"],
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key."""
    return secrets.token_urlsafe(32)


def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Validate API key.

    Args:
        api_key: API key string

    Returns:
        Key metadata or None if invalid
    """
    if not API_KEYS_FILE.exists():
        return None

    import json

    with open(API_KEYS_FILE) as f:
        keys = json.load(f)

    hashed_key = hash_api_key(api_key)
    return keys.get(hashed_key)


def check_rate_limit(client_ip: str, limit: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW_SECONDS) -> bool:
    """
    Check if client has exceeded rate limit using Redis sliding window.

    Args:
        client_ip: Client IP address
        limit: Maximum requests allowed in window
        window: Window size in seconds

    Returns:
        True if request is allowed, False if rate limited
    """
    current_time = datetime.now().timestamp()
    key = f"rate_limit:{client_ip}"

    try:
        pipeline = redis_client.pipeline()
        # Remove old requests outside window
        pipeline.zremrangebyscore(key, 0, current_time - window)
        # Count current requests in window
        pipeline.zcard(key)
        # Add current request
        pipeline.zadd(key, {str(current_time): current_time})
        # Set expiry on the key to clean up inactive IPs
        pipeline.expire(key, window + 1)

        _, count, _, _ = pipeline.execute()

        return count < limit
    except redis.RedisError as e:
        # Log error and allow request to avoid blocking users on Redis failure
        print(f"Redis rate limit error: {e}")
        return True


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User payload or None
    """
    if not credentials:
        return None

    token = credentials.credentials
    return verify_jwt_token(token)


async def get_api_key_user(
    x_api_key: Optional[str] = Header(None),
) -> Optional[Dict[str, Any]]:
    """
    Get user from API key header.

    Args:
        x_api_key: API key from header

    Returns:
        User metadata or None
    """
    if not x_api_key:
        return None

    return validate_api_key(x_api_key)


def require_auth(user: Optional[Dict] = Depends(get_current_user)):
    """
    Dependency requiring valid JWT authentication.

    Args:
        user: User payload from get_current_user

    Raises:
        HTTPException: If not authenticated
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_api_key(user: Optional[Dict] = Depends(get_api_key_user)):
    """
    Dependency requiring valid API key.

    Args:
        user: User metadata from get_api_key_user

    Raises:
        HTTPException: If no valid API key
    """
    if not user:
        raise HTTPException(status_code=401, detail="Valid API key required")
    return user


def require_role(roles: list):
    """
    Factory for role-based access control dependency.

    Args:
        roles: List of required roles

    Returns:
        Dependency function
    """

    async def role_checker(user: Dict = Depends(require_auth)):
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )
        return user

    return role_checker


def add_security_headers(response):
    """Add security headers to response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


def sanitize_input(value: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not value:
        return ""

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", ";", "(", ")"]
    for char in dangerous_chars:
        value = value.replace(char, "")

    return value.strip()[:255]  # Limit length
