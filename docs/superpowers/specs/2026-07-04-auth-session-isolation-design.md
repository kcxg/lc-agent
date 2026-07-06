# 用户认证 & 会话隔离 & 智能体授权 — 设计规格

> Created: 2026-07-04
> Branch: `feat/auth-session-isolation`

## 1. 目标

为 lc-agent 框架添加：
1. **用户登录**：本地账号密码认证（JWT）
2. **会话隔离**：每个用户只能看到/操作自己的对话
3. **智能体授权**：Admin 将 Agent 预设分配给用户，默认仅 `__chat__`

## 2. 场景 & 约束

- 企业内部部署，非互联网产品
- 无自注册，Admin 创建账号并分发随机初始密码
- 用户可自行修改密码
- 工具权限白名单（HITL）保持全局，不按用户区分
- 单机 SQLite 部署，无需集群 session

## 3. 数据模型

### 3.1 新增表

#### `users`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | 用户 ID |
| username | VARCHAR (UNIQUE, NOT NULL) | 登录用户名 |
| password_hash | VARCHAR (NOT NULL) | bcrypt 密码哈希 |
| role | ENUM('admin', 'user') | 角色，默认 'user' |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 最后更新时间 |

#### `user_agent_access`

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | UUID (FK → users.id) | 用户 |
| agent_id | VARCHAR (FK → agent_presets.id) | Agent 预设 ID |

复合主键 `(user_id, agent_id)`。

### 3.2 修改表

#### `sessions`

新增字段：`user_id UUID NOT NULL FK → users.id`

### 3.3 迁移策略

- 首次启动若 `users` 表为空 → 自动创建 admin 账号，随机密码打印到控制台
- 现有 session 数据的 `user_id` 填充为该 admin 的 id
- Admin 自动拥有所有 Agent 访问权限（不在 `user_agent_access` 中记录，代码逻辑判断）

## 4. 认证机制

### 4.1 JWT

- 算法：HS256
- Secret：配置项 `config.auth.secret`（必填，无默认值，启动时校验）
- 有效期：7 天（配置项 `config.auth.token_expire_days`，默认 7）
- Payload：`{ "sub": "<user_id>", "username": "<username>", "role": "<role>", "exp": <timestamp> }`

### 4.2 Token 传递

- HTTP 请求：`Authorization: Bearer <token>` header
- SSE 连接：URL query parameter `?token=<jwt>`（EventSource 不支持自定义 header）

### 4.3 认证端点

| 端点 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `POST /api/auth/login` | Public | — | 登录，返回 JWT + 用户信息 |
| `GET /api/auth/me` | Auth | 任意已登录 | 获取当前用户信息 |
| `POST /api/auth/change-password` | Auth | 任意已登录 | 修改自己密码 |

### 4.4 认证中间件

FastAPI 中间件拦截所有 `/api/*` 请求（排除白名单路径）：
- 提取 token → 验证签名+过期 → 查 DB 确认用户存在 → 注入 `request.state.current_user`
- 失败返回 `401 Unauthorized`

白名单路径：
- `POST /api/auth/login`
- `GET /api/health`

## 5. 权限控制

### 5.1 角色

| 角色 | 说明 |
|------|------|
| `admin` | 全部权限，管理用户和授权 |
| `user` | 仅操作自己的数据，使用被授权的 Agent |

### 5.2 权限矩阵

| 操作 | Admin | User |
|------|-------|------|
| 查看自己会话 | ✓ | ✓ |
| 查看他人会话 | ✓ | ✗ |
| 使用 Agent | 全部 | 仅被分配的 |
| CRUD Agent 预设 | ✓ | ✗ |
| 管理用户 | ✓ | ✗ |
| 分配 Agent | ✓ | ✗ |
| 修改工具白名单 | ✓ | ✗ |
| 修改自己密码 | ✓ | ✓ |

### 5.3 Admin 管理 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `GET /api/admin/users` | GET | 列出所有用户 |
| `POST /api/admin/users` | POST | 创建用户（返回随机密码） |
| `DELETE /api/admin/users/{id}` | DELETE | 删除用户 |
| `PUT /api/admin/users/{id}/reset-password` | PUT | 重置密码（返回新随机密码） |
| `GET /api/admin/users/{id}/agents` | GET | 查看用户 Agent 授权 |
| `PUT /api/admin/users/{id}/agents` | PUT | 设置用户 Agent 列表 |

## 6. 后端路由保护

### 6.1 依赖注入

```python
async def get_current_user(request: Request) -> User:
    """从 JWT 提取并验证用户"""

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """额外要求 admin 角色"""
```

### 6.2 现有路由改造

| 路由 | 改造 |
|------|------|
| `GET /api/sessions` | `WHERE user_id = current_user.id` |
| `POST /api/sessions` | 绑定 `user_id` |
| `PUT/DELETE /api/sessions/{id}` | 校验归属 |
| `GET /api/sessions/{id}/messages` | 校验归属 |
| `POST /api/threads/{id}/runs/stream` | 从 query token 认证 + 校验归属 |
| `GET /api/agents` | 过滤已授权 Agent |
| `CRUD /api/agents/*` | 仅 Admin |
| `CRUD /api/permissions/*` | 仅 Admin |
| `GET /api/tools`, `/api/models` | 已登录即可 |

### 6.3 SSE 认证

- 从 `?token=<jwt>` 提取
- 验证 token → 验证 thread_id 对应 session 归属
- 失败 → 关闭连接返回 401

## 7. 前端变更

### 7.1 新增页面

- `LoginView.vue`：登录表单
- `AdminView.vue`：用户管理 + Agent 授权
- `ChangePasswordDialog.vue`：修改密码弹窗

### 7.2 路由守卫

```
访问页面 → token 存在？
  → 否 → /login
  → 是 → GET /api/auth/me 有效？
    → 否 → 清除 token → /login
    → 是 → 放行
    
/admin → 额外检查 role === 'admin'
```

### 7.3 Store 变更

- 新增 `stores/auth.ts`：token、用户信息、登录/登出/改密
- `stores/sessions.ts`：后端已按 user_id 过滤，前端无需改查询逻辑
- `stores/agents.ts`：后端已过滤授权 Agent

### 7.4 HTTP 客户端

- `api/http.ts`：所有请求添加 `Authorization: Bearer <token>` header
- `api/sse-client.ts`：SSE URL 拼接 `?token=<jwt>`
- 401 响应全局拦截 → 清除 token → 跳转 /login

### 7.5 UI 变化

- Header 显示用户名 + 登出按钮 + 修改密码入口
- 侧边栏：Admin 可见"管理"导航项

## 8. 配置项

`config.jsonc` 新增 `auth` section：

```jsonc
{
  "auth": {
    // JWT 签名密钥（必填，无默认值）
    "secret": "your-secret-key-here",
    // Token 有效期（天）
    "token_expire_days": 7
  }
}
```

启动时若 `auth.secret` 未配置 → 抛出错误拒绝启动。

## 9. 安全考虑

- 密码使用 bcrypt 哈希（cost factor 12）
- JWT secret 不能为空或弱密码（启动校验最小长度 16）
- 401/403 错误消息不泄漏具体原因（统一 "认证失败" / "权限不足"）
- 删除用户时级联处理：清空其会话？或保留数据标记为已删除？→ **直接删除其会话和消息**
- Admin 不能删除自己

## 10. 测试策略

- 单元测试：JWT 生成/验证、密码哈希、权限检查
- 集成测试：各 API 端点的认证和授权
- 前端：路由守卫跳转、token 过期处理
