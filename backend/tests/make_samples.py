"""Generates sample PDF / PPTX / DOCX / TXT files in tests/samples for testing."""
from pathlib import Path

import fitz
from docx import Document
from pptx import Presentation
from pptx.util import Inches

SAMPLES = Path(__file__).parent / "samples"
SAMPLES.mkdir(exist_ok=True)

LECTURE = [
    ("Introduction to Machine Learning",
     "Machine learning is the study of algorithms that improve through experience. "
     "Supervised learning uses labelled data; unsupervised learning finds structure in unlabelled data."),
    ("Linear Regression",
     "Linear regression models the relationship y = w*x + b. "
     "The loss function is Mean Squared Error: MSE = (1/n) * sum((y_i - y_hat_i)^2). "
     "Gradient descent updates w := w - alpha * dL/dw."),
    ("Overfitting and Regularisation",
     "Overfitting occurs when a model memorises training data. "
     "L2 regularisation adds lambda * ||w||^2 to the loss to penalise large weights."),
]


def make_pdf():
    doc = fitz.open()
    for title, body in LECTURE:
        page = doc.new_page()
        page.insert_text((72, 72), title, fontsize=16)
        page.insert_textbox(fitz.Rect(72, 100, 540, 700), body, fontsize=11)
    doc.save(SAMPLES / "lecture.pdf")
    doc.close()


def make_pptx():
    prs = Presentation()
    for title, body in LECTURE:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = title
        slide.placeholders[1].text = body
        slide.notes_slide.notes_text_frame.text = f"Notes for {title}"
    # a slide with a table
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Comparison Table"
    table = slide.shapes.add_table(2, 2, Inches(1), Inches(2), Inches(6), Inches(1)).table
    table.cell(0, 0).text = "Algorithm"
    table.cell(0, 1).text = "Type"
    table.cell(1, 0).text = "K-Means"
    table.cell(1, 1).text = "Unsupervised"
    prs.save(SAMPLES / "lecture.pptx")


def make_docx():
    doc = Document()
    doc.add_heading("Machine Learning Lecture Notes", level=0)
    for title, body in LECTURE:
        doc.add_heading(title, level=1)
        doc.add_paragraph(body)
    t = doc.add_table(rows=2, cols=2)
    t.cell(0, 0).text = "Term"
    t.cell(0, 1).text = "Definition"
    t.cell(1, 0).text = "Epoch"
    t.cell(1, 1).text = "One full pass over the training data"
    doc.save(SAMPLES / "lecture.docx")


def make_txt():
    lines = []
    for title, body in LECTURE:
        lines += [title.upper(), body, ""]
    (SAMPLES / "lecture.txt").write_text("\n".join(lines), encoding="utf-8")
    (SAMPLES / "empty.txt").write_text("   \n  ", encoding="utf-8")
    (SAMPLES / "fake.pdf").write_text("this is not a pdf", encoding="utf-8")


if __name__ == "__main__":
    make_pdf()
    make_pptx()
    make_docx()
    make_txt()
    print("Samples written to", SAMPLES)
