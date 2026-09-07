# Token 用量统计任务计划

> 目标：让 lc-agent 能回答三个问题——**一共烧了多少**、**每个人/每个 agent 各烧多少**、**谁在白嫖**。
>
> **核心设计（已定）**
>
> - `llm_usage` 只存**原始 token 数**，不存钱、不算积分、不要倍率
> - 单价在**管理页面**配置，存 `model_pricing` 表，带**生效时间**，改价走新增而非覆盖
> - 金额在**查询时按当时生效价**计算 —— 历史账单不因日后调价而漂移
>
> 状态：待评审 → 待实施。动手前先过一遍 §9 待定问题。

---

## 0. 目标与非目标

**做**

- 每一次 LLM 调用的 token 明细落结构化表（可 SQL 聚合）
- 按 人 / agent / 模型 / 天 多维聚合；导出 CSV 给老板看
- 页面配置单价，按生效时间算真实金额（元）
- 会话级下钻：从"某人烧了 200 万 token"点到"他到底问了什么"

**明确不做**

- **积分 / 倍率** —— 内部工具模型就那么几个，真实金额天然承担了倍率的作用，  
  多一层积分 = 多一套配置 + 多一套要向老板解释的口径，纯自找麻烦
- **金额入库时固化** —— 价格会调，写死就得迁移历史数据；查询时算，改价立即生效
- **运行时从 jsonc 读价格** —— 改价要上服务器改文件 + 重启，摩擦太大
- 自动限流 / 配额封禁（一期）—— 误伤成本高于 token 钱，先只做可见性
- 实时流式计费展示（每轮实时扣费）

---


## 1. 现状问题（代码级定位）

| # | 问题                   | 位置                                                                                                                                                                                                                                 | 后果                                          |
| - | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 1 | **子 agent token 全丢** | `stream_utils.accumulate_usage()` 里 `if _extract_subagent_tool_call_id(checkpoint_ns) is not None: return` 主动跳过；而 `subagent_tracker.py:208` 调 `finalize_subsession_message()` 时只传 `content/tool_calls/http_traces`，`usage` 参数存在但没传 | 主会话跳过、子会话不存 → 两头不记。而子 agent 恰恰是最烧 token 的部分 |
| 2 | **没有 model_id 字段**   | `accumulate_usage()` 只输出 `input/output/cache_read/reasoning`                                                                                                                                                                       | 不知道是哪个模型烧的 → 算不了钱                           |
| 3 | **存成 JSON blob**     | `chat_ui_messages.usage = {"rounds": [...]}`                                                                                                                                                                                       | 无法 `GROUP BY`，统计只能全表扫 + 反序列化                |
| 4 | **图外调用不记**           | `engine.generate_title()`（标题生成）、`SummarizationMiddleware`（压缩）                                                                                                                                                                      | 每个新会话至少漏一次调用                                |
| 5 | **中断恢复会重复追加**        | `persistence.append_to_last_assistant_message()` 往 `rounds` 数组 append                                                                                                                                                              | 改明细表时必须有幂等键                                 |

**基础是好的**：`sessions` 表已有 `user_id` / `agent_id` / `parent_session_id`，`users` 表有 `role`，  
`file_changes` 表有改动文件清单。差的就是把 token 落成结构化事实表。

---

## 2. 数据模型


### 2.1 `llm_usage`（一次 LLM 调用一行，只记原始消耗）

新建 `lc_agent/db/models_usage.py`：

```python
class LlmUsage(SQLModel, table=True):
    __tablename__ = "llm_usage"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ts: datetime = Field(default_factory=utcnow, index=True)

    # ---- 归属维度 ----
    user_id: str = Field(default="", index=True)
    session_id: str = Field(default="", index=True)
    parent_session_id: str | None = Field(default=None, index=True)
    agent_id: str = Field(default="", index=True)
    model_id: str = Field(default="", index=True)    # 配置里的模型 id（全局唯一），见 §3.5
    raw_model_id: str = Field(index=True)            # 渠道原始模型名，必填，见 §3.5
    provider: str = Field(default="")   # 纯记录字段：凭据分组，不参与任何 key
    role: str = "main"      # main(主会话) | sub(子 agent)
    source: str = "chat"    # chat | title | summarize | automation

    # ---- 原始消耗（唯一事实来源，不存任何金额）----
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0   # 已包含在 output 内，仅用于分析

    # ---- 元信息 ----
    duration_ms: int = 0
    run_id: str = Field(default="", index=True)   # 一次 invoke 唯一 id
    seq: int = 0                                   # 该 run 内第几次调用
```

**为什么按"一次调用"而不是"一轮"**：一轮里可能有多步 LLM 调用，按次才能算缓存命中率、  
才能定位是哪一步把上下文撑爆了。

**为什么记 `cache_write`**：OpenAI 的缓存写入比普通输入还贵（~1.25×），DeepSeek 没有。  
多存一列成本为零，缺了以后补要迁移。

**索引**

```python
Index("ix_llm_usage_user_ts", "user_id", "ts")
Index("ix_llm_usage_agent_ts", "agent_id", "ts")
Index("ix_llm_usage_model_ts", "model_id", "ts")
Index("uq_llm_usage_run_seq", "run_id", "seq", unique=True)   # 幂等：中断恢复重放不重复计
```

**不建 rollup 日表**。SQLite 几百万行聚合无压力；等明细表超过 ~500 万行或统计接口 P95 > 500ms 再说。


### 2.2 `model_pricing`（单价表，页面维护）

```python
class ModelPrice(SQLModel, table=True):
    __tablename__ = "model_pricing"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    model: str = Field(index=True)        # 匹配键：填 model_id 或 raw_model_id
    kind: str = ""                         # input | output | cache_read | cache_write
    price_per_1m: float = 0.0              # 元 / 百万 tokens
    currency: str = "CNY"
    effective_from: datetime = Field(default_factory=utcnow)   # 生效时间
    note: str = ""
```

**匹配键只有 `model` 一列，没有 `provider`。**

> **模型标识只有一个：`model_id`，它必须全局唯一。**  
> `provider` 只是 `base_url` + `api_key` 的**配置分组** —— 把共用同一套凭据的模型写在一起，  
> 省得每个模型重复配一遍。**它不参与标识、不参与定价、不参与统计**（见 §3.5①）。  
> 所以定价表里干脆不留 `provider` 列 —— 留着就总会有人往里填值，  
> 然后产生"匹配不上时到底要不要看 provider"的疑问。没有列，就没有这个问题。

匹配规则（两级，从精到粗，命中即停）：

1. `model = model_id`
2. `model = raw_model_id`

同 key 取 `effective_from <= 统计时间` 的**最新一条**。  
`raw_model_id` 必填（§3.5）；当 `raw_model_id == model_id`（原厂直连）时两级查到同一行，无害重复查询而已。

> **顺序不能反**：`raw_model_id` 只能是**兜底继承层**，显式配给某个 model_id 的价必须优先。  
> 否则"某条路由其实更贵"这种场景就没法单独定价了。

**铁律：改价 = INSERT 一条新记录，绝不 UPDATE 覆盖。**  
否则历史账单会随调价漂移，老板 1 月看到的 5000 元到 3 月变成 3000 元，  
第一反应是"数据被人动过"而不是"降价了" —— 统计系统一旦失去可信度就废了。

### 2.3 迁移

新建 `lc_agent/db/migrations/versions/20260907_add_llm_usage.py`，  
`down_revision = "20260904_add_can_be_subagent"`（当前 head）。  
只建两张表 + 索引，**不动任何现有表、不删数据**。

---

## 3. 金额计算：按时间桶聚合 + 按当时价匹配

### 3.1 聚合 SQL（只做求和，不碰价格）

```sql
SELECT :bucket AS bucket, model_id, provider,
       sum(input_tokens), sum(output_tokens),
       sum(cache_read_tokens), sum(cache_write_tokens),
       count(*)
FROM llm_usage
WHERE ts BETWEEN :from AND :to
GROUP BY bucket, model_id, provider
```

`bucket` 按 `granularity` 取值：

| granularity | SQL 表达式                                        | 结果集规模        |
| ----------- | ---------------------------------------------- | ------------ |
| `day`（默认）   | `date(datetime(ts, 'localtime'))`              | 天数 × 模型数，几百行 |
| `month`     | `strftime('%Y-%m', datetime(ts, 'localtime'))` | 更小           |

> **时区（2026-09-07 定）**：`ts` 存 UTC（与其他表一致），**切桶按服务器本地时区**（`localtime`）。  
> 否则国内用户北京时间 8 点前的用量会算进"昨天"，按天趋势和"非工作时段占比"信号整体偏 8 小时。  
> 代价：部署机时区必须设对（部署文档写明）；将来要配置化时只改这一处表达式。

> **一期不做 `hour`**：结果集 ×24，而"抓白嫖"靠的是月度/日度账单和派生指标  
> （非工作时段占比），不是小时曲线。真要加就是换一个 `strftime` 表达式的事。

分组维度（人 / agent / 模型）不进这条 SQL —— 它在 §5 的 `group_by` 里另外拼列；  
金额换算始终以 `(bucket, model_id)` 为最小单元，多维度只是再往上一层汇总。

### 3.2 金额换算（Python 侧）

```python
cost = (input_t  / 1_000_000) * p_in  \
     + (output_t / 1_000_000) * p_out \
     + (cache_r  / 1_000_000) * p_cr  \
     + (cache_w  / 1_000_000) * p_cw
```

价格表总共几十行，全量读进内存（带 TTL 缓存），对每个 `(bucket, model_id)` 找当时生效的那一版。

**这个方案的好处**：聚合 SQL 保持极简（不用写价格 join 的相关子查询），  
历史账单自动按当时价算，改价只影响改价之后，实现成本几乎为零。

### 3.2.1 价格匹配时刻（必须定死，否则会算错）

按天/月聚合后，一行只剩 `2026-09-07` 这种桶值，**拿哪个时刻去比 `effective_from` 是有歧义的**：

- 用当天 `00:00` → 管理员下午改的价，当天用量仍走旧价，"改了没生效"
- 用当天 `23:59:59` → 当天早上的用量也被算成新价

**定死规则：**

1. **价格生效时间精确到天**，管理页面只让选日期，时间部分归零
2. 匹配时刻取**该时间桶的结束时刻**（`day` → 当天 `23:59:59`，`month` → 当月最后一天 `23:59:59`）
3. 同一 `(model, kind, 生效日)` 有多条 → 取 `effective_from` 最大的一条

&#x5373;**"当天改价、当天生效"**。一天内改两次价的场景不存在，按天精度足够；  
关键在于消除歧义，否则两个人对账时对不上数，又是一笔糊涂账。

### 3.3 兜底展示规则

- **某模型没配价 → 金额显示 `—`，token 照常显示**  
  绝不用 0 假装算出来了。自建模型、某些代理不返回 usage，token 本来就是 0，  
  显示 0 元是在骗人。
- 币种统一 CNY，一期不搞多币种。**录价口径（2026-09-07 定）**：渠道按美元计费的  
  （如中转站），由配置者自行折算成人民币后录入，不在系统内做汇率换算——  
  折算时把当日汇率写进该条价格的 `note`，日后对账有据可查。

### 3.4 配置文件

`config.jsonc` 只留一个开关：

```jsonc
"usage_stats": {
    "enabled": true
}
```

`config/schema.py` 加 `UsageStatsConfig(enabled: bool = True)` 挂到 `AppConfig`。

**单价一个都不写进配置文件，也不提供初始种子价（已定）** —— 它是运行时数据，归页面管。  
新部署的代价：管理员需先在 `/admin/usage/pricing` 录入单价，看板才有金额；  
未录入期间 token 照常统计，金额显示 `—`。这个代价可接受，换来的好处是  
"价格只有一个来源"，不存在 config 和 DB 两份价格打架的问题。


### 3.5 模型标识：就两个字段，`model_id` + `raw_model_id`，同时必填

`model_id` 是**配置者自己命名的、全局唯一的名字**，不是厂商给的。  
厂商/渠道提供的原始模型名记在 `raw_model_id` 里。两个字段**同时必填**：

```jsonc
{
  "model_id": "zzz-auto-gpt-5.4",  // 自己命名的、全局唯一 —— 标识、统计、显示都用它
  "raw_model_id": "gpt-5.4",     // 渠道提供的原始模型名 —— 定价兜底 + 统计归并用
  "context_limit": 400000,
  "max_output_tokens": 32000
}
```

`provider` 在这里完全缺席 —— 它只是 `base_url` + `api_key` 的**配置分组**  
（把共用同一套凭据的模型写在一起，省得每个模型重复配），  
**不参与标识、定价、统计的任何 key**。配置结构里它照样存在，仅此而已。

**启动时一次性校验，任何一条不过就拒绝启动，错误信息列出全部问题项：**

1. **`model_id` 全局唯一**，跨 provider 重复也算撞 —— `sessions.model`、preset 的  
   `default_model`、定价、统计全靠它定位，撞了账就算不清
2. **`raw_model_id` 必填**，空字符串等同缺字段。**允许 `raw_model_id == model_id`**  
   （原厂直连时这是唯一正确答案），校验器绝不能把"两者相同"判为错误
3. **`(provider, raw_model_id)` 唯一** —— 同一个渠道里，同一个底层模型只允许声明**一个入口**，  
   重复 = 启动失败。路由 / 故障转移 / 多账号负载均衡是**渠道侧的事**  
   （litellm 的 fallbacks / loadbalancing 配置），不进 lc-agent 的模型列表 ——  
   lc-agent 只认"一渠道一底层模型一入口"

**显示直接用 `model_id`，没有 `display_model_name`（已砍）。**

它以前的存在理由在新设计下全都不成立：

- 防跨 provider 撞名 —— `model_id` 已全局唯一，没有撞名可防
- model_id 太丑、需要友好名 —— 原厂直连 `model_id` 就是厂商名（`deepseek-chat`，可读）；  
  反代 `model_id` 是**你自己起的**（litellm 的 model_name 由你定），觉得丑就在配置里起个好看的，  
  起名一次做对，不需要第二个名字打补丁

砍掉净赚：少一个字段、少一个唯一性校验、少一个前端 `useModelName()` 映射函数、  
少一整类"某个页面忘了映射直接露出 id"的 bug，统计接口也不用 join 配置返回显示名。

> ⚠️ **必须承认的一个约束**：原厂直连下 `model_id` 必须等于厂商原始模型名  
> （`core/engine.py` 里 `ChatOpenAI(model=model_id)` 直接把它发给 API），配置者**没有自由改名的空间**。  
> 所以"两个 provider 都提供同名的模型"是**真会撞**的（DeepSeek 官方 / 火山都卖 DeepSeek 系），  
> 撞了只有两条路：删掉其中一个，或走反代（在 litellm 侧改名）。  
> 反代下 `model_id` 由你在 litellm 配置里命名，天然可控 —— bfzs 那套 `ark-` / `go-` / `zzz-`  
> 前缀就是这么来的。

**为什么需要 `raw_model_id`**：同一个底层模型会以完全不同的 model_id 出现在多个渠道 ——  
中转站叫 `zzz-gpt-5.4`，另一家叫 `go-gpt54`，官方叫 `gpt-5.4`；  
中转站换马甲更是不可控。没有这个字段，跨渠道的账就对不到一起：

- 每个渠道的 model_id 都得单独配一遍价，漏一个就静默显示 `—`，而且没人会发现
- "哪个模型最烧钱"被拆成 N 行，结论被稀释，看不出该换哪个

用途与去向：

- **定价**：只作兜底继承层（`model_id` 精确 → `raw_model_id` 兜底，两级链见 §2.2）。  
  配在 `raw_model_id` 上 = 该底层模型**所有渠道统一价**；某渠道单独加价，  
  就在那个渠道的 model_id 上显式配一条覆盖
- **统计**：`group_by` 增列 `raw_model_id`，但**默认仍按 `model_id` 分组** ——  
  默认归并会掩盖"某条路由其实更贵"，归并应当是用户主动切的视角
- **落库**：`llm_usage` 存一列，写入时由 `usage_recorder` 从配置解析。  
  **不做运行时 join config** —— 它是算钱用的，config 一改历史账单就漂移
- **不参与显示** —— 显示就是 `model_id` 本身，路由信息天然在 model_id 里

> **为什么不是反过来**（`model_id` 改逻辑名 `gpt-5.4` + 另加 `upstream_id` 用于实际请求）：  
> 显示/统计/定价确实天然统一，但要改 engine 建 LLM 处（现在 `ChatOpenAI(model=model_id)`）、  
> `sessions.model` 语义、preset 的 `default_model` 引用，改动面大一个量级；  
> 而且"我在哪条路由上"这个排查中转站问题的关键信息会从 id 里消失。  
> `raw_model_id` 是**加一列**的方案，那个是**改一遍语义**的方案。
>
> **为什么不是"价格组 / 复制到多个 id"**：那是操作型的 —— 新增一个 `zzz-auto-gpt-5.6`  
> 忘了加进组就静默显示 `—`。`raw_model_id` 是声明式的，新 id 填了字段就自动继承。
>
> **不做**：不加 `channel` 字段把不同渠道的同名模型聚合成一行。  
> 它们价格不同，分开统计才对 —— 老板看到多行反而能直接看出"火山的最贵，该切官方的"。

---

## 4. 采集改造（4 个改动点）

### 4.1 `server/stream_utils.py` — `accumulate_usage()`

1. 补 `model_id`：`event["metadata"].get("ls_model_name")` 或 `response_metadata.model_name`，  
   取不到用当前请求的 `model_id`，再取不到写 `"unknown"`（宁可 unknown 也不能丢行）
2. **同时补 `provider`**（从当前请求的 provider 推导）—— 纯记录字段，供看板按渠道过滤，  
   **不参与标识**（标识是全局唯一的 `model_id`，见 §3.5）；同时解析出 `raw_model_id` 一并落库
3. **删掉"跳过子 agent"的 return**，改为打标记：
   ```python
   sub_id = _extract_subagent_tool_call_id(checkpoint_ns)
   usage["role"] = "sub" if sub_id else "main"
   usage["sub_session_id"] = sub_id or ""
   ```
4. 补 `cache_write_tokens`（目前没采）和 `seq`

### 4.2 ~~`server/subagent_tracker.py` — 子会话落库~~ **已砍（2026-09-07 grill 定）**

原方案是给 `finalize_subsession_message(...)` 补传 `usage=run.usage`。勘察后确认**不需要**：
子 agent 的 `on_chat_model_end` 事件本来就流经**同一条主流**（`checkpoint_ns` 特征识别，
§4.1 第 3 条已改为打 `role=sub` 标记而不是跳过），所以子 agent 的 usage 行在主流循环里
就能标记完整，由 §4.3 的 `usage_recorder` 在流结束的 `finally` 里统一落库。
`finalize_subsession_message` / `SubAgentRun` 完全不动 —— 少一条穿线，少一处时序竞态
（不存在"finalize 时流还没走完"的问题）。

### 4.3 新增 `server/usage_recorder.py`

- `record_usage(rows: list[dict], ctx)`：批量 insert，不做单条写（SQLite 写放大，多实例更痛）
- 从 session 元数据补 `user_id` / `agent_id` / `parent_session_id`
- **只落原始 token，不查价格、不算钱**（价格留给查询时算）
- 失败只记日志，**绝不能因为统计失败打断对话流**

调用点：`sse.py`（两处流）和 `agent_runner.py`，统一放 `finally` 里，中断/异常也要落库。

### 4.4 图外调用（P2，可延后）

- `engine.generate_title()`：包一层，`source="title"` 单独记一行
- `SummarizationMiddleware`：在图内，理论能被 `on_chat_model_end` 抓到，标 `source="summarize"`  
  （识别方式看 `metadata.langgraph_node` 或 checkpoint_ns 特征，需实测确认）
- 自动化任务：会话本身带 `user_id`，通过 `automation_runs.session_id` 反查标 `source="automation"`，不加字段

---

## 5. 聚合与 API

新增 `lc_agent/server/routes/usage.py`。**`/admin/usage/*` 全部 `Depends(require_admin)`，  
`/me/usage` 走普通登录态。**

### 5.1 通用聚合（admin）

```
GET /admin/usage/summary
    ?from=2026-09-01&to=2026-09-30
    &group_by=user,day          # 多值，逗号分隔；可选 user/agent/model_id/raw_model_id/bucket
    &granularity=day            # day（默认）| month
    &include_sub=true           # 是否含子 agent 消耗
```

**`group_by` 必须支持多值组合** —— 老板要看的是"每人每天多少"这种二维表，  
单选 `group_by` 只能出"谁一共多少"或"哪天一共多少"，查不出交叉。

常用组合：

| 场景                 | group_by              | granularity |
| ------------------ | --------------------- | ----------- |
| 每人每月花了多少（老板主视图）    | `user,bucket`         | `month`     |
| 某人每天花了多少（看趋势）      | `user,bucket`         | `day`       |
| 某人对每个 agent 花了多少   | `user,agent`          | `month`     |
| 哪个 agent 最烧钱       | `agent`               | `month`     |
| 哪个模型最烧钱（决定要不要换便宜的） | `model_id,bucket`     | `month`     |
| 底层模型谁最烧钱（路由/马甲合并后） | `raw_model_id,bucket` | `month`     |

> **默认分组是 `model_id` 而不是 `raw_model_id`** —— 归并是用户主动切的视角。  
> 默认归并会掩盖"某条路由其实更贵"这类信息（§3.5）。

底层就是 `GROUP BY` 多跟几列 + 外层按 `(bucket, model_id)` 换算金额，SQL 复杂度不变。


### 5.2 端点清单

| 端点                                       | 权限    | 说明                                        |
| ---------------------------------------- | ----- | ----------------------------------------- |
| `GET /admin/usage/summary`               | admin | 见 §5.1，返回 tokens / 金额 / 调用次数              |
| `GET /admin/usage/by-user`               | admin | 按人小计（含会话数、平均单次消耗）                         |
| `GET /admin/usage/by-agent`              | admin | 按 agent，支持"含子 agent"/"仅主 agent"开关         |
| `GET /admin/usage/top-sessions?limit=50` | admin | 最烧钱的会话，反白嫖主入口                             |
| `GET /admin/usage/session/{id}`          | admin | 下钻：该会话每次调用明细 + 原始消息                       |
| `GET /admin/usage/export.csv`            | admin | CSV 导出（老板要 Excel），参数同 summary             |
| `GET/POST /admin/usage/pricing`          | admin | 单价查询 / **新增**（不提供 UPDATE，见 §2.2 铁律）       |
| `GET /me/usage`                          | 登录即可  | **个人用量**，参数同 summary，但 `user_id` 强制锁为当前用户 |

**`/me/usage` 与 admin 走同一套聚合与价格计算**，只是：

- `user_id` 由 token 推导，不接受 `group_by=user`（避免横向看别人）
- 参数：`from` / `to` / `granularity` / `group_by=agent|model_id|bucket`
- 返回字段与 admin 完全一致 —— 用户看到的金额口径和管理员一致，不会出现两套数

**未配价的模型，个人页同样显示 `—` 而不是 0**，避免用户误以为免费。

聚合逻辑放 `db/repository.py` 新增 `UsageRepository`；金额换算放 `server/usage_pricing.py`  
（`resolve_price(model_id, raw_model_id, kind, at)` + `compute_cost(...)`），与存储层解耦。

---

## 6. 前端（二期）

### 6.1 管理页 `/admin/usage`（仅 admin）

- 顶部 4 张卡：总消耗（元）/ 本月消耗 / 活跃人数 / 人均
- 主表：**人 × 时间桶**二维表（默认 `group_by=user,bucket` + `granularity=month`），  
  列头是月份，行是用户，可直接改成按 agent / 按模型维度
- 点行下钻 → 该用户的会话列表（按消耗排序）→ 点会话看调用明细 + 原始 prompt
- 时间范围选择（本月 / 上月 / 近 30 天 / 自定义）+ 导出 CSV 按钮
- **单价管理子页签**：表格列出 model × kind 当前价；  
  改价弹窗只让选**日期**（时间归零），提交走新增；可查看历史价格版本

### 6.2 个人页 `/me/usage`（所有登录用户可见）

- 顶部卡：本月消耗（元）/ 本月 token / 最常用 agent
- 趋势图：按天或按月（复用 `granularity`）
- 明细表：按 agent 或按模型拆分
- **与 admin 同源同口径**；未配价的模型显示 `—`
- 目的不是"考核用户"，是让**有自觉的人自己收敛** —— 大多数滥用是无意识的，  
  看到自己一天烧了 80 块，很多人自己就停了

---

## 7. 反白嫖：先可见，后干预

**核心判断**：token 高 ≠ 滥用。真跑复杂任务的人本来就烧得多，一刀切限流先误伤干活的人。

先做**可下钻**，让老板自己一眼看出来。可选的排序信号（只标注，不封禁）：

| 信号                         | 数据源                                                |
| -------------------------- | -------------------------------------------------- |
| 文件改动数 == 0 但消耗高 → 纯聊天      | join `file_changes`                                |
| 改动文件不在公司项目目录 → 拿公司 key 跑私活 | `file_changes.file_path` vs agent 的 `project_root` |
| 非工作时段占比高                   | `llm_usage.ts`                                     |
| 缓存命中率异常低 → 反复重开会话灌同样的东西    | `cache_read / input`                               |
| 单会话消耗突增                    | `group by session_id`                              |

---

## 8. 实施清单与验收

> **分期合并（2026-09-07 grill 定）**：原"一期止血 / 二期可见"的拆分取消，
> **一次性实施** —— 采集、聚合、API、前端看板一起做。
> 理由：一期做完若没有任何查询手段，采集正确性无法验收；分开做只会拖时间，不降低风险。
> 下面的分组仅表示实施顺序（先数据后展示），不再是发布边界。

### 数据层：建表 + 采集

- [x] alembic 迁移建 `llm_usage` + `model_pricing` 表及索引
- [x] `accumulate_usage` 补 `model_id`、不再丢弃子 agent（`role=main/sub`）、补 `cache_write`
- [x] ~~`subagent_tracker` 落库传 `usage`~~ **已砍（§4.2，recorder-only）**
- [x] `usage_recorder` 批量写入（只落 token）
- [x] config schema + `config.example.jsonc` 加 `usage_stats.enabled`
  （语义：`false` 只关采集，recorder 直接 no-op；表照建、已落库数据照常可查）
- [ ] `ModelConfig.id` 改名 **`model_id`**，并加**必填** `raw_model_id`（允许 `== model_id`），`ModelInfo` 透传
- [ ] `llm_usage` 存**非空** `raw_model_id` 列，`usage_recorder` 写入时从配置解析一并落库
- [ ] **启动校验：`model_id` 全局唯一（跨 provider 也算）+ `(provider, raw_model_id)` 唯一  
  （同渠道同底层模型只许一个入口），连同其他问题一次性列全，拒绝启动**
- [ ] **显示一律直接用 `model_id`，全项目不做显示名映射层（`display_model_name` 已砍，见 §3.5）**
- [x] ~~backfill 脚本~~ **砍掉（2026-09-07 定）**：lc-agent 自身库 0 条历史消息无意义；  
  bfzs 的 2005 条历史里 42% 因 `sessions.model` 为空而算不出金额、usage JSON 本身无 model 字段，  
  回填产出一个占一半的 unknown 桶得不偿失。**历史不补，统计从上线日开始积累**


### 8.1 改动点地图（2026-09-07 源码实测，行号实施时可能漂移）

> ✅ **2026-09-07 已实施完成**（本节 1-8、11-16 项；第 9 项 llm_usage 表/usage_recorder 属 token 统计主体，尚未开始）。  
> 启动校验已挂在 `engine._parse_models`：缺 `model_id`/`raw_model_id`、`model_id` 重复、  
> `(provider, raw_model_id)` 重复 → 一次性列出全部问题并拒绝启动。全量测试 360 通过。  
> bfzs config.jsonc 46 条已转换，`raw_model_id` 与原 id 同值（litellm 反代，渠道名即现 id）。

| #  | 文件                                                                            | 改动                                                                                                                             |
| -- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1  | `lc_agent/config/schema.py:6-9`                                               | `ModelConfig.id` → `model_id`；新增必填 `raw_model_id`（无默认值，pydantic 直接 fail-fast）                                                  |
| 2  | `lc_agent/core/models.py:10-14`                                               | `ModelInfo.id` → `model_id`；新增 `raw_model_id`；`provider` 保留为记录字段                                                               |
| 3  | `lc_agent/core/engine.py:89-103`                                              | `_parse_models`：读 `model_id` / `raw_model_id`（raw 用 `model_conf["raw_model_id"]` 直接 KeyError）；启动校验也挂在这里（唯一性两条 + 问题一次性列全）       |
| 4  | `lc_agent/core/engine.py:575`                                                 | `model=model_info.id` → `model=model_info.model_id`。**发给 API 的值语义不变**（现在发的就是配置 id 本身），`raw_model_id` 不进请求                      |
| 5  | `lc_agent/core/engine.py:608-613`                                             | `_find_model`：`m.id` → `m.model_id`                                                                                            |
| 6  | `lc_agent/core/engine.py:736-739`                                             | `_resolve_preset_for_model` / preset `default_model`：值域变为 model_id，逻辑不变                                                        |
| 7  | `lc_agent/server/routes/models.py:17-25`                                      | `/models` 返回 key `id` → `model_id`（连带前端类型）                                                                                     |
| 8  | `lc_agent/server/sse.py:318,422-425`、`agent_runner.py:76`                     | `model_id = req.model`（请求体字段名不动）；`resolved_model = model_info.id` → `model_info.model_id`                                      |
| 9  | 新增 `lc_agent/server/usage_recorder.py` + alembic 迁移                           | `llm_usage` 建表（`model_id` / `raw_model_id` / `provider` 列）；recorder 写入时从配置解析 raw_model_id 一并落库                                 |
| 10 | `lc_agent/db/models.py:128`（`SessionMeta.model`）                              | **不改**。sessions 表列名不动，值 = model_id                                                                                             |
| 11 | `frontend/src/api/http.ts:43`                                                 | `getModels` 返回类型 `{id,...}` → `{model_id,...}`                                                                                 |
| 12 | `frontend/src/components/panels/ModelSelector.vue:13-17,28`                   | `model.id` → `model.model_id`（含 props 类型）                                                                                      |
| 13 | `frontend/src/components/layout/AppHeader.vue:82-86`、`RightPanel.vue:118-120` | 同上                                                                                                                             |
| 14 | `frontend/src/components/dialogs/AgentManagerDialog.vue:336-338`              | 同上；label 里的 `(${model.provider})` 可留（纯显示）                                                                                      |
| 15 | `frontend/src/stores/tools.ts:51,279-288`                                     | 类型 + `applyModel`/`setModel`：值仍是模型 id 字符串，逻辑不变                                                                                 |
| 16 | `lc-agent-bfzs/config.jsonc`                                                  | 全部模型条目补 `raw_model_id`；同渠道同 raw_model_id 只留一个入口（`zzz-gpt-5.4` / `zzz-auto-gpt-5.4` / `zzz-fallback-gpt-5.4` 收敛，路由挪 litellm 配置） |

**明确不动的**：`http_trace.py` / `traced_llm.py` 的 `self.model`（记录实际请求模型名，语义不变）；`memory.py` 的 `model`（embedding 模型 BAAI/bge-m3，无关）；`AgentPreset.default_model` 字段名（值 = model_id，改名收益低）；sessions 表 `model` 列名。

**验收**：新建会话（含触发子 agent 的场景）跑完，`llm_usage` 有行，`role=sub` 记录存在，  
`model_id` + `provider` + `raw_model_id` 均非空，同一 `run_id+seq` 重复提交不产生重复行；  
**所有模型展示点直接显示 `model_id`，全链路没有显示名映射层**；  
故意配两个相同 `model_id`、缺 `raw_model_id`、或同渠道两个入口指向同一 `raw_model_id` 时，  
服务拒绝启动并一次性列出全部问题项。

### 展示层：聚合 API + 前端（与数据层同批实施）

- [x] `/admin/usage/*` + `/me/usage` API、`UsageRepository`、`usage_pricing`
- [x] `/admin/usage` 页面（含单价管理）+ CSV 导出
- [x] `/me/usage` 个人页
- [x] 下钻到会话

**验收**（逐条对照，缺一不可）：

- [ ] 能出**人 × 月**二维表：每行一个用户，每列一个月，单元格是金额
- [ ] 能出**人 × 天**趋势：单看某人的每日消耗曲线
- [ ] 能出**人 × agent** 拆分：某人花在各个 agent 上的钱
- [ ] 能看到**全局总量**：所有人、所有 agent、全时间段的消耗与金额
- [ ] 普通用户打开 `/me/usage` 只能看到自己的，改 `user_id` 参数无效（服务端强制锁定）
- [ ] 手动插入一条历史价格后，老账单金额变化符合预期（新价只影响生效日之后）
- [ ] 未配价的模型金额显示 `—` 而非 0，admin 页与个人页口径一致
- [ ] `group_by=raw_model_id` 把同一底层模型的多条路由合并成一行；与按 `model_id` 分组的**金额合计一致**（归并只是换视角，不能改数）

### 后续可选

- [ ] 异常信号标注
- [ ] 配额告警（仍然不自动封禁）
- [ ] rollup 日表（性能不够时才做）

---

## 9. 已决定 / 待定问题


### 已决定

| #  | 问题                                    | 结论                                                                                                                                                                                                            |
| -- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | config 里放不放初始种子价？                     | **不放**。价格只有一个来源（DB），避免 config 与 DB 两份价格打架。代价是新部署要先录价才有金额，期间 token 照常统计、金额显示 `—`                                                                                                                               |
| 2  | 要不要积分 / 倍率？                           | **不要**。内部工具模型就几个，真实金额本身就是最好的倍率                                                                                                                                                                                |
| 3  | 金额入库时固化还是查询时算？                        | **查询时算**，价格带生效时间，历史账单不漂移                                                                                                                                                                                      |
| 4  | 定价 key 用 `model` 还是 `provider/model`？ | **只有 `model` 一列：`model_id` 精确 → `raw_model_id` 兜底**。`model_id` 全局唯一，`provider` 只是凭据分组，不参与定价/统计/标识，定价表不留 provider 列                                                                                            |
| 5  | 时间粒度做不做小时？                            | **一期只做 day / month**。抓异常靠派生指标，不靠小时曲线                                                                                                                                                                          |
| 6  | 还要不要 `display_model_name`？            | **不要，已砍**。显示直接用 `model_id`：原厂直连的 model_id 本就可读（`deepseek-chat`）；反代的 model_id 是自己起的，觉得丑就起个好看的，不需要第二个名字打补丁                                                                                                      |
| 7  | 前端显示 id 还是友好名？                        | **直接显示 `model_id`**。全链路没有显示名映射层，统计接口原样返回 `model_id` / `raw_model_id`                                                                                                                                          |
| 8  | 加不加 `raw_model_id`（渠道原始模型名）？          | **加，与 `model_id` 同时必填、无缺省回退**（缺 → 启动失败并列出全部问题项）。允许 `== model_id`（原厂直连时这是唯一正确答案）。只服务定价继承（兜底层，显式配 model_id 的价优先）与统计归并（`group_by` 增列，**默认仍按 `model_id` 分组**）。落库 `llm_usage.raw_model_id`，不做运行时 join config。不参与显示 |
| 9  | `(provider, raw_model_id)` 要唯一吗？      | **要，启动校验，重复拒绝启动**。同一渠道里同一底层模型只声明一个入口；auto/fallback/多账号负载均衡是渠道侧（litellm）的事，不进 lc-agent 模型列表。bfzs 那组 `zzz-gpt-5.4` / `zzz-auto-gpt-5.4` / `zzz-fallback-gpt-5.4` 需收敛为一个入口，路由挪到 litellm 配置                       |
| 10 | 历史 model id 要不要统一加渠道前缀？               | **不加，也不强制**，不靠命名约定保证唯一性（前缀是使用者自己加的，原厂直连部署没有）。唯一性由启动校验保证：`model_id` 全局唯一 + `(provider, raw_model_id)` 唯一，重复直接拒绝启动                                                                                              |
| 11 | backfill 要不要做？                        | **不做（2026-09-07 定）**。lc-agent 自身库 0 条历史；bfzs 2005 条里 42% 因 `sessions.model` 为空 + usage JSON 无 model 字段而永远算不出金额。历史不补，从上线日开始积累                                                                                  |
| 12 | 子 agent token 归谁？                     | **两列都记 + 看板开关（2026-09-07 定）**。`role=sub` 行：`agent_id` = 实际执行的子 agent，`user_id` = 发起会话的用户，`parent_session_id` = 主会话。看板默认"含子 agent"（全行计入），开关切"仅主 agent"（过滤 role=main）。两个视角都在，口径由看板说明                            |
| 13 | 切桶时区？ | **存 UTC、按服务器本地时区切桶（2026-09-07 定，§3.1）**。`ts` 用 `datetime(ts, 'localtime')` 参与分组；国内部署即 +8，避免按天趋势 / 非工作时段信号整体偏 8 小时。部署机时区必须设对 |
| 14 | 货币口径？ | **死按 CNY（2026-09-07 定，§3.3）**。渠道按美元计费的（如中转站）由配置者自行折算录入，当日汇率写进该条价格的 `note` 备查。系统内不做汇率换算、不做多币种 |
| 15 | 一期 / 二期拆分？ | **合并，一次性实施（2026-09-07 定，§8）**。采集 + 聚合 + API + 前端一起做；拆开的唯一后果是"数据可信"无法验收 |

### 待定（动手前定）

1. ~~**子 agent 的 token 归主 agent 还是子 agent？**~~ **已定（§9 表第 12 条）**
2. **是否要给每个用户设月度额度上限？**  
   一期**不做**。等看板跑一个月、摸清正常基线再说。
3. **金额要不要物化回 `llm_usage`？**  
   一期**不物化**，查询时算。若将来数据量上来导致聚合慢，  
   再加一个"按当前价重算并回填"的后台任务 —— 那时它仍是可重算的，不是写死的。
