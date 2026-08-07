# 知乎 URL 的浏览器读取指南

## 何时使用

`extract` 抓取知乎页面返回 `HTTP 403 访问失败`（换 `--client requests` 也一样），页面是 JS 动态渲染，正文不在初始 HTML 中。

**当 `extract` 对某个 URL 返回 403 或"页面无正文"时，改用浏览器读取，不要反复重试 `extract`。**

## 步骤

### 1. 打开页面

调用 `browser_navigate` 打开 URL：

- 知乎 URL 直接打开：`https://www.zhihu.com/question/<id>`
- 百度跳转链接（`http://www.baidu.com/link?url=...`）也可直接打开，浏览器会自动跟随 302 到目标页。

### 2. 判断页面类型

打开后先调 `browser_snapshot` 看页面结构，按 URL 形态分流：

- **答案页**（URL 含 `/answer/<aid>`）：直接显示单条回答，正文就在快照里，读完即可。
- **问题页**（URL 只有 `/question/<id>`）：只显示前几条回答，需滚动加载，进入第 3 步。
- **专栏页**（URL 为 `zhuanlan.zhihu.com/p/<id>`）：正文直接渲染在页面中，无需滚动，用 `browser_evaluate` 提取 `.Post-RichTextContainer`（兜底 `.RichText`）文本，跳过第 3 步。

### 3. 问题页：滚动加载回答

知乎回答懒加载，且**加载更多只会在"接近列表底部"时触发**。不要用 `scrollTo(0, document.body.scrollHeight)` 一步跳到底 —— 会跳过触发点，回答数卡住不涨。

**用单次 `browser_run_code_unsafe` 完成全部滚动加载**（不要在循环里逐轮调用工具，每轮调用都有固定 token 开销）：

```js
async (page) => {
  let n = 0, prev = -1, stuck = 0, rounds = 0;
  while (n < 30 && rounds < 10 && stuck < 3) {   // 三个停止条件，任一满足即停
    prev = n;
    await page.keyboard.press('End');            // 真实键盘滚动，触发懒加载
    await page.waitForTimeout(2500);             // 等回答渲染
    n = await page.evaluate(() => document.querySelectorAll('.List-item').length);
    if (n === prev) stuck++; else stuck = 0;     // 连续 3 轮不涨 = 加载失效，提前停
    rounds++;
  }
  return { loaded: n, rounds, stuck };           // 只返回 3 个数字
}
```

`n < 30` 里的 `30` 是默认目标条数，按需下调（如 20~25）可明显省时间——实测 30 条约 5 轮、25 条约 4 轮。不要调大超过 30。

**必须用真实键盘滚动（`page.keyboard.press('End')`）**：知乎部分页面只认真实输入事件，`window.scrollTo`/`scrollBy` 等 JS 滚动不触发懒加载（实测回答数卡住不涨）。实测每按一次 End 约新增 5~10 条，30 条约需 4~8 轮。

停止条件（防止无限加载、控制 token 开销）：

- `n < 30`：达到目标条数即停，不追求加载全部回答 —— 上百条的问题页要滚几十轮，无意义。
- `rounds < 10`：硬上限 10 轮（约 25 秒），即使一直不达标也强制停。
- `stuck < 3`：连续 3 轮条数不涨说明触发失效（被反爬或页面限制），提前退出，用已加载的回答继续。

**懒加载提前失效（stuck 提前触发）**：部分问题页（回答数少、或页面限制）只滚出几条就不再增长，此时不要硬滚——直接用已加载的回答继续；若回答数明显不足（如 <10）且用户确实需要更多，可先切换页面排序（如"按时间"）再滚一轮，仍无效就放弃该页，换 search 结果里其他相关链接。

注意：`document.body.scrollHeight` 的增长滞后于回答加载，**不要用它判断加载进度**，以 `.List-item` 数量为准。

### 4. 批量提取回答内容

回答渲染在 `.List-item` 卡片中，用 `browser_evaluate` 一次提取全部回答：

```js
() => {
  const answers = [];
  document.querySelectorAll('.List-item').forEach((card) => {
    const contentEl = card.querySelector('.RichContent-inner');
    const voteEl = card.querySelector('button[aria-label*="赞同"]');
    const authorEl = card.querySelector('.AuthorInfo-name, .UserLink-link');
    const timeEl = card.querySelector('.ContentItem-time');
    answers.push({
      votes: voteEl ? voteEl.textContent.trim() : '?',
      author: authorEl ? authorEl.textContent.trim() : '',
      time: timeEl ? timeEl.textContent.trim() : '',
      content: contentEl ? contentEl.textContent.trim() : '',
    });
  });
  return { count: answers.length, answers };
}
```

**作者名经常取不到（实测多数卡片返回空）**：不要把 `author` 当必需字段，取不到就留空。确实需要作者名时，以 `browser_snapshot` 中对应卡片的 `AuthorInfo-name` / `UserLink-link` 为准，不要为取作者名反复跑 JS。按赞同数或用户需要整理后输出。

### 5. 特殊内容

- **图片回答**：快照中是 `figure`，文字为空，用 `browser_take_screenshot` 截取该回答区域。
- **折叠回答**：正文被折叠时快照里有"展开"按钮，先 `browser_click` 展开再快照。
- **只读单条回答**：直接 `browser_navigate` 打开该回答的 `/answer/<aid>` 链接（快照中发布时间链接可拿），加载最快。

## 注意事项

- 登录态影响可见内容：未登录时部分内容不可见。当前环境已登录（顶部有"私信/消息"入口），无需额外处理。
- 知乎页面 console 有 2 个左右报错属正常噪音，忽略。
- 滚动、点击等操作间隔至少 1 秒，避免触发反爬拦截。
- 若 `search` 返回的跳转链接落到答案页或专栏页，先按 URL 形态判断页面类型（见第 2 步），再走对应流程。
