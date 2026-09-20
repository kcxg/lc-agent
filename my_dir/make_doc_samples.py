"""生成五种办公文档的丰富样例，用于手动验证文档只读预览链路。

每个文件主题不同，内容均为虚构：
- sample.docx   《智慧园区二期建设项目计划书》  多页 / 标题分级 / 表格 / 配图 / 页眉页脚
- sample.xlsx   《2026 年度经营分析》            多工作表 / 公式 / 条件格式 / 原生图表
- sample.pptx   《星云协作 3.0 新品发布会》      6 页 / 原生图表 / 表格 / 备注
- sample.pdf    Aurora Analytics 2026 Annual Review（英文，多页 + 表格 + 图表）
- sample_cjk.pdf《员工手册（节选）》（中文，多页 + 表格 + 图表）

依赖：python-docx / openpyxl / python-pptx / reportlab / matplotlib / Pillow
"""

from copy import deepcopy
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Mm, Pt, RGBColor  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.chart import BarChart, PieChart, Reference  # noqa: E402
from openpyxl.chart.label import DataLabelList  # noqa: E402
from openpyxl.formatting.rule import CellIsRule, DataBarRule  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.chart.data import ChartData  # noqa: E402
from pptx.dml.color import RGBColor as PptRGB  # noqa: E402
from pptx.enum.chart import XL_CHART_TYPE  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import PP_ALIGN  # noqa: E402
from pptx.util import Inches, Pt as PPt  # noqa: E402
from reportlab.graphics.shapes import Drawing  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.cidfonts import UnicodeCIDFont  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable  # noqa: E402

OUT_DIR = Path(__file__).parent / "doc_preview_samples"

NAVY = "1E2761"
CORAL = "C0392B"
LIGHT_BG = "EEF1F7"
GOLD = "B7952B"

CJK_FONT = "Microsoft YaHei"

from matplotlib.font_manager import FontProperties  # noqa: E402

_CJK_FONT_FILE = r"C:\Windows\Fonts\msyh.ttc"
_CJK_FONT_PROP = FontProperties(fname=_CJK_FONT_FILE)
_CJK_FAMILY = _CJK_FONT_PROP.get_name()

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [_CJK_FAMILY, "Noto Sans SC", "Source Han Sans SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ---------------------------------------------------------------- matplotlib
def _chart_png(draw):
    """用 matplotlib 画一张图，返回 BytesIO（PNG）。"""
    fig = plt.figure(figsize=(7.2, 3.6), dpi=150)
    try:
        draw(fig)
        fig.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf
    finally:
        plt.close(fig)


def _set_chart_cjk_font(ax):
    """把 axes 内所有文本显式绑定中文字体文件，避免 rcParams fallback 失效。"""
    for text in [ax.title, ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels():
        text.set_fontproperties(_CJK_FONT_PROP)
    leg = ax.get_legend()
    if leg is not None:
        for text in leg.get_texts():
            text.set_fontproperties(_CJK_FONT_PROP)


def budget_chart():
    def draw(fig):
        ax = fig.add_subplot(111)
        items = ["人力成本", "设备采购", "软件许可", "施工集成", "测试验收", "预备费"]
        values = [96, 128, 54, 72, 28, 32]
        bars = ax.bar(items, values, color=["#1E2761", "#2E5AAC", "#3E8EDE", "#E67E22", "#27AE60", "#95A5A6"])
        ax.set_title("智慧园区二期预算分布（万元）", fontsize=13)
        ax.set_ylabel("万元")
        ax.bar_label(bars, fmt="%.0f")
        ax.set_ylim(0, 150)
        _set_chart_cjk_font(ax)

    return _chart_png(draw)


def annual_bar_chart_en():
    def draw(fig):
        ax = fig.add_subplot(111)
        regions = ["East", "South", "North"]
        q2 = [34.8, 22.1, 24.6]
        q3 = [39.1, 20.5, 30.0]
        x = range(len(regions))
        ax.bar([i - 0.2 for i in x], q2, width=0.4, label="Q2", color="#7FB3D5")
        bars = ax.bar([i + 0.2 for i in x], q3, width=0.4, label="Q3", color="#1E2761")
        ax.set_xticks(list(x), regions)
        ax.set_title("Regional Sales: Q2 vs Q3 ($10K)", fontsize=13)
        ax.legend()
        ax.bar_label(bars, fmt="%.1f")

    return _chart_png(draw)


def leave_chart_cjk():
    def draw(fig):
        ax = fig.add_subplot(111)
        kinds = ["年假", "病假", "事假", "调休", "产假/陪产假"]
        days = [420, 96, 58, 132, 45]
        bars = ax.bar(kinds, days, color=["#1E2761", "#2980B9", "#E67E22", "#27AE60", "#8E44AD"])
        ax.set_title("2026 年上半年各类假期使用总量（天）", fontsize=13)
        ax.set_ylabel("天")
        ax.bar_label(bars, fmt="%.0f")
        _set_chart_cjk_font(ax)

    return _chart_png(draw)


# ---------------------------------------------------------------- docx
def _set_run_font(run, name=CJK_FONT, size=None, bold=None, color=None):
    # 注意：不要手写 <w:eastAsia>，必须经由 rFonts 的 eastAsia 属性设置，
    # 否则元素顺序违反 wml.xsd（rPrChange 之前不允许出现 eastAsia），validate 会报：
    # "Element eastAsia: This element is not expected. Expected is rPrChange"。
    run.font.name = name
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is not None:
        rFonts.set(qn("w:eastAsia"), name)
        rFonts.set(qn("w:cs"), name)
    if size is not None:
        run.font.size = size
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)


def _docx_para(doc, text, style=None, size=None, bold=None, color=None, align=None, space_after=None):
    p = doc.add_paragraph()
    if style is not None:
        try:
            p.style = doc.styles[style]
        except KeyError:
            pass
    run = p.add_run(text)
    _set_run_font(run, size=size, bold=bold, color=color)
    if align is not None:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    return p


def _docx_mixed_para(doc, segments, style=None, align=None):
    """segments: [(text, dict(font kwargs))]，用于同一段落多种格式。"""
    p = doc.add_paragraph()
    if style is not None:
        try:
            p.style = doc.styles[style]
        except KeyError:
            pass
    for text, kwargs in segments:
        run = p.add_run(text)
        _set_run_font(run, **kwargs)
    if align is not None:
        p.alignment = align
    return p


def _shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def _docx_table(doc, headers, rows, widths=None, zebra=True):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    try:
        table.style = doc.styles["Table Grid"]
    except KeyError:
        pass
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        _set_run_font(run, bold=True, color="FFFFFF", size=Pt(10.5))
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _shade_cell(cell, NAVY)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(val))
            _set_run_font(run, size=Pt(10.5))
            if zebra and i % 2 == 1:
                _shade_cell(cell, LIGHT_BG)
    if widths:
        for j, w in enumerate(widths):
            for i in range(len(rows) + 1):
                doc_cell = table.cell(i, j)
                doc_cell.width = Mm(w)
    doc.add_paragraph()
    return table


def _add_page_number(paragraph):
    p = paragraph._p
    run = OxmlElement("w:r")
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run.append(fld_begin)
    p.append(run)
    run2 = OxmlElement("w:r")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    run2.append(instr)
    p.append(run2)
    run3 = OxmlElement("w:r")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run3.append(fld_end)
    p.append(run3)


def make_docx():
    doc = Document()
    for section in doc.sections:
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.top_margin = Mm(25)
        section.bottom_margin = Mm(22)
        section.left_margin = Mm(24)
        section.right_margin = Mm(24)
        header = section.header.paragraphs[0]
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = header.add_run("智慧园区二期 · 内部资料  version 2.3")
        _set_run_font(run, size=Pt(8), color="808080")
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = footer.add_run("第 ")
        _set_run_font(run, size=Pt(8), color="808080")
        _add_page_number(footer)
        run = footer.add_run(" 页 · 星野科技集团")
        _set_run_font(run, size=Pt(8), color="808080")

    # 封面
    _docx_para(doc, "星野科技集团", size=Pt(14), color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    _docx_para(doc, "智慧园区二期建设项目", style="Title", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    _docx_para(doc, "项 目 计 划 书", size=Pt(22), bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER)
    _docx_para(
        doc,
        "以「安全、节能、体验」为纲， delivering a future-ready campus（打造面向未来的园区）",
        size=Pt(10.5),
        color="555555",
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    _docx_table(
        doc,
        ["项目编号", "版本", "编制日期", "编制人"],
        [["XY-PARK-2026-02", "V2.3", "2026-09-10", "林晓峰（PMO）"]],
        widths=[45, 25, 35, 45],
        zebra=False,
    )
    _docx_para(
        doc,
        "密级：内部公开  |  本计划书经立项评审会（2026-09-05）审议通过，作为二期建设的执行基准，"
        "后续变更须走 CCB 流程。",
        size=Pt(9),
        color="808080",
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    doc.add_page_break()

    # 目录（手写目录，便于预览）
    _docx_para(doc, "目  录", style="Heading 1")
    for title, pg in [
        ("一、项目背景与目标", "3"),
        ("二、建设范围与交付物", "3"),
        ("三、里程碑计划", "4"),
        ("四、预算概览", "4"),
        ("五、风险登记册与应对", "5"),
        ("六、附则", "5"),
    ]:
        _docx_mixed_para(doc, [(title, {"size": Pt(11)}), (f"  ……  {pg}", {"size": Pt(11), "color": "808080"})])

    _docx_para(doc, "一、项目背景与目标", style="Heading 1")
    _docx_para(doc, "1.1 背景", style="Heading 2")
    _docx_para(
        doc,
        "一期工程已于 2026 年 6 月完成验收，覆盖 3 栋办公楼的门禁、能耗计量与会议室预定系统。"
        "投运三个月来，园区月均接待访客 4200 余人次，能耗同比下降 9.6%。但随着 D、E 栋投入使用，"
        "既有平台出现设备接入瓶颈：边缘网关 CPU 常年高于 75%，访客高峰期闸机通行排队超过 2 分钟。"
        "二期建设旨在扩容并补齐智能化短板，支撑未来三年 3000 人规模的办公需求。",
    )
    _docx_para(doc, "1.2 总体目标", style="Heading 2")
    _docx_para(doc, "项目总体目标可概括为「三个一」：", size=Pt(11))
    for item in [
        "一张网：全园区物联设备统一接入，纳管设备突破 12000 台，在线率不低于 99.5%。",
        "一朵云：算力与数据中台扩容 2 倍，报表查询 P95 延迟控制在 800ms 以内。",
        "一体验：访客无感通行、员工一码通办，满意度调查得分不低于 4.6 分（5 分制）。",
    ]:
        _docx_para(doc, item, style="List Bullet")
    _docx_table(
        doc,
        ["目标维度", "关键指标", "基线（2026Q2）", "目标（2027Q1）"],
        [
            ["设备在线率", "在线设备占比", "97.8%", "≥ 99.5%"],
            ["通行效率", "高峰排队时长", "约 2 分钟", "≤ 30 秒"],
            ["能耗", "单位面积电耗", "基准 100%", "下降 15%"],
            ["满意度", "季度调研得分", "4.2 分", "≥ 4.6 分"],
        ],
        widths=[32, 40, 38, 40],
    )

    _docx_para(doc, "二、建设范围与交付物", style="Heading 1")
    _docx_para(doc, "2.1 在建范围", style="Heading 2")
    for item in [
        "D、E 栋共 46 个点位的人脸闸机与访客机更换，支持刷脸 + 工卡 + 访客码三合一。",
        "地下二层新增 800 路高清摄像头，视频流全部上云存储，保留 90 天。",
        "能耗子系统扩展至空调末端与照明回路，新增 1200 个采集点。",
        "移动端「星野通」App 上线访客邀请、报修、订餐三大高频功能。",
    ]:
        _docx_para(doc, item, style="List Number")
    _docx_para(doc, "2.2 明确不做（Out of Scope）", style="Heading 2")
    _docx_para(
        doc,
        "需要特别说明的是：食堂团餐系统、地下车库充电桩运营不在本次范围内，避免边界 creep 导致延期。"
        "这两块已列入 2027 年度专项，由行政部另行立项。",
        style="Quote",
    )

    _docx_para(doc, "三、里程碑计划", style="Heading 1")
    _docx_table(
        doc,
        ["阶段", "起止时间", "关键交付", "负责人"],
        [
            ["M1 详细设计", "2026-10-08 ~ 2026-11-15", "施工图 / 点位表 / 设备清单", "林晓峰"],
            ["M2 设备到货", "2026-11-16 ~ 2026-12-20", "到货验收单（抽检 20%）", "赵一鸣"],
            ["M3 安装调试", "2026-12-21 ~ 2027-02-10", "单机调试报告 46 份", "赵一鸣"],
            ["M4 联调联试", "2027-02-11 ~ 2027-03-15", "联调报告 / 压力测试报告", "沈佳宜"],
            ["M5 试运行验收", "2027-03-16 ~ 2027-04-10", "验收纪要 / 运维移交清单", "林晓峰"],
        ],
        widths=[32, 48, 48, 22],
    )
    _docx_para(
        doc,
        "注：春节假期（2027-02-06 ~ 2027-02-14）为停工窗口，已在 M3 工期中预留 9 天缓冲；"
        "关键路径为 M2→M3→M4，设备到货延期超过 5 天将触发赶工预案。",
        size=Pt(9),
        color="555555",
    )

    _docx_para(doc, "四、预算概览", style="Heading 1")
    _docx_para(
        doc,
        "项目总预算 410 万元，其中设备采购占比最高（31%）。预备费按 8% 计提，仅 CCB 批准后方可动用。",
    )
    _docx_table(
        doc,
        ["费用大类", "金额（万元）", "占比", "备注"],
        [
            ["人力成本", "96", "23.4%", "14 人 × 平均 5 个月"],
            ["设备采购", "128", "31.2%", "闸机 / 摄像头 / 网关"],
            ["软件许可", "54", "13.2%", "视频云存储 + 中间件"],
            ["施工集成", "72", "17.6%", "含辅材与夜间施工补贴"],
            ["测试验收", "28", "6.8%", "第三方测评 12 万"],
            ["预备费", "32", "7.8%", "CCB 审批后动用"],
            ["合计", "410", "100%", "含税价"],
        ],
        widths=[32, 30, 25, 63],
    )
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(budget_chart(), width=Mm(150))
    _docx_para(doc, "图 1  预算分布（设备采购为最大头）", size=Pt(9), color="808080", align=WD_ALIGN_PARAGRAPH.CENTER)

    _docx_para(doc, "五、风险登记册与应对", style="Heading 1")
    _docx_table(
        doc,
        ["编号", "风险描述", "概率 / 影响", "应对措施", "责任人"],
        [
            ["R-01", "进口闸机交期延误", "中 / 高", "双供应商备选 + 提前 30 天下单", "赵一鸣"],
            ["R-02", "夜间施工遭投诉", "高 / 中", "仅工作日 22:00 前作业，提前公示", "施工队长老周"],
            ["R-03", "老系统接口不兼容", "中 / 高", "M1 阶段完成接口联调验证", "沈佳宜"],
            ["R-04", "预算超支超 5%", "低 / 高", "冻结预备费，超支项逐笔上 CCB", "林晓峰"],
        ],
        widths=[16, 48, 26, 48, 22],
    )

    _docx_para(doc, "六、附则", style="Heading 1")
    for item in [
        "本计划书自签发之日起生效，执行中如需调整里程碑超过 5 个工作日，须重新评审。",
        "周报（每周五 18:00 前）与月度 steering 会议为固定动作，缺席需提前请假。",
        "项目文档统一存放于知识库「智慧园区 / 二期」目录，版本号与本文档保持一致。",
    ]:
        _docx_para(doc, item, style="List Number")
    _docx_para(
        doc,
        "—— 全文完，共六章。签发：________    日期：________",
        size=Pt(11),
        align=WD_ALIGN_PARAGRAPH.RIGHT,
    )

    doc.core_properties.title = "智慧园区二期建设项目计划书"
    doc.core_properties.author = "PMO 林晓峰"
    doc.save(OUT_DIR / "sample.docx")


# ---------------------------------------------------------------- xlsx
THIN = Side(style="thin", color="B0B0B0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
NAVY_FILL = PatternFill("solid", fgColor=NAVY)
LIGHT_FILL = PatternFill("solid", fgColor=LIGHT_BG)
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
WHITE_FONT = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
BODY_FONT = Font(name="微软雅黑", size=11)
TITLE_FONT = Font(name="微软雅黑", size=16, bold=True, color=NAVY)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def _style_header_row(ws, row, ncols):
    for col in range(1, ncols + 1):
        c = ws.cell(row=row, column=col)
        c.fill = NAVY_FILL
        c.font = WHITE_FONT
        c.alignment = CENTER
        c.border = BORDER


def _style_body(ws, row, ncols, zebra=True):
    for col in range(1, ncols + 1):
        c = ws.cell(row=row, column=col)
        c.font = BODY_FONT
        c.border = BORDER
        if zebra and row % 2 == 0:
            c.fill = LIGHT_FILL


def make_xlsx():
    wb = Workbook()

    # ---- 参数表 ----
    param = wb.active
    param.title = "参数表"
    param.sheet_properties.tabColor = "808080"
    param.merge_cells("A1:E1")
    param["A1"] = "2026 年度经营分析 · 参数表（黄色为可改区）"
    param["A1"].font = TITLE_FONT
    param["A1"].alignment = CENTER
    param.row_dimensions[1].height = 30
    for col, w in zip("ABCDE", [14, 14, 6, 14, 16]):
        param.column_dimensions[col].width = w
    param["A2"], param["B2"] = "大区", "提成比例"
    param["D2"], param["E2"] = "大区", "年度目标（元）"
    for col in (1, 2, 4, 5):
        c = param.cell(row=2, column=col)
        c.fill = NAVY_FILL
        c.font = WHITE_FONT
        c.alignment = CENTER
        c.border = BORDER
    rates = [("华东", 0.08, 450000), ("华南", 0.10, 300000), ("华北", 0.12, 350000)]
    for i, (region, rate, target) in enumerate(rates, start=3):
        param.cell(row=i, column=1, value=region)
        param.cell(row=i, column=2, value=rate).number_format = "0%"
        param.cell(row=i, column=4, value=region)
        param.cell(row=i, column=5, value=target).number_format = "#,##0"
        for col in (1, 2, 4, 5):
            c = param.cell(row=i, column=col)
            c.font = BODY_FONT
            c.border = BORDER
            c.alignment = CENTER
        for col in (2, 5):
            param.cell(row=i, column=col).fill = INPUT_FILL
    param["A6"] = "说明：提成比例与年度目标为手工填写区（黄色），改动后各表自动重算。"
    param["A6"].font = Font(name="微软雅黑", size=10, color="808080")

    # ---- 销售明细 ----
    from datetime import date  # noqa: PLC0415

    detail = wb.create_sheet("销售明细")
    detail.sheet_properties.tabColor = NAVY
    headers = ["订单号", "日期", "大区", "销售员", "产品线", "数量", "单价（元）", "金额（元）", "提成比例", "提成（元）", "季度"]
    detail.merge_cells("A1:K1")
    detail["A1"] = "2026 年销售明细（黄色为填写区，金额 / 提成 / 季度均为公式，请勿手工改动）"
    detail["A1"].font = TITLE_FONT
    detail["A1"].alignment = CENTER
    detail.row_dimensions[1].height = 30
    widths = [14, 13, 9, 9, 11, 8, 12, 13, 10, 12, 8]
    for col, w in enumerate(widths, start=1):
        detail.column_dimensions[detail.cell(row=3, column=col).column_letter].width = w
    for col, h in enumerate(headers, start=1):
        detail.cell(row=3, column=col, value=h)
    _style_header_row(detail, 3, len(headers))

    people = {
        "华东": ["张三", "李四", "周九"],
        "华南": ["王五", "赵六", "吴十"],
        "华北": ["钱七", "孙八", "郑十一"],
    }
    products = [("标准版", 2980), ("专业版", 6880), ("旗舰版", 12800), ("定制服务", 20000)]
    order_rows = []
    seed = 20260917
    n = 0
    for month in range(1, 13):
        for k in range(3 if month % 2 else 2):
            seed = (seed * 1103515245 + 12345) % 2**31
            regions = ["华东", "华南", "华北"]
            region = regions[(seed // 7 + month + k) % 3]
            seed = (seed * 1103515245 + 12345) % 2**31
            person = people[region][seed % 3]
            seed = (seed * 1103515245 + 12345) % 2**31
            pname, price = products[seed % 4]
            seed = (seed * 1103515245 + 12345) % 2**31
            qty = seed % 10 + 1
            day = seed % 27 + 1
            n += 1
            order_rows.append((f"DD2026-{n:03d}", date(2026, month, day), region, person, pname, qty, price))
    first, last = 4, 3 + len(order_rows)
    for i, (oid, d, region, person, pname, qty, price) in enumerate(order_rows, start=first):
        detail.cell(row=i, column=1, value=oid)
        detail.cell(row=i, column=2, value=d).number_format = "yyyy-mm-dd"
        detail.cell(row=i, column=3, value=region)
        detail.cell(row=i, column=4, value=person)
        detail.cell(row=i, column=5, value=pname)
        detail.cell(row=i, column=6, value=qty).number_format = "#,##0"
        detail.cell(row=i, column=7, value=price).number_format = "#,##0.00"
        detail.cell(row=i, column=8, value=f"=ROUND(F{i}*G{i},2)").number_format = "#,##0.00"
        detail.cell(row=i, column=9, value=f"=VLOOKUP(C{i},参数表!$A$3:$B$5,2,FALSE)").number_format = "0%"
        detail.cell(row=i, column=10, value=f"=ROUND(H{i}*I{i},2)").number_format = "#,##0.00"
        detail.cell(row=i, column=11, value=f"=CHOOSE(MONTH(B{i}),1,1,1,2,2,2,3,3,3,4,4,4)").number_format = '"Q"0'
        _style_body(detail, i, len(headers))
        detail.cell(row=i, column=6).fill = INPUT_FILL
        detail.cell(row=i, column=7).fill = INPUT_FILL
        for col in (1, 2, 3, 4, 5, 11):
            detail.cell(row=i, column=col).alignment = CENTER
        for col in (6, 7, 8, 9, 10):
            detail.cell(row=i, column=col).alignment = CENTER
    total = last + 1
    detail.cell(row=total, column=1, value="合计").font = Font(name="微软雅黑", size=11, bold=True)
    detail.cell(row=total, column=8, value=f"=SUM(H{first}:H{last})").number_format = "#,##0.00"
    detail.cell(row=total, column=10, value=f"=SUM(J{first}:J{last})").number_format = "#,##0.00"
    detail.cell(row=total, column=6, value=f"=SUM(F{first}:F{last})").number_format = "#,##0"
    _style_body(detail, total, len(headers), zebra=False)
    for col in (1, 6, 8, 10):
        detail.cell(row=total, column=col).font = Font(name="微软雅黑", size=11, bold=True)
    detail.freeze_panes = "A4"
    detail.auto_filter.ref = f"A3:K{last}"
    dv = DataValidation(type="list", formula1='"华东,华南,华北"', allow_blank=False)
    dv.error = "请从下拉选择大区"
    detail.add_data_validation(dv)
    dv.add(f"C{first}:C{last}")
    detail.conditional_formatting.add(
        f"H{first}:H{last}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=200000, color=NAVY)
    )
    detail.sheet_properties.pageSetUpPr.fitToPage = True
    detail.page_setup.orientation = "landscape"
    detail.page_setup.fitToWidth = 1
    detail.page_setup.fitToHeight = 0
    detail.oddHeader.center.text = "2026 年销售明细（内部资料）"
    detail.oddFooter.center.text = "第 &P 页 / 共 &N 页"

    # ---- 区域汇总 ----
    summary = wb.create_sheet("区域汇总")
    summary.sheet_properties.tabColor = CORAL
    summary.merge_cells("A1:G1")
    summary["A1"] = "2026 年大区汇总（全部为公式，自动随明细与参数变化）"
    summary["A1"].font = TITLE_FONT
    summary["A1"].alignment = CENTER
    summary.row_dimensions[1].height = 30
    for col, w in zip("ABCDEFG", [10, 10, 15, 14, 15, 11, 14]):
        summary.column_dimensions[col].width = w
    sheaders = ["大区", "订单数", "销售额（元）", "提成（元）", "年度目标（元）", "达成率", "平均单（元）"]
    for col, h in enumerate(sheaders, start=1):
        summary.cell(row=3, column=col, value=h)
    _style_header_row(summary, 3, len(sheaders))
    for i, region in enumerate(["华东", "华南", "华北"], start=4):
        summary.cell(row=i, column=1, value=region)
        summary.cell(row=i, column=2, value=f"=COUNTIFS(销售明细!$C${first}:$C${last},A{i})").number_format = "#,##0"
        summary.cell(row=i, column=3, value=f"=SUMIFS(销售明细!$H${first}:$H${last},销售明细!$C${first}:$C${last},A{i})").number_format = "#,##0.00"
        summary.cell(row=i, column=4, value=f"=SUMIFS(销售明细!$J${first}:$J${last},销售明细!$C${first}:$C${last},A{i})").number_format = "#,##0.00"
        summary.cell(row=i, column=5, value=f"=VLOOKUP(A{i},参数表!$D$3:$E$5,2,FALSE)").number_format = "#,##0"
        summary.cell(row=i, column=6, value=f"=IFERROR(C{i}/E{i},0)").number_format = "0.0%"
        summary.cell(row=i, column=7, value=f"=IFERROR(C{i}/B{i},0)").number_format = "#,##0.00"
        _style_body(summary, i, len(sheaders))
        for col in range(1, len(sheaders) + 1):
            summary.cell(row=i, column=col).alignment = CENTER
    trow = 7
    summary.cell(row=trow, column=1, value="合计")
    summary.cell(row=trow, column=2, value="=SUM(B4:B6)").number_format = "#,##0"
    summary.cell(row=trow, column=3, value="=SUM(C4:C6)").number_format = "#,##0.00"
    summary.cell(row=trow, column=4, value="=SUM(D4:D6)").number_format = "#,##0.00"
    summary.cell(row=trow, column=5, value="=SUM(E4:E6)").number_format = "#,##0"
    summary.cell(row=trow, column=6, value="=IFERROR(C7/E7,0)").number_format = "0.0%"
    _style_body(summary, trow, len(sheaders), zebra=False)
    for col in range(1, len(sheaders) + 1):
        summary.cell(row=trow, column=col).font = Font(name="微软雅黑", size=11, bold=True)
        summary.cell(row=trow, column=col).alignment = CENTER
    summary.conditional_formatting.add(
        "F4:F7",
        CellIsRule(operator="lessThan", formula=["0.9"], fill=PatternFill("solid", fgColor="F4CCCC")),
    )
    summary.conditional_formatting.add(
        "F4:F7",
        CellIsRule(operator="greaterThanOrEqual", formula=["1"], fill=PatternFill("solid", fgColor="D9EAD3")),
    )

    # ---- 季度仪表 ----
    dash = wb.create_sheet("季度仪表")
    dash.sheet_properties.tabColor = "27AE60"
    dash.merge_cells("A1:D1")
    dash["A1"] = "2026 年经营仪表盘"
    dash["A1"].font = TITLE_FONT
    dash["A1"].alignment = CENTER
    dash.row_dimensions[1].height = 30
    for col, w in zip("ABCD", [18, 18, 18, 18]):
        dash.column_dimensions[col].width = w
    kpis = [
        ("总销售额（元）", f"=SUM(销售明细!H{first}:H{last})", "#,##0.00"),
        ("总提成（元）", f"=SUM(销售明细!J{first}:J{last})", "#,##0.00"),
        ("订单总数", f"=COUNTA(销售明细!A{first}:A{last})", "#,##0"),
        ("最大单（元）", f"=MAX(销售明细!H{first}:H{last})", "#,##0.00"),
        ("平均单（元）", f"=AVERAGE(销售明细!H{first}:H{last})", "#,##0.00"),
        ("年度总达成率", "=IFERROR(B3/区域汇总!E7,0)", "0.0%"),
    ]
    dash["A2"] = "核心指标"
    dash["A2"].font = Font(name="微软雅黑", size=12, bold=True, color=NAVY)
    for i, (name, formula, fmt) in enumerate(kpis, start=3):
        dash.cell(row=i, column=1, value=name).font = BODY_FONT
        dash.cell(row=i, column=1).alignment = LEFT
        dash.cell(row=i, column=2, value=formula).number_format = fmt
        dash.cell(row=i, column=2).font = Font(name="微软雅黑", size=11, bold=True)
        dash.cell(row=i, column=2).alignment = CENTER
        for col in (1, 2):
            dash.cell(row=i, column=col).border = BORDER
    dash["A9"] = "分季度销售额"
    dash["A9"].font = Font(name="微软雅黑", size=12, bold=True, color=NAVY)
    dash["A10"], dash["B10"] = "季度", "销售额（元）"
    _style_header_row(dash, 10, 2)
    for i, q in enumerate([1, 2, 3, 4], start=11):
        dash.cell(row=i, column=1, value=f"Q{q}")
        dash.cell(row=i, column=2, value=f"=SUMIF(销售明细!$K${first}:$K${last},{q},销售明细!$H${first}:$H${last})").number_format = "#,##0.00"
        _style_body(dash, i, 2)
        dash.cell(row=i, column=1).alignment = CENTER
        dash.cell(row=i, column=2).alignment = CENTER
    dash["A16"] = "产品线构成"
    dash["A16"].font = Font(name="微软雅黑", size=12, bold=True, color=NAVY)
    dash["A17"], dash["B17"] = "产品线", "销售额（元）"
    _style_header_row(dash, 17, 2)
    for i, pname in enumerate(["标准版", "专业版", "旗舰版", "定制服务"], start=18):
        dash.cell(row=i, column=1, value=pname)
        dash.cell(row=i, column=2, value=f'=SUMIF(销售明细!$E${first}:$E${last},A{i},销售明细!$H${first}:$H${last})').number_format = "#,##0.00"
        _style_body(dash, i, 2)
        dash.cell(row=i, column=1).alignment = CENTER
        dash.cell(row=i, column=2).alignment = CENTER

    bar = BarChart()
    bar.type = "col"
    bar.style = 10
    bar.title = "分季度销售额"
    bar.y_axis.title = "元"
    bar.height = 7.5
    bar.width = 13
    bar.dataLabels = DataLabelList()
    bar.dataLabels.showVal = True
    bar.add_data(Reference(dash, min_col=2, min_row=10, max_row=14), titles_from_data=True)
    bar.set_categories(Reference(dash, min_col=1, min_row=11, max_row=14))
    dash.add_chart(bar, "D2")

    pie = PieChart()
    pie.style = 10
    pie.title = "产品线构成"
    pie.height = 7.5
    pie.width = 13
    pie.dataLabels = DataLabelList()
    pie.dataLabels.showVal = True
    pie.dataLabels.showPercent = True
    pie.add_data(Reference(dash, min_col=2, min_row=17, max_row=21), titles_from_data=True)
    pie.set_categories(Reference(dash, min_col=1, min_row=18, max_row=21))
    dash.add_chart(pie, "D17")

    wb.save(OUT_DIR / "sample.xlsx")


# ---------------------------------------------------------------- pptx
PPT_NAVY = PptRGB(0x1E, 0x27, 0x61)
PPT_CORAL = PptRGB(0xF9, 0x61, 0x67)
PPT_GOLD = PptRGB(0xF9, 0xE7, 0x95)
PPT_INK = PptRGB(0x31, 0x31, 0x31)
PPT_MUTED = PptRGB(0x5F, 0x6B, 0x7A)
PPT_CARD = PptRGB(0xF2, 0xF4, 0xFA)
PPT_WHITE = PptRGB(0xFF, 0xFF, 0xFF)


def _ppt_pt(value):
    return value if isinstance(value, PPt) else PPt(value)


def _ppt_textbox(slide, left, top, width, height, runs, size=18, bold=False, color=PPT_INK, align=PP_ALIGN.LEFT,
                 space_after=PPt(6), line_spacing=1.15):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    for idx, item in enumerate(runs):
        text, kw = item if isinstance(item, tuple) else (item, {})
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = kw.get("align", align)
        p.space_after = kw.get("space_after", space_after)
        p.line_spacing = kw.get("line_spacing", line_spacing)
        r = p.add_run()
        r.text = text
        font = r.font
        font.size = _ppt_pt(kw.get("size", size))
        font.bold = kw.get("bold", bold)
        font.color.rgb = kw.get("color", color)
        font.name = kw.get("font", "微软雅黑")
    return txBox


def _ppt_card(slide, left, top, width, height, title, body, title_size=20, body_size=13, fill=PPT_CARD,
              title_color=PPT_NAVY):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.15)
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title
    r.font.size = PPt(title_size)
    r.font.bold = True
    r.font.color.rgb = title_color
    r.font.name = "微软雅黑"
    p.space_after = PPt(8)
    p2 = tf.add_paragraph()
    r2 = p2.add_run()
    r2.text = body
    r2.font.size = PPt(body_size)
    r2.font.color.rgb = PPT_INK
    r2.font.name = "微软雅黑"
    p2.line_spacing = 1.2
    return shape


def _ppt_table(slide, left, top, width, height, headers, rows, col_widths=None, highlight_col=None):
    gframe = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(left), Inches(top), Inches(width), Inches(height))
    tbl = gframe.table
    if col_widths:
        for j, w in enumerate(col_widths):
            tbl.columns[j].width = Inches(w)
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = h
        r.font.size = PPt(14)
        r.font.bold = True
        r.font.color.rgb = PPT_WHITE
        r.font.name = "微软雅黑"
        cell.fill.solid()
        cell.fill.fore_color.rgb = PPT_NAVY
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(val)
            r.font.size = PPt(12)
            r.font.color.rgb = PPT_INK
            r.font.name = "微软雅黑"
            if j == 0:
                r.font.bold = True
                r.font.color.rgb = PPT_NAVY
            cell.fill.solid()
            if highlight_col is not None and j == highlight_col:
                cell.fill.fore_color.rgb = PptRGB(0xFF, 0xF3, 0xD6)
            else:
                cell.fill.fore_color.rgb = PPT_WHITE if i % 2 == 0 else PPT_CARD
    return tbl


def make_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # 1 封面（深色）
    s1 = prs.slides.add_slide(blank)
    s1.background.fill.solid()
    s1.background.fill.fore_color.rgb = PPT_NAVY
    _ppt_textbox(s1, 1, 1.1, 11.3, 0.6, ["星云协作 NEBULA · 2026 秋季新品发布会"],
                 size=20, color=PPT_GOLD, align=PP_ALIGN.LEFT)
    _ppt_textbox(s1, 1, 1.8, 11.3, 2.4, ["星云协作 3.0", "让每一次协作，都快人一步"],
                 size=54, bold=True, color=PPT_WHITE, align=PP_ALIGN.LEFT, space_after=PPt(10))
    _ppt_textbox(s1, 1, 4.9, 7, 1.2,
                 ["全新 AI 会议纪要 · 跨组织空间 · 99.99% 可用性 SLA", "2026 年 10 月 18 日 · 杭州云栖小镇"],
                 size=18, color=PPT_WHITE, align=PP_ALIGN.LEFT)
    _ppt_card(s1, 9, 4.6, 3.3, 1.8, "预约内测", "扫码锁定 500 个首批名额\n发布会现场公布价格", title_size=22, body_size=14,
              fill=PPT_CORAL, title_color=PPT_WHITE)
    for card in s1.shapes:
        if card.has_text_frame:
            for p in card.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.color.rgb == PPT_INK:
                        r.font.color.rgb = PPT_WHITE
    s1.notes_slide.placeholders[1].text = "开场：主持人介绍发布会流程，总时长约 45 分钟。记得播放暖场视频。"

    # 2 议程
    s2 = prs.slides.add_slide(blank)
    _ppt_textbox(s2, 0.8, 0.4, 11.7, 0.9, ["今天的三个篇章", "AGENDA · 全程约 45 分钟"], size=36, bold=True, color=PPT_NAVY)
    agenda = [
        ("01", "看见变化", "混合办公 3 年：协作工具的 5 个真实痛点，来自 1200 份问卷。"),
        ("02", "三款亮点", "AI 纪要、跨组织空间、离线优先——现场逐一演示。"),
        ("03", "价格与路线", "版本定价、迁移政策与未来 12 个月路线图。"),
    ]
    for i, (num, title, body) in enumerate(agenda):
        _ppt_card(s2, 0.8 + i * 4.0, 2.0, 3.7, 4.3, f"{num}\n{title}", body, title_size=26, body_size=15)
    s2.notes_slide.placeholders[1].text = "议程页停留 1 分钟，预告最后有抽奖，留住观众。"

    # 3 市场洞察（含原生柱状图）
    s3 = prs.slides.add_slide(blank)
    _ppt_textbox(s3, 0.8, 0.4, 11.7, 0.9, ["市场在快速长大", "INSIGHT · 协作 SaaS 市场规模（亿元）"], size=36, bold=True, color=PPT_NAVY)
    _ppt_textbox(s3, 0.8, 1.7, 4.6, 4.5, [
        ("1200 份问卷的三个结论", {"size": 22, "bold": True, "color": PPT_NAVY}),
        ("68% 的团队同时用 3 款以上协作工具，切换成本极高。", {"size": 15}),
        ("会议纪要整理平均耗时 47 分钟，是最痛的环节。", {"size": 15}),
        ("跨公司协作时，72% 的人被迫用私人微信传文件。", {"size": 15}),
    ], size=15)
    chart_data = ChartData()
    chart_data.categories = ["2023", "2024", "2025", "2026E"]
    chart_data.add_series("市场规模", [12.4, 18.6, 27.3, 41.2])
    frame = s3.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(6.0), Inches(1.7), Inches(6.3), Inches(4.4),
                                chart_data)
    chart = frame.chart
    chart.has_title = True
    chart.chart_title.text_frame.text = "协作 SaaS 市场规模（亿元）"
    chart.has_legend = False
    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.show_value = True
    series = chart.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = PPT_NAVY
    chart.value_axis.has_major_gridlines = False
    _ppt_textbox(s3, 0.8, 6.5, 11.7, 0.5, ["数据来源：内部问卷（n=1200）+ 公开研报整理"], size=11, color=PPT_MUTED)
    s3.notes_slide.placeholders[1].text = "讲三个问卷结论时配合手势，图表数字逐个出现（动画略）。"

    # 4 三大亮点
    s4 = prs.slides.add_slide(blank)
    _ppt_textbox(s4, 0.8, 0.4, 11.7, 0.9, ["三大亮点，现场演示", "HIGHLIGHTS · 全部可在发布会后即刻试用"], size=36, bold=True,
                 color=PPT_NAVY)
    _ppt_card(s4, 0.8, 2.0, 3.7, 4.3, "AI 会议纪要", "开完会 10 秒出纪要：待办自动@到人，支持 12 种语言互译，准确率 97.3%。")
    _ppt_card(s4, 4.8, 2.0, 3.7, 4.3, "跨组织空间", "和上下游建共享空间：文件、任务、日程三同步，权限可细到单个文档。")
    _ppt_card(s4, 8.8, 2.0, 3.7, 4.3, "离线优先", "高铁、机舱照样用：弱网秒开，联网后自动合并，多端零冲突。")
    s4.notes_slide.placeholders[1].text = "每个亮点演示约 5 分钟，提前准备演示账号与脏数据清理。"

    # 5 版本与定价（表格）
    s5 = prs.slides.add_slide(blank)
    _ppt_textbox(s5, 0.8, 0.4, 11.7, 0.9, ["版本与定价", "PRICING · 按人按年，老用户续费 8 折"], size=36, bold=True, color=PPT_NAVY)
    _ppt_table(s5, 0.8, 1.7, 11.7, 3.4,
               ["版本", "免费版", "专业版 ★", "旗舰版"],
               [
                   ["价格", "¥0", "¥198 / 人/年", "¥398 / 人/年"],
                   ["空间上限", "10 GB", "1 TB", "不限量"],
                   ["AI 纪要", "每月 5 次", "无限次", "无限次 + 定制词库"],
                   ["跨组织空间", "—", "5 个", "不限 + 审计日志"],
                   ["SLA", "—", "99.9%", "99.99% 专属客服"],
               ],
               col_widths=[2.6, 3.0, 3.2, 2.9], highlight_col=2)
    _ppt_textbox(s5, 0.8, 5.5, 11.7, 1.2,
                 ["迁移政策：Notion / 飞书 / 钉钉一键导入，100 人以下团队免费协助迁移。", "教育与公益组织全年 5 折。"],
                 size=15)
    s5.notes_slide.placeholders[1].text = "价格公布后停顿 3 秒，等掌声。随后讲迁移政策打消顾虑。"

    # 6 路线图与致谢
    s6 = prs.slides.add_slide(blank)
    _ppt_textbox(s6, 0.8, 0.4, 11.7, 0.9, ["未来 12 个月", "ROADMAP · 今天只是起点"], size=36, bold=True, color=PPT_NAVY)
    steps = [
        ("2026 Q4", "开放 API 与 Webhook，上线 50+ 集成。"),
        ("2027 Q1", "桌面端 2.0：多窗口与全局搜索。"),
        ("2027 Q2", "出海版：英文、日文数据中心上线。"),
        ("2027 Q3", "AI 助手开放平台，支持企业私域知识。"),
    ]
    for i, (t, b) in enumerate(steps):
        _ppt_card(s6, 0.8 + i * 3.05, 1.8, 2.85, 2.6, t, b, title_size=20, body_size=13)
    _ppt_textbox(s6, 0.8, 4.9, 11.7, 1.6,
                 [("谢谢观看 · Q&A", {"size": 30, "bold": True, "color": PPT_NAVY}),
                  ("商务合作：partner@nebula.example.com · 内测申请：nebula.example.com/early-access",
                   {"size": 15, "color": PPT_MUTED})],
                 size=15)
    s6.notes_slide.placeholders[1].text = "结尾抽奖 + 合影，提醒观众填写反馈问卷领取周边。"

    prs.core_properties.title = "星云协作 3.0 新品发布会"
    prs.core_properties.author = "星云协作市场部"
    prs.save(OUT_DIR / "sample.pptx")


# ---------------------------------------------------------------- pdf (reportlab)
def _pdf_header_footer(canvas, doc, title, font="Helvetica"):
    canvas.saveState()
    canvas.setFont(font, 8)
    canvas.setFillColor(colors.HexColor("#808080"))
    if font == "STSong-Light":
        canvas.drawString(20 * mm, 282 * mm, "员工手册（节选） V4.2")
    else:
        canvas.drawString(20 * mm, 282 * mm, title)
    canvas.drawRightString(190 * mm, 282 * mm, "Confidential")
    canvas.drawCentredString(105 * mm, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
    canvas.line(20 * mm, 280 * mm, 190 * mm, 280 * mm)
    canvas.restoreState()


def _styled_table(data, col_widths, header_bg="#1E2761"):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B0B0B0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#EEF1F7")))
    t.setStyle(TableStyle(style))
    return t


def make_pdf_en():
    from reportlab.platypus import SimpleDocTemplate  # noqa: PLC0415

    path = OUT_DIR / "sample.pdf"
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("Title2", parent=styles["Title"], fontSize=28, textColor=colors.HexColor("#1E2761"),
                             spaceAfter=4)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#1E2761"),
                        spaceBefore=14, spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12.5, textColor=colors.HexColor("#2E5AAC"),
                        spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("Body2", parent=styles["Normal"], fontSize=10.5, leading=15.5, alignment=TA_JUSTIFY,
                          spaceAfter=6)
    caption = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#808080"),
                             alignment=TA_CENTER, spaceAfter=10)
    meta = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#555555"),
                          alignment=TA_CENTER, spaceAfter=2)

    story = [
        Paragraph("Aurora Analytics", ParagraphStyle("Eyebrow", parent=styles["Normal"], fontSize=11,
                                                     textColor=colors.HexColor("#B7952B"), alignment=TA_CENTER,
                                                     spaceAfter=2)),
        Paragraph("2026 Annual Review", title_s),
        Paragraph("Growth with discipline: revenue, customers, and what's next", meta),
        Paragraph("Document No. AA-2026-AR · Prepared by Strategy Office · 18 Sep 2026", meta),
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1E2761")),
        Spacer(1, 8),
    ]
    story.append(Paragraph("1 &nbsp; Highlights", h1))
    story.append(Paragraph(
        "2026 was the year Aurora Analytics turned scale into operating leverage. Full-year revenue reached "
        "$8.96M, up 12.4% year over year, while net revenue retention climbed to 118%. The North region passed "
        "$3M for the first time and became the main growth driver; the East stayed solid and the South is under "
        "a structured recovery plan. Headcount grew 22% with attrition at a five-year low of 6.1%.", body))
    bullets = [
        "<b>Revenue $8.96M (+12.4% YoY)</b> — new-product attach rate hit 78%, 6 points above plan.",
        "<b>1,240 enterprise customers</b> — including 36 Fortune-500 logos won this year.",
        "<b>NRR 118%</b> — expansion outpaced churn for the sixth consecutive quarter.",
        "<b>Cash runway 28 months</b> — burn multiple improved from 2.1x to 1.4x.",
    ]
    story.append(ListFlowable([ListItem(Paragraph(b, body), leftIndent=18) for b in bullets], bulletType="bullet",
                              start="\u2022", leftIndent=12))
    story.append(Paragraph("2 &nbsp; Financials by region", h1))
    story.append(Paragraph("Regional performance ($10K)", h2))
    story.append(_styled_table(
        [["Region", "Q2", "Q3", "QoQ", "Share"],
         ["East", "348.0", "391.0", "+12.4%", "43.6%"],
         ["South", "221.0", "205.0", "-7.2%", "22.9%"],
         ["North", "246.0", "300.0", "+22.0%", "33.5%"],
         ["Total", "815.0", "896.0", "+9.9%", "100%"]],
        [38 * mm, 28 * mm, 28 * mm, 28 * mm, 28 * mm]))
    story.append(Paragraph("Figure 1 — Q3 regional mix. North is now one-third of the business.", caption))
    story.append(Image(annual_bar_chart_en(), width=150 * mm, height=75 * mm))
    story.append(Paragraph("Figure 2 — Regional sales, Q2 vs Q3 ($10K).", caption))
    story.append(Paragraph("What drove the South decline?", h2))
    story.append(Paragraph(
        "Two enterprise renewals slipped into October ($160K combined) and one distributor churned after an "
        "acquisition. Excluding timing effects, South grew 3.1%. A dedicated recovery squad now owns the top-20 "
        "Southern accounts with weekly pipeline reviews.", body))
    story.append(PageBreak())
    story.append(Paragraph("3 &nbsp; Customers &amp; product", h1))
    story.append(Paragraph(
        "Net new ARR of $1.9M came 60% from expansion. The new Metric Studio (launched May) already contributes "
        "14% of new bookings, with trial-to-paid conversion at 31% — double the company average.", body))
    story.append(_styled_table(
        [["Product line", "New ARR ($K)", "Conv.", "NPS"],
         ["Core Dashboards", "820", "18%", "52"],
         ["Metric Studio", "610", "31%", "61"],
         ["Data Pipelines", "340", "22%", "48"],
         ["Professional Svcs", "130", "—", "57"]],
        [45 * mm, 32 * mm, 32 * mm, 32 * mm]))
    story.append(Paragraph("Table 1 — 2026 new ARR by product line.", caption))
    story.append(Paragraph("4 &nbsp; 2027 priorities", h1))
    story.append(Paragraph("Three bets, in order:", body))
    numbered = [
        "<b>Hold the North's lead</b> — add a second solutions team in Chicago before March.",
        "<b>Bring the South back</b> — recover to +10% growth by Q2 with the top-20 account plan.",
        "<b>Finish the platform rollout</b> — SSO/SIEM pack and EU data residency in H1.",
    ]
    story.append(ListFlowable([ListItem(Paragraph(b, body), leftIndent=18) for b in numbered], bulletType="1",
                              leftIndent=12))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    story.append(Paragraph(
        "Contact: strategy@aurora.example.com · Next business review: 8 Oct 2026, all hands. "
        "Figures are unaudited and exported from the finance system.", meta))

    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=28 * mm,
                            bottomMargin=18 * mm, title="Aurora Analytics 2026 Annual Review",
                            author="Strategy Office")
    doc.build(story, onFirstPage=lambda c, d: _pdf_header_footer(c, d, "Aurora Analytics · 2026 Annual Review"),
              onLaterPages=lambda c, d: _pdf_header_footer(c, d, "Aurora Analytics · 2026 Annual Review"))


def make_pdf_cjk():
    from reportlab.platypus import SimpleDocTemplate  # noqa: PLC0415

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    path = OUT_DIR / "sample_cjk.pdf"
    F = "STSong-Light"
    title_s = ParagraphStyle("CTitle", fontName=F, fontSize=26, textColor=colors.HexColor("#1E2761"),
                             alignment=TA_CENTER, spaceAfter=4, wordWrap="CJK")
    h1 = ParagraphStyle("CH1", fontName=F, fontSize=16, textColor=colors.HexColor("#1E2761"), spaceBefore=14,
                        spaceAfter=6, wordWrap="CJK")
    h2 = ParagraphStyle("CH2", fontName=F, fontSize=12.5, textColor=colors.HexColor("#2E5AAC"), spaceBefore=10,
                        spaceAfter=4, wordWrap="CJK")
    body = ParagraphStyle("CBody", fontName=F, fontSize=10.5, leading=16, alignment=TA_JUSTIFY, spaceAfter=6,
                          wordWrap="CJK")
    caption = ParagraphStyle("CCap", fontName=F, fontSize=9, textColor=colors.HexColor("#808080"),
                             alignment=TA_CENTER, spaceAfter=10, wordWrap="CJK")
    meta = ParagraphStyle("CMeta", fontName=F, fontSize=10, textColor=colors.HexColor("#555555"),
                          alignment=TA_CENTER, spaceAfter=2, wordWrap="CJK")
    bullet_s = ParagraphStyle("CBul", parent=body, leftIndent=18, firstLineIndent=0)

    story = [
        Paragraph("星野科技集团", ParagraphStyle("CEye", fontName=F, fontSize=11,
                                                 textColor=colors.HexColor("#B7952B"), alignment=TA_CENTER,
                                                 spaceAfter=2, wordWrap="CJK")),
        Paragraph("员 工 手 册（节 选）", title_s),
        Paragraph("适用范围：全体正式员工 · 版本 V4.2 · 生效日期 2026-07-01", meta),
        Paragraph("编制：人力资源部 · 审批：CEO 办公室", meta),
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1E2761")),
        Spacer(1, 8),
    ]
    story.append(Paragraph("一、 考勤与假期", h1))
    story.append(Paragraph(
        "公司实行弹性工作制：核心工作时间为 10:00—16:00，上下班各浮动 2 小时，每月需保证 176 小时出勤。"
        "考勤以门禁与「星野通」App 打卡为准，忘记打卡可在 3 个工作日内补卡，每月限 3 次。", body))
    story.append(Paragraph("年假标准", h2))
    data = [["司龄", "年假天数", "有效期", "备注"],
            ["不满 1 年", "5 天（按比例折算）", "当年有效", "入职满 3 个月起休"],
            ["1 年（含）~ 3 年", "7 天", "当年有效", "可拆零，最小单位 0.5 天"],
            ["3 年（含）~ 5 年", "10 天", "可结转 5 天", "需在次年 3 月底前休完"],
            ["5 年（含）以上", "15 天", "可结转 5 天", "可申请一次性连休"]]
    rows = [[Paragraph(f"<font name='{F}'>{c}</font>", ParagraphStyle(f"cc{i}_{j}", fontName=F, fontSize=9.5,
                                                                      leading=13, alignment=TA_LEFT if j == 0 else TA_CENTER,
                                                                      wordWrap="CJK")) for j, c in enumerate(r)]
            for i, r in enumerate(data)]
    t = Table(rows, colWidths=[38 * mm, 42 * mm, 32 * mm, 38 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E2761")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B0B0B0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF1F7")]),
    ]))
    story.append(t)
    story.append(Paragraph("表 1 — 年假标准（司龄按入职周年计算）。", caption))
    story.append(Paragraph(
        "病假凭三甲医院证明可全薪 10 天 / 年；事假需提前 1 天申请，扣发当日 100% 日薪；"
        "产假、陪产假、婚丧假按国家规定执行，申请时附证明材料即可。", body))
    story.append(Image(leave_chart_cjk(), width=150 * mm, height=75 * mm))
    story.append(Paragraph("图 1 — 2026 年上半年各类假期使用总量（天）。", caption))

    story.append(Paragraph("二、 薪酬与绩效", h1))
    story.append(Paragraph("发薪与构成", h2))
    story.append(Paragraph(
        "每月 10 日发放上月工资（遇节假日提前）。工资条在「星野通」App 内查看，由基本工资、岗位津贴、"
        "绩效奖金三部分构成，其中绩效奖金按季度核算，随季度工资一次性发放。", body))
    story.append(ListFlowable([
        ListItem(Paragraph("试用期 3 个月，薪资为转正后 80%，试用期计入司龄。", bullet_s)),
        ListItem(Paragraph("年度调薪窗口为每年 4 月，综合绩效、司龄与市场分位确定涨幅。", bullet_s)),
        ListItem(Paragraph("对薪资有疑问，可在发薪后 5 个工作日内向 HRBP 提起复核。", bullet_s)),
    ], bulletType="bullet", leftIndent=12))
    story.append(Paragraph("绩效等级", h2))
    story.append(_styled_table_cjk(F, [
        ["等级", "占比", "奖金系数", "说明"],
        ["S（卓越）", "约 10%", "1.5", "超额达成且有组织级贡献"],
        ["A（优秀）", "约 25%", "1.2", "全面达成并有亮点"],
        ["B（达标）", "约 55%", "1.0", "达成岗位基本要求"],
        ["C（待改进）", "约 10%", "0.5", "进入 3 个月改进期"],
    ], [30 * mm, 25 * mm, 25 * mm, 70 * mm]))
    story.append(Paragraph("表 2 — 绩效等级与奖金系数。", caption))

    story.append(PageBreak())
    story.append(Paragraph("三、 行为规范", h1))
    story.append(Paragraph(
        "以下红线触碰任何一条即解除劳动合同：泄露公司商业秘密；伪造考勤、报销凭证；"
        "在职期间兼职竞品业务且拒不改正；对同事实施骚扰、歧视或暴力行为。", body))
    story.append(Paragraph("日常办公约定", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("会议室使用后复位桌椅、带走垃圾，白板内容拍照后擦除。", bullet_s)),
        ListItem(Paragraph("开源与外部技术分享前，先经直属主管与法务双重确认。", bullet_s)),
        ListItem(Paragraph("下班后非紧急事项不 @ 全体成员，跨时区协作注明期望回复时间。", bullet_s)),
    ], bulletType="1", leftIndent=14))
    story.append(Paragraph("四、 附则", h1))
    story.append(Paragraph(
        "本手册由人力资源部负责解释，自 2026 年 7 月 1 日起生效。未尽事宜参照国家法律法规与公司专项制度执行；"
        "如与新颁布的专项制度冲突，以新制度为准。祝大家在这里工作顺利、成长飞快！", body))
    story.append(Spacer(1, 12))
    story.append(Paragraph("人力资源部 · 2026 年 6 月 28 日", meta))
    story.append(Paragraph("咨询：hr@xingye.example.com · 内线 8800", meta))

    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=28 * mm,
                            bottomMargin=18 * mm, title="员工手册（节选）", author="人力资源部")
    doc.build(story, onFirstPage=lambda c, d: _pdf_header_footer(c, d, "", font="STSong-Light"),
              onLaterPages=lambda c, d: _pdf_header_footer(c, d, "", font="STSong-Light"))


def _styled_table_cjk(font, data, col_widths):
    inner = ParagraphStyle("inner", fontName=font, fontSize=9.5, leading=13, wordWrap="CJK")
    rows = [[Paragraph(c, inner) for c in r] for r in data]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E2761")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B0B0B0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#EEF1F7")))
    t.setStyle(TableStyle(style))
    return t


def _fix_docx_settings_zoom(docx_path):
    """python-docx 默认写 <w:zoom w:val='bestFit'/>，缺必需的 w:percent 属性，
    Word/LibreOffice 能正常打开，但 XSD 校验会报。生成后顺手修成合法形式。"""
    import zipfile  # noqa: PLC0415

    with zipfile.ZipFile(docx_path, "r") as z:
        parts = {name: z.read(name) for name in z.namelist()}
    old = b'<w:zoom w:val="bestFit"/>'
    if old in parts["word/settings.xml"]:
        parts["word/settings.xml"] = parts["word/settings.xml"].replace(old, b'<w:zoom w:percent="120"/>')
        with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in parts.items():
                z.writestr(name, data)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    make_docx()
    _fix_docx_settings_zoom(OUT_DIR / "sample.docx")
    make_xlsx()
    make_pptx()
    make_pdf_en()
    make_pdf_cjk()
    for f in sorted(OUT_DIR.iterdir()):
        print(f.name, f.stat().st_size)


if __name__ == "__main__":
    # 避免 matplotlib 中文字体缺失导致 fallback 警告刷屏
    import warnings  # noqa: PLC0415

    warnings.filterwarnings("ignore")
    main()
