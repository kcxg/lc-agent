# -*- coding: utf-8 -*-
"""
百度搜索结果抓取测试脚本 —— 验证"抓包接口 + 关键词找网页"的难度

用法:
    python baidu_search_test.py "关键词"
    python baidu_search_test.py "关键词" --num 5 --resolve   # --resolve 额外解析真实 URL

函数入参: 被搜索字符串
返回: list[dict] = {title, url, abstract, date}
"""
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.baidu.com/",
}

# 摘要节点选择器（百度前端 class 经常变，多备几个）
ABSTRACT_SELECTORS = (
    "span.content-right_8Zs40",
    "div.c-abstract",
    "span.c-abstract",
    "div[class*=content-right]",
    "span[class*=content-right]",
    "div.c-span-last",
)


def _resolve_real_url(session: requests.Session, baidu_url: str) -> str:
    """把百度的 /link?url= 跳转链接解析成真实 URL（HEAD 跟随重定向）"""
    try:
        r = session.head(baidu_url, allow_redirects=True, timeout=5)
        return r.url
    except Exception:
        return baidu_url


def search_baidu(keyword: str, num: int = 10, resolve_url: bool = False) -> list[dict]:
    """按关键词搜索百度，返回每条结果的 title/url/abstract/date"""
    session = requests.Session()
    session.headers.update(HEADERS)
    # 先访问首页拿必要 cookie，降低被拦概率
    session.get("https://www.baidu.com/", timeout=10)

    resp = session.get("https://www.baidu.com/s", params={"wd": keyword, "rn": num}, timeout=10)
    resp.raise_for_status()
    # 百度 PC 页是 UTF-8，apparent_encoding 有时会误判导致乱码，优先信任响应头 charset
    resp.encoding = resp.encoding or "utf-8"
    html = resp.text

    # 反爬判定：验证码 / 安全验证页面
    if ("百度安全验证" in html) or ("wappass.baidu.com" in html) or ("通过验证码" in html):
        raise RuntimeError("触发百度安全验证，被反爬拦截（换 IP 或降低频率）")

    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []
    for div in soup.select("div.result, div.result-op, div.c-container"):
        h3 = div.find("h3")
        if not h3:
            continue
        a = h3.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        url = a.get("href", "")

        # 摘要
        abstract = ""
        for sel in ABSTRACT_SELECTORS:
            node = div.select_one(sel)
            if node:
                abstract = node.get_text(" ", strip=True)
                break
        if not abstract:  # 兜底：容器全文去掉标题
            abstract = div.get_text(" ", strip=True).replace(title, "", 1).strip()

        # 时间：摘要中的日期（百度通常把日期塞进摘要里）
        date = ""
        m = re.search(r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})", abstract or "")
        if m:
            date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

        item = {
            "title": title,
            "url": url,
            "abstract": abstract[:200],
            "date": date,
        }
        if resolve_url and url:
            item["real_url"] = _resolve_real_url(session, url)
        results.append(item)
        if len(results) >= num:
            break
    return results


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "python 爬虫"
    num = 10
    resolve = False
    if "--num" in sys.argv:
        num = int(sys.argv[sys.argv.index("--num") + 1])
    if "--resolve" in sys.argv:
        resolve = True

    try:
        items = search_baidu(keyword, num=num, resolve_url=resolve)
        print(f"关键词: {keyword}  命中 {len(items)} 条")
        for i, it in enumerate(items, 1):
            print(f"\n[{i}] {it['title']}")
            print(f"    url     : {it['url']}")
            if it.get("real_url"):
                print(f"    real_url: {it['real_url']}")
            print(f"    date    : {it['date']}")
            print(f"    abstract: {it['abstract'][:120]}...")
        # 同时输出 JSON 供程序调用
        print("\n=== JSON ===")
        print(json.dumps(items, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"失败: {e}")
        sys.exit(1)
