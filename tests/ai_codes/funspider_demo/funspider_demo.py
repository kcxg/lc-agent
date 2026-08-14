# -*- coding: utf-8 -*-
"""
funspider 爬虫 Demo —— 三层分布式爬虫 (列表页 → 详情页 → 评论)

演示 funspider + funboost 的核心能力：
- @boost 装饰器：函数即分布式任务消费者
- SimpleSpiderClient / AsyncSpiderClient：同步 + 异步 httpx 双客户端混用
- SpiderItem (SQLModel ORM)：一行 upsert 入库，自动建表
- 精确 QPS 控频 / 任务去重 / 分组一键消费
- 链式派发：crawl_list.push() -> crawl_detail.push() -> crawl_comments.push()

运行：
    pip install funboost>=54.9 httpx parsel sqlmodel fastapi uvicorn   # funspider 自 54.9 起随 pip 发布
    1) python fake_news_site.py        # 先起目标站 (127.0.0.1:8888)
    2) python funspider_demo.py        # 再跑爬虫
    详见同目录 README.md
"""
from typing import ClassVar, Optional

from funboost import (
    boost, BoosterParams, BoostersManager, BrokerEnum,
    ctrl_c_recv, ConcurrentModeEnum,
)
from funboost.contrib.funspider import (
    SimpleSpiderClient, AsyncSpiderClient,
    SpiderItem, create_engine, create_async_engine, Field,
)

NEWS_GROUP = "news_crawler"


# ---------- 爬虫公共配置：继承 BoosterParams，一处配置多处复用 ----------
class NewsCrawlerParams(BoosterParams):
    broker_kind: str = BrokerEnum.SQLITE_QUEUE   # 本地 sqlite 持久化队列，免 Redis，支持断点续爬
    booster_group: str = NEWS_GROUP              # 分组名，consume_group 一键启动


# ---------- 数据库 (SQLite，零外部依赖) ----------
DB_PATH = "funspider_demo.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}")
ASYNC_ENGINE = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}")


class NewsItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "news"
    __engine__ = ENGINE
    __async_engine__ = ASYNC_ENGINE
    __default_upsert_unique_fields__ = ["news_id"]   # news_id 相同则更新，否则插入

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(unique=True)
    title: str
    summary: str
    author: str
    category: str
    publish_time: str
    url: str


class CommentItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "comments"
    __engine__ = ENGINE
    __async_engine__ = ASYNC_ENGINE
    __default_upsert_unique_fields__ = ["comment_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    comment_id: int = Field(unique=True)
    news_id: int
    user: str
    content: str
    like_count: int


NewsItem.create_table()
CommentItem.create_table()

# ---------- 客户端 ----------
sync_client = SimpleSpiderClient(retry_times=3)        # 同步，基于 httpx
async_client = AsyncSpiderClient(retry_times=3)       # 异步，基于 httpx

BASE_URL = "http://127.0.0.1:8888"


# ---------- 1. 列表页爬虫（同步）：解析列表，推送详情页任务 ----------
@boost(NewsCrawlerParams(queue_name="news_list", qps=2))
def crawl_list(page: int):
    resp = sync_client.get(f"{BASE_URL}/news/list?page={page}")
    links = resp.css("table a::attr(href)").getall()
    for href in links:
        if href and "/news/detail/" in href:
            detail_url = f"{BASE_URL}{href}" if href.startswith("/") else href
            crawl_detail.push(detail_url=detail_url)      # 链式派发：详情页任务
    next_href = resp.css("a.next-page::attr(href)").get("")
    if next_href:
        crawl_list.push(page=page + 1)                    # 翻页
    print(f"[列表页] page={page} 解析出 {len(links)} 条链接")


# ---------- 2. 详情页爬虫（同步）：解析详情，入库 + 推送评论任务 ----------
@boost(NewsCrawlerParams(queue_name="news_detail", qps=5, max_retry_times=3))
def crawl_detail(detail_url: str):
    resp = sync_client.get(detail_url)
    title = resp.css("h1::text").get("").strip()
    content_p = resp.css("div.content p::text").getall()
    summary = content_p[0] if content_p else ""

    author = category = publish_time = ""
    for p_text in content_p:
        if p_text.startswith("作者："):
            author = p_text.replace("作者：", "").strip()
        elif p_text.startswith("分类："):
            category = p_text.replace("分类：", "").strip()
        elif p_text.startswith("发布时间："):
            publish_time = p_text.replace("发布时间：", "").strip()

    news_id = int(detail_url.rsplit("/", 1)[-1])

    NewsItem(news_id=news_id, title=title, summary=summary,
             author=author, category=category, publish_time=publish_time,
             url=detail_url).upsert()                     # 一行入库

    crawl_comments.push(news_id=news_id)                  # 链式派发：评论任务
    print(f"[详情页] news_id={news_id} 已入库，标题={title[:20]}...")


# ---------- 3. 评论爬虫（异步）：请求 JSON 接口，异步入库 ----------
@boost(NewsCrawlerParams(queue_name="news_comments", qps=10,
                         concurrent_mode=ConcurrentModeEnum.ASYNC,
                         do_task_filtering=True, task_filtering_expire_seconds=3600))
async def crawl_comments(news_id: int):
    resp = await async_client.get(f"{BASE_URL}/news/comments/{news_id}")
    data = resp.resp_dict                              # 自动 json.loads
    for c in data.get("comments", []):
        await CommentItem(comment_id=c["id"], news_id=c["news_id"],
                          user=c["user"], content=c["content"],
                          like_count=c["like_count"]).aio_upsert()   # 异步入库
    print(f"[评论页] news_id={news_id} 入库 {len(data.get('comments', []))} 条评论")


if __name__ == '__main__':
    BoostersManager.consume_group(NEWS_GROUP)          # 一键启动分组内所有消费函数

    crawl_list.push(page=1)                            # 发布种子任务

    ctrl_c_recv()                                      # 阻塞主线程，Ctrl+C 优雅退出
