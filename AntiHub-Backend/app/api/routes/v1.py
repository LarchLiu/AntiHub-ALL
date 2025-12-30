"""
OpenAI兼容的API端点
支持API key或JWT token认证
根据API key的config_type自动选择Antigravity或Kiro配置
用户通过我们的key/token调用，我们再用plug-in key调用plug-in-api
"""
from typing import List, Dict, Any, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_flexible import get_user_flexible
from app.api.deps import get_plugin_api_service, get_db_session, get_redis
from app.models.user import User
from app.services.plugin_api_service import PluginAPIService
from app.services.kiro_service import KiroService, UpstreamAPIError
from app.services.anthropic_adapter import AnthropicAdapter
from app.schemas.plugin_api import ChatCompletionRequest
from app.cache import RedisClient


router = APIRouter(prefix="/v1", tags=["OpenAI兼容API"])

def get_kiro_service(
    db: AsyncSession = Depends(get_db_session),
    redis: RedisClient = Depends(get_redis)
) -> KiroService:
    """获取Kiro服务实例（带Redis缓存支持）"""
    return KiroService(db, redis)


@router.get(
    "/models",
    summary="获取模型列表",
    description="获取可用的AI模型列表（OpenAI兼容）。根据API key的config_type自动选择Antigravity或Kiro配置"
)
async def list_models(
    request: Request,
    current_user: User = Depends(get_user_flexible),
    antigravity_service: PluginAPIService = Depends(get_plugin_api_service),
    kiro_service: KiroService = Depends(get_kiro_service)
):
    """
    获取模型列表
    支持API key或JWT token认证
    
    **配置选择:**
    - 使用API key认证时，根据API key创建时选择的config_type自动选择配置
    - 使用JWT token认证时，默认使用Antigravity配置，但可以通过X-Api-Type请求头指定配置
    - Kiro配置需要beta权限
    """
    try:
        # 判断使用哪个服务
        # 如果用户有config_type属性（来自API key），使用该配置
        config_type = getattr(current_user, '_config_type', None)
        
        # 如果是JWT token认证（无_config_type），检查请求头
        if config_type is None:
            api_type = request.headers.get("X-Api-Type")
            if api_type in ["kiro", "antigravity"]:
                config_type = api_type
        
        use_kiro = config_type == "kiro"
        
        if use_kiro:
            # 检查beta权限
            if current_user.beta != 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Kiro配置仅对beta计划用户开放"
                )
            result = await kiro_service.get_models(current_user.id)
        else:
            # 默认使用Antigravity，传递config_type
            result = await antigravity_service.get_models(current_user.id, config_type=config_type)
        
        return result
    except HTTPException:
        raise
    except UpstreamAPIError as e:
        # 返回上游API的错误消息
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.extracted_message,
                "type": "api_error"
            }
        )
    except httpx.HTTPStatusError as e:
        # 直接返回上游API的原始响应（Antigravity服务）
        upstream_response = getattr(e, 'response_data', None)
        if upstream_response is None:
            try:
                upstream_response = e.response.json()
            except Exception:
                upstream_response = {"error": e.response.text}
        
        return JSONResponse(
            status_code=e.response.status_code,
            content=upstream_response
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型列表失败: {str(e)}"
        )


@router.post(
    "/chat/completions",
    summary="聊天补全",
    description="使用plug-in-api进行聊天补全（OpenAI兼容）。根据API key的config_type自动选择Antigravity或Kiro配置"
)
async def chat_completions(
    request: ChatCompletionRequest,
    raw_request: Request,
    current_user: User = Depends(get_user_flexible),
    antigravity_service: PluginAPIService = Depends(get_plugin_api_service),
    kiro_service: KiroService = Depends(get_kiro_service)
):
    """
    聊天补全
    支持两种认证方式：
    1. API key认证 - 用于程序调用，根据API key的config_type自动选择配置
    2. JWT token认证 - 用于网页聊天，默认使用Antigravity配置，但可以通过X-Api-Type请求头指定配置
    
    **配置选择:**
    - 使用API key时，根据创建时选择的config_type（antigravity/kiro）自动路由
    - 使用JWT token时，默认使用Antigravity配置，但可以通过X-Api-Type请求头指定配置
    - Kiro配置需要beta权限
    
    我们使用用户对应的plug-in key调用plug-in-api
    """
    try:
        # 判断使用哪个服务
        config_type = getattr(current_user, '_config_type', None)
        
        # 如果是JWT token认证（无_config_type），检查请求头
        if config_type is None:
            api_type = raw_request.headers.get("X-Api-Type")
            if api_type in ["kiro", "antigravity"]:
                config_type = api_type
        
        use_kiro = config_type == "kiro"
        
        if use_kiro:
            # 检查beta权限
            if current_user.beta != 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Kiro配置仅对beta计划用户开放"
                )
        
        # 准备额外的请求头
        extra_headers = {}
        if config_type:
            extra_headers["X-Account-Type"] = config_type
        
        # 如果是流式请求
        if request.stream:
            async def generate():
                if use_kiro:
                    async for chunk in kiro_service.chat_completions_stream(
                        user_id=current_user.id,
                        request_data=request.model_dump()
                    ):
                        yield chunk
                else:
                    async for chunk in antigravity_service.proxy_stream_request(
                        user_id=current_user.id,
                        method="POST",
                        path="/v1/chat/completions",
                        json_data=request.model_dump(),
                        extra_headers=extra_headers if extra_headers else None
                    ):
                        yield chunk
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            # 非流式请求
            # 上游总是返回流式响应，所以使用流式接口获取并收集响应
            if use_kiro:
                openai_stream = kiro_service.chat_completions_stream(
                    user_id=current_user.id,
                    request_data=request.model_dump()
                )
            else:
                openai_stream = antigravity_service.proxy_stream_request(
                    user_id=current_user.id,
                    method="POST",
                    path="/v1/chat/completions",
                    json_data=request.model_dump(),
                    extra_headers=extra_headers if extra_headers else None
                )
            
            # 收集流式响应并转换为完整的OpenAI响应
            result = await AnthropicAdapter.collect_openai_stream_to_response(
                openai_stream
            )
            return result
            
    except HTTPException:
        raise
    except UpstreamAPIError as e:
        # 返回上游API的错误消息
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.extracted_message,
                "type": "api_error"
            }
        )
    except httpx.HTTPStatusError as e:
        # 直接返回上游API的原始响应（Antigravity服务）
        upstream_response = getattr(e, 'response_data', None)
        if upstream_response is None:
            try:
                upstream_response = e.response.json()
            except Exception:
                upstream_response = {"error": e.response.text}
        
        return JSONResponse(
            status_code=e.response.status_code,
            content=upstream_response
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天补全失败: {str(e)}"
        )