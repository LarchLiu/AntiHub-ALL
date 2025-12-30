# Antigravity API 服务文档

## 概述

这是一个支持多用户、多账号管理的 Antigravity API 服务，提供 OAuth 认证、账号管理、配额管理和 OpenAI 兼容的聊天接口。

每个用户都有自己的 API Key（`sk-xxx` 格式），通过 `Authorization: Bearer sk-xxx` 进行认证。

## 目录

- [快速开始](#快速开始)
- [数据库配置](#数据库配置)
- [认证说明](#认证说明)
- [API 接口](#api-接口)
  - [用户管理（管理员）](#用户管理管理员)
  - [OAuth 相关](#oauth-相关)
  - [账号管理](#账号管理)
  - [配额管理](#配额管理)
  - [OpenAI 兼容接口](#openai-兼容接口)
  - [图片生成接口](#图片生成接口)

---

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置数据库

编辑 `config.json` 文件中的数据库配置：

```json
{
  "oauth": {
    "callbackUrl": "https://your-domain.com/api/oauth/callback"
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "antigravity",
    "user": "postgres",
    "password": "your_password"
  },
  "security": {
    "adminApiKey": "sk-admin-your-secret-key-here"
  }
}
```

**注意**: `oauth.callbackUrl` 必须配置为公网可访问的地址，用于 Google OAuth 回调。

### 3. 初始化数据库

执行 `database/schema.sql` 文件创建数据表：

```bash
psql -U postgres -d antigravity -f database/schema.sql
```

### 4. 启动服务

```bash
npm start
```

服务将在 `http://0.0.0.0:8045` 启动。

### 5. 创建用户

使用管理员 API Key 创建第一个用户：

```bash
curl -X POST http://localhost:8045/api/users \
  -H "Authorization: Bearer sk-admin-your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试用户"}'
```

响应中会返回该用户的 `api_key`（如 `sk-x4wIrzp6I8yTe8ARVIYxi9XVke9GNNCEBVi20IqVpuJgISRX`），用户使用此 Key 进行后续操作。

---

## 数据库配置

### 配置说明

在 `config.json` 中配置 PostgreSQL 数据库连接信息：

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "antigravity",
    "user": "postgres",
    "password": "your_password",
    "max": 20,
    "idleTimeoutMillis": 30000,
    "connectionTimeoutMillis": 2000
  }
}
```

### 数据表结构

服务使用三个主要数据表：

1. **users** - 存储用户信息和 API Key
2. **accounts** - 存储用户的 OAuth 账号信息
3. **model_quotas** - 存储模型配额信息

详细表结构见 [`database/schema.sql`](database/schema.sql:1)

---

## 认证说明

### API Key 类型

1. **管理员 API Key**: 在 `config.json` 的 `security.adminApiKey` 中配置，用于用户管理等管理操作
2. **用户 API Key**: 创建用户时自动生成（`sk-xxx` 格式），用于用户的日常操作

### 认证方式

所有 API 请求都需要在请求头中携带 API Key：

```
Authorization: Bearer sk-xxx
```

示例：

```bash
curl -X GET http://localhost:8045/v1/models \
  -H "Authorization: Bearer sk-x4wIrzp6I8yTe8ARVIYxi9XVke9GNNCEBVi20IqVpuJgISRX"
```

---

## API 接口

## 用户管理（管理员）

### 1. 创建用户

**请求**

```http
POST /api/users
Authorization: Bearer {管理员API Key}
Content-Type: application/json

{
  "name": "用户名称"
}
```

**参数说明**

- `name` (可选): 用户名称

**响应**

```json
{
  "success": true,
  "message": "用户创建成功",
  "data": {
    "user_id": "uuid-xxx",
    "api_key": "sk-x4wIrzp6I8yTe8ARVIYxi9XVke9GNNCEBVi20IqVpuJgISRX",
    "name": "用户名称",
    "created_at": "2025-11-21T14:00:00.000Z"
  }
}
```

---

### 2. 获取所有用户列表

**请求**

```http
GET /api/users
Authorization: Bearer {管理员API Key}
```

**响应**

```json
{
  "success": true,
  "data": [
    {
      "user_id": "uuid-xxx",
      "name": "用户名称",
      "status": 1,
      "created_at": "2025-11-21T14:00:00.000Z",
      "updated_at": "2025-11-21T14:00:00.000Z"
    }
  ]
}
```

---

### 3. 重新生成用户 API Key

**请求**

```http
POST /api/users/{user_id}/regenerate-key
Authorization: Bearer {管理员API Key}
```

**响应**

```json
{
  "success": true,
  "message": "API Key已重新生成",
  "data": {
    "user_id": "uuid-xxx",
    "api_key": "sk-new-key-xxx"
  }
}
```

---

### 4. 更新用户状态

**请求**

```http
PUT /api/users/{user_id}/status
Authorization: Bearer {管理员API Key}
Content-Type: application/json

{
  "status": 0
}
```

**参数说明**

- `status` (必需): 用户状态，0=禁用，1=启用

**响应**

```json
{
  "success": true,
  "message": "用户状态已更新为禁用",
  "data": {
    "user_id": "uuid-xxx",
    "status": 0
  }
}
```

---

### 5. 删除用户

**请求**

```http
DELETE /api/users/{user_id}
Authorization: Bearer {管理员API Key}
```

**响应**

```json
{
  "success": true,
  "message": "用户已删除"
}
```

**注意**: 删除用户会级联删除该用户的所有账号和配额记录。

---

## OAuth 相关

### 1. 获取 OAuth 授权 URL

**请求**

```http
POST /api/oauth/authorize
Authorization: Bearer {用户API Key}
Content-Type: application/json

{
  "is_shared": 0
}
```

**参数说明**

- `is_shared` (可选): Cookie 共享标识，0=专属，1=共享，默认为 0

**注意**: 回调地址由服务器配置（`config.json` 中的 `oauth.callbackUrl`），用户无需传入。

**响应**

```json
{
  "success": true,
  "data": {
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
    "state": "uuid-state",
    "expires_in": 300
  }
}
```

**使用流程**

1. 调用此接口获取 `auth_url`
2. 引导用户在浏览器中打开 `auth_url` 进行授权
3. 用户授权成功后，会被重定向到 `redirect_uri`，携带 `code` 和 `state` 参数

---

### 2. OAuth 回调处理

**请求**

```http
GET /api/oauth/callback?code=xxx&state=xxx
```

**参数说明**

- `code` (必需): OAuth 授权码
- `state` (必需): 状态标识（由获取授权 URL 接口返回）

**响应**

```json
{
  "success": true,
  "message": "账号添加成功",
  "data": {
    "cookie_id": "abc123...",
    "user_id": "user-123",
    "is_shared": 0,
    "created_at": "2025-11-21T14:00:00.000Z"
  }
}
```

---

## 账号管理

### 1. 获取当前用户的账号列表

**请求**

```http
GET /api/accounts
Authorization: Bearer {用户API Key}
```

**响应**

```json
{
  "success": true,
  "data": [
    {
      "cookie_id": "abc123...",
      "user_id": "user-123",
      "is_shared": 0,
      "status": 1,
      "expires_at": 1732201200000,
      "created_at": "2025-11-21T14:00:00.000Z",
      "updated_at": "2025-11-21T14:00:00.000Z"
    }
  ]
}
```

---

### 2. 获取单个账号信息

**请求**

```http
GET /api/accounts/{cookie_id}
Authorization: Bearer {用户API Key}
```

**响应**

```json
{
  "success": true,
  "data": {
    "cookie_id": "abc123...",
    "user_id": "user-123",
    "is_shared": 0,
    "status": 1,
    "expires_at": 1732201200000,
    "created_at": "2025-11-21T14:00:00.000Z",
    "updated_at": "2025-11-21T14:00:00.000Z"
  }
}
```

---

### 3. 更新账号状态

**请求**

```http
PUT /api/accounts/{cookie_id}/status
Authorization: Bearer {用户API Key}
Content-Type: application/json

{
  "status": 0
}
```

**参数说明**

- `status` (必需): 账号状态，0=禁用，1=启用

**响应**

```json
{
  "success": true,
  "message": "账号状态已更新为禁用",
  "data": {
    "cookie_id": "abc123...",
    "status": 0
  }
}
```

---

### 4. 删除账号

**请求**

```http
DELETE /api/accounts/{cookie_id}
Authorization: Bearer {用户API Key}
```

**响应**

```json
{
  "success": true,
  "message": "账号已删除"
}
```

**注意**: 删除账号会级联删除该账号的所有配额记录。

---

## 配额管理

### 1. 获取用户共享配额池

**请求**

```http
GET /api/quotas/user
Authorization: Bearer {用户API Key}
```

**响应**

```json
{
  "success": true,
  "data": [
    {
      "pool_id": 1,
      "user_id": "user-123",
      "model_name": "gemini-3-pro-high",
      "quota": "1.5000",
      "max_quota": "2.0000",
      "last_recovered_at": "2025-11-21T16:00:00.000Z",
      "last_updated_at": "2025-11-21T16:30:00.000Z"
    }
  ]
}
```

**字段说明**

- `quota`: 当前配额（使用共享池时会扣减）
- `max_quota`: 配额上限（= 2 * n，n为用户的共享cookie数量）
- `last_recovered_at`: 最后恢复时间
- `last_updated_at`: 最后更新时间

**配额机制说明**

1. **初始值**：用户首次创建时，共享配额池为 0
2. **上限**：配额上限 = 2 × 用户共享cookie数量
3. **恢复**：每小时自动恢复 2n × 0.2（n为用户共享cookie数）
4. **扣减**：仅使用共享cookie时才扣减配额池
5. **用途**：专属cookie不影响配额池，只有使用共享池时才需要配额

---

### 2. 获取共享池配额

**请求**

```http
GET /api/quotas/shared-pool
Authorization: Bearer {用户API Key}
```

**响应**

```json
{
  "success": true,
  "data": [
    {
      "model_name": "gemini-3-pro-high",
      "total_quota": "2.4500",
      "earliest_reset_time": "2025-11-22T01:18:08.000Z",
      "available_cookies": 5,
      "status": 1,
      "last_fetched_at": "2025-11-21T16:45:30.000Z"
    }
  ]
}
```

**字段说明**

- `total_quota`: 所有共享cookie的配额总和（每个cookie的quota相加）
- `earliest_reset_time`: 最早的配额重置时间
- `available_cookies`: 可用的共享cookie数量
- `status`: 状态（1=可用，0=不可用）
- `last_fetched_at`: 最后一次获取配额的时间

---

### 3. 获取账号配额信息

**请求**

```http
GET /api/accounts/{cookie_id}/quotas
Authorization: Bearer {用户API Key}
```

**响应**

```json
{
  "success": true,
  "data": [
    {
      "quota_id": 1,
      "cookie_id": "abc123...",
      "model_name": "gemini-3-pro-high",
      "reset_time": "2025-11-21T17:18:08.000Z",
      "quota": "0.9800",
      "status": 1,
      "last_fetched_at": "2025-11-21T14:00:00.000Z",
      "created_at": "2025-11-21T14:00:00.000Z"
    }
  ]
}
```

---

### 4. 获取用户配额消耗记录

**请求**

```http
GET /api/quotas/consumption?limit=100&start_date=2025-11-01&end_date=2025-11-30
Authorization: Bearer {用户API Key}
```

**参数说明**

- `limit` (可选): 限制返回数量
- `start_date` (可选): 开始日期（ISO 8601格式）
- `end_date` (可选): 结束日期（ISO 8601格式）

**响应**

```json
{
  "success": true,
  "data": [
    {
      "log_id": 1,
      "user_id": "user-123",
      "cookie_id": "abc123...",
      "model_name": "gemini-3-pro-high",
      "quota_before": "0.8500",
      "quota_after": "0.7200",
      "quota_consumed": "0.1300",
      "is_shared": 1,
      "consumed_at": "2025-11-21T14:00:00.000Z"
    }
  ]
}
```

**字段说明**

- `quota_before`: 对话开始前的cookie quota值
- `quota_after`: 对话结束后的cookie quota值
- `quota_consumed`: 本次消耗的quota（quota_before - quota_after）
- `is_shared`: 是否使用共享cookie（1=共享，0=专属）

**注意**

- 只有使用共享cookie（is_shared=1）的消耗会从用户共享配额池扣除
- 使用专属cookie（is_shared=0）的消耗仅作记录，不扣除配额池

---

### 5. 获取用户模型消耗统计

**请求**

```http
GET /api/quotas/consumption/stats/{model_name}
Authorization: Bearer {用户API Key}
```

**响应**

```json
{
  "success": true,
  "data": {
    "total_requests": "150",
    "total_quota_consumed": "19.5000",
    "avg_quota_consumed": "0.1300",
    "last_used_at": "2025-11-21T14:00:00.000Z"
  }
}
```

**字段说明**

- `total_requests`: 总请求次数
- `total_quota_consumed`: 总配额消耗量
- `avg_quota_consumed`: 平均每次消耗的配额
- `last_used_at`: 最后使用时间

---

### 6. 获取配额即将耗尽的模型（管理员）

**请求**

```http
GET /api/quotas/low?threshold=0.1
Authorization: Bearer {管理员API Key}
```

**参数说明**

- `threshold` (可选): 配额阈值，默认为 0.1（即 10%）

**响应**

```json
{
  "success": true,
  "data": [
    {
      "quota_id": 2,
      "cookie_id": "abc123...",
      "model_name": "claude-sonnet-4-5",
      "reset_time": "2025-11-21T17:16:32.000Z",
      "quota": "0.0500",
      "status": 1,
      "user_id": "user-123",
      "is_shared": 0
    }
  ]
}
```

---

## OpenAI 兼容接口

### 1. 获取模型列表

**请求**

```http
GET /v1/models
Authorization: Bearer {用户API Key}
```

**响应**

```json
{
  "object": "list",
  "data": [
    {
      "id": "gemini-3-pro-high",
      "object": "model",
      "created": 1732201200,
      "owned_by": "google"
    },
    {
      "id": "claude-sonnet-4-5",
      "object": "model",
      "created": 1732201200,
      "owned_by": "google"
    }
  ]
}
```


### 3. 图片生成

**请求**

```http
POST /v1beta/models/{model}:generateContent
Authorization: Bearer {用户API Key}
Content-Type: application/json

{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "生成一只可爱的猫"
        }
      ]
    }
  ],
  "generationConfig": {
    "imageConfig": {
      "aspectRatio": "1:1",
      "imageSize": "1K"
    }
  }
}
```

**参数说明**

- `model` (必需): 模型名称，例如 `gemini-2.5-flash-image` 或 `gemini-2.5-pro-image`
- `contents` (必需): 包含提示词的消息数组
- `generationConfig.imageConfig` (可选): 图片生成配置
  - `aspectRatio`: 宽高比。支持的宽高比：`1:1`、`2:3`、`3:2`、`3:4`、`4:3`、`9:16`、`16:9`、`21:9`。如果未指定，模型将根据提供的任何参考图片选择默认宽高比。
  - `imageSize`: 图片尺寸。支持的值为 `1K`、`2K`、`4K`。如果未指定，模型将使用默认值 `1K`。

**响应**

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "inlineData": {
              "mimeType": "image/jpeg",
              "data": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDA..."
            }
          }
        ],
        "role": "model"
      },
      "finishReason": "STOP"
    }
  ]
}
```

**字段说明**

- `candidates[0].content.parts[0].inlineData.data`: Base64 编码的图片数据
- `candidates[0].content.parts[0].inlineData.mimeType`: 图片 MIME 类型，例如 `image/jpeg`

---

### 2. 聊天补全

**请求 (流式)**

```http
POST /v1/chat/completions
Authorization: Bearer {用户API Key}
Content-Type: application/json

{
  "model": "gemini-3-pro-high",
  "messages": [
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "stream": true,
  "temperature": 1.0,
  "max_tokens": 8096
}
```

**请求 (非流式)**

```http
POST /v1/chat/completions
Authorization: Bearer {用户API Key}
Content-Type: application/json

{
  "model": "gemini-3-pro-high",
  "messages": [
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "stream": false
}
```

**参数说明**

- `model` (必需): 模型名称
- `messages` (必需): 消息数组
- `stream` (可选): 是否使用流式输出，默认为 true
- `temperature` (可选): 温度参数，默认为 1.0
- `max_tokens` (可选): 最大输出 token 数
- `tools` (可选): 工具调用配置

**响应 (流式)**

```
data: {"id":"chatcmpl-1732201200","object":"chat.completion.chunk","created":1732201200,"model":"gemini-3-pro-high","choices":[{"index":0,"delta":{"content":"你"},"finish_reason":null}]}

data: {"id":"chatcmpl-1732201200","object":"chat.completion.chunk","created":1732201200,"model":"gemini-3-pro-high","choices":[{"index":0,"delta":{"content":"好"},"finish_reason":null}]}

data: {"id":"chatcmpl-1732201200","object":"chat.completion.chunk","created":1732201200,"model":"gemini-3-pro-high","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**响应 (非流式)**

```json
{
  "id": "chatcmpl-1732201200",
  "object": "chat.completion",
  "created": 1732201200,
  "model": "gemini-3-pro-high",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！有什么我可以帮助你的吗？"
      },
      "finish_reason": "stop"
    }
  ]
}
```

---

## 工作流程

### 添加账号流程

1. 管理员使用 `POST /api/users` 创建用户，获取用户的 `api_key`
2. 用户使用自己的 `api_key` 调用 `POST /api/oauth/authorize` 获取 OAuth URL
3. 用户在浏览器中打开 OAuth URL 进行授权
4. 授权成功后自动回调 `GET /api/oauth/callback`
5. 系统自动保存账号信息到数据库

### 聊天请求流程

1. 用户使用自己的 `api_key` 发送聊天请求到 `POST /v1/chat/completions`
2. 系统根据用户 ID 和模型查找可用的账号（优先使用专属账号）
3. 检查账号对该模型的配额是否可用
4. 如果 token 过期，自动刷新 token
5. 使用账号的 token 调用 Antigravity API
6. 对话完成后，自动更新配额信息

### 配额管理流程

#### Cookie配额更新
1. 每次对话完成后，系统自动调用 `fetchAvailableModels` API
2. 更新数据库中的cookie配额信息（`remainingFraction` 和 `resetTime`）
3. 如果某个模型的 `remainingFraction` 为 0，将该模型的 `status` 设置为 0
4. 下次请求该模型时，会跳过配额为 0 的账号

#### 用户共享配额池
1. **初始化**：用户创建时，共享配额池初始值为 0
2. **上限设置**：用户添加共享cookie时，配额池上限自动更新为 2 × n（n为共享cookie数）
3. **配额消耗**：
   - 使用共享cookie对话时，记录 quota_before 和 quota_after
   - 计算消耗量：quota_consumed = quota_before - quota_after
   - 从用户共享配额池扣除消耗量
4. **配额恢复**：
   - 每小时自动执行恢复任务（定时任务）
   - 恢复量 = 2n × 0.2（n为用户有效的共享cookie数）
   - 恢复后不超过配额上限（2n）
5. **注意**：专属cookie的使用不影响共享配额池，仅作记录

#### 配额恢复定时任务
```bash
# 手动执行恢复任务
node scripts/quota-recovery-cron.js

# 添加到 crontab（每小时执行一次）
0 * * * * /usr/bin/node /path/to/scripts/quota-recovery-cron.js
```

---

## 错误处理

### 常见错误码

- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: API Key 验证失败或缺少认证信息
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

### 错误响应格式

```json
{
  "error": "错误信息"
}
```

---

## 最佳实践

### 1. API Key 管理

- 每个用户使用独立的 API Key
- 管理员 API Key 仅用于用户管理，不要分发给普通用户
- 如果 API Key 泄露，使用 `POST /api/users/{user_id}/regenerate-key` 重新生成

### 2. 账号管理

- 建议为每个用户创建专属账号（`is_shared=0`）
- 共享账号（`is_shared=1`）仅作为备用
- 定期检查配额使用情况，及时添加新账号

### 3. 配额监控

- 管理员使用 `GET /api/quotas/low` 接口监控配额低的模型
- 在配额耗尽前添加新账号或切换模型

### 4. 错误重试

- 如果请求失败，可以重试（系统会自动切换到下一个可用账号）
- 建议实现指数退避重试策略

---

## 许可证

MIT License