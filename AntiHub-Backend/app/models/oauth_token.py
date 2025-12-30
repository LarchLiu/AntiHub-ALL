"""
OAuth 令牌数据模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class OAuthToken(Base):
    """
    OAuth 令牌模型
    存储用户的 OAuth 访问令牌和刷新令牌
    """
    __tablename__ = "oauth_tokens"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 用户 ID（外键，唯一）
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="关联的用户 ID"
    )
    
    # 访问令牌
    access_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="OAuth 访问令牌"
    )
    
    # 刷新令牌
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="OAuth 刷新令牌"
    )
    
    # 令牌类型
    token_type: Mapped[str] = mapped_column(
        String(50),
        default="bearer",
        nullable=False,
        comment="令牌类型"
    )
    
    # 过期时间
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="令牌过期时间"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    
    # 关系定义（用于方便查询）
    user: Mapped["User"] = relationship(
        "User",
        back_populates="oauth_token",
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return f"<OAuthToken(id={self.id}, user_id={self.user_id}, expires_at='{self.expires_at}')>"