"""复现 edit_block 在同一文件上的并发丢更新问题，并验证"模块级锁"方案。

实验目的：
    模型在同一轮里对同一个文件发出两个 edit_block（改两个不同区域）时，
    lc-agent 的 ToolNode 会并发执行这两个调用。由于两者都基于同一份旧内容
    做 read -> replace -> write，后写入的会覆盖先写入的，导致其中一处改动
    静默丢失。

本脚本做四件事：
    Section 0  测量单次 edit_block 的真实耗时（回应"1 纳秒"的说法）
    Section 1  并发调用注册表里的真工具：统计丢更新发生率（回归检查，
               修复前约 96%，修复后应为 0%）
    Section 2  对照组：另建一个显式加锁的副本，确认锁本身有效
    Section 3  机制演示：在 read 与 write 之间注入一个耗时窗口，证明
               "操作越快越安全" 的直觉是反的

运行方式（PowerShell，项目根目录为 D:\\codes\\lc-agent）：
    $env:PYTHONPATH = "D:\\codes\\lc-agent"
    D:\\ProgramData\\Miniconda3\\envs\\py312\\python.exe `
        tests\\ai_codes\\edit_block_concurrency\\repro_edit_block_race.py
"""

import asyncio
import statistics
import threading
import time
from pathlib import Path

from langchain_core.tools import StructuredTool

from lc_agent.tools.system_tools._config import set_active_project

# 导入即触发 @tool 装饰器注册 file_write__edit_block
import lc_agent.tools.system_tools.file_write_tools  # noqa: F401
from lc_agent.tools.registry import ToolRegistry

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TMP_DIR = PROJECT_ROOT / ".tmp" / "edit_block_race"
WORK_FILE = TMP_DIR / "work.txt"

ITERATIONS = 300          # 并发丢更新实验的轮数
TIMING_CALLS = 200        # 单次耗时测量次数

BASE_CONTENT = (
    "# demo file\n"
    "REGION_A_ORIGINAL\n"
    "middle line 1\n"
    "middle line 2\n"
    "middle line 3\n"
    "REGION_B_ORIGINAL\n"
)

A_OLD, A_NEW = "REGION_A_ORIGINAL", "REGION_A_CHANGED"
B_OLD, B_NEW = "REGION_B_ORIGINAL", "REGION_B_CHANGED"


def get_real_edit_block() -> StructuredTool:
    """从注册表取出真正的 edit_block 工具（生产路径用的那个对象）。"""
    reg = ToolRegistry()
    try:
        return reg._global_tools["file_write__edit_block"]["tool"]
    except KeyError as exc:  # pragma: no cover - 环境问题时的清晰报错
        raise RuntimeError(
            "未找到 file_write__edit_block，请确认 lc_agent 可被导入、"
            f"PYTHONPATH 指向项目根目录。当前已注册：{list(reg._global_tools)}"
        ) from exc


def make_locked_copy(tool: StructuredTool) -> StructuredTool:
    """构造一个语义相同、但整段执行被模块级锁保护的 edit_block。

    锁覆盖 read -> replace -> write 全过程（因为在锁内调用原函数），
    这正是修复丢更新所要求的范围。
    """
    lock = threading.Lock()
    original = tool.func

    def locked_fn(*args, **kwargs):
        with lock:
            return original(*args, **kwargs)

    return StructuredTool.from_function(
        func=locked_fn,
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
        infer_schema=False,
    )


async def run_concurrent_pair(tool: StructuredTool, file_path: Path) -> str:
    """重置文件后并发执行两个 edit_block，返回本轮结果分类。"""
    file_path.write_text(BASE_CONTENT, encoding="utf-8")

    await asyncio.gather(
        tool.ainvoke(
            {"file_path": str(file_path), "old_string": A_OLD, "new_string": A_NEW}
        ),
        tool.ainvoke(
            {"file_path": str(file_path), "old_string": B_OLD, "new_string": B_NEW}
        ),
    )

    final = file_path.read_text(encoding="utf-8")
    has_a = A_NEW in final
    has_b = B_NEW in final

    if has_a and has_b:
        return "both"
    if has_a:
        return "only_A"
    if has_b:
        return "only_B"
    return "neither"


async def measure(title: str, tool: StructuredTool) -> dict:
    """跑 ITERATIONS 轮并发，统计结果分布。"""
    counts = {"both": 0, "only_A": 0, "only_B": 0, "neither": 0}
    for _ in range(ITERATIONS):
        counts[await run_concurrent_pair(tool, WORK_FILE)] += 1

    lost = ITERATIONS - counts["both"]
    print(f"\n===== {title} =====")
    print(f"  两处改动都保留   both    : {counts['both']}")
    print(f"  只剩 A，丢了 B   only_A  : {counts['only_A']}")
    print(f"  只剩 B，丢了 A   only_B  : {counts['only_B']}")
    print(f"  两处都没了       neither : {counts['neither']}")
    print(f"  --> 丢更新发生率: {lost}/{ITERATIONS} = {lost / ITERATIONS:.1%}")
    return counts


async def section0_timing(tool: StructuredTool) -> None:
    """测量单次 edit_block 的真实耗时，用于检验"1 纳秒"的说法。"""
    durations_ms: list[float] = []
    for _ in range(TIMING_CALLS):
        WORK_FILE.write_text(BASE_CONTENT, encoding="utf-8")
        start = time.perf_counter()
        await tool.ainvoke(
            {"file_path": str(WORK_FILE), "old_string": A_OLD, "new_string": A_NEW}
        )
        durations_ms.append((time.perf_counter() - start) * 1000)

    print("\n===== Section 0: 单次 edit_block 耗时 =====")
    print(f"  次数           : {TIMING_CALLS}")
    print(f"  中位数         : {statistics.median(durations_ms):.3f} ms")
    print(f"  最小 / 最大    : {min(durations_ms):.3f} / {max(durations_ms):.3f} ms")
    print(f"  （1 纳秒 = 0.000001 ms，可自行对比数量级）")


def _demo_worker(file_path: Path, old: str, new: str, window_s: float, lock) -> None:
    """模拟 edit_block 的 read -> [窗口] -> write 结构。"""
    def work() -> None:
        content = file_path.read_text(encoding="utf-8")
        time.sleep(window_s)          # 模拟 read 与 write 之间的耗时窗口
        file_path.write_text(content.replace(old, new), encoding="utf-8")

    if lock is None:
        work()
    else:
        with lock:
            work()


def section3_mechanism() -> None:
    """机制演示：窗口越"实"，无锁丢更新越必然；加锁后必然为 0。"""
    print("\n===== Section 3: 机制演示（read 与 write 之间注入耗时窗口）=====")

    for window_s in (0.0, 0.002):
        for use_lock in (False, True):
            trials = 100
            lost = 0
            lock = threading.Lock() if use_lock else None
            for _ in range(trials):
                WORK_FILE.write_text(BASE_CONTENT, encoding="utf-8")
                t1 = threading.Thread(
                    target=_demo_worker, args=(WORK_FILE, A_OLD, A_NEW, window_s, lock)
                )
                t2 = threading.Thread(
                    target=_demo_worker, args=(WORK_FILE, B_OLD, B_NEW, window_s, lock)
                )
                t1.start()
                t2.start()
                t1.join()
                t2.join()

                final = WORK_FILE.read_text(encoding="utf-8")
                if not (A_NEW in final and B_NEW in final):
                    lost += 1

            label = "加锁" if use_lock else "无锁"
            print(
                f"  窗口={window_s * 1000:.0f}ms  {label}  "
                f"-> 丢更新 {lost}/{trials} = {lost / trials:.1%}"
            )


async def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    # 锁定文件访问边界到临时目录，避免触碰真实项目文件
    set_active_project(str(TMP_DIR))

    real_tool = get_real_edit_block()
    print(f"已加载真实工具: {real_tool.name}")
    print(f"临时工作文件  : {WORK_FILE}")

    await section0_timing(real_tool)
    await measure("Section 1: 当前实现（注册表真工具 file_write__edit_block）", real_tool)
    await measure("Section 2: 对照组（另建一个显式加锁的副本）", make_locked_copy(real_tool))
    section3_mechanism()

    print("\n完成。")


if __name__ == "__main__":
    asyncio.run(main())
