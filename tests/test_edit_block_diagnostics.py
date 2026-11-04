"""edit_block 的失败诊断、成功回执与大块提示。

定位说明：匹配失败时只回一句 "not found" 会让调用方只能整段重读再猜；这里锁定
"给出最接近的真实原文 + 首个差异字符 + 绝不自动落盘" 的行为。
"""

import pytest

from lc_agent.tools.system_tools import file_write_tools as fw
from lc_agent.tools.system_tools._config import set_active_project


@pytest.fixture(autouse=True)
def _project(tmp_path):
    set_active_project(str(tmp_path))
    yield tmp_path
    set_active_project(None)


def _edit(path, old, new, **kw):
    return fw.edit_block(file_path=str(path), old_string=old, new_string=new, **kw)


# --- 成功回执 ---------------------------------------------------------------

def test_receipt_names_the_edited_line_and_shows_context(tmp_path):
    p = tmp_path / "code.py"
    p.write_text("\n".join(f"line {i}" for i in range(1, 41)) + "\n", encoding="utf-8")

    result = _edit(p, "line 20", "LINE 20")

    assert "starting at line 20" in result
    assert "file has 40 lines" in result
    assert "[lines 10-30 of 40" in result
    assert "line 10" in result           # 前文
    assert "LINE 20" in result           # 改后的真实文本
    assert "line 31" not in result       # 预览有边界


def test_receipt_preview_matches_the_file_after_the_edit(tmp_path):
    p = tmp_path / "short.txt"
    p.write_text("a\nb\nc\n", encoding="utf-8")

    result = _edit(p, "b", "B")

    assert "B" in result
    assert "Replaced 1 occurrence(s)" in result


# --- 次数不符 ---------------------------------------------------------------

def test_count_mismatch_changes_nothing_and_explains_both_ways(tmp_path):
    p = tmp_path / "dup.txt"
    p.write_text("x\nx\n", encoding="utf-8")

    result = _edit(p, "x", "y")

    assert "occurs 2 time(s)" in result
    assert "expected_replacements=2" in result
    assert "add more surrounding lines" in result
    assert "Nothing was modified" in result
    assert p.read_text(encoding="utf-8") == "x\nx\n"


def test_replace_all_when_count_is_declared(tmp_path):
    p = tmp_path / "dup2.txt"
    p.write_text("x\nx\n", encoding="utf-8")

    _edit(p, "x", "y", expected_replacements=2)

    assert p.read_text(encoding="utf-8") == "y\ny\n"


# --- 找不到时的诊断 ---------------------------------------------------------

def test_not_found_returns_the_exact_text_for_a_retry(tmp_path):
    p = tmp_path / "src.py"
    p.write_text("def f():\n    return 1\n", encoding="utf-8")

    # 锚点用了 Tab 缩进，文件里是空格
    result = _edit(p, "def f():\n\treturn 1", "def f():\n    return 2")

    assert "Nothing was modified" in result
    assert "--- exact text in the file ---" in result
    assert "    return 1" in result                 # 可直接照抄的准确原文
    assert "TAB" in result and "SPACE" in result     # 差异字符被指名
    assert "Re-send the edit with the exact text" in result
    assert p.read_text(encoding="utf-8") == "def f():\n    return 1\n"


def test_fuzzy_fallback_never_writes_on_its_own(tmp_path):
    p = tmp_path / "src2.py"
    original = "class A:\n    def run(self):\n        return 1\n"
    p.write_text(original, encoding="utf-8")

    _edit(p, "    def run(self):\n       return 1", "    def run(self):\n        return 2")

    assert p.read_text(encoding="utf-8") == original


def test_not_found_with_low_similarity_asks_to_read_again(tmp_path):
    p = tmp_path / "other.txt"
    p.write_text("hello world\n", encoding="utf-8")

    result = _edit(p, "completely different content that is nowhere in the file", "y")

    assert "old_string not found" in result
    assert "Read the file again" in result


def test_char_labels_name_invisible_characters():
    assert "TAB" in fw._char_label("\t")
    assert "SPACE" in fw._char_label(" ")
    assert "U+00A0" in fw._char_label("\u00a0")
    assert "ZERO-WIDTH" in fw._char_label("\u200b")


# --- 大块提示 ---------------------------------------------------------------

def test_large_block_warns_but_still_edits(tmp_path, monkeypatch):
    monkeypatch.setattr(fw, "get_file_write_config", lambda: {"edit_max_lines": 3})
    p = tmp_path / "big.txt"
    old = "\n".join(f"l{i}" for i in range(1, 6))
    p.write_text(old + "\n", encoding="utf-8")

    result = _edit(p, old, "done")

    assert "guideline: 3" in result
    assert "splitting the change into smaller edits is safer" in result
    assert p.read_text(encoding="utf-8") == "done\n"


def test_small_block_has_no_warning(tmp_path, monkeypatch):
    monkeypatch.setattr(fw, "get_file_write_config", lambda: {"edit_max_lines": 3})
    p = tmp_path / "small.txt"
    p.write_text("a\nb\n", encoding="utf-8")

    result = _edit(p, "a", "A")

    assert "guideline" not in result
