# System Tools 设计规格书

> 决策日期：2026-07-29
> 参考项目：D:\codes\DesktopCommanderMCP (v0.2.46)

## 1. 文件结构

```
lc_agent/tools/system_tools/
├── __init__.py              # 注册所有工具，导出工具列表
├── _config.py              # 读取 config.jsonc 中 system_tools 配置的辅助模块
├── file_read_tools.py      # group: "file_read", group_description: "文件读取"
├── file_write_tools.py     # group: "file_write", group_description: "文件写入"
└── command_tools.py        # group: "command", group_description: "命令执行"
```

## 2. 工具分组与权限模型

三个 group 独立控制，读写分离。AI 可以只有 `file_read` 权限而没有 `file_write`。

| group | 风险等级 | 工具 |
|-------|---------|------|
| file_read | 低（只读） | read_file, read_multiple_files, list_directory, get_file_info, search_files |
| file_write | 高（修改文件系统） | write_file, create_directory, move_file, edit_block |
| command | 高（执行命令） | run_command, list_processes, kill_process |

## 3. config.jsonc 配置段

```jsonc
{
  "system_tools": {
    "file_read": {
      "allowed_directories": []   // 空数组 = 不限制；非空 = 只允许指定目录及其子目录
    },
    "file_write": {
      "allowed_directories": [],  // 同上，可以比 file_read 更严格
      "blocked_extensions": [".exe", ".dll", ".sys"]  // 禁止写入的扩展名
    },
    "command": {
      "blocked_commands": ["format", "diskpart", "shutdown", "del /s"],
      "default_shell": "powershell",
      "timeout_ms": 30000
    }
  }
}
```

配置注入方式：工具内部直接 `from lc_agent.config import get_config` 读取全局配置。

## 4. 各工具详细设计

### 4.1 file_read 组

#### read_file
- 参数：`path: str`, `offset: int = 0`, `length: int = 1000`
- offset >= 0：从第 N 行起读 length 行
- offset < 0：tail 模式，读最后 |offset| 行
- 图片文件（.png/.jpg/.gif/.webp）：返回 base64 编码
- 安全：校验 allowed_directories

#### read_multiple_files
- 参数：`paths: list[str]`
- 并行读取多个文件，单个失败不影响整体
- 返回：每个文件的路径 + 内容（或错误信息）

#### list_directory
- 参数：`path: str`, `depth: int = 2`
- 递归列出目录结构，标记 [FILE] / [DIR]
- 深层目录截断提示

#### get_file_info
- 参数：`path: str`
- 返回：size, created, modified, type, line_count

#### search_files
- 参数：`path: str`, `pattern: str`, `search_type: "files" | "content" = "content"`, `max_results: int = 50`, `ignore_case: bool = True`, `file_pattern: str | None = None`, `context_lines: int = 3`
- 内部调用 ripgrep（subprocess 同步执行）
- 一次性返回结果（非会话模式）
- 有超时保护

### 4.2 file_write 组

#### write_file
- 参数：`path: str`, `content: str`, `mode: "rewrite" | "append" = "rewrite"`
- rewrite 模式：如果文件存在，覆盖
- append 模式：追加到末尾
- 安全：校验 allowed_directories + blocked_extensions
- 自动创建父目录

#### create_directory
- 参数：`path: str`
- recursive=True（自动创建父级）
- 安全：校验 allowed_directories

#### move_file
- 参数：`source: str`, `destination: str`
- 支持重命名和移动
- 安全：source 和 destination 都要校验

#### edit_block
- 参数：`file_path: str`, `old_string: str`, `new_string: str`, `expected_replacements: int = 1`
- 精确匹配替换（不做模糊匹配）
- 校验替换数量是否符合预期
- 返回替换前后的 diff 预览

### 4.3 command 组

#### run_command
- 参数：`command: str`, `timeout_ms: int = 30000`, `shell: str | None = None`
- 一次性执行，等待完成
- 返回：stdout, stderr, exit_code, duration_ms
- 安全：blocked_commands 校验（递归解析 && || ; 等组合命令）
- shell 默认从配置读取

#### list_processes
- 无参数
- Windows: `tasklist` / Unix: `ps aux`
- 返回：PID, 名称, 内存, CPU 等

#### kill_process
- 参数：`pid: int`
- 终止指定进程

## 5. 安全机制

### 5.1 路径校验（file_read / file_write 共用逻辑）
1. 解析路径（支持 ~、相对路径 → 绝对路径）
2. resolve symlink（防止通过软链接绕过目录限制）
3. 检查是否在 allowed_directories 内

### 5.2 命令校验（command 组）
1. 解析命令字符串，提取所有子命令（处理 &&, ||, ;, |, $(), `` 等）
2. 逐个检查是否在 blocked_commands 列表中

## 6. 设计决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 搜索模式 | 同步单次返回 | LLM 一次调用即得结果，不需要多轮交互 |
| 命令执行 | 一次性 subprocess | 简单直接，覆盖 90% 场景 |
| 编辑匹配 | 精确匹配 | 可靠，避免误替换 |
| 文件类型 | 文本 + 图片 base64 | 核心需求 + 多模态支持 |
| 配置注入 | 全局 config 直接读 | 简单，无需复杂 DI |
| 读写分离 | 不同 group | 防止 AI 不当写入 |
