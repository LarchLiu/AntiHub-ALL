"""
加密工具模块
用于加密和解密敏感数据
"""
from cryptography.fernet import Fernet
from app.core.config import get_settings


def get_cipher():
    """获取Fernet加密器"""
    settings = get_settings()
    # 确保密钥是32字节的URL安全base64编码
    key = settings.plugin_api_encryption_key.encode()
    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """
    加密API密钥
    
    Args:
        api_key: 原始API密钥
        
    Returns:
        加密后的API密钥字符串
    """
    cipher = get_cipher()
    encrypted = cipher.encrypt(api_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    解密API密钥
    
    Args:
        encrypted_key: 加密后的API密钥
        
    Returns:
        解密后的原始API密钥
    """
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_key.encode())
    return decrypted.decode()