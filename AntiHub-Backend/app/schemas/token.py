"""
令牌相关的 Pydantic Schema
定义 JWT 和 OAuth 令牌的数据模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ==================== JWT 令牌相关 ====================

class TokenPayload(BaseModel):
    """JWT 令牌 Payload"""
    
    sub: str = Field(..., description="Subject: 用户 ID")
    username: str = Field(..., description="用户名")
    exp: datetime = Field(..., description="过期时间")
    iat: datetime = Field(..., description="签发时间")
    jti: str = Field(..., description="JWT ID: 唯一标识符")
    type: Optional[str] = Field(default="access", description="令牌类型: access 或 refresh")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sub": "123",
                    "username": "johndoe",
                    "exp": "2024-12-31T23:59:59",
                    "iat": "2024-12-30T00:00:00",
                    "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "type": "access"
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """令牌响应"""
    
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: Optional[int] = Field(None, description="过期时间(秒)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400
                }
            ]
        }
    }


class TokenPairResponse(BaseModel):
    """令牌对响应（包含 access_token 和 refresh_token）"""
    
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="Access Token 过期时间(秒)")
    refresh_expires_in: int = Field(..., description="Refresh Token 过期时间(秒)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400,
                    "refresh_expires_in": 604800
                }
            ]
        }
    }


# ==================== OAuth 令牌相关 ====================

class OAuthTokenData(BaseModel):
    """OAuth 令牌数据"""
    
    access_token: str = Field(..., description="OAuth 访问令牌")
    refresh_token: Optional[str] = Field(None, description="OAuth 刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: Optional[int] = Field(None, description="过期时间(秒)")
    scope: Optional[str] = Field(None, description="令牌作用域")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "oauth_access_token_string",
                    "refresh_token": "oauth_refresh_token_string",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "scope": "read write"
                }
            ]
        }
    }


class OAuthTokenResponse(BaseModel):
    """OAuth 令牌响应(存储在数据库中的格式)"""
    
    id: int = Field(..., description="令牌记录 ID")
    user_id: int = Field(..., description="用户 ID")
    access_token: str = Field(..., description="OAuth 访问令牌")
    refresh_token: Optional[str] = Field(None, description="OAuth 刷新令牌")
    token_type: str = Field(..., description="令牌类型")
    expires_at: datetime = Field(..., description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class OAuthTokenCreate(BaseModel):
    """创建 OAuth 令牌记录"""
    
    user_id: int = Field(..., description="用户 ID")
    access_token: str = Field(..., description="OAuth 访问令牌")
    refresh_token: Optional[str] = Field(None, description="OAuth 刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_at: datetime = Field(..., description="过期时间")


class OAuthTokenUpdate(BaseModel):
    """更新 OAuth 令牌"""
    
    access_token: str = Field(..., description="OAuth 访问令牌")
    refresh_token: Optional[str] = Field(None, description="OAuth 刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_at: datetime = Field(..., description="过期时间")


# ==================== 令牌验证相关 ====================

class TokenVerifyRequest(BaseModel):
    """令牌验证请求"""
    
    token: str = Field(..., description="要验证的令牌")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    }


class TokenVerifyResponse(BaseModel):
    """令牌验证响应"""
    
    valid: bool = Field(..., description="令牌是否有效")
    payload: Optional[TokenPayload] = Field(None, description="令牌 payload")
    error: Optional[str] = Field(None, description="错误信息")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "valid": True,
                    "payload": {
                        "sub": "123",
                        "username": "johndoe",
                        "exp": "2024-12-31T23:59:59",
                        "iat": "2024-12-30T00:00:00",
                        "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "type": "access"
                    },
                    "error": None
                }
            ]
        }
    }