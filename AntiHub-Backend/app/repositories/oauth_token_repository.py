"""
OAuth 令牌数据仓储
提供 OAuth 令牌数据的增删改查操作

重要说明：
- Repository 层不应该调用 commit()，事务管理由调用方（依赖注入）统一处理
- 这样可以避免连接被长时间占用，防止连接池耗尽
"""
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oauth_token import OAuthToken
from app.core.exceptions import DatabaseError


class OAuthTokenRepository:
    """OAuth 令牌数据仓储类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化仓储
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def get_by_id(self, token_id: int) -> Optional[OAuthToken]:
        """
        根据 ID 获取令牌
        
        Args:
            token_id: 令牌 ID
            
        Returns:
            OAuthToken 对象,不存在返回 None
        """
        result = await self.db.execute(
            select(OAuthToken).where(OAuthToken.id == token_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int) -> Optional[OAuthToken]:
        """
        根据用户 ID 获取令牌
        
        Args:
            user_id: 用户 ID
            
        Returns:
            OAuthToken 对象,不存在返回 None
        """
        result = await self.db.execute(
            select(OAuthToken).where(OAuthToken.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str],
        token_type: str,
        expires_at: datetime
    ) -> OAuthToken:
        """
        创建新的 OAuth 令牌记录
        
        注意：不调用 commit()，由调用方统一管理事务
        
        Args:
            user_id: 用户 ID
            access_token: 访问令牌
            refresh_token: 刷新令牌
            token_type: 令牌类型
            expires_at: 过期时间
            
        Returns:
            创建的 OAuthToken 对象
        """
        oauth_token = OAuthToken(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            expires_at=expires_at
        )
        
        self.db.add(oauth_token)
        await self.db.flush()  # 刷新以获取ID，但不提交事务
        await self.db.refresh(oauth_token)
        
        return oauth_token
    
    async def update(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str],
        token_type: str,
        expires_at: datetime
    ) -> OAuthToken:
        """
        更新用户的 OAuth 令牌
        如果令牌不存在则创建新记录
        
        注意：不调用 commit()，由调用方统一管理事务
        
        Args:
            user_id: 用户 ID
            access_token: 访问令牌
            refresh_token: 刷新令牌
            token_type: 令牌类型
            expires_at: 过期时间
            
        Returns:
            更新后的 OAuthToken 对象
        """
        # 查找现有令牌
        existing_token = await self.get_by_user_id(user_id)
        
        if existing_token:
            # 更新现有令牌
            existing_token.access_token = access_token
            existing_token.refresh_token = refresh_token
            existing_token.token_type = token_type
            existing_token.expires_at = expires_at
            
            await self.db.flush()  # 刷新但不提交
            await self.db.refresh(existing_token)
            
            return existing_token
        else:
            # 创建新令牌
            return await self.create(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type=token_type,
                expires_at=expires_at
            )
    
    async def delete_by_user_id(self, user_id: int) -> bool:
        """
        删除用户的 OAuth 令牌
        
        注意：不调用 commit()，由调用方统一管理事务
        
        Args:
            user_id: 用户 ID
            
        Returns:
            删除成功返回 True,令牌不存在返回 False
        """
        oauth_token = await self.get_by_user_id(user_id)
        if not oauth_token:
            return False
        
        await self.db.delete(oauth_token)
        await self.db.flush()  # 刷新但不提交
        
        return True
    
    async def is_token_expired(self, user_id: int) -> Optional[bool]:
        """
        检查用户的 OAuth 令牌是否已过期
        
        Args:
            user_id: 用户 ID
            
        Returns:
            已过期返回 True,未过期返回 False,令牌不存在返回 None
        """
        oauth_token = await self.get_by_user_id(user_id)
        if not oauth_token:
            return None
        
        return oauth_token.expires_at < datetime.utcnow()
    
    async def get_token_expire_time(self, user_id: int) -> Optional[datetime]:
        """
        获取用户 OAuth 令牌的过期时间
        
        Args:
            user_id: 用户 ID
            
        Returns:
            过期时间,令牌不存在返回 None
        """
        oauth_token = await self.get_by_user_id(user_id)
        if not oauth_token:
            return None
        
        return oauth_token.expires_at