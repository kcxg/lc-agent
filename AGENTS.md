
# 1 当前项目，请使用python3.12运行

解释器在 `D:\ProgramData\Miniconda3\envs\py312\python.exe`


# 2 项目开发阶段

目前还是已非常早期开发阶段，没人使用，数据和代码中不要写兼容性迁移，没有任何历史包袱。
但sqlite里面有数据，不得自行删除。

# 3.AI 写langchain 家族框架代码时候的规则

## 3.1 写 langchain / langgraph / deepagents 代码时，禁止使用ai预训练的过时的语法写法。
  要使用最新的框架语法。 写代码时候要用 `docs-langchain` 和 `reference-langchain` 这个两个langchain官方文档的mcp工具查询框架最新用法。
以及使用`context7`这个mcp工具查询框架最新用法。
要尽量符合langchian框架教程最佳实践用法，不重复造轮子

## 3.2 如果有必要，要用 nb_rag mcp查询 langchain / langgraph / deepagents  用法
  如果官方的文档，不够用，ai要调用 `nbrag` mcp的一些列工具来查询用法，要多次多轮深入调用nbrag的一系列工具，不要浅尝辄止，没检索足够足够的资料就开始回答。

  nbrag已向量化langchain相关源码和教程到知识库 `langchain_ai_codes_and_docs`

  langchain_ai_codes_and_docs 知识库包含如下文件件的内容
  ```python
  r'D:\codes\docs\src',
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_anthropic",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_classic",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_community",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_core",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_deepseek",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_google_genai",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_openai",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_protocol",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_text_splitters",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langdetect",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langgraph",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langgraph_sdk",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langsmith",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain",
       r"D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\deepagents",
  ```

## 3.3 ai可以从 `D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\` 目录下深入 langchain 相关的源码，包含函数入参和注释和用法。

ai可以从 `D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\` 目录下深入 langchain 相关的源码，包含函数入参和注释和用法。


# 4 理解项目定位

lc-agent 是一个框架，是作为python包被导入使用。
`D:\codes\lc-agent-bfzs` 项目是基于lc-agent框架开发的演示项目。
`D:\codes\lc-agent-bfzs\bfzs\main.py` 是演示项目的入口文件。

lc-agent-bfzs的数据库是 `D:\codes\lc-agent-bfzs\bfzs_data.db` 和 `D:\codes\lc-agent-bfzs\bfzs_checkpoints.db` 。不是在lc-agent框架的默认目录`D:\codes\lc-agent\` 下。


<comet-ambient-resume>
<!-- Managed by Comet. Edits inside this block may be replaced by comet init/update. -->
<!-- Contract: comet.resume_probe.v2 -->

## Comet Ambient Resume

在这个仓库中，开始处理需要改动或调查的任务前，如果可能存在活跃 Comet workflow，把当前用户请求传入只读探针：`comet resume-probe . --stdin --json`。

- 如果用户通过宿主明确调用任意 Comet Skill（例如 `@comet`、`/comet`、`@comet-native` 或 `/comet-hotfix`），显式调用优先于本恢复协议；不要运行 resume probe，直接进入被调用的 Skill。
- 只信任返回的 `workflow`、`skill` 和 `entrySource`；它们只由项目配置或无配置兼容回退决定。不得扫描或切换另一套 workflow。
- 如果 probe 返回 `auto_resume`，简短说明选中的 active change，并进入 `nextCommand` 指向的永久入口。不要把状态命令当作恢复入口直接推进。
- 如果 probe 返回 `ask_user`，只问一个简短问题并等待用户回复。
- 如果当前请求未明确调用 Comet Skill，且 probe 返回 `out_of_scope` 或 `none`，不要进入 Comet workflow。
- 如果配置或状态无效且没有 `nextCommand`，停止并报告原因；不要猜测另一个 workflow。
- 不能只因为存在 active change 就把无关任务挂到该 change。Native 的未提交改动由 Native 入口检查，不由探针自动归因。
</comet-ambient-resume>
