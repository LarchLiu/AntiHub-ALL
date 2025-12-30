"""
SQLAlchemy Base 类定义
所有数据模型都应继承此 Base 类
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass
