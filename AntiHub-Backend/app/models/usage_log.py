"""
使用记录模型
记录用户的API调用，用于统计
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class UsageLog(Base):
    """使用记录表"""
    
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    
    # 请求信息
    endpoint = Column(String(255), nullable=False)  # 调用的端点
    method = Column(String(10), nullable=False)  # HTTP方法
    model_name = Column(String(100), nullable=True)  # 使用的模型
    
    # 配额消耗
    quota_consumed = Column(Float, default=0.0, nullable=False)  # 消耗的配额
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # 关系
    user = relationship("User", backref="usage_logs")
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, user_id={self.user_id}, endpoint={self.endpoint})>"