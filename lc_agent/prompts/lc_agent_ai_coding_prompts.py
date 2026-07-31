"""
lc-agent 内置编程纪律提示词
============================

这些提示词描述的是 AI 在使用 lc-agent 工具时应遵循的工程约束，
与 Cursor 不同，这里的规则基于 lc-agent 实际提供的工具和运行环境。

**使用方式**
    from lc_agent.prompts.lc_agent_ai_coding_prompts import CODING_GUIDELINES_PROMPT

    # 注入到 system message 里的某个 block
    middleware.append(_SystemBlockMiddleware(CODING_GUIDELINES_PROMPT, "CodingGuidelinesMiddleware"))
"""

# ---------------------------------------------------------------------------
# 工具使用约束（项目模式下自动注入）
# ---------------------------------------------------------------------------
TOOL_USAGE_PROMPT = """\
## 工具使用规范

### 读取文件
- 修改文件前必须先用 `read_file` 读取其当前内容；禁止凭记忆直接写入
- 需要读取大文件的局部内容时，使用 `read_file` 的 `offset`/`length` 参数指定行范围
- 禁止用 `run_command` + `cat`/`type`/`head` 间接读取文件

### 搜索代码
- 在项目里查找函数、类名、字符串时，优先用 `search_files`（底层为 ripgrep）
- 需要列出目录结构时使用 `list_directory`，禁止用 `run_command dir/ls` 间接列目录

### 写入 / 修改文件
- 优先使用 `edit_block` 对文件进行精确的字符串替换，而不是整体重写
- 整体重写时使用 `write_file`；确保内容完整，不截断
- 不创建不必要的临时文件；创建的文件一旦不再需要，及时清理

### 运行命令
- `run_command` 在 Windows 上默认使用 PowerShell，在 Linux/macOS 上使用 $SHELL
- 运行可能挂起或耗时很长的命令（如服务器、监控进程）时，使用 `start_background_process`；
  短命令用 `run_command`
- 运行测试或需要超时终止的命令时，在命令本身加超时参数，或用 `run_command` 的 `max_run_ms` 参数
- 杀掉进程使用 `kill_process`，查看进程列表使用 `list_all_processes`
"""

# ---------------------------------------------------------------------------
# 注释约束（与 Cursor 内置一致，此处针对 lc-agent 工具名重申）
# ---------------------------------------------------------------------------
_COMMENT_DISCIPLINE = """\
## 注释约束

- **不写废话注释**：禁止写只是复述代码功能的注释（如 "# 读取文件"、"# 返回结果"）；
  注释只用于解释非显然的意图、权衡取舍或外部约束
- **不解释改动**：不在注释里描述"你做了什么改动"，只描述代码的"为什么"
"""

# ---------------------------------------------------------------------------
# 导出（不由引擎自动注入；可在有需要的 Preset 的 system_prompt 中手动引用）
# ---------------------------------------------------------------------------
CODING_GUIDELINES_PROMPT = f"""\
{TOOL_USAGE_PROMPT}

{_COMMENT_DISCIPLINE}"""
