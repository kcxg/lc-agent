"""xlsx 预览前的部件归一化。

前端 xlsx 预览由 @vue-office/excel 承担，它内部使用 exceljs 解析工作簿。
exceljs 在绘图与批注两类部件上不按命名空间解析，而是拿标签名的字面字符串查表，
且对部件路径有硬编码假设。openpyxl（含 pandas 默认的 to_excel 引擎）的序列化形式
恰好落在它的盲区里，导致整份工作簿解析失败：

1. 绘图部件 xl/drawings/*.xml
   openpyxl 把 spreadsheetDrawing 命名空间声明为默认命名空间，元素不带前缀；
   exceljs 的 DrawingXform 只认 `xdr:wsDr`、`xdr:oneCellAnchor` 这类带前缀的标签名，
   匹配不到就留下空模型，读取 anchors 时抛 TypeError。含图表或图片的文件都命中。

2. 批注部件
   openpyxl 写成 xl/comments/commentN.xml 与 xl/drawings/commentsDrawingN.vml，
   关系 Target 用绝对路径；exceljs 只认 xl/commentsN.xml、xl/drawings/vmlDrawingN.vml，
   且要求 Target 为相对形式，读取 comments 时抛 TypeError。

本模块按 exceljs 的期望形式改写这两类部件，其余部件原样透传。
任何一步失败都回退为原始字节，预览退回到原有报错，不会让文件变得更不可读。
"""

import posixpath
import re
import zipfile
from io import BytesIO

from lc_agent.utils.loggers import server_logger

_SPREADSHEET_DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
_DRAWING_NS_DECL = f'xmlns="{_SPREADSHEET_DRAWING_NS}"'
_DRAWING_NS_DECL_PREFIXED = f'xmlns:xdr="{_SPREADSHEET_DRAWING_NS}"'

# 声明为默认命名空间的绘图部件：根节点必须是不带前缀的 wsDr
_DRAWING_ROOT_WITH_DEFAULT_NS = re.compile(r"<wsDr\b[^>]*" + re.escape(_DRAWING_NS_DECL))

# 匹配不带前缀的元素标签；名字里出现冒号的（a:、r:、c: 等）天然不会命中
_OPEN_TAG = re.compile(r"<([A-Za-z_][\w.\-]*)((?:\s+[^<>]*?)?)(/?)>")
_CLOSE_TAG = re.compile(r"</([A-Za-z_][\w.\-]*)>")
# 归一化后仍存在无前缀元素标签说明改写不完整，此时整体回退
_LEFTOVER_OPEN_TAG = re.compile(r"<[A-Za-z_][\w.\-]*[\s/>]")

_DRAWING_PART = re.compile(r"xl/drawings/[^/]+\.xml\Z")
_COMMENT_PART = re.compile(r"xl/comments/comment(\d+)\.xml\Z")
_COMMENT_VML_PART = re.compile(r"xl/drawings/commentsDrawing(\d+)\.vml\Z")
_RELS_PART = re.compile(r"(?P<base>.*?)/?_rels/[^/]+\.rels\Z")
_TARGET_ATTR = re.compile(r'Target="([^"]*)"')
_CONTENT_TYPE_PART_NAME = re.compile(r'PartName="([^"]*)"')


def _prefix_drawing_namespace(text: str) -> str:
    """给默认命名空间下的绘图元素补上 xdr: 前缀，其余内容保持不变。"""
    if "xmlns:xdr=" in text or _DRAWING_NS_DECL not in text:
        return text
    if not _DRAWING_ROOT_WITH_DEFAULT_NS.search(text):
        return text

    prefixed = _OPEN_TAG.sub(lambda m: f"<xdr:{m.group(1)}{m.group(2)}{m.group(3)}>", text)
    prefixed = _CLOSE_TAG.sub(lambda m: f"</xdr:{m.group(1)}>", prefixed)

    if _LEFTOVER_OPEN_TAG.search(prefixed):
        return text

    return prefixed.replace(_DRAWING_NS_DECL, _DRAWING_NS_DECL_PREFIXED, 1)


def _rels_base_dir(rels_name: str) -> str:
    """rels 部件对应的源部件所在目录，用于把 Target 解析成包内路径。"""
    match = _RELS_PART.fullmatch(rels_name)
    if not match:
        return ""
    return match.group("base").rstrip("/")


def _to_package_path(base_dir: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target[1:])
    return posixpath.normpath(posixpath.join(base_dir, target))


def _relative_target(base_dir: str, part_name: str) -> str:
    return posixpath.relpath(part_name, base_dir or ".")


def _comment_part_plan(name: str) -> tuple[str, int] | None:
    """openpyxl 的批注部件名 → (预览组件认得的命名模板, 序号)；非批注部件返回 None。"""
    comment = _COMMENT_PART.fullmatch(name)
    if comment:
        return "xl/comments{index}.xml", int(comment.group(1))
    vml = _COMMENT_VML_PART.fullmatch(name)
    if vml:
        return "xl/drawings/vmlDrawing{index}.vml", int(vml.group(1))
    return None


def _plan_part_moves(names: set[str]) -> dict[str, str]:
    """openpyxl 的非标准批注部件路径 → 预览组件能识别的路径。"""
    moves: dict[str, str] = {}
    for name in sorted(names):
        plan = _comment_part_plan(name)
        if plan is None:
            continue
        template, index = plan
        moved = _free_name(names, moves, template, index)
        if moved is not None:
            moves[name] = moved
    return moves


def _free_name(names: set[str], moves: dict[str, str], template: str, index: int) -> str | None:
    """按格式惯例换序号取名。

    预览组件用 `comments\\d+` / `vmlDrawing\\d+` 匹配部件名，所以冲突时只能换数字，
    不能加后缀，否则改名后的部件照样不被识别。
    """
    taken = (names - set(moves)) | set(moves.values())
    for candidate_index in range(index, index + 1000):
        candidate = template.format(index=candidate_index)
        if candidate not in taken:
            return candidate
    return None


def _drawing_text_needing_prefix(raw: bytes) -> str | None:
    """返回需要补命名空间前缀的绘图原文；无需处理或解不开时返回 None。"""
    text = _decode_xml(raw)
    if text is None or "xmlns:xdr=" in text or _DRAWING_NS_DECL not in text:
        return None
    return text if _DRAWING_ROOT_WITH_DEFAULT_NS.search(text) else None


def _decode_xml(raw: bytes) -> str | None:
    """XML 部件按规范是 UTF-8；解不开时跳过该部件，而不是让整份文件放弃归一化。"""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def normalize_xlsx_for_preview(data: bytes) -> bytes:
    """把 xlsx 字节归一化成 exceljs 可解析的形式；无需处理或处理失败时原样返回。"""
    try:
        source = zipfile.ZipFile(BytesIO(data))
    except (zipfile.BadZipFile, OSError):
        return data

    try:
        names = set(source.namelist())
        drawing_parts = [name for name in names if _DRAWING_PART.fullmatch(name)]
        moves = _plan_part_moves(names)
        if not moves and not any(
            _drawing_text_needing_prefix(source.read(name)) for name in drawing_parts
        ):
            return data

        changed = False
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                name = item.filename
                new_name = moves.get(name, name)
                original = source.read(name)
                rewritten = _rewrite_part(name, original, moves)
                if rewritten is not None or new_name != name:
                    changed = True
                target.writestr(_carry_over(item, new_name), original if rewritten is None else rewritten)

        return buffer.getvalue() if changed else data
    except Exception as exc:  # noqa: BLE001 - 归一化失败不能影响预览主流程
        server_logger.warning("xlsx 预览归一化失败，按原始字节下发: %s", exc)
        return data
    finally:
        source.close()


def _carry_over(item: zipfile.ZipInfo, name: str) -> zipfile.ZipInfo:
    """复用原部件的时间与压缩方式，让同一份输入始终产出同一份字节。"""
    info = zipfile.ZipInfo(name, date_time=item.date_time)
    info.compress_type = item.compress_type
    info.external_attr = item.external_attr
    info.internal_attr = item.internal_attr
    info.create_system = item.create_system
    return info


def _rewrite_part(name: str, raw: bytes, moves: dict[str, str]) -> bytes | None:
    """按部件类型改写内容；无需改写或解不开时返回 None。"""
    if _DRAWING_PART.fullmatch(name):
        text = _drawing_text_needing_prefix(raw)
        if text is None:
            return None
        rewritten = _prefix_drawing_namespace(text)
        return None if rewritten == text else rewritten.encode("utf-8")

    text = _decode_xml(raw)
    if text is None:
        return None
    if name.endswith(".rels"):
        rewritten = _rewrite_rels(text, _rels_base_dir(name), moves)
    elif name == "[Content_Types].xml":
        rewritten = _rewrite_content_types(text, moves)
    else:
        return None
    return None if rewritten == text else rewritten.encode("utf-8")


def _rewrite_rels(text: str, base_dir: str, moves: dict[str, str]) -> str:
    if not moves:
        return text

    def replace(match: re.Match[str]) -> str:
        target = match.group(1)
        package_path = _to_package_path(base_dir, target)
        moved = moves.get(package_path)
        if moved is None:
            return match.group(0)
        return f'Target="{_relative_target(base_dir, moved)}"'

    return _TARGET_ATTR.sub(replace, text)


def _rewrite_content_types(text: str, moves: dict[str, str]) -> str:
    if not moves:
        return text

    def replace(match: re.Match[str]) -> str:
        part_name = match.group(1)
        if not part_name.startswith("/"):
            return match.group(0)
        moved = moves.get(part_name[1:])
        if moved is None:
            return match.group(0)
        return f'PartName="/{moved}"'

    return _CONTENT_TYPE_PART_NAME.sub(replace, text)
