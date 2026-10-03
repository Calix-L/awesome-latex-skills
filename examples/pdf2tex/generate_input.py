#!/usr/bin/env python3
"""Regenerate the synthetic example PDF (optional reportlab>=4,<5 dependency)."""
import argparse
from io import BytesIO
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from reportlab.pdfgen import canvas
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(540, 500), invariant=True)
    pdf.setTitle("Synthetic PDF recovery case")
    pdf.setAuthor("awesome-latex-skills maintained examples")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(45, 450, "Synthetic reconstruction case")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(45, 415, "Abstract claim: accuracy is 92.3%.")
    pdf.drawString(45, 395, "The weight is 0.5. All values are illustrative.")
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(45, 352, "Method")
    pdf.drawCentredString(267, 352, "Score (%)")
    pdf.drawString(395, 352, "Note")
    pdf.line(205, 343, 335, 343)
    pdf.drawString(205, 325, "Mean")
    pdf.drawString(290, 325, "Spread")
    pdf.line(45, 365, 495, 365)
    pdf.line(45, 314, 495, 314)
    pdf.setFont("Helvetica", 11)
    for y, values in ((292, ("A&B", "76.10", "0.30", "Measured")),
                      (268, ("Ours", "78.20", "0.40", "Measured")),
                      (244, ("Variant", "--", "", "Not measured"))):
        for x, value in zip((45, 205, 290, 395), values):
            pdf.drawString(x, y, value)
    pdf.line(45, 231, 495, 231)
    pdf.drawString(45, 206, "Spread is blank for Variant; no value was supplied.")
    pdf.drawString(45, 155, "Vector diagram: input -> scorer -> output")
    for x, label in ((65, "Input"), (230, "Scorer"), (395, "Output")):
        pdf.rect(x, 90, 80, 35)
        pdf.drawCentredString(x + 40, 103, label)
    pdf.line(145, 107, 230, 107)
    pdf.line(310, 107, 395, 107)
    pdf.drawString(45, 35, "Page 1 / synthetic example")
    pdf.showPage()
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(45, 450, "Continuation")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(45, 410, "The observation applies only to the tested setting.")
    pdf.drawString(45, 386, "Original citation marker [42]; its entry was not supplied.")
    pdf.drawString(45, 35, "Page 2 / synthetic example")
    pdf.save()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        output.write(buffer.getvalue())


if __name__ == "__main__":
    main()
