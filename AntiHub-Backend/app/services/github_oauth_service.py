"""
GitHub OAuth 服务
专门处理 GitHub SSO 登录流程
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


class GitHubOAuthService:
    """GitHub OAuth 服务类"""
    
    def __init__(self, db: AsyncSession, redis: RedisClient):
        """
        初始化 GitHub OAuth 服务
        
        Args:
            db: 数据库会话
            redis: Redis 客户端
        """
        self.db = db
        self.redis = redis
        self.settings = get_settings()
        self.token_repo = OAuthTokenRepository(db)# GitHub OAuth 端点
        self.authorize_url = self.settings.github_authorize_url
        self.token_url = self.settings.github_token_url
        self.user_api_url = self.settings.github_user_api_url
    
    #==================== OAuth 授权流程 ====================
    
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
        state_key = f"github_oauth_state:{state}"
        return await self.redis.store_oauth_state(state_key, data, ttl)
    
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
        state_key = f"github_oauth_state:{state}"
        data = await self.redis.verify_oauth_state(state_key)
        if data is None:
            raise InvalidOAuthStateError(
                message="无效的 GitHub OAuth state",
                details={"state": state}
            )
        return data
    
    def generate_authorization_url(
        self,
        state: str,
        redirect_uri: Optional[str] = None,
        scope: str = "read:user user:email"
    ) -> str:
        """
        生成 GitHub OAuth 授权 URL
        
        Args:
            state: OAuth state 参数
            redirect_uri: 回调地址(可选)
            scope: 请求的权限范围
            
        Returns:
            授权 URL
        """
        params = {
            "client_id": self.settings.github_client_id,
            "redirect_uri": redirect_uri or self.settings.github_redirect_uri,
            "state": state,
            "scope": scope,
        }
        
        return f"{self.authorize_url}?{urlencode(params)}"
    
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
                    "client_id": self.settings.github_client_id,
                    "client_secret": self.settings.github_client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri or self.settings.github_redirect_uri,
                }
                
                # GitHub 需要 Accept header 来返回 JSON
                headers = {
                    "Accept": "application/json"
                }
                
                # 发送令牌交换请求
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise OAuthTokenExchangeError(
                        message="GitHub OAuth 令牌交换失败",
                        details={
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    )
                
                # 解析响应
                token_data = response.json()
                
                # 检查是否有错误
                if "error" in token_data:
                    raise OAuthTokenExchangeError(
                        message=f"GitHub OAuth 错误: {token_data.get('error_description', token_data.get('error'))}",
                        details=token_data
                    )
                
                return OAuthTokenData(
                    access_token=token_data.get("access_token"),
                    refresh_token=token_data.get("refresh_token"),
                    token_type=token_data.get("token_type", "bearer"),
                    expires_in=token_data.get("expires_in"),
                    scope=token_data.get("scope")
                )
                
        except httpx.HTTPError as e:
            raise OAuthTokenExchangeError(
                message="GitHub OAuth 令牌交换请求失败",
                details={"error": str(e)}
            )
        except Exception as e:
            if isinstance(e, OAuthTokenExchangeError):
                raise
            raise OAuthTokenExchangeError(
                message="GitHub OAuth 令牌交换失败",
                details={"error": str(e)}
            )
    
    # ==================== 用户信息获取 ====================
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        获取 GitHub 用户信息
        
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
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                response = await client.get(
                    self.user_api_url,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise OAuthUserInfoError(
                        message="获取 GitHub 用户信息失败",
                        details={
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    )
                
                # 解析用户信息
                user_info = response.json()
                
                # 标准化用户信息格式，使其与系统期望的格式一致
                standardized_info = {
                    "id": user_info.get("id"),
                    "username": user_info.get("login"),
                    "name": user_info.get("name"),
                    "email": user_info.get("email"),
                    "avatar_url": user_info.get("avatar_url"),
                    "bio": user_info.get("bio"),
                    "location": user_info.get("location"),
                    "html_url": user_info.get("html_url"),
                    "created_at": user_info.get("created_at"),
                    "provider": "github"
                }
                
                return standardized_info
                
        except httpx.HTTPError as e:
            raise OAuthUserInfoError(
                message="获取 GitHub 用户信息请求失败",
                details={"error": str(e)}
            )
        except Exception as e:
            if isinstance(e, OAuthUserInfoError):
                raise
            raise OAuthUserInfoError(
                message="获取 GitHub 用户信息失败",
                details={"error": str(e)}
            )
    
    async def get_user_emails(self, access_token: str) -> list[Dict[str, Any]]:
        """
        获取 GitHub 用户的邮箱列表
        
        Args:
            access_token: OAuth 访问令牌
            
        Returns:
            邮箱信息列表
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                response = await client.get(
                    f"{self.user_api_url}/emails",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                return []
                
        except Exception:
            return []
    
    # ==================== 辅助方法 ====================
    
    def calculate_token_expiry(
        self,
        expires_in: Optional[int] = None
    ) -> datetime:
        """
        计算令牌过期时间
        GitHub 的token 通常不会过期，如果没有 expires_in，设置为较长时间
        
        Args:
            expires_in: 过期时间(秒)，如果为 None 则设置为 1 年
            
        Returns:
            过期时间
        """
        if expires_in is None:
            # GitHub token 通常不会过期，设置为 1 年
            seconds = 365 * 24 * 3600
        else:
            seconds = expires_in
        return datetime.utcnow() + timedelta(seconds=seconds)