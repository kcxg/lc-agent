---
name: restart-bfzs
description: >-
  Rebuild lc-agent frontend and restart the bfzs Python server.
  Use when the user asks to restart, rebuild, or redeploy the bfzs application,
  or after making significant code changes to the framework or frontend.
---

# Restart bfzs Server

## ⚠️ 核心判断规则（必须首先判断）

在执行任何操作前，AI 必须先判断改动类型：

| 改动类型 | 操作 |
|---------|------|
| **仅前端代码**（.vue / .ts / .css 等 frontend/ 目录下的文件） | **只构建前端，不重启 Python 服务** |
| **后端代码**（.py 文件）或 **config.jsonc** | 运行完整重启脚本 |
| **前端 + 后端都改了** | 运行完整重启脚本 |

### 仅前端编译（不重启服务）

```powershell
powershell -ExecutionPolicy Bypass -File "D:\codes\lc-agent\.agents\skills\restart-bfzs\scripts\build-frontend.ps1"
```

在 `D:\codes\lc-agent\frontend` 执行 `npm run build`（vue-tsc 类型检查 + vite build），产物输出到 `D:\codes\lc-agent\lc_agent\web\dist\`。

### 完整重启（停旧服务 + 构建前端 + 启新服务）

```powershell
powershell -ExecutionPolicy Bypass -File "D:\codes\lc-agent\.agents\skills\restart-bfzs\scripts\restart.ps1"
```

直接前台运行即可（不需要后台任务等特殊技巧）；服务进程由脚本独立启动，不会随脚本退出而结束（2026-09-14 实测：跨多次工具调用仍存活）。执行时给足超时（建议 ≥240 秒），脚本在端口开始监听后打印 `listening on ...` 并退出（退出码 0）。

## restart.ps1 三步流程

1. **停旧服务** —— 结束占用 8001 端口的进程：先正常结束（最多等 15 秒），仍未退出则用 `taskkill /F /T` 强制结束
2. **构建前端** —— 在 frontend 目录执行 `npx vite build`（跳过 vue-tsc 类型检查，避免内存不足）；构建失败立即中止
3. **启新服务** —— `Start-Process` 启动 `python -u -m bfzs.main`，日志写入 `.tmp\bfzs-runlogs\bfzs-restart-<时间戳>.out/.err.log`；最多等 90 秒，端口进入监听状态即成功，否则报错并打印日志文件路径

### Parameters

| Param | Default | Description |
|---------|-------------|--------------------|
| -Port   | 8001        | Server listen port |
| -Host_  | 0.0.0.0     | Server bind address |
| -SkipBuild | 默认关闭 | 跳过前端构建，只做停旧服务 + 启动新服务 |

## 验证服务

```powershell
Get-NetTCPConnection -LocalPort 8001 -State Listen                                       # 应有监听
(Invoke-WebRequest 'http://127.0.0.1:8001/' -UseBasicParsing -TimeoutSec 8).StatusCode   # 应为 200
```

## Notes

- Python: `D:\ProgramData\miniconda3\envs\py312\python.exe`；bfzs 工作目录: `D:\codes\lc-agent-bfzs`
- 脚本为服务进程设置 `PYTHONPATH=D:\codes\lc-agent`、`PYTHONUNBUFFERED=1`
- 构建中途失败可能留下不完整的 `dist` 目录：重跑一次干净的完整构建即可（配置 `emptyOutDir: true` 会自动清空输出目录），不要用 `--emptyOutDir=false` 反复重试（会不断积攒过时的旧构建文件）
- **不要删除脚本启动服务前处理 PATH 环境变量的那段代码**：它先删除环境里 `Path`、`PATH`、`path` 这三个名字只差大小写的重复条目，再重新设置一份 `Path`（值不变）。原因：WorkBuddy 工具会话实测会同时存在这 3 个重复条目，PS 5.1 的 `Start-Process` 带 `-RedirectStandard*` 参数时遇到重复条目会报错 `Item has already been added`，脚本因此停在第 3 步、服务起不来。环境里只有 1 份 `Path` 时，这段代码不改变任何东西
