from fpdf import FPDF
import tempfile
import datetime


def generate_pdf_report(project_name, kpi_data, geometry_data):
    """Generates a professional PDF report for field engineers."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Blast Design Report: {project_name}", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    for key, value in kpi_data.items():
        pdf.cell(0, 8, f"{key}: {value}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "2. Drill Pattern Geometry", ln=True)
    pdf.set_font("Arial", "", 12)
    for key, value in geometry_data.items():
        pdf.cell(0, 8, f"{key}: {value}", ln=True)

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name
