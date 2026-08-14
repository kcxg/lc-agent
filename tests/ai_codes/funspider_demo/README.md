# funspider 爬虫 Demo（三层分布式爬虫）

演示 **funspider + funboost** 的核心能力：函数即任务消费者、同步/异步双客户端、
SQLModel ORM 一行入库、精确 QPS 控频、任务去重、分组一键消费、链式派发。

## 结构

```
fake_news_site.py    本地假新闻站 (FastAPI, 127.0.0.1:8888)：列表页 / 详情页 / 评论接口
funspider_demo.py    三层爬虫：crawl_list -> crawl_detail -> crawl_comments
funboost_config.py   本 demo 专用 funboost 配置（sqlite 队列路径指向本目录）
```

## 运行

> 依赖：`pip install funboost>=54.9 httpx parsel sqlmodel fastapi uvicorn`
> （funspider 自 funboost 54.9 起已随 pip 发布）

```bash
# 1. 启动目标站
python fake_news_site.py

# 2. 另开终端，启动爬虫
python funspider_demo.py
```

## 技术要点

- `@boost(BoosterParams(...))`：把普通函数变成分布式任务消费者，调度单元是**函数**（非 URL）
- `BoosterParams` 子类统一 broker / 分组配置；`BoostersManager.consume_group(group)` 一键启动
- 链式派发：`crawl_list.push(page=...)` -> `crawl_detail.push(detail_url=...)` -> `crawl_comments.push(news_id=...)`
- `SimpleSpiderClient`（httpx 同步）/ `AsyncSpiderClient`（httpx 异步）双客户端，自动重试、可选代理轮换
- `SpiderItem`（SQLModel ORM）：`.upsert()` / `await .aio_upsert()` 一行入库，按唯一字段去重更新
- 本地持久化队列 `BrokerEnum.SQLITE_QUEUE`：免 Redis，支持断点续爬
- `do_task_filtering` 按函数参数做任务去重（demo 中仅评论任务启用，列表/详情页翻页场景不应开启）

## 预期结果

爬完 `funspider_demo.db` 中：
- `news` 表 20 行（20 条新闻）
- `comments` 表 80 行（每条新闻 2~6 条评论）
