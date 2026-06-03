from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(
    repo_name: str,
    daily_stats: list[dict],
    weekly_stats: list[dict],
    collaboration_data: dict | None = None,
    violations: list[dict] | None = None,
    streak_current: int = 0,
    streak_longest: int = 0,
) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
    )

    story = []

    # Title
    story.append(Paragraph(f"Git Analysis Report: {repo_name}", title_style))
    story.append(Spacer(1, 8 * mm))

    # Summary stats
    total_commits = sum(d.get("commit_count", 0) for d in daily_stats)
    total_insertions = sum(d.get("insertions", 0) for d in daily_stats)
    total_deletions = sum(d.get("deletions", 0) for d in daily_stats)
    date_range = ""
    if daily_stats:
        date_range = f"{daily_stats[0].get('date', '')} ~ {daily_stats[-1].get('date', '')}"

    summary_data = [
        ["Metric", "Value"],
        ["Total Commits", str(total_commits)],
        ["Active Days", str(len(daily_stats))],
        ["Total Insertions", str(total_insertions)],
        ["Total Deletions", str(total_deletions)],
        ["Current Streak", f"{streak_current} days"],
        ["Longest Streak", f"{streak_longest} days"],
        ["Date Range", date_range],
    ]

    story.append(Paragraph("Summary", heading_style))
    summary_table = Table(summary_data, colWidths=[6 * cm, 10 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90D9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8 * mm))

    # Daily stats table (last 30 days)
    story.append(Paragraph("Daily Statistics (Recent 30 Days)", heading_style))
    recent_daily = daily_stats[-30:] if len(daily_stats) > 30 else daily_stats
    daily_table_data = [["Date", "Commits", "Insertions", "Deletions", "Files Changed"]]
    for d in recent_daily:
        daily_table_data.append([
            d.get("date", ""),
            str(d.get("commit_count", 0)),
            str(d.get("insertions", 0)),
            str(d.get("deletions", 0)),
            str(d.get("files_changed", 0)),
        ])

    daily_table = Table(daily_table_data, colWidths=[3.2 * cm, 2.5 * cm, 3 * cm, 2.8 * cm, 3.2 * cm])
    daily_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90D9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(daily_table)
    story.append(Spacer(1, 8 * mm))

    # Collaboration network image
    if collaboration_data and collaboration_data.get("nodes"):
        story.append(Paragraph("Developer Collaboration Network", heading_style))
        from app.services.collaboration import render_collaboration_image
        img_buf = render_collaboration_image(collaboration_data)
        img = Image(img_buf, width=16 * cm, height=10 * cm)
        story.append(img)
        story.append(Spacer(1, 8 * mm))

    # Violations table
    if violations:
        story.append(Paragraph(f"Commit Violations ({len(violations)} total)", heading_style))
        viol_data = [["Hash", "Rule", "Severity", "Description", "Author"]]
        for v in violations[:50]:
            viol_data.append([
                v.get("commit_hash", ""),
                v.get("rule_name", ""),
                v.get("severity", ""),
                (v.get("description", "") or "")[:40],
                (v.get("author", "") or "")[:20],
            ])

        viol_table = Table(viol_data, colWidths=[2 * cm, 3 * cm, 2 * cm, 5.5 * cm, 3.2 * cm])
        viol_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E74C3C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF0EF")]),
        ]))
        story.append(viol_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
