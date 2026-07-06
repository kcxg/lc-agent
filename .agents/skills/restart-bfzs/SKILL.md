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
| **仅前端代码**（.vue / .ts / .css 等 frontend/ 目录下的文件） | **只运行 npm run build，不重启 Python 服务** |
| **后端代码**（.py 文件）或 **config.jsonc** | 运行完整重启脚本 |
| **前端 + 后端都改了** | 运行完整重启脚本 |

### 仅前端编译（不重启服务）

```powershell
# working_directory: D:\codes\lc-agent\frontend
npm run build
```

### 完整重启（前端编译 + 停旧服务 + 启新服务）

```powershell
# working_directory: D:\codes\lc-agent
# block_until_ms: 0 (background — server is long-running)
powershell -ExecutionPolicy Bypass -File "D:\codes\lc-agent\.agents\skills\restart-bfzs\scripts\restart.ps1"
```

## Verify Startup

After backgrounding, poll the terminal output until you see:
- `Uvicorn running on http://127.0.0.1:8001` — server ready
- `[MCP] Connected:` — MCP integrations online

## Script Details

The script (`scripts/restart.ps1`) performs three steps:
1. **Build frontend** — `npm run build` in `D:\codes\lc-agent\frontend`
2. **Stop existing server** — kills any process on port 8001
3. **Start bfzs server** — runs `python -u -m bfzs.main --port 8001`

### Parameters

| Param   | Default     | Description        |
|---------|-------------|--------------------|
| -Port   | 8001        | Server listen port |
| -Host_  | 127.0.0.1   | Server bind address|

## Notes

- Python interpreter: `D:\ProgramData\miniconda3\envs\py312\python.exe`
- Frontend build output: `D:\codes\lc-agent\lc_agent\web\dist\`
- Working directory for bfzs: `D:\codes\lc-agent-bfzs`
- The script sets `PYTHONUNBUFFERED=1` for immediate log output
