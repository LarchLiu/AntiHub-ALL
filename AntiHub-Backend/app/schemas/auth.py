"""
认证相关的 Pydantic Schema
定义登录、登出等认证相关的请求和响应模型
"""
from typing import Optional
from pydantic import BaseModel, Field


# ==================== 传统登录相关 ====================

class LoginRequest(BaseModel):
    """传统用户名密码登录请求"""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名"
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="密码"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "johndoe",
                    "password": "secretpassword123"
                }
            ]
        }
    }


class LoginResponse(BaseModel):
    """登录响应（包含 refresh token）"""
    
    access_token: str = Field(..., description="JWT 访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="Access Token 过期时间（秒）")
    user: "UserResponse" = Field(..., description="用户信息")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400,
                    "user": {
                        "id": 1,
                        "username": "johndoe",
                        "avatar_url": "https://example.com/avatar.jpg",
                        "trust_level": 1,
                        "is_active": True,
                        "is_silenced": False
                    }
                }
            ]
        }
    }


# ==================== Token 刷新相关 ====================

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    
    refresh_token: str = Field(..., description="刷新令牌")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    }


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应"""
    
    access_token: str = Field(..., description="新的 JWT 访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌（可选轮换）")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="Access Token 过期时间（秒）")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400
                }
            ]
        }
    }


# ==================== 登出相关 ====================

class LogoutRequest(BaseModel):
    """登出请求（可选提供 refresh token 以使其失效）"""
    
    refresh_token: Optional[str] = Field(None, description="刷新令牌（可选）")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    }


class LogoutResponse(BaseModel):
    """登出响应"""
    
    message: str = Field(default="登出成功", description="响应消息")
    success: bool = Field(default=True, description="是否成功")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "登出成功",
                    "success": True
                }
            ]
        }
    }


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应"""
    
    message: str = Field(..., description="响应消息")
    success: bool = Field(default=True, description="是否成功")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "操作成功",
                    "success": True
                }
            ]
        }
    }


# 避免循环导入,在文件末尾导入
from app.schemas.user import UserResponse

# 更新 LoginResponse 的前向引用
LoginResponse.model_rebuild()
