#!/bin/sh
# ============================================
# AntiHub Plugin - Docker Entry Point
# ============================================
# 从环境变量生成 config.json
# 支持挂载自定义配置文件
# ============================================

CONFIG_FILE="/app/config.json"

# 如果已存在自定义配置文件，跳过生成
if [ -f "$CONFIG_FILE" ]; then
    echo "使用已存在的配置文件: $CONFIG_FILE"
else
    echo "从环境变量生成配置文件..."

    # 生成 config.json
    cat > "$CONFIG_FILE" << EOF
{
  "server": {
    "port": "${PORT:-8045}",
    "host": "0.0.0.0"
  },
  "database": {
    "host": "${DB_HOST:-localhost}",
    "port": ${DB_PORT:-5432},
    "database": "${DB_NAME:-antigv}",
    "user": "${DB_USER:-postgres}",
    "password": "${DB_PASSWORD:-postgres}",
    "max": 20,
    "idleTimeoutMillis": 30000,
    "connectionTimeoutMillis": 2000
  },
  "redis": {
    "host": "${REDIS_HOST:-localhost}",
    "port": ${REDIS_PORT:-6379},
    "password": "${REDIS_PASSWORD:-}",
    "db": 0
  },
  "oauth": {
    "callbackUrl": "${OAUTH_CALLBACK_URL:-http://localhost:8045/api/oauth/callback}"
  },
  "security": {
    "maxRequestSize": "50mb",
    "adminApiKey": "${ADMIN_API_KEY:-sk-admin-default-key}"
  },
  "systemInstruction": ""
}
EOF

    echo "配置文件已生成: $CONFIG_FILE"
    cat "$CONFIG_FILE"
fi

echo ""
echo "启动 AntiHub API 服务..."
echo "================================"

# 启动主应用
exec node src/server/index.js
