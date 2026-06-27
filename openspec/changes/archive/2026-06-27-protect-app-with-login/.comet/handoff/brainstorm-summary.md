# Brainstorm Summary

- Change: protect-app-with-login
- Date: 2026-06-27
- Status: 用户已确认

## 确认的技术方案

采用单管理员配置凭据 + 签名 HttpOnly Cookie + 集中 HTTP 依赖校验 + WebSocket accept 前校验 + Vue auth store/router guard。

- 后端新增独立 auth 模块，负责读取 `config["auth"]`、校验管理员凭据、创建/验证签名 session cookie、清除 cookie。
- 新增 `/api/auth/login`、`/api/auth/logout`、`/api/auth/me`；auth router 公开，业务 API 受认证依赖保护。
- 在 `LcAgentApp._setup_websocket_route()` 中，于 `ChatWebSocketHandler.connect()` 前校验 cookie；未认证连接不进入聊天循环。
- 前端新增 auth store、`/login` 路由和路由守卫；`App.vue` 只在认证通过后初始化 tools/agents/sessions。
- 登出调用后端清 cookie，并让前端返回登录页。

## 关键取舍与风险

- 不新增用户表，避免过早引入多用户模型和迁移。
- 不使用 localStorage/JWT，降低前端脚本读取 token 的风险。
- 无服务端 session 存储时，无法逐个吊销未过期 session；通过较短可配置 TTL 和 logout 清 Cookie 缓解。
- 静态资源仍可被未登录访问；保护重点放在 UI 路由、API 数据和 WebSocket 通道。
- `auth.enabled=true` 但缺少账号、密码或 session secret 时，后端应显式失败，不静默开放。

## 测试策略

- 后端覆盖登录成功、登录失败、`/api/auth/me`、logout、未登录访问业务 API 返回 401、带 cookie 后正常访问。
- WebSocket 覆盖未登录连接被拒绝/关闭、登录后连接成功。
- 前端覆盖未登录进入 `/` 或 `/c/:id` 跳 `/login`、登录后跳回目标页、401 时清 auth 状态回登录页。
- 验证时运行相关 pytest、前端 contract/build 检查。

## Spec Patch

无。
