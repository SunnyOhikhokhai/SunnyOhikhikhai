"""
PDF report generation with ReportLab.

The PDF is built from the same ``Report`` object as the results page, so
the figures always match. Amounts use currency codes (e.g. "NGN 1,000.00")
because ReportLab's built-in fonts do not include the ₦ symbol.
"""
from __future__ import annotations

from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image, KeepTogether, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from xml.sax.saxutils import escape

from financial_models.common.report import Report

NAVY = colors.HexColor("#0B1F46")
BLUE = colors.HexColor("#0878E8")
GREEN = colors.HexColor("#10B981")
SOFT = colors.HexColor("#F3F6FA")
SLATE = colors.HexColor("#475569")
RED = colors.HexColor("#DC2626")
TONE_COLOURS = {"positive": GREEN, "negative": RED, "neutral": NAVY}

DISCLAIMER = (
    "This report was produced by FINPLAN from the assumptions entered by the user. All figures are estimates "
    "and projections, not actual results, predictions or guarantees. They do not constitute financial, tax, "
    "legal or investment advice. Check important decisions with a qualified professional."
)


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], textColor=NAVY, alignment=TA_LEFT, fontSize=20, spaceAfter=4),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("b", parent=base["BodyText"], textColor=SLATE, fontSize=9, leading=12),
        "small": ParagraphStyle("s", parent=base["BodyText"], textColor=SLATE, fontSize=7.5, leading=10),
        "cell": ParagraphStyle("c", parent=base["BodyText"], fontSize=8, leading=10, textColor=colors.black),
        "cellr": ParagraphStyle("cr", parent=base["BodyText"], fontSize=8, leading=10, alignment=2),
        "head": ParagraphStyle("h", parent=base["BodyText"], fontSize=8, leading=10, textColor=colors.white,
                               fontName="Helvetica-Bold"),
        "headr": ParagraphStyle("hr", parent=base["BodyText"], fontSize=8, leading=10, textColor=colors.white,
                                fontName="Helvetica-Bold", alignment=2),
        "metric_label": ParagraphStyle("ml", parent=base["BodyText"], fontSize=8, textColor=SLATE),
        "metric_value": ParagraphStyle("mv", parent=base["BodyText"], fontSize=12, leading=15, fontName="Helvetica-Bold"),
    }


def _p(text: str, style) -> Paragraph:
    return Paragraph(escape(str(text)), style)


def _logo(max_width: float, max_height: float):
    path = finders.find("images/finplan-logo.png") or str(settings.BASE_DIR / "static" / "images" / "finplan-logo.png")
    try:
        reader = ImageReader(path)
    except Exception:  # pragma: no cover - missing logo should not break reports
        return None
    width, height = reader.getSize()
    scale = min(max_width / width, max_height / height)  # keep proportions
    return Image(path, width=width * scale, height=height * scale, hAlign="LEFT")


def _table(columns, rows, styles, col_widths=None, total_row=False, row_tones=None, numeric_from=1):
    data = [[_p(c, styles["headr"] if i >= numeric_from else styles["head"]) for i, c in enumerate(columns)]]
    for row in rows:
        data.append([_p(cell, styles["cellr"] if i >= numeric_from else styles["cell"]) for i, cell in enumerate(row)])
    table = LongTable(data, colWidths=col_widths, repeatRows=1)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E1EC")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for index, row_tone in enumerate(row_tones or [], start=1):
        if row_tone == "negative" and index < len(data):
            commands.append(("TEXTCOLOR", (0, index), (-1, index), RED))
    if total_row:
        commands.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
    table.setStyle(TableStyle(commands))
    return table


def build_pdf(project, report: Report, model_label: str) -> bytes:
    buffer = BytesIO()
    styles = _styles()
    generated = timezone.localtime()
    wide = any(len(t.columns) > 6 for t in report.tables)
    pagesize = landscape(A4) if wide else A4
    doc = SimpleDocTemplate(
        buffer, pagesize=pagesize, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=16 * mm,
        title=f"{project.name} – FINPLAN report", author="FINPLAN",
    )
    usable = pagesize[0] - 32 * mm

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SLATE)
        canvas.drawString(16 * mm, 9 * mm, f"FINPLAN · Plan Smarter. Grow Further. · {project.name}")
        canvas.drawRightString(pagesize[0] - 16 * mm, 9 * mm, f"Page {document.page}")
        canvas.restoreState()

    story = []
    logo = _logo(55 * mm, 16 * mm)
    if logo:
        story += [logo, Spacer(1, 4 * mm)]
    story.append(_p(project.name, styles["title"]))
    story.append(_p(model_label, styles["body"]))
    story.append(Spacer(1, 3 * mm))

    meta = [
        ["Model", model_label],
        ["Currency", project.currency],
        ["Report generated", generated.strftime("%d %B %Y, %H:%M")],
        ["Inputs last saved", timezone.localtime(project.updated_at).strftime("%d %B %Y, %H:%M")],
        ["Prepared for", project.owner.get_full_name() or project.owner.get_username()],
    ]
    meta_table = Table([[_p(a, styles["metric_label"]), _p(b, styles["cell"])] for a, b in meta],
                       colWidths=[40 * mm, usable - 40 * mm], hAlign="LEFT")
    meta_table.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 2)]))
    story += [meta_table, Spacer(1, 4 * mm)]

    # Headline metrics as a row of boxes.
    cells = []
    for metric in report.headline:
        value_style = ParagraphStyle("v", parent=styles["metric_value"], textColor=TONE_COLOURS.get(metric.tone, NAVY))
        cells.append([_p(metric.label, styles["metric_label"]), _p(metric.value, value_style)])
    if cells:
        width = usable / len(cells)
        boxes = Table([[Table([[label], [value]], colWidths=[width - 6 * mm]) for label, value in cells]], colWidths=[width] * len(cells))
        boxes.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E1EC")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E1EC")),
            ("BACKGROUND", (0, 0), (-1, -1), SOFT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story += [_p("Key results", styles["h2"]), boxes]

    for warning in report.warnings:
        story.append(Paragraph(f"<font color='#DC2626'><b>Note:</b></font> {escape(warning)}", styles["body"]))

    for section in report.sections:
        rows = [[m.label, m.value] for m in section.metrics]
        block = [_p(section.title, styles["h2"])]
        if section.intro:
            block.append(_p(section.intro, styles["small"]))
        block.append(_table(["Measure", "Value"], rows, styles, col_widths=[usable * 0.6, usable * 0.4]))
        story.append(KeepTogether(block))

    if report.scenario_table:
        st = report.scenario_table
        first = usable * 0.34
        rest = (usable - first) / (len(st.columns) - 1)
        story.append(KeepTogether([
            _p(st.title, styles["h2"]),
            _table(st.columns, st.rows, styles, col_widths=[first] + [rest] * (len(st.columns) - 1)),
            Spacer(1, 2 * mm),
            _p(st.note, styles["small"]),
        ]))

    story.append(PageBreak())
    story.append(_p("Assumptions", styles["h2"]))
    story.append(_table(["Assumption", "Value"], [list(a) for a in report.assumptions], styles,
                        col_widths=[usable * 0.4, usable * 0.6], numeric_from=99))

    for table in report.tables:
        first = usable * 0.22 if len(table.columns) > 3 else usable * 0.45
        rest = (usable - first) / max(len(table.columns) - 1, 1)
        story.append(_p(table.title, styles["h2"]))
        story.append(_table(table.columns, table.rows, styles, col_widths=[first] + [rest] * (len(table.columns) - 1),
                            total_row=table.total_row, row_tones=table.row_tones))
        if table.note:
            story.append(_p(table.note, styles["small"]))

    if report.explanations:
        story.append(_p("Understanding these results", styles["h2"]))
        for title, text in report.explanations:
            story.append(Paragraph(f"<b>{escape(title)}.</b> {escape(text)}", styles["body"]))
            story.append(Spacer(1, 1.5 * mm))

    story.append(_p("Limitations", styles["h2"]))
    for item in report.limitations:
        story.append(_p(f"• {item}", styles["body"]))
    story.append(_p("Disclaimer", styles["h2"]))
    story.append(_p(DISCLAIMER, styles["body"]))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
