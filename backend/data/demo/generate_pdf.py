from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

demo_dir = Path(__file__).resolve().parent
txt_file = demo_dir / "Bali_Travel_Guide.txt"
pdf_file = demo_dir / "Bali_Travel_Guide.pdf"

def generate_pdf():
    with open(txt_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by pages indicator
    sections = content.split("--- Page ")
    c = canvas.Canvas(str(pdf_file), pagesize=letter)
    width, height = letter

    # Title cover on first page
    first_section = sections[0].strip()
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawString(54, height - 60, "TripQuery AI - Travel Destination Guide")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#0284C7"))
    c.drawString(54, height - 85, "Bali: The Island of the Gods")

    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.setLineWidth(1)
    c.line(54, height - 95, width - 54, height - 95)

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#334155"))

    # Render each page section onto a separate PDF page
    for i, sec in enumerate(sections[1:], 1):
        if i > 1:
            c.showPage()

        # Header on each page
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#0369A1"))
        header_title = sec.split("---")[0].strip()
        c.drawString(54, height - 50, f"Bali Travel Guide - {header_title}")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawRightString(width - 54, height - 50, f"Page {i} of {len(sections)-1}")

        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.line(54, height - 60, width - 54, height - 60)

        # Body text
        body = sec.split("---", 1)[1].strip() if "---" in sec else sec
        y = height - 85
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#1E293B"))

        for line in body.split("\n"):
            line = line.strip()
            if not line:
                y -= 10
                continue
            
            # Simple text wrap at ~90 characters
            words = line.split(" ")
            curr_line = ""
            for w in words:
                if len(curr_line + " " + w) > 85:
                    c.drawString(54, y, curr_line)
                    y -= 14
                    curr_line = w
                else:
                    curr_line = curr_line + " " + w if curr_line else w
            if curr_line:
                c.drawString(54, y, curr_line)
                y -= 14

            if y < 60:
                c.showPage()
                y = height - 60

    c.save()
    print(f"Generated {pdf_file.name} successfully at {pdf_file}!")

if __name__ == "__main__":
    generate_pdf()
