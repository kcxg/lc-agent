---
name: codegraph
description: >-
  使用 codegraph MCP 进行代码结构查询时加载此 Skill。
  触发场景：查找函数定义、理解调用链、分析代码影响范围、
  回答"X 是怎么实现的"等结构性代码问题时使用。
---

# CodeGraph 使用指南

本项目配置了 CodeGraph MCP 服务器，只暴露一个工具：`codegraph_explore`。CodeGraph 是基于 tree-sitter 解析的知识图谱，索引了代码库中的每个符号、边和文件。查询亚毫秒级，返回 grep 无法提供的结构化信息。

## 用 `codegraph_explore` 代替读文件

在任何**结构性问题**（X 是怎么工作的、X 怎么到达 Y、谁调用了谁、X 在哪里定义、了解某个区域）上，优先用 `codegraph_explore`，而不是 grep/find/search_files 或 read_file。它接受自然语言问题或一组符号名/文件名，返回相关符号的**逐行带编号的完整源码**（按文件分组，与 read_file 格式一致，可直接用于编辑），加上符号之间的**调用路径**（包括动态分发跳转：回调、React 重渲染、JSX children 等 grep 无法追踪的路径），以及**影响范围摘要**（哪些代码依赖了这些符号）。在查询中指定文件名或符号名即可读取其当前源码。

## 使用原则

1. **直接回答，不要委派探索任务**。一次 `codegraph_explore` 通常就能回答整个问题；如果需要更多细节，再次调用 `codegraph_explore` 指定更具体的符号名即可。codegraph 本身就是预构建的索引，不需要再派子 agent 去读文件——也不需要跑 grep + read 循环——那是在重复 codegraph 已经做过的工作，且消耗更多 token。

2. **信任 codegraph 的结果**。它来自完整的 AST 解析。不要用 grep 重新验证——那样更慢、更不准确、且浪费上下文。

3. **不要先 grep 或 read_file**。一次 `codegraph_explore` 就能在一个来回中返回相关源码。只有在需要确认 codegraph 未覆盖的细节，或查看 codegraph 不索引的内容（配置文件、文档）时，才用 read_file / search_files。

4. **索引延迟——看过期提示，不要猜等待时间**。如果 codegraph 返回 "⚠️ Some files referenced below were edited since the last index sync…"，对列出的文件使用 `read_file` 获取最新内容。未列出的文件仍然可信，codegraph 对它们是权威的。

## 未初始化时

如果 codegraph 返回 "not initialized"，提示用户：

> 这个项目还没有初始化 CodeGraph 索引。需要我运行 `codegraph init -i` 来构建索引吗？
