"""edit_block / write_file 的字节保真：行尾（LF/CRLF）与 BOM 不能被改写。

定位说明：这两个工具以前用 read_text/write_text 的默认换行处理，编辑一个 LF 文件会把
整篇变成 CRLF（Windows 上 os.linesep 是 \r\n），git diff 会整文件变化。
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


def _write(path, content, mode="rewrite"):
    return fw.write_file(path=str(path), content=content, mode=mode)


def _raw(path):
    return path.read_bytes()


# --- edit_block -------------------------------------------------------------

def test_edit_keeps_lf_line_endings(tmp_path):
    p = tmp_path / "lf.txt"
    p.write_bytes("alpha\nbeta\n".encode("utf-8"))

    _edit(p, "beta", "BETA")

    raw = _raw(p)
    assert raw.count(b"\r") == 0
    assert raw.decode("utf-8") == "alpha\nBETA\n"


def test_edit_keeps_crlf_line_endings(tmp_path):
    p = tmp_path / "crlf.txt"
    p.write_bytes("alpha\r\nbeta\r\n".encode("utf-8"))

    _edit(p, "beta", "BETA")

    raw = _raw(p)
    assert raw.count(b"\r\n") == 2
    assert raw.count(b"\r") == raw.count(b"\n") == 2


def test_inserted_lines_follow_the_file_style(tmp_path):
    p = tmp_path / "crlf_insert.txt"
    p.write_bytes("alpha\r\nbeta\r\n".encode("utf-8"))

    _edit(p, "beta", "BETA\ninserted")

    raw = _raw(p)
    assert raw.count(b"\r\n") == 3
    assert b"BETA\r\ninserted\r\n" in raw


def test_anchor_uses_plain_lf_even_for_crlf_files(tmp_path):
    """调用方永远用普通 \\n 写锚点，行尾差异由工具适配。"""
    p = tmp_path / "crlf_anchor.txt"
    p.write_bytes("one\r\ntwo\r\nthree\r\n".encode("utf-8"))

    result = _edit(p, "one\ntwo", "uno\ndos")

    assert "Replaced 1 occurrence(s)" in result
    assert b"uno\r\ndos\r\n" in _raw(p)


def test_edit_preserves_bom_and_never_adds_one(tmp_path):
    with_bom = tmp_path / "with_bom.txt"
    with_bom.write_bytes("\ufeffalpha\n".encode("utf-8"))
    _edit(with_bom, "alpha", "ALPHA")
    assert _raw(with_bom).startswith(b"\xef\xbb\xbf")

    without_bom = tmp_path / "no_bom.txt"
    without_bom.write_bytes("alpha\n".encode("utf-8"))
    _edit(without_bom, "alpha", "ALPHA")
    assert not _raw(without_bom).startswith(b"\xef\xbb\xbf")


def test_edit_keeps_non_ascii_content_intact(tmp_path):
    p = tmp_path / "cn.txt"
    p.write_bytes("中文一行\n第二行\n".encode("utf-8"))

    _edit(p, "第二行", "改过的第二行")

    assert _raw(p).decode("utf-8") == "中文一行\n改过的第二行\n"


# --- write_file -------------------------------------------------------------

def test_write_file_rewrite_keeps_existing_crlf(tmp_path):
    p = tmp_path / "keep_crlf.txt"
    p.write_bytes("a\r\nb\r\n".encode("utf-8"))

    _write(p, "x\ny\n")

    raw = _raw(p)
    assert raw.count(b"\r\n") == 2
    assert raw.decode("utf-8") == "x\r\ny\r\n"


def test_write_file_rewrite_keeps_existing_lf(tmp_path):
    p = tmp_path / "keep_lf.txt"
    p.write_bytes("a\nb\n".encode("utf-8"))

    _write(p, "x\ny\n")

    assert _raw(p).count(b"\r") == 0


def test_write_file_new_file_is_written_as_given(tmp_path):
    p = tmp_path / "brand_new.txt"

    _write(p, "a\nb\n")

    assert _raw(p) == b"a\nb\n"


def test_write_file_append_follows_existing_style(tmp_path):
    p = tmp_path / "append.txt"
    p.write_bytes("a\r\n".encode("utf-8"))

    _write(p, "b\n", mode="append")

    raw = _raw(p)
    assert raw.count(b"\r\n") == 2
    assert raw.decode("utf-8") == "a\r\nb\r\n"
