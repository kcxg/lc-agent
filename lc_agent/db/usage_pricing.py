"""单价匹配与金额换算（docs/tasks/token_stats.md §2.2 / §3.2）。

- 匹配键只有 model 一列：model_id 精确 → raw_model_id 兜底，命中即停
- 同 key 取 effective_from <= 统计时刻的最新一条
- 价格全量读进内存（几十行），对每个 (bucket, model_id) 找当时生效的那一版
- 未配价返回 None，调用方显示 `—`，绝不用 0 假装算出来了
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models_usage import ModelPrice

KINDS = ("input", "output", "cache_read", "cache_write")


def bucket_end(bucket: str, granularity: str) -> datetime:
    """时间桶的结束时刻 —— 价格匹配时刻（§3.2.1：当天改价、当天生效）。

    granularity=day → 当天 23:59:59；month → 当月最后一天 23:59:59。
    bucket 由 localtime 切出，视为本地时间；与 effective_from（页面只选日期、
    时间归零，存库时按本地语义解释）同口径比较。
    """
    if granularity == "month":
        year, month = int(bucket[:4]), int(bucket[5:7])
        if month == 12:
            nxt = datetime(year + 1, 1, 1)
        else:
            nxt = datetime(year, month + 1, 1)
        end = nxt - timedelta(seconds=1)
    else:
        d = datetime.strptime(bucket, "%Y-%m-%d")
        end = d.replace(hour=23, minute=59, second=59)
    return end


async def load_price_table(session: AsyncSession) -> list[ModelPrice]:
    """价格表总共几十行，全量载入。"""
    result = await session.execute(select(ModelPrice))
    return list(result.scalars().all())


def resolve_price(
    prices: list[ModelPrice],
    model_id: str,
    raw_model_id: str,
    kind: str,
    at: datetime,
) -> float | None:
    """两级匹配（model_id 精确 → raw_model_id 兜底），同 key 取当时生效的最新一条。

    返回 None = 该维度没配价（或该 kind 没配价）。
    """
    for key in (model_id, raw_model_id):
        if not key:
            continue
        candidates = [
            p for p in prices
            if p.model == key and p.kind == kind and _as_naive_local(p.effective_from) <= at
        ]
        if candidates:
            best = max(candidates, key=lambda p: _as_naive_local(p.effective_from))
            return best.price_per_1m
    return None


def resolve_prices_for(
    prices: list[ModelPrice],
    model_id: str,
    raw_model_id: str,
    at: datetime,
) -> dict[str, float | None]:
    return {kind: resolve_price(prices, model_id, raw_model_id, kind, at) for kind in KINDS}


def compute_cost(token_sums: dict[str, int], prices: dict[str, float | None]) -> float | None:
    """按 §3.2 公式换算。返回 None = 无法算（有 token 消耗的维度没配价），显示 `—`。"""
    cost = 0.0
    for kind in KINDS:
        tokens = token_sums.get(kind, 0) or 0
        if tokens <= 0:
            continue
        price = prices.get(kind)
        if price is None:
            return None
        cost += (tokens / 1_000_000) * price
    return round(cost, 4)


def _as_naive_local(dt: datetime) -> datetime:
    """剥离 tzinfo（页面录入的 effective_from 视为本地时间语义）。"""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
