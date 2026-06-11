
# 1. 开发一个 lc_agent 的框架

使用langchain  langgraph deepagents 框架技术开发，


功能要类似nb_agent框架， 但是不使用tui终端，而是使用web界面。web采用vue + element-ui-plus 框架。

lc_agent 定位是一个框架， 然后用户可以导入lc_agent 框架开发，开发自己的具体的agent应用。可以在页面创建智能体。

后端采用fastapi + sqlmodel ，要使用asyncio生态编程

# 2. nb_agent 项目文件夹
ai先必须熟悉nb_agent框架，以及nb_agent_bfzs项目和nb_agent之间的关系。

nb_agent 项目文件夹：
"D:\codes\nb_agent"   

nb_agent_bfzs(基于nb_agent框架开发的自定义项目)项目文件夹:
"D:\codes\nb_agent_bfzs"

我是让你参考nb_agent，内让你照抄， 尽量使用langchain全家桶的2026年最新用法，不用学nb_agent那样都自己实现。

# 3.AI 写langchain 家族框架代码时候的规则

## 3.1 写 langchain / langgraph / deepagents 代码时，禁止使用ai预训练的过时的语法写法。
  要使用最新的框架语法。 写代码时候要用 docs-langchain 和 reference-langchain 这个两个langchain官方文档的mcp工具查询框架最新用法。


## 3.2 如果有必要，要用 nb_rag mcp查询 langchain / langgraph / deepagents  用法
  如果官方的文档，不够用，ai要调用 nbrag mcp的一些列工具来查询用法，要多次多轮深入调用nbrag的一系列工具，不要浅尝辄止，没检索足够足够的资料就开始回答。

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


# 4 web界面

web界面要需要非常炫酷黑暗风， 要使用vue + element-ui-plus 框架。
采用左边菜单栏，中间内容区的方式，右边显示现在nbagent tui那些模型 tools 和 mcp skill，可以热切换屏蔽和激活。

不要照抄 nb_agent tui的布局和相似，因为python开发的tui有固定的局限性，web要按照最佳实践来设计和开发。

# 5 所有 tools 和 mcp 和 skills 都能快速按分组屏蔽
tools 和 mcp 都要能方便按分组激活和屏蔽

例如skill.md 的 希望题头元数据如果加上 ,方便快速激活或者屏蔽一组技能
metadata
    group: "技能组1"$

# 6 关于智能体

智能体就是langchian的 complinedgraph类型， 用户可以在python代码在创建多个agent，页面要能显示这些智能体。

并且支持用户在页面创建智能体， 就像nbaegnt那样的是 promote + tools + mcp + skills 的组合。