"""Token 用量统计相关表。

设计文档：docs/tasks/token_stats.md §2。
- llm_usage 只存原始 token 数，不存任何金额；金额在查询时按当时生效价计算。
- model_pricing 由管理页面维护；改价 = INSERT 新记录（带 effective_from），绝不 UPDATE 覆盖。
"""

import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Index, String, text

from lc_agent.db.models import utcnow


class LlmUsage(SQLModel, table=True):
    __tablename__ = "llm_usage"
    __table_args__ = (
        Index("ix_llm_usage_user_ts", "user_id", "ts"),
        Index("ix_llm_usage_agent_ts", "agent_id", "ts"),
        Index("ix_llm_usage_model_ts", "model_id", "ts"),
        Index("uq_llm_usage_run_seq", "run_id", "seq", unique=True),
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ts: datetime = Field(default_factory=utcnow, index=True)

    # ---- 归属维度 ----
    user_id: str = Field(default="", index=True)
    session_id: str = Field(default="", index=True)
    parent_session_id: str | None = Field(default=None, index=True)
    agent_id: str = Field(default="", index=True)
    model_id: str = Field(default="", index=True)  # 配置里的模型 id（全局唯一），见 token_stats.md §3.5
    raw_model_id: str = Field(
        default="",
        sa_column=Column(String, nullable=False, server_default=text("''")),
    )  # 渠道原始模型名，写入时由 usage_recorder 从配置解析
    provider: str = Field(default="")  # 纯记录字段：凭据分组，不参与任何 key
    role: str = "main"  # main(主会话) | sub(子 agent)
    sub_session_id: str = ""  # role=sub 时为子会话 id
    source: str = "chat"  # chat | title | summarize | automation

    # ---- 原始消耗（唯一事实来源，不存任何金额）----
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0  # 已包含在 output 内，仅用于分析

    # ---- 元信息 ----
    duration_ms: int = 0
    run_id: str = Field(default="", index=True)  # 一次 invoke 唯一 id
    seq: int = 0  # 该 run 内第几次调用


class ModelPrice(SQLModel, table=True):
    __tablename__ = "model_pricing"
    __table_args__ = (
        Index("ix_model_pricing_model_kind_from", "model", "kind", "effective_from"),
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    model: str = Field(index=True)  # 匹配键：填 model_id 或 raw_model_id（两级匹配，见 §2.2）
    kind: str = ""  # input | output | cache_read | cache_write
    price_per_1m: float = 0.0  # 元 / 百万 tokens
    currency: str = "CNY"
    effective_from: datetime = Field(default_factory=utcnow)  # 生效时间（精确到天）
    note: str = ""
