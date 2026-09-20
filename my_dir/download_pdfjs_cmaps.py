"""下载 pdfjs-dist 的 CMap 数据到 frontend/public/cmaps/，供中文 PDF 离线预览。

@vue-office/pdf 默认从 unpkg 拉 CMap，内网或无外网环境会导致中文缺字。
前端构建时 public/ 会原样拷到 dist 根，因此预览走本地 /cmaps/。

升级 @vue-office/pdf 时需确认其内置 pdfjs-dist 版本，并同步修改 PDFJS_VERSION。
"""

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PDFJS_VERSION = "3.1.81"
BASE_URL = f"https://unpkg.com/pdfjs-dist@{PDFJS_VERSION}/cmaps"
OUT_DIR = Path(__file__).parent.parent / "frontend" / "public" / "cmaps"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def main() -> None:
    meta = json.loads(fetch(f"{BASE_URL}/?meta").decode("utf-8"))
    names = [f["path"].split("/")[-1] for f in meta["files"]]
    print(f"remote files: {len(names)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def download(name: str) -> str:
        target = OUT_DIR / name
        if target.exists() and target.stat().st_size > 0:
            return "skip"
        target.write_bytes(fetch(f"{BASE_URL}/{name}"))
        return "ok"

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(download, names))

    total = sum(f.stat().st_size for f in OUT_DIR.iterdir() if f.is_file())
    print(f"downloaded={results.count('ok')} skipped={results.count('skip')} files={len(list(OUT_DIR.iterdir()))} bytes={total}")


if __name__ == "__main__":
    main()
