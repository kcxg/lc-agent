"""read_file / read_multiple_files 的编码标记：行尾与 BOM。

定位说明：行尾和 BOM 在返回的正文里看不出来，而编辑会按读到的内容保真，
所以这是调用方唯一的知情渠道。常规 LF 无 BOM 时不得添加任何噪声。
"""

import pytest

from lc_agent.tools.system_tools import file_read_tools as fr
from lc_agent.tools.system_tools._config import set_active_project


@pytest.fixture(autouse=True)
def _project(tmp_path):
    set_active_project(str(tmp_path))
    yield tmp_path
    set_active_project(None)


def _read(path, **kw):
    return fr.read_file(path=str(path), **kw)


def test_plain_lf_adds_no_marker(tmp_path):
    p = tmp_path / "plain.txt"
    p.write_bytes("alpha\nbeta\n".encode("utf-8"))

    result = _read(p)

    assert result.startswith("[Lines 1-2 of 2 total]")
    assert "line endings" not in result
    assert "BOM" not in result


def test_crlf_is_reported(tmp_path):
    p = tmp_path / "crlf.txt"
    p.write_bytes("alpha\r\nbeta\r\n".encode("utf-8"))

    assert "| CRLF line endings" in _read(p)


def test_bom_is_reported(tmp_path):
    p = tmp_path / "bom.txt"
    p.write_bytes("\ufeffalpha\n".encode("utf-8"))

    assert "| UTF-8 BOM" in _read(p)


def test_mixed_line_endings_are_reported(tmp_path):
    p = tmp_path / "mixed.txt"
    p.write_bytes(b"alpha\r\nbeta\ngamma\r\n")

    assert "| mixed line endings" in _read(p)


def test_lone_cr_is_reported(tmp_path):
    p = tmp_path / "cr.txt"
    p.write_bytes(b"alpha\rbeta\r")

    assert "| CR line endings" in _read(p)


def test_crlf_and_bom_together(tmp_path):
    p = tmp_path / "both.txt"
    p.write_bytes("\ufeffalpha\r\nbeta\r\n".encode("utf-8"))

    result = _read(p)

    assert "| CRLF line endings" in result
    assert "| UTF-8 BOM" in result


def test_marker_follows_paged_reads(tmp_path):
    p = tmp_path / "long_crlf.txt"
    p.write_bytes("".join(f"l{i}\r\n" for i in range(1, 11)).encode("utf-8"))

    result = _read(p, offset=0, length=3)

    assert result.startswith("[Lines 1-3 of 10 total | CRLF line endings]")
    assert "use offset=3 to read more" in result


def test_read_multiple_files_marks_each_file(tmp_path):
    plain = tmp_path / "plain.txt"
    plain.write_bytes("alpha\n".encode("utf-8"))
    crlf = tmp_path / "crlf.txt"
    crlf.write_bytes("alpha\r\n".encode("utf-8"))

    result = fr.read_multiple_files(paths=[str(plain), str(crlf)])

    assert f"--- {plain} ---\n" in result
    assert f"--- {crlf} --- | CRLF line endings\n" in result
