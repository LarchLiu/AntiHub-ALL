"""
健康检查 API 路由
提供系统健康状态检查端点
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_redis
from app.cache.redis_client import RedisClient


router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get(
    "",
    summary="健康检查",
    description="检查系统各组件的健康状态"
)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
    redis: RedisClient = Depends(get_redis)
) -> Dict[str, Any]:
    """
    健康检查端点
    
    检查以下组件的状态:
    - API 服务本身
    - PostgreSQL 数据库连接
    - Redis 缓存连接
    
    返回各组件的健康状态
    """
    health_status = {
        "status": "healthy",
        "components": {}
    }
    
    # 检查 API 服务
    health_status["components"]["api"] = {
        "status": "healthy",
        "message": "API 服务运行正常"
    }
    
    # 检查 PostgreSQL 数据库连接
    try:
        # 执行简单查询测试连接
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "数据库连接正常",
            "type": "PostgreSQL"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"数据库连接失败",
            "type": "PostgreSQL"
        }
    
    # 检查 Redis 缓存连接
    try:
        # 执行 ping 测试连接
        ping_result = await redis.ping()
        
        if ping_result:
            health_status["components"]["cache"] = {
                "status": "healthy",
                "message": "缓存连接正常",
                "type": "Redis"
            }
        else:
            health_status["status"] = "unhealthy"
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "message": "Redis ping 失败",
                "type": "Redis"
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "message": f"缓存连接失败",
            "type": "Redis"
        }
    
    # 根据整体状态设置 HTTP 状态码
    status_code = (
        status.HTTP_200_OK 
        if health_status["status"] == "healthy" 
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return health_status