"""Builds downloadable PDF (ReportLab) and DOCX (python-docx) versions of a saved study pack."""
import io
import re
from datetime import datetime
from xml.sax.saxutils import escape

from docx import Document as DocxDocument
from docx.shared import Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LETTERS = "ABCD"


def safe_download_name(title: str, fmt: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._ -]+", "", title or "study-pack").strip().replace(" ", "_")[:60] or "study-pack"
    return f"{base}_study_pack.{fmt}"


def _fmt_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return value


# ============================================================ PDF
class _Pdf:
    def __init__(self):
        base = getSampleStyleSheet()
        self.h1 = ParagraphStyle("h1", parent=base["Title"], fontSize=20, spaceAfter=6, textColor=colors.HexColor("#1e3a8a"))
        self.h2 = ParagraphStyle("h2", parent=base["Heading2"], fontSize=14, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1e40af"))
        self.h3 = ParagraphStyle("h3", parent=base["Heading3"], fontSize=11.5, spaceBefore=8, spaceAfter=3, textColor=colors.HexColor("#312e81"))
        self.body = ParagraphStyle("body", parent=base["BodyText"], fontSize=10, leading=14, alignment=TA_LEFT)
        self.small = ParagraphStyle("small", parent=self.body, fontSize=9, textColor=colors.HexColor("#475569"))
        self.bullet = ParagraphStyle("bullet", parent=self.body, leftIndent=14, bulletIndent=4)
        self.option = ParagraphStyle("option", parent=self.body, leftIndent=18)
        self.answer = ParagraphStyle("answer", parent=self.body, leftIndent=18, textColor=colors.HexColor("#065f46"))
        self.story: list = []

    def p(self, text: str, style=None):
        self.story.append(Paragraph(escape(str(text)), style or self.body))

    def bullets(self, items: list[str]):
        for item in items:
            self.story.append(Paragraph(escape(str(item)), self.bullet, bulletText="•"))

    def gap(self, h: float = 4):
        self.story.append(Spacer(1, h))


def build_pdf(pack: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                            title=pack.get("document", {}).get("title", "Study Pack"), author="Smart Study Pack Generator")
    w = _Pdf()
    d, s, k, q, r, m = (pack.get(x) or {} for x in ("document", "summaries", "key_concepts", "questions", "review", "meta"))

    w.p(d.get("title", "Study Pack"), w.h1)
    w.p(f"Subject: {d.get('subject', '')}   |   Source: {pack.get('filename', '')}   |   Generated: {_fmt_date(pack.get('generated_at'))}", w.small)
    w.p(f"Prompt version {m.get('prompt_version', '')}   |   Model {m.get('model', '')}   |   Audience: {d.get('audience_level', '')}", w.small)
    w.gap(8)

    if s.get("overall_summary"):
        w.p("Overview", w.h2)
        w.p(s["overall_summary"])

    w.p("Topic Outline", w.h2)
    for t in d.get("main_topics", []):
        w.p(t.get("name", ""), w.h3)
        if t.get("description"):
            w.p(t["description"])
        if t.get("subtopics"):
            w.bullets(t["subtopics"])

    w.p("Topic-wise Summaries", w.h2)
    for t in s.get("topics", []):
        w.p(t.get("topic", ""), w.h3)
        w.p(t.get("summary", ""))
        if t.get("simple_explanation"):
            w.p(f"In simple terms: {t['simple_explanation']}", w.small)
        if t.get("important_points"):
            w.p("Important points:", w.small)
            w.bullets(t["important_points"])
        if t.get("formulas"):
            w.p("Formulas:", w.small)
            w.bullets(t["formulas"])
        if t.get("examples"):
            w.p("Examples:", w.small)
            w.bullets(t["examples"])

    pa = pack.get("practice_assignment") or {}
    pa_questions = pa.get("questions") or []
    if pa_questions:
        w.story.append(PageBreak())
        w.p("Practice Assignment (Multiple-Choice Questions)", w.h2)
        w.p(f"Difficulty: {str(pa.get('difficulty', 'mixed')).title()}   |   Total MCQs: {len(pa_questions)}   |   Total Marks: {len(pa_questions)}", w.small)
        w.p("Instructions: Select exactly one answer option (A, B, C, or D) for each question. All questions are grounded in the lecture notes.", w.small)
        w.gap(6)
        for i, mc in enumerate(pa_questions, 1):
            w.p(f"Q{i}. {mc['question']}  [{mc.get('difficulty', '')}{', ' + mc['topic'] if mc.get('topic') else ''}]", w.body)
            for j, opt in enumerate(mc.get("options", [])):
                w.p(f"{LETTERS[j]}. {opt}", w.option)
            w.gap(3)
        w.gap(6)
        w.p("Practice Assignment Answer Key & Explanations", w.h3)
        for i, mc in enumerate(pa_questions, 1):
            w.p(f"Q{i}: Answer {mc.get('correct_option', '?')}", w.body)
            if mc.get("explanation"):
                w.p(f"Explanation: {mc['explanation']}", w.answer)
            w.gap(2)

    w.story.append(PageBreak())
    w.p("Key Concepts", w.h2)
    if k.get("terms"):
        w.p("Terms and Definitions", w.h3)
        rows = [["Term", "Definition"]] + [[Paragraph(escape(t["term"]), w.body), Paragraph(escape(t["definition"] + (f" Example: {t['example']}" if t.get("example") else "")), w.body)] for t in k["terms"]]
        tbl = Table(rows, colWidths=[4.5 * cm, 12.5 * cm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ]))
        w.story.append(tbl)
    if k.get("formulas"):
        w.p("Formulas", w.h3)
        for f in k["formulas"]:
            w.p(f"{f.get('name', '')}: {f.get('formula', '')}")
            if f.get("variables") or f.get("usage"):
                w.p(f"{f.get('variables', '')}  {f.get('usage', '')}".strip(), w.small)
    if k.get("key_concepts"):
        w.p("Core Concepts", w.h3)
        for c in k["key_concepts"]:
            w.p(f"{c.get('concept', '')} — {c.get('explanation', '')}")
    if k.get("examples"):
        w.p("Examples from the notes", w.h3)
        w.bullets(k["examples"])

    w.story.append(PageBreak())
    mcqs = q.get("mcqs", [])
    if mcqs:
        w.p("Multiple Choice Questions", w.h2)
        for i, mc in enumerate(mcqs, 1):
            w.p(f"Q{i}. {mc['question']}  [{mc.get('difficulty', '')}, {mc.get('topic', '')}]", w.body)
            for j, opt in enumerate(mc.get("options", [])):
                w.p(f"{LETTERS[j]}. {opt}", w.option)
            w.gap(3)
        w.p("MCQ Answer Key", w.h2)
        for i, mc in enumerate(mcqs, 1):
            w.p(f"Q{i}: {mc.get('correct_option', '?')}", w.body)
            if mc.get("explanation"):
                w.p(mc["explanation"], w.answer)

    sa = q.get("short_answer", [])
    if sa:
        w.p("Short-Answer Questions", w.h2)
        for i, item in enumerate(sa, 1):
            w.p(f"Q{i}. {item['question']}  [{item.get('difficulty', '')}, {item.get('topic', '')}]")
            if item.get("answer"):
                w.p(f"Answer: {item['answer']}", w.answer)
            if item.get("explanation"):
                w.p(f"Explanation: {item['explanation']}", w.small)
            w.gap(3)

    la = q.get("long_answer", [])
    if la:
        w.p("Long-Answer Questions", w.h2)
        for i, item in enumerate(la, 1):
            w.p(f"Q{i}. {item['question']}  [{item.get('difficulty', '')}, {item.get('topic', '')}]")
            if item.get("answer"):
                for para in str(item["answer"]).split("\n"):
                    if para.strip():
                        w.p(para, w.answer)
            if item.get("key_points"):
                w.p("Key points for marks:", w.small)
                w.bullets(item["key_points"])
            w.gap(3)

    if r:
        w.story.append(PageBreak())
        w.p("Quality Evaluation Report", w.h2)
        sc = r.get("scores", {})
        rows = [["Criterion", "Score /10"]] + [[k_.replace("_", " ").title(), str(v)] for k_, v in sc.items()]
        rows.append(["Overall", str(r.get("overall_score", ""))])
        tbl = Table(rows, colWidths=[8 * cm, 3 * cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ]))
        w.story.append(tbl)
        w.gap(6)
        w.p(f"Verdict: {r.get('verdict', '')}")
        if r.get("strengths"):
            w.p("Strengths", w.h3)
            w.bullets(r["strengths"])
        if r.get("issues"):
            w.p("Issues", w.h3)
            w.bullets([f"[{i.get('severity', '')}] {i.get('type', '')} at {i.get('location', '')}: {i.get('description', '')}" + (f" Fix: {i['suggested_fix']}" if i.get("suggested_fix") else "") for i in r["issues"]])
        if r.get("unsupported_claims"):
            w.p("Unsupported claims", w.h3)
            w.bullets(r["unsupported_claims"])
        if r.get("corrections"):
            w.p("Corrections applied", w.h3)
            w.bullets([f"{c.get('target_type', '')} {c.get('target_id', '')}.{c.get('field', '')}: {c.get('corrected_value', '')}" for c in r["corrections"]])
        if r.get("reviewer_notes"):
            w.p("Reviewer notes", w.h3)
            w.p(r["reviewer_notes"])

    doc.build(w.story)
    return buf.getvalue()


# ============================================================ DOCX
def build_docx(pack: dict) -> bytes:
    d, s, k, q, r, m = (pack.get(x) or {} for x in ("document", "summaries", "key_concepts", "questions", "review", "meta"))
    doc = DocxDocument()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    doc.add_heading(d.get("title", "Study Pack"), level=0)
    meta = doc.add_paragraph(
        f"Subject: {d.get('subject', '')}  |  Source: {pack.get('filename', '')}  |  Generated: {_fmt_date(pack.get('generated_at'))}\n"
        f"Prompt version {m.get('prompt_version', '')}  |  Model {m.get('model', '')}  |  Audience: {d.get('audience_level', '')}"
    )
    for run in meta.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    if s.get("overall_summary"):
        doc.add_heading("Overview", level=1)
        doc.add_paragraph(s["overall_summary"])

    doc.add_heading("Topic Outline", level=1)
    for t in d.get("main_topics", []):
        doc.add_heading(t.get("name", ""), level=2)
        if t.get("description"):
            doc.add_paragraph(t["description"])
        for sub in t.get("subtopics", []):
            doc.add_paragraph(sub, style="List Bullet")

    doc.add_heading("Topic-wise Summaries", level=1)
    for t in s.get("topics", []):
        doc.add_heading(t.get("topic", ""), level=2)
        doc.add_paragraph(t.get("summary", ""))
        if t.get("simple_explanation"):
            p = doc.add_paragraph()
            p.add_run("In simple terms: ").italic = True
            p.add_run(t["simple_explanation"])
        for label, key in (("Important points", "important_points"), ("Formulas", "formulas"), ("Examples", "examples")):
            if t.get(key):
                doc.add_paragraph(f"{label}:").runs[0].bold = True
                for item in t[key]:
                    doc.add_paragraph(item, style="List Bullet")

    pa = pack.get("practice_assignment") or {}
    pa_questions = pa.get("questions") or []
    if pa_questions:
        doc.add_page_break()
        doc.add_heading("Practice Assignment (Multiple-Choice Questions)", level=1)
        meta_p = doc.add_paragraph(
            f"Difficulty: {str(pa.get('difficulty', 'mixed')).title()}  |  Total MCQs: {len(pa_questions)}  |  Total Marks: {len(pa_questions)}\n"
            "Instructions: Select exactly one answer option (A, B, C, or D) for each question. All questions are grounded in the lecture notes."
        )
        for run in meta_p.runs:
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
        for i, mc in enumerate(pa_questions, 1):
            p = doc.add_paragraph()
            p.add_run(f"Q{i}. {mc['question']}").bold = True
            p.add_run(f"  [{mc.get('difficulty', '')}{', ' + mc['topic'] if mc.get('topic') else ''}]").italic = True
            for j, opt in enumerate(mc.get("options", [])):
                doc.add_paragraph(f"{LETTERS[j]}. {opt}")
        doc.add_heading("Practice Assignment Answer Key & Explanations", level=2)
        for i, mc in enumerate(pa_questions, 1):
            p = doc.add_paragraph()
            p.add_run(f"Q{i}: Answer {mc.get('correct_option', '?')}  ").bold = True
            if mc.get("explanation"):
                p.add_run(f"Explanation: {mc['explanation']}")

    doc.add_page_break()
    doc.add_heading("Key Concepts", level=1)
    if k.get("terms"):
        doc.add_heading("Terms and Definitions", level=2)
        table = doc.add_table(rows=1, cols=2)
        table.style = "Light Grid Accent 1"
        table.rows[0].cells[0].text, table.rows[0].cells[1].text = "Term", "Definition"
        for t in k["terms"]:
            row = table.add_row().cells
            row[0].text = t.get("term", "")
            row[1].text = t.get("definition", "") + (f" Example: {t['example']}" if t.get("example") else "")
    if k.get("formulas"):
        doc.add_heading("Formulas", level=2)
        for f in k["formulas"]:
            p = doc.add_paragraph()
            p.add_run(f"{f.get('name', '')}: ").bold = True
            p.add_run(f.get("formula", ""))
            if f.get("variables") or f.get("usage"):
                doc.add_paragraph(f"{f.get('variables', '')}  {f.get('usage', '')}".strip()).runs[0].font.size = Pt(9)
    if k.get("key_concepts"):
        doc.add_heading("Core Concepts", level=2)
        for c in k["key_concepts"]:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(f"{c.get('concept', '')}: ").bold = True
            p.add_run(c.get("explanation", ""))
    if k.get("examples"):
        doc.add_heading("Examples from the notes", level=2)
        for e in k["examples"]:
            doc.add_paragraph(e, style="List Bullet")

    doc.add_page_break()
    mcqs = q.get("mcqs", [])
    if mcqs:
        doc.add_heading("Multiple Choice Questions", level=1)
        for i, mc in enumerate(mcqs, 1):
            p = doc.add_paragraph()
            p.add_run(f"Q{i}. {mc['question']}").bold = True
            p.add_run(f"  [{mc.get('difficulty', '')}, {mc.get('topic', '')}]").italic = True
            for j, opt in enumerate(mc.get("options", [])):
                doc.add_paragraph(f"{LETTERS[j]}. {opt}")
        doc.add_heading("MCQ Answer Key", level=1)
        for i, mc in enumerate(mcqs, 1):
            p = doc.add_paragraph()
            p.add_run(f"Q{i}: {mc.get('correct_option', '?')}  ").bold = True
            p.add_run(mc.get("explanation", ""))

    sa = q.get("short_answer", [])
    if sa:
        doc.add_heading("Short-Answer Questions", level=1)
        for i, item in enumerate(sa, 1):
            p = doc.add_paragraph()
            p.add_run(f"Q{i}. {item['question']}").bold = True
            p.add_run(f"  [{item.get('difficulty', '')}, {item.get('topic', '')}]").italic = True
            if item.get("answer"):
                a = doc.add_paragraph()
                a.add_run("Answer: ").bold = True
                a.add_run(item["answer"])
            if item.get("explanation"):
                doc.add_paragraph(f"Explanation: {item['explanation']}").runs[0].font.size = Pt(9)

    la = q.get("long_answer", [])
    if la:
        doc.add_heading("Long-Answer Questions", level=1)
        for i, item in enumerate(la, 1):
            p = doc.add_paragraph()
            p.add_run(f"Q{i}. {item['question']}").bold = True
            p.add_run(f"  [{item.get('difficulty', '')}, {item.get('topic', '')}]").italic = True
            if item.get("answer"):
                a = doc.add_paragraph()
                a.add_run("Model answer: ").bold = True
                a.add_run(item["answer"])
            if item.get("key_points"):
                doc.add_paragraph("Key points for marks:").runs[0].bold = True
                for kp in item["key_points"]:
                    doc.add_paragraph(kp, style="List Bullet")

    if r:
        doc.add_page_break()
        doc.add_heading("Quality Evaluation Report", level=1)
        table = doc.add_table(rows=1, cols=2)
        table.style = "Light Grid Accent 1"
        table.rows[0].cells[0].text, table.rows[0].cells[1].text = "Criterion", "Score /10"
        for k_, v in r.get("scores", {}).items():
            row = table.add_row().cells
            row[0].text, row[1].text = k_.replace("_", " ").title(), str(v)
        row = table.add_row().cells
        row[0].text, row[1].text = "Overall", str(r.get("overall_score", ""))
        doc.add_paragraph(f"Verdict: {r.get('verdict', '')}")
        if r.get("strengths"):
            doc.add_heading("Strengths", level=2)
            for item in r["strengths"]:
                doc.add_paragraph(item, style="List Bullet")
        if r.get("issues"):
            doc.add_heading("Issues", level=2)
            for i in r["issues"]:
                text = f"[{i.get('severity', '')}] {i.get('type', '')} at {i.get('location', '')}: {i.get('description', '')}"
                if i.get("suggested_fix"):
                    text += f" Fix: {i['suggested_fix']}"
                doc.add_paragraph(text, style="List Bullet")
        if r.get("unsupported_claims"):
            doc.add_heading("Unsupported claims", level=2)
            for item in r["unsupported_claims"]:
                doc.add_paragraph(item, style="List Bullet")
        if r.get("corrections"):
            doc.add_heading("Corrections applied", level=2)
            for c in r["corrections"]:
                doc.add_paragraph(f"{c.get('target_type', '')} {c.get('target_id', '')}.{c.get('field', '')}: {c.get('corrected_value', '')}", style="List Bullet")
        if r.get("reviewer_notes"):
            doc.add_heading("Reviewer notes", level=2)
            doc.add_paragraph(r["reviewer_notes"])

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
