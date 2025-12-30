"""
核心模块
提供配置、安全和异常处理功能
"""
from app.core.config import Settings, get_settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
    decode_token_without_verification,
    get_token_expire_time,
    get_token_remaining_seconds,
    extract_token_jti,
)
from app.core.exceptions import (
    BaseAPIException,
    AuthenticationError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    TokenBlacklistedError,
    OAuthError,
    InvalidOAuthStateError,
    OAuthTokenExchangeError,
    OAuthUserInfoError,
    DatabaseError,
    UserNotFoundError,
    UserAlreadyExistsError,
    DatabaseConnectionError,
    CacheError,
    RedisConnectionError,
    PermissionError,
    AccountDisabledError,
    AccountSilencedError,
    ValidationError,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Security
    "hash_password",
    "verify_password",
    "create_access_token",
    "verify_access_token",
    "decode_token_without_verification",
    "get_token_expire_time",
    "get_token_remaining_seconds",
    "extract_token_jti",
    # Exceptions
    "BaseAPIException",
    "AuthenticationError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "TokenExpiredError",
    "TokenBlacklistedError",
    "OAuthError",
    "InvalidOAuthStateError",
    "OAuthTokenExchangeError",
    "OAuthUserInfoError",
    "DatabaseError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "DatabaseConnectionError",
    "CacheError",
    "RedisConnectionError",
    "PermissionError",
    "AccountDisabledError",
    "AccountSilencedError",
    "ValidationError",
]