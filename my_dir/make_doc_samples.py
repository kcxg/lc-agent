"""生成四种格式的最小样例文件，用于手动验证文档只读预览链路。"""

import zipfile
from pathlib import Path

import openpyxl
import pptx
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

OUT_DIR = Path(__file__).parent / "doc_preview_samples"

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:r><w:t>Docx Preview 标题</w:t></w:r></w:p>
<w:p><w:r><w:t>这是中文正文，用于验证只读预览。</w:t></w:r></w:p>
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>
</w:body>
</w:document>"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    docx_path = OUT_DIR / "sample.docx"
    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/document.xml", DOCUMENT)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["B1"] = "姓名", "金额"
    ws["A2"], ws["B2"] = "张三", 123.45
    wb.save(OUT_DIR / "sample.xlsx")

    prs = pptx.Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "测试标题"
    slide.placeholders[1].text = "副标题内容"
    prs.save(OUT_DIR / "sample.pptx")

    pdf = canvas.Canvas(str(OUT_DIR / "sample.pdf"))
    pdf.drawString(100, 700, "Hello PDF Preview")
    pdf.showPage()
    pdf.save()

    # 中文 PDF：走 CID 字体，预览依赖 pdfjs 的 CMap 数据（默认从 unpkg 拉取）
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    cjk = canvas.Canvas(str(OUT_DIR / "sample_cjk.pdf"))
    cjk.setFont("STSong-Light", 20)
    cjk.drawString(80, 700, "中文 PDF 预览测试：这是一段中文字符")
    cjk.showPage()
    cjk.save()

    for f in sorted(OUT_DIR.iterdir()):
        print(f.name, f.stat().st_size)


if __name__ == "__main__":
    main()
