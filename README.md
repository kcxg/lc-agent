# lc_agent

基于 LangChain / LangGraph 的智能体框架，自带炫酷深色 Web UI。

用户导入框架即可拥有完整的 Agent 运行环境 —— 无需自己写前端。

## 特性

- **流式对话** — 通过 WebSocket 实时流式输出 LLM 回复
- **工具系统** — `@tool` 装饰器 + 分组管理 + 三值语义（全选/全关/指定）
- **MCP 集成** — 配置声明 MCP 服务器，启动后自动连接并发现工具
- **Skills 注入** — 扫描 `SKILL.md` 文件，自动注入到系统提示词
- **Agent 预设** — 页面可视化创建/编辑/切换 Agent（prompt + tools + skills 组合）
- **Human-in-the-Loop** — 危险工具自动暂停，等待用户审批
- **多会话管理** — 多轮对话持久化，随时切换/恢复完整历史
- **代码注册** — `app.add_agent(name, graph)` 注册自定义 CompiledStateGraph
- **深色主题** — Vue 3 + Element Plus，三栏布局，开箱即用

## 快速开始

### 安装

```bash
pip install -e .
```

### 配置

创建 `config.jsonc`：

```jsonc
{
  "provider": {
    "deepseek": {
      "api_key": "{env:DEEPSEEK_API_KEY}",
      "base_url": "https://api.deepseek.com",
      "models": [
        {"id": "deepseek-chat", "context_limit": 64000}
      ]
    }
  },
  "agent": {
    "system_prompt": "你是一个有用的AI助手。",
    "default_model": "deepseek-chat"
  }
}
```

支持环境变量替换（`{env:VAR_NAME}`），兼容 OpenAI / DeepSeek / Ollama / LiteLLM 等任何 OpenAI 兼容接口。

### 启动

```bash
lc-agent
# 或
python -m lc_agent
```

打开浏览器访问 http://localhost:8000 即可开始对话。

### 命令行参数

```bash
lc-agent --host 0.0.0.0 --port 8080 --config ./my-config.jsonc
```

## 作为框架使用

```python
from lc_agent import LcAgentApp, load_config, tool

# 定义工具
@tool(group="math")
def add(a: int, b: int) -> int:
    """两数相加"""
    return a + b

# 加载配置并启动
config = load_config("config.jsonc")
app = LcAgentApp(config)

# 注册自定义 Agent（可选）
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

my_llm = ChatOpenAI(model="gpt-4o", api_key="...")
my_graph = create_react_agent(my_llm, tools=[add])
app.add_agent("my_math_agent", my_graph, description="数学计算专用")

app.run()
```

## 配置详解

### Provider（LLM 提供商）

```jsonc
{
  "provider": {
    "<provider_name>": {
      "api_key": "your-key",
      "base_url": "https://api.example.com/v1",  // 可选，用于自定义端点
      "models": [
        {"id": "model-id", "context_limit": 8000}
      ]
    }
  }
}
```

### MCP 服务器

```jsonc
{
  "mcp_servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-filesystem", "/tmp"],
      "env": {}
    }
  }
}
```

### Skills

在 `skills/` 目录下放置 `SKILL.md` 文件：

```markdown
---
name: code-review
description: 代码审查技能
---

# 代码审查

审查时请关注...
```

### Agent 预设

通过 Web UI 创建，或通过 API：

```bash
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "代码助手", "system_prompt": "你是代码专家", "default_model": "deepseek-chat"}'
```

## API 文档

启动后访问 http://localhost:8000/api/docs 查看完整 OpenAPI 文档。

主要端点：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/models` | GET | 可用模型列表 |
| `/api/tools` | GET | 已注册工具 |
| `/api/tools/groups` | GET | 工具分组 |
| `/api/agents` | GET/POST/PUT/DELETE | Agent 预设 CRUD |
| `/api/sessions` | GET/POST/PUT/DELETE | 会话管理 |
| `/api/mcp` | GET | MCP 服务器状态 |
| `/api/skills` | GET | Skills 列表 |
| `/ws/chat` | WebSocket | 实时对话 |

## 技术栈

- **后端**: FastAPI + SQLModel + LangChain + LangGraph
- **前端**: Vue 3 + Element Plus + Pinia + Vite
- **数据库**: SQLite (异步) + LangGraph Checkpoint
- **协议**: WebSocket (流式) + REST API

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -q

# 前端开发（热更新）
cd frontend
npm install
npm run dev
```

## License

MIT
