#!/usr/bin/env python3
"""
生成 Fernet 加密密钥
运行: python generate_encryption_key.py
"""
from cryptography.fernet import Fernet

# 生成密钥
key = Fernet.generate_key()
print("请将以下密钥复制到 .env 文件的 PLUGIN_API_ENCRYPTION_KEY：")
print(key.decode())