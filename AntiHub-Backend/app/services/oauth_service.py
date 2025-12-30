"""
OAuth 服务
提供 OAuth 授权流程、令牌交换、用户信息获取等功能
"""
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    OAuthError,
    InvalidOAuthStateError,
    OAuthTokenExchangeError,
    OAuthUserInfoError,
)
from app.cache.redis_client import RedisClient
from app.repositories.oauth_token_repository import OAuthTokenRepository
from app.schemas.token import OAuthTokenData


class OAuthService:
    """OAuth 服务类"""
    
    def __init__(self, db: AsyncSession, redis: RedisClient):
        """
        初始化 OAuth 服务
        
        Args:
            db: 数据库会话
            redis: Redis 客户端
        """
        self.db = db
        self.redis = redis
        self.settings = get_settings()
        self.token_repo = OAuthTokenRepository(db)
    
    # ==================== OAuth 授权流程 ====================
    
    def generate_state(self) -> str:
        """
        生成 OAuth state 参数
        
        Returns:
            随机 state 字符串
        """
        return secrets.token_urlsafe(32)
    
    async def store_state(
        self,
        state: str,
        data: Optional[Dict[str, Any]] = None,
        ttl: int = 600  # 10分钟
    ) -> bool:
        """
        存储 OAuth state
        
        Args:
            state: OAuth state 字符串
            data: 额外的状态数据
            ttl: 有效期(秒)
            
        Returns:
            存储成功返回 True
        """
        return await self.redis.store_oauth_state(state, data, ttl)
    
    async def verify_state(self, state: str) -> Optional[Dict[str, Any]]:
        """
        验证 OAuth state
        验证后会自动删除 state
        
        Args:
            state: OAuth state 字符串
            
        Returns:
            state 有效则返回存储的数据,无效返回 None
            
        Raises:
            InvalidOAuthStateError: state 无效
        """
        data = await self.redis.verify_oauth_state(state)
        if data is None:
            raise InvalidOAuthStateError(
                message="无效的 OAuth state",
                details={"state": state}
            )
        return data
    
    def generate_authorization_url(
        self,
        state: str,
        redirect_uri: Optional[str] = None
    ) -> str:
        """
        生成 OAuth 授权 URL
        
        Args:
            state: OAuth state 参数
            redirect_uri: 回调地址(可选)
            
        Returns:
            授权 URL
        """
        params = {
            "client_id": self.settings.oauth_client_id,
            "response_type": "code",
            "state": state,
            "redirect_uri": redirect_uri or self.settings.oauth_redirect_uri,
        }
        
        base_url = self.settings.oauth_authorization_endpoint
        return f"{base_url}?{urlencode(params)}"
    
    # ==================== 令牌交换 ====================
    
    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: Optional[str] = None
    ) -> OAuthTokenData:
        """
        使用授权码交换访问令牌
        
        Args:
            code: OAuth 授权码
            redirect_uri: 回调地址(可选)
            
        Returns:
            OAuth 令牌数据
            
        Raises:
            OAuthTokenExchangeError: 令牌交换失败
        """
        try:
            async with httpx.AsyncClient() as client:
                # 准备请求参数
                data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri or self.settings.oauth_redirect_uri,
                }
                
                # 使用 Basic Auth 传递 client_id 和 client_secret
                auth = (
                    self.settings.oauth_client_id,
                    self.settings.oauth_client_secret
                )
                
                # 发送令牌交换请求
                response = await client.post(
                    self.settings.oauth_token_endpoint,
                    data=data,
                    auth=auth,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise OAuthTokenExchangeError(
                        message="OAuth 令牌交换失败",
                        details={
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    )
                
                # 解析响应
                token_data = response.json()
                
                return OAuthTokenData(
                    access_token=token_data.get("access_token"),
                    refresh_token=token_data.get("refresh_token"),
                    token_type=token_data.get("token_type", "bearer"),
                    expires_in=token_data.get("expires_in"),
                    scope=token_data.get("scope")
                )
                
        except httpx.HTTPError as e:
            raise OAuthTokenExchangeError(
                message="OAuth 令牌交换请求失败",
                details={"error": str(e)}
            )
        except Exception as e:
            raise OAuthTokenExchangeError(
                message="OAuth 令牌交换失败",
                details={"error": str(e)}
            )
    
    # ==================== 用户信息获取 ====================
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        获取 OAuth 用户信息
        
        Args:
            access_token: OAuth 访问令牌
            
        Returns:
            用户信息字典
            
        Raises:
            OAuthUserInfoError: 获取用户信息失败
        """
        try:
            async with httpx.AsyncClient() as client:
                # 使用访问令牌请求用户信息
                headers = {
                    "Authorization": f"Bearer {access_token}"
                }
                
                response = await client.get(
                    self.settings.oauth_user_info_endpoint,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise OAuthUserInfoError(
                        message="获取用户信息失败",
                        details={
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    )
                
                # 解析用户信息
                user_info = response.json()
                
                return user_info
                
        except httpx.HTTPError as e:
            raise OAuthUserInfoError(
                message="获取用户信息请求失败",
                details={"error": str(e)}
            )
        except Exception as e:
            raise OAuthUserInfoError(
                message="获取用户信息失败",
                details={"error": str(e)}
            )
    
    # ==================== 令牌刷新 ====================
    
    async def should_refresh_token(self, user_id: int) -> bool:
        """
        检查是否需要刷新令牌
        在令牌过期前 5 分钟触发刷新
        
        Args:
            user_id: 用户 ID
            
        Returns:
            需要刷新返回 True
        """
        oauth_token = await self.token_repo.get_by_user_id(user_id)
        if not oauth_token:
            return False
        
        # 计算令牌是否在过期前 5 分钟内
        time_until_expiry = oauth_token.expires_at - datetime.utcnow()
        return time_until_expiry.total_seconds() <= 300  # 5分钟
    
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> OAuthTokenData:
        """
        使用刷新令牌获取新的访问令牌
        
        Args:
            refresh_token: OAuth 刷新令牌
            
        Returns:
            新的 OAuth 令牌数据
            
        Raises:
            OAuthTokenExchangeError: 令牌刷新失败
        """
        try:
            async with httpx.AsyncClient() as client:
                # 准备请求参数
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }
                
                # 使用 Basic Auth
                auth = (
                    self.settings.oauth_client_id,
                    self.settings.oauth_client_secret
                )
                
                # 发送刷新令牌请求
                response = await client.post(
                    self.settings.oauth_token_endpoint,
                    data=data,
                    auth=auth,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise OAuthTokenExchangeError(
                        message="OAuth 令牌刷新失败",
                        details={
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    )
                
                # 解析响应
                token_data = response.json()
                
                return OAuthTokenData(
                    access_token=token_data.get("access_token"),
                    refresh_token=token_data.get("refresh_token") or refresh_token,
                    token_type=token_data.get("token_type", "bearer"),
                    expires_in=token_data.get("expires_in"),
                    scope=token_data.get("scope")
                )
                
        except httpx.HTTPError as e:
            raise OAuthTokenExchangeError(
                message="OAuth 令牌刷新请求失败",
                details={"error": str(e)}
            )
        except Exception as e:
            raise OAuthTokenExchangeError(
                message="OAuth 令牌刷新失败",
                details={"error": str(e)}
            )
    
    # ==================== 辅助方法 ====================
    
    def calculate_token_expiry(
        self,
        expires_in: Optional[int] = None
    ) -> datetime:
        """
        计算令牌过期时间
        
        Args:
            expires_in: 过期时间(秒),默认 3600
            
        Returns:
            过期时间
        """
        seconds = expires_in or 3600
        return datetime.utcnow() + timedelta(seconds=seconds)