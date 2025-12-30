"""
Plug-in API相关的数据模式
"""
from typing import Optional, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== Plug-in API密钥相关 ====================

class PluginAPIKeyCreate(BaseModel):
    """创建Plug-in API密钥请求"""
    api_key: str = Field(..., description="用户在plug-in-api系统中的API密钥")


class PluginAPIKeyResponse(BaseModel):
    """Plug-in API密钥响应"""
    id: int
    user_id: int
    plugin_user_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class PluginAPIKeyUpdate(BaseModel):
    """更新Plug-in API密钥"""
    api_key: Optional[str] = Field(None, description="新的API密钥")
    is_active: Optional[bool] = Field(None, description="是否激活")


# ==================== Plug-in API代理请求 ====================

class CreatePluginUserRequest(BaseModel):
    """创建plug-in-api用户请求（管理员操作）"""
    name: Optional[str] = Field(None, description="用户名称")
    prefer_shared: int = Field(0, description="Cookie优先级，0=专属优先，1=共享优先")


class CreatePluginUserResponse(BaseModel):
    """创建plug-in-api用户响应"""
    success: bool
    message: str
    data: Dict[str, Any]


class OAuthAuthorizeRequest(BaseModel):
    """获取OAuth授权URL请求"""
    is_shared: int = Field(0, description="0=专属cookie，1=共享cookie")


class OAuthAuthorizeResponse(BaseModel):
    """OAuth授权响应"""
    success: bool
    data: Dict[str, Any]


class OAuthCallbackRequest(BaseModel):
    """手动提交OAuth回调"""
    callback_url: str = Field(..., description="完整的回调URL")


class UpdateCookiePreferenceRequest(BaseModel):
    """更新Cookie优先级"""
    prefer_shared: int = Field(..., description="0=专属优先，1=共享优先")


class UpdateAccountStatusRequest(BaseModel):
    """更新账号状态"""
    status: int = Field(..., description="0=禁用，1=启用")


class UpdateAccountTypeRequest(BaseModel):
    """更新账号类型（专属/共享）"""
    is_shared: int = Field(..., description="账号类型：0=专属，1=共享")


class UpdateAccountNameRequest(BaseModel):
    """更新账号名称"""
    name: str = Field(..., description="账号名称")


class ChatCompletionRequest(BaseModel):
    """聊天补全请求（支持多模态）"""
    model: str = Field(..., description="模型名称")
    messages: List[Dict[str, Any]] = Field(..., description="消息列表，支持文本和多模态内容")
    stream: bool = Field(True, description="是否流式输出")
    temperature: Optional[float] = Field(1.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用配置")
    
    model_config = {"extra": "allow"}  # 允许额外字段，支持OpenAI的所有参数


class QuotaConsumptionQuery(BaseModel):
    """配额消耗查询参数"""
    limit: Optional[int] = Field(None, description="限制返回数量")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


# ==================== 图片生成相关 ====================

class ImageConfigRequest(BaseModel):
    """图片生成配置"""
    aspectRatio: Optional[str] = Field(
        None,
        description="宽高比。支持的值：1:1、2:3、3:2、3:4、4:3、9:16、16:9、21:9。如果未指定，模型将根据提供的任何参考图片选择默认宽高比。"
    )
    imageSize: Optional[str] = Field(
        None,
        description="图片尺寸。支持的值为 1K、2K、4K。如果未指定，模型将使用默认值 1K。"
    )


class GenerationConfigRequest(BaseModel):
    """生成配置"""
    imageConfig: Optional[ImageConfigRequest] = Field(None, description="图片生成配置")
    
    model_config = {"extra": "allow"}  # 允许额外字段


class ContentPartText(BaseModel):
    """文本内容部分"""
    text: str = Field(..., description="文本内容")


class ContentPartInlineData(BaseModel):
    """内联数据内容部分（用于图片等）"""
    mimeType: str = Field(..., description="MIME类型，例如 image/jpeg")
    data: str = Field(..., description="Base64编码的数据")


class InlineDataWrapper(BaseModel):
    """内联数据包装器"""
    inlineData: ContentPartInlineData


class ContentMessage(BaseModel):
    """内容消息"""
    role: str = Field(..., description="角色，例如 user, model")
    parts: List[Dict[str, Any]] = Field(..., description="内容部分列表，可包含text或inlineData")


class GenerateContentRequest(BaseModel):
    """图片生成请求（Gemini格式）"""
    contents: List[ContentMessage] = Field(..., description="包含提示词的消息数组")
    generationConfig: Optional[GenerationConfigRequest] = Field(None, description="生成配置")
    
    model_config = {"extra": "allow"}  # 允许额外字段，支持其他Gemini参数


class InlineDataResponse(BaseModel):
    """内联数据响应"""
    mimeType: str = Field(..., description="MIME类型，例如 image/jpeg")
    data: str = Field(..., description="Base64编码的图片数据")


class ContentPartResponse(BaseModel):
    """内容部分响应"""
    inlineData: Optional[InlineDataResponse] = None
    text: Optional[str] = None


class ContentResponse(BaseModel):
    """内容响应"""
    parts: List[ContentPartResponse] = Field(..., description="内容部分列表")
    role: str = Field("model", description="角色")


class CandidateResponse(BaseModel):
    """候选响应"""
    content: ContentResponse
    finishReason: str = Field("STOP", description="完成原因")


class GenerateContentResponse(BaseModel):
    """图片生成响应"""
    candidates: List[CandidateResponse] = Field(..., description="候选结果列表")


# ==================== 通用响应 ====================

class PluginAPIResponse(BaseModel):
    """通用Plug-in API响应"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None