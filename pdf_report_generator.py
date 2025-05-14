
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from datetime import datetime

def generate_pdf(trait_results, score, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("DairyBioControl Report", styles['Title'])
    lab_name = Paragraph("Presented by LaPointes Research Group", styles['Normal'])
    timestamp = Paragraph(datetime.now().strftime("Generated on %Y-%m-%d at %H:%M:%S"), styles['Normal'])
    score_text = Paragraph(f"<b>Biocontrol Score:</b> {score}%", styles['Normal'])

    elements.extend([title, lab_name, Spacer(1, 12), timestamp, Spacer(1, 12), score_text, Spacer(1, 24)])

    table_data = [["Category", "Trait", "Hits", "Status"]]
    for row in trait_results:
        table_data.append([row["category"], row["trait"], str(row.get("hits", 0)), row["status"]])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))
    footer = Paragraph("© 2025 DairyBioControl | LaPointes Research Group", styles["Normal"])
    elements.append(footer)

    doc.build(elements)
