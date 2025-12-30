"""
数据库会话管理
实现异步数据库连接和会话管理

优化说明：
1. 调整连接池参数以提高并发处理能力
2. 缩短 pool_timeout 以快速发现问题
3. 缩短 pool_recycle 以避免使用过期连接
"""
from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 全局引擎实例
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    获取数据库引擎实例
    使用单例模式确保只创建一个引擎
    
    连接池配置说明：
    - pool_size: 保持的连接数，根据服务器配置调整
    - max_overflow: 允许的额外连接数，高峰期使用
    - pool_timeout: 获取连接的超时时间，不宜过长
    - pool_recycle: 连接回收时间，避免使用过期连接
    - pool_pre_ping: 使用前检查连接有效性
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        
        # 优化后的连接池参数
        # 对于 3 核 / 22G 的服务器，PostgreSQL 默认 max_connections=100
        # 优化：增加连接池大小以应对高并发场景
        pool_config = {
            "pool_size": 30,           # 基础连接池大小（从20增加到30）
            "max_overflow": 30,        # 最大溢出连接数（从20增加到30，总共最多60个连接）
            "pool_timeout": 10,        # 获取连接超时时间（秒），缩短以快速发现问题
            "pool_recycle": 1800,      # 连接回收时间（30分钟），避免使用过期连接
            "pool_pre_ping": True,     # 连接前检查连接是否有效，防止使用"半死不活"的连接
        }
        
        # 测试环境使用 NullPool
        if settings.app_env == "test":
            pool_config = {"poolclass": NullPool}
        else:
            pool_config["poolclass"] = QueuePool
        
        logger.info(
            f"创建数据库引擎，连接池配置: pool_size={pool_config.get('pool_size', 'N/A')}, "
            f"max_overflow={pool_config.get('max_overflow', 'N/A')}, "
            f"pool_timeout={pool_config.get('pool_timeout', 'N/A')}s"
        )
        
        _engine = create_async_engine(
            settings.database_url,
            echo=False,  # 关闭 SQL 日志
            **pool_config
        )
    
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    获取会话工厂
    """
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # 提交后不过期对象
            autocommit=False,
            autoflush=False,
        )
    
    return _async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    用于依赖注入
    
    重要说明：
    - 使用 async with 上下文管理器自动处理连接的获取和释放
    - 请求成功时自动 commit
    - 发生异常时自动 rollback
    - 上下文退出时自动关闭 session 并归还连接到连接池
    
    使用示例:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        # 注意：不需要显式调用 session.close()
        # async with 上下文管理器会自动处理连接的释放


async def init_db() -> None:
    """
    初始化数据库连接
    应在应用启动时调用
    """
    # 初始化引擎和会话工厂
    get_engine()
    get_session_maker()


async def close_db() -> None:
    """
    关闭数据库连接
    应在应用关闭时调用
    """
    global _engine, _async_session_maker
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
