"""
Plug-in API密钥数据模型
存储用户的plug-in-api密钥
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class PluginAPIKey(Base):
    """
    Plug-in API密钥模型
    存储用户在plug-in-api系统中的API密钥
    """
    __tablename__ = "plugin_api_keys"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 用户ID（外键）
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="用户ID"
    )
    
    # Plug-in API密钥（加密存储）
    api_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="用户的plug-in API密钥（加密存储）"
    )
    
    # Plug-in API用户ID
    plugin_user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="plug-in-api系统中的用户ID"
    )
    
    # 密钥状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="密钥是否激活"
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
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后使用时间"
    )
    
    # 关系定义
    user: Mapped["User"] = relationship(
        "User",
        back_populates="plugin_api_key"
    )
    
    def __repr__(self) -> str:
        return f"<PluginAPIKey(id={self.id}, user_id={self.user_id}, plugin_user_id='{self.plugin_user_id}')>"