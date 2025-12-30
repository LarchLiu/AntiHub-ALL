"""
安全模块
提供密码哈希和 JWT 令牌管理功能
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
import secrets

from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from app.core.config import get_settings


# ==================== 密码哈希配置 ====================

# 配置 bcrypt 哈希算法,rounds=12
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def hash_password(password: str) -> str:
    """
    哈希密码
    
    Args:
        password: 明文密码
        
    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        密码正确返回 True,否则返回 False
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT 令牌管理 ====================

def create_access_token(
    user_id: int,
    username: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    创建 JWT 访问令牌
    
    Args:
        user_id: 用户 ID
        username: 用户名
        additional_claims: 额外的声明数据
        
    Returns:
        JWT 令牌字符串
    """
    settings = get_settings()
    
    # 计算过期时间
    now = datetime.utcnow()
    expire = now + timedelta(seconds=settings.jwt_expire_seconds)
    
    # 构建 JWT payload
    payload = {
        "sub": str(user_id),  # Subject: 用户 ID
        "username": username,  # 用户名
        "exp": expire,  # Expiration Time: 过期时间
        "iat": now,  # Issued At: 签发时间
        "jti": str(uuid.uuid4()),  # JWT ID: 唯一标识符
        "type": "access",  # Token 类型
    }
    
    # 添加额外的声明
    if additional_claims:
        payload.update(additional_claims)
    
    # 生成 JWT 令牌
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证 JWT 访问令牌
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        验证成功返回 payload 字典,失败返回 None
        
    Raises:
        ExpiredSignatureError: 令牌已过期
        InvalidTokenError: 令牌无效
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except ExpiredSignatureError:
        # 令牌已过期
        raise
    except InvalidTokenError:
        # 令牌无效
        raise


# ==================== Refresh Token 管理 ====================

def create_refresh_token(
    user_id: int,
    username: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    创建 Refresh Token
    
    Args:
        user_id: 用户 ID
        username: 用户名
        additional_claims: 额外的声明数据
        
    Returns:
        Refresh Token 字符串
    """
    settings = get_settings()
    
    # 计算过期时间
    now = datetime.utcnow()
    expire = now + timedelta(seconds=settings.refresh_token_expire_seconds)
    
    # 构建 JWT payload
    payload = {
        "sub": str(user_id),  # Subject: 用户 ID
        "username": username,  # 用户名
        "exp": expire,  # Expiration Time: 过期时间
        "iat": now,  # Issued At: 签发时间
        "jti": str(uuid.uuid4()),  # JWT ID: 唯一标识符
        "type": "refresh",  # Token 类型
    }
    
    # 添加额外的声明
    if additional_claims:
        payload.update(additional_claims)
    
    # 生成 Refresh Token（使用不同的密钥）
    token = jwt.encode(
        payload,
        settings.refresh_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证 Refresh Token
    
    Args:
        token: Refresh Token 字符串
        
    Returns:
        验证成功返回 payload 字典
        
    Raises:
        ExpiredSignatureError: 令牌已过期
        InvalidTokenError: 令牌无效
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.refresh_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # 验证 token 类型
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")
        
        return payload
    except ExpiredSignatureError:
        # 令牌已过期
        raise
    except InvalidTokenError:
        # 令牌无效
        raise


def generate_token_pair(
    user_id: int,
    username: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> tuple[str, str]:
    """
    生成 Access Token 和 Refresh Token 对
    
    Args:
        user_id: 用户 ID
        username: 用户名
        additional_claims: 额外的声明数据
        
    Returns:
        (access_token, refresh_token) 元组
    """
    access_token = create_access_token(user_id, username, additional_claims)
    refresh_token = create_refresh_token(user_id, username, additional_claims)
    return access_token, refresh_token


# ==================== 通用令牌工具函数 ====================

def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    解码令牌但不验证签名和过期时间
    用于获取令牌信息(如 JTI)而不进行完整验证
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        payload 字典,失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except Exception:
        return None


def get_token_expire_time(token: str) -> Optional[datetime]:
    """
    获取令牌过期时间
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        过期时间,失败返回 None
    """
    payload = decode_token_without_verification(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


def get_token_remaining_seconds(token: str) -> Optional[int]:
    """
    获取令牌剩余有效时间(秒)
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        剩余秒数,已过期或失败返回 None
    """
    expire_time = get_token_expire_time(token)
    if expire_time is None:
        return None
    
    remaining = (expire_time - datetime.utcnow()).total_seconds()
    return int(remaining) if remaining > 0 else None


def extract_token_jti(token: str) -> Optional[str]:
    """
    提取令牌的 JTI (JWT ID)
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        JTI 字符串,失败返回 None
    """
    payload = decode_token_without_verification(token)
    if payload and "jti" in payload:
        return payload["jti"]
    return None


def get_token_type(token: str) -> Optional[str]:
    """
    获取令牌类型 (access 或 refresh)
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        令牌类型字符串,失败返回 None
    """
    payload = decode_token_without_verification(token)
    if payload and "type" in payload:
        return payload["type"]
    return None