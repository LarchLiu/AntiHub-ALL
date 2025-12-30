"""
Pydantic Schema 模块
定义所有数据验证和序列化模型
"""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    OAuthCallbackParams,
    OAuthInitiateResponse,
    LogoutResponse,
    MessageResponse,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    UserProfile,
    OAuthUserCreate,
)
from app.schemas.token import (
    TokenPayload,
    TokenResponse,
    OAuthTokenData,
    OAuthTokenResponse,
    OAuthTokenCreate,
    OAuthTokenUpdate,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from app.schemas.plugin_api import (
    PluginAPIKeyCreate,
    PluginAPIKeyResponse,
    PluginAPIKeyUpdate,
    CreatePluginUserRequest,
    CreatePluginUserResponse,
    OAuthAuthorizeRequest,
    OAuthAuthorizeResponse,
    OAuthCallbackRequest,
    UpdateCookiePreferenceRequest,
    UpdateAccountStatusRequest,
    ChatCompletionRequest,
    QuotaConsumptionQuery,
    PluginAPIResponse,
)

__all__ = [
    # Auth schemas
    "LoginRequest",
    "LoginResponse",
    "OAuthCallbackParams",
    "OAuthInitiateResponse",
    "LogoutResponse",
    "MessageResponse",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "UserProfile",
    "OAuthUserCreate",
    # Token schemas
    "TokenPayload",
    "TokenResponse",
    "OAuthTokenData",
    "OAuthTokenResponse",
    "OAuthTokenCreate",
    "OAuthTokenUpdate",
    "TokenVerifyRequest",
    "TokenVerifyResponse",
    # Plug-in API schemas
    "PluginAPIKeyCreate",
    "PluginAPIKeyResponse",
    "PluginAPIKeyUpdate",
    "CreatePluginUserRequest",
    "CreatePluginUserResponse",
    "OAuthAuthorizeRequest",
    "OAuthAuthorizeResponse",
    "OAuthCallbackRequest",
    "UpdateCookiePreferenceRequest",
    "UpdateAccountStatusRequest",
    "ChatCompletionRequest",
    "QuotaConsumptionQuery",
    "PluginAPIResponse",
]