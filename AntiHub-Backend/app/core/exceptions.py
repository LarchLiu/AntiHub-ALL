"""
自定义异常类
定义系统中使用的各种异常类型
"""
from typing import Optional, Any, Dict


class BaseAPIException(Exception):
    """
    API 异常基类
    所有自定义异常都应继承此类
    """
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            status_code: HTTP 状态码
            details: 额外的错误详情
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含错误信息的字典
        """
        result = {
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


# ==================== 认证相关异常 ====================

class AuthenticationError(BaseAPIException):
    """认证失败异常"""
    
    def __init__(
        self,
        message: str = "认证失败",
        error_code: str = "AUTHENTICATION_FAILED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details
        )


class InvalidCredentialsError(AuthenticationError):
    """用户名或密码错误"""
    
    def __init__(
        self,
        message: str = "用户名或密码错误",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS",
            details=details
        )


class InvalidTokenError(AuthenticationError):
    """令牌无效异常"""
    
    def __init__(
        self,
        message: str = "令牌无效",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="INVALID_TOKEN",
            details=details
        )


class TokenExpiredError(AuthenticationError):
    """令牌已过期异常"""
    
    def __init__(
        self,
        message: str = "令牌已过期",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="TOKEN_EXPIRED",
            details=details
        )


class TokenBlacklistedError(AuthenticationError):
    """令牌已被加入黑名单异常"""
    
    def __init__(
        self,
        message: str = "令牌已失效",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="TOKEN_BLACKLISTED",
            details=details
        )


# ==================== OAuth 相关异常 ====================

class OAuthError(BaseAPIException):
    """OAuth 异常基类"""
    
    def __init__(
        self,
        message: str = "OAuth 认证失败",
        error_code: str = "OAUTH_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details
        )


class InvalidOAuthStateError(OAuthError):
    """无效的 OAuth state 异常"""
    
    def __init__(
        self,
        message: str = "无效的 OAuth state",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="INVALID_OAUTH_STATE",
            details=details
        )


class OAuthTokenExchangeError(OAuthError):
    """OAuth 令牌交换失败异常"""
    
    def __init__(
        self,
        message: str = "OAuth 令牌交换失败",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="OAUTH_TOKEN_EXCHANGE_FAILED",
            details=details
        )


class OAuthUserInfoError(OAuthError):
    """获取 OAuth 用户信息失败异常"""
    
    def __init__(
        self,
        message: str = "获取用户信息失败",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="OAUTH_USER_INFO_FAILED",
            details=details
        )


# ==================== 数据库相关异常 ====================

class DatabaseError(BaseAPIException):
    """数据库异常基类"""
    
    def __init__(
        self,
        message: str = "数据库操作失败",
        error_code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details
        )


class UserNotFoundError(DatabaseError):
    """用户不存在异常"""
    
    def __init__(
        self,
        message: str = "用户不存在",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND",
            details=details
        )


class UserAlreadyExistsError(DatabaseError):
    """用户已存在异常"""
    
    def __init__(
        self,
        message: str = "用户已存在",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="USER_ALREADY_EXISTS",
            details=details
        )


class DatabaseConnectionError(DatabaseError):
    """数据库连接失败异常"""
    
    def __init__(
        self,
        message: str = "数据库连接失败",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR",
            details=details
        )


# ==================== 缓存相关异常 ====================

class CacheError(BaseAPIException):
    """缓存异常基类"""
    
    def __init__(
        self,
        message: str = "缓存操作失败",
        error_code: str = "CACHE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details
        )


class RedisConnectionError(CacheError):
    """Redis 连接失败异常"""
    
    def __init__(
        self,
        message: str = "Redis 连接失败",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="REDIS_CONNECTION_ERROR",
            details=details
        )


# ==================== 权限相关异常 ====================

class PermissionError(BaseAPIException):
    """权限不足异常"""
    
    def __init__(
        self,
        message: str = "权限不足",
        error_code: str = "PERMISSION_DENIED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details
        )


class AccountDisabledError(PermissionError):
    """账号已被禁用异常"""
    
    def __init__(
        self,
        message: str = "账号已被禁用",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="ACCOUNT_DISABLED",
            details=details
        )


class AccountSilencedError(PermissionError):
    """账号已被禁言异常"""
    
    def __init__(
        self,
        message: str = "账号已被禁言",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="ACCOUNT_SILENCED",
            details=details
        )


# ==================== 验证相关异常 ====================

class ValidationError(BaseAPIException):
    """数据验证失败异常"""
    
    def __init__(
        self,
        message: str = "数据验证失败",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details
        )