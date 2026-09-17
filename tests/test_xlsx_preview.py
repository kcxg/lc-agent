"""xlsx 预览归一化的契约测试。

预览组件按标签名前缀字面匹配解析绘图/批注部件，openpyxl 的序列化形式落在其盲区里。
这里用手工拼装的 xlsx 覆盖归一化行为与"不该动就不动"的边界。
"""

import base64
import zipfile
from io import BytesIO

import pytest

from lc_agent.server.routes.tools import read_file_content
from lc_agent.utils.xlsx_preview import normalize_xlsx_for_preview

SPREADSHEET_DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"

DRAWING_DEFAULT_NS = (
    f'<wsDr xmlns="{SPREADSHEET_DRAWING_NS}">'
    "<oneCellAnchor><from><col>2</col><colOff>0</colOff><row>2</row><rowOff>0</rowOff></from>"
    '<ext cx="381000" cy="381000"/><pic><nvPicPr><cNvPr id="1" name="Image 1"/><cNvPicPr/></nvPicPr>'
    '<blipFill><a:blip xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="rId1"/>'
    "</blipFill><spPr/></pic><clientData/></oneCellAnchor></wsDr>"
)

DRAWING_PREFIXED_NS = (
    '<xdr:wsDr xmlns:xdr="%s">'
    "<xdr:oneCellAnchor><xdr:from><xdr:col>2</xdr:col><xdr:colOff>0</xdr:colOff>"
    "<xdr:row>2</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from>"
    '<xdr:ext cx="381000" cy="381000"/><xdr:pic><xdr:clientData/></xdr:pic></xdr:oneCellAnchor>'
    "</xdr:wsDr>" % SPREADSHEET_DRAWING_NS
)

CONTENT_TYPES = (
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/comments/comment1.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.comments+xml"/>'
    '<Override PartName="/xl/drawings/drawing1.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>'
    "</Types>"
)

SHEET_RELS_BOTH_KINDS = (
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" '
    'Target="/xl/comments/comment1.xml" Id="comments"/>'
    '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing" '
    'Target="/xl/drawings/commentsDrawing1.vml" Id="anysvml"/>'
    '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
    'Target="/xl/media/image1.png" Id="rId1"/>'
    "</Relationships>"
)


def build_xlsx(
    *,
    drawing: str | None = None,
    comments: bool = False,
    extra_parts: dict[str, str] | None = None,
) -> bytes:
    """按 openpyxl 的写法拼出最小 xlsx。"""
    parts = {
        "[Content_Types].xml": CONTENT_TYPES,
        "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
        "xl/worksheets/sheet1.xml": (
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData/></worksheet>"
        ),
    }
    if drawing is not None:
        parts["xl/drawings/drawing1.xml"] = drawing
    if comments:
        parts["xl/worksheets/_rels/sheet1.xml.rels"] = SHEET_RELS_BOTH_KINDS
        parts["xl/comments/comment1.xml"] = (
            '<comments xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<authors><author>me</author></authors>"
            '<commentList><comment ref="A1" authorId="0"><text><t>hi</t></text></comment></commentList>'
            "</comments>"
        )
        parts["xl/drawings/commentsDrawing1.vml"] = (
            '<xml><ns0:shape xmlns:ns0="urn:schemas-microsoft-com:vml">'
            '<ns1:ClientData xmlns:ns1="urn:schemas-microsoft-com:office:excel">'
            "<ns1:Row>0</ns1:Row></ns1:ClientData></ns0:shape></xml>"
        )

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
        for name, content in (extra_parts or {}).items():
            archive.writestr(name, content)
    return buffer.getvalue()


def read_parts(data: bytes) -> dict[str, str]:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        return {name: archive.read(name).decode("utf-8") for name in archive.namelist()}


def test_drawing_default_namespace_gets_prefix() -> None:
    """默认命名空间的绘图元素必须补上 xdr: 前缀，否则预览组件识别不到。"""
    result = read_parts(normalize_xlsx_for_preview(build_xlsx(drawing=DRAWING_DEFAULT_NS)))
    drawing = result["xl/drawings/drawing1.xml"]

    assert drawing.startswith(f'<xdr:wsDr xmlns:xdr="{SPREADSHEET_DRAWING_NS}">')
    for tag in ("xdr:oneCellAnchor", "xdr:from", "xdr:colOff", "xdr:pic", "xdr:clientData"):
        assert f"<{tag}" in drawing
    assert "</xdr:wsDr>" in drawing
    # 已经是前缀写法的 DrawingML 命名空间不能被改动
    assert "<a:blip" in drawing and "r:embed=\"rId1\"" in drawing


def test_drawing_without_prefix_is_not_touched() -> None:
    """已符合规范的绘图部件应原样返回，避免无谓地重写文件。"""
    data = build_xlsx(drawing=DRAWING_PREFIXED_NS)

    assert normalize_xlsx_for_preview(data) == data


def test_comment_parts_are_relocated_and_rels_rewritten() -> None:
    """批注部件需改成预览组件认得的路径，关系目标需改为相对形式。"""
    result = read_parts(normalize_xlsx_for_preview(build_xlsx(comments=True)))

    assert "xl/comments1.xml" in result
    assert "xl/drawings/vmlDrawing1.vml" in result
    assert "xl/comments/comment1.xml" not in result
    assert "xl/drawings/commentsDrawing1.vml" not in result

    rels = result["xl/worksheets/_rels/sheet1.xml.rels"]
    assert 'Target="../comments1.xml"' in rels
    assert 'Target="../drawings/vmlDrawing1.vml"' in rels
    # 不在迁移范围内的关系必须保持原样
    assert 'Target="/xl/media/image1.png"' in rels

    content_types = result["[Content_Types].xml"]
    assert 'PartName="/xl/comments1.xml"' in content_types
    assert "/xl/comments/comment1.xml" not in content_types


def test_comment_part_collision_renames_by_index() -> None:
    """目标名已被占用时必须换序号而不是加后缀。

    预览组件用 `comments\\d+` / `vmlDrawing\\d+` 匹配部件名，加后缀得到的名字同样不被识别，
    等于改名失败；只有换数字才能让文件重新可解析。
    """
    canonical_comments = (
        '<comments xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<authors><author>x</author></authors><commentList/></comments>"
    )
    canonical_vml = '<xml><v:shape xmlns:v="urn:schemas-microsoft-com:vml"/></xml>'
    result = read_parts(
        normalize_xlsx_for_preview(
            build_xlsx(
                comments=True,
                extra_parts={
                    "xl/comments1.xml": canonical_comments,
                    "xl/drawings/vmlDrawing1.vml": canonical_vml,
                },
            )
        )
    )

    # 包内原有的命名规范部件必须原样保留
    assert result["xl/comments1.xml"] == canonical_comments
    assert result["xl/drawings/vmlDrawing1.vml"] == canonical_vml
    # 迁移后的名字必须仍符合预览组件识别得出来的格式
    assert "xl/comments2.xml" in result
    assert "xl/drawings/vmlDrawing2.vml" in result
    assert "xl/comments/comment1.xml" not in result
    assert "xl/drawings/commentsDrawing1.vml" not in result

    rels = result["xl/worksheets/_rels/sheet1.xml.rels"]
    assert 'Target="../comments2.xml"' in rels
    assert 'Target="../drawings/vmlDrawing2.vml"' in rels
    assert 'PartName="/xl/comments2.xml"' in result["[Content_Types].xml"]


def test_normalize_is_deterministic_and_idempotent() -> None:
    """同一份输入必须产出同一份字节；对自身产出再跑不应再有变化。

    产出带时间戳会让同一文件每次下发不同字节，也让"是否已处理过"变得无法判断。
    """
    data = build_xlsx(drawing=DRAWING_DEFAULT_NS, comments=True)

    first = normalize_xlsx_for_preview(data)

    assert normalize_xlsx_for_preview(data) == first
    assert normalize_xlsx_for_preview(first) == first


def test_drawing_and_comment_are_normalized_together() -> None:
    """两类部件同时存在时要一起处理，缺一都会让整份工作簿打不开。"""
    result = read_parts(
        normalize_xlsx_for_preview(build_xlsx(drawing=DRAWING_DEFAULT_NS, comments=True))
    )

    assert "<xdr:wsDr" in result["xl/drawings/drawing1.xml"]
    assert "xl/comments1.xml" in result
    assert "xl/drawings/vmlDrawing1.vml" in result


def test_normalized_output_is_still_a_valid_zip() -> None:
    """归一化后的字节必须仍是可读的 zip，且原有部件不丢失。"""
    data = build_xlsx(drawing=DRAWING_DEFAULT_NS, comments=True)
    result = normalize_xlsx_for_preview(data)

    parts = read_parts(result)
    assert parts["xl/workbook.xml"]
    assert parts["xl/worksheets/sheet1.xml"]
    assert "[Content_Types].xml" in parts


def test_plain_workbook_without_drawings_is_not_touched() -> None:
    """没有绘图/批注的工作簿不应被改写。"""
    data = build_xlsx()

    assert normalize_xlsx_for_preview(data) == data


@pytest.mark.parametrize(
    "payload",
    [b"", b"hello world", b"PK\x03\x04document-bytes", b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"],
)
def test_non_zip_payload_is_returned_untouched(payload: bytes) -> None:
    """非 zip 输入必须原样返回，不能因为归一化把文件弄坏。"""
    assert normalize_xlsx_for_preview(payload) == payload


async def test_read_file_content_normalizes_xlsx_preview(tmp_path) -> None:
    """接口下发的 xlsx 字节应是归一化后的结果，前端才能直接渲染。"""
    doc = tmp_path / "sample.xlsx"
    doc.write_bytes(build_xlsx(drawing=DRAWING_DEFAULT_NS, comments=True))

    result = await read_file_content(path=str(doc))
    decoded = base64.b64decode(result["data_url"].split(",", 1)[1])

    assert result["document_kind"] == "xlsx"
    parts = read_parts(decoded)
    assert "<xdr:wsDr" in parts["xl/drawings/drawing1.xml"]
    assert "xl/comments1.xml" in parts
    # 原始文件本身不能被改写
    assert doc.read_bytes() == build_xlsx(drawing=DRAWING_DEFAULT_NS, comments=True)


async def test_read_file_content_keeps_non_zip_document_bytes(tmp_path) -> None:
    """非 zip 的 xlsx 文件仍按原字节下发，归一化不得介入。"""
    doc = tmp_path / "broken.xlsx"
    doc.write_bytes(b"PK\x03\x04not-a-real-zip")

    result = await read_file_content(path=str(doc))

    assert base64.b64decode(result["data_url"].split(",", 1)[1]) == b"PK\x03\x04not-a-real-zip"
