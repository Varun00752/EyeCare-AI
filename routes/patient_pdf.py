import os
import io
from flask import current_app, send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from ml.predict import GRADE_ADVICE

def generate_scan_pdf(scan):
    """
    Generate a clinical PDF report for a given Scan record using ReportLab.
    Returns Flask send_file response.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0d9488"),
        alignment=1  # Center
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=1  # Center
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f766e"),
        spaceBefore=8,
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )

    disclaimer_style = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e40af"),
        alignment=1
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("EyeCare AI &bull; Clinical Screening Report", title_style))
    story.append(Paragraph("Diabetic Retinopathy Automated Deep Learning Assessment", subtitle_style))
    story.append(Spacer(1, 10))

    # Demo Mode Notice (only if scan was recorded in demo mode)
    if getattr(scan, "is_demo", False):
        demo_p = Paragraph(
            "<b>DEMO MODE REPORT:</b> Generated using educational demo mode simulation for academic presentation.",
            ParagraphStyle("DemoStyle", fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#92400e"), alignment=1)
        )
        demo_table = Table([[demo_p]], colWidths=[540])
        demo_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d97706")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(demo_table)
        story.append(Spacer(1, 10))

    # 2. Patient & Scan Metadata Table
    patient = scan.patient
    user = patient.user if patient else None

    meta_data = [
        [
            Paragraph("<b>Patient Name:</b>", normal_style),
            Paragraph(user.name if user else "Unknown", normal_style),
            Paragraph("<b>Scan Reference ID:</b>", normal_style),
            Paragraph(f"#{scan.id}", normal_style)
        ],
        [
            Paragraph("<b>Age / Gender:</b>", normal_style),
            Paragraph(f"{patient.age or 'N/A'} yrs / {patient.gender or 'N/A'}", normal_style),
            Paragraph("<b>Date & Time:</b>", normal_style),
            Paragraph(scan.created_at.strftime("%d %b %Y, %I:%M %p"), normal_style)
        ],
        [
            Paragraph("<b>Diabetes History:</b>", normal_style),
            Paragraph(f"{patient.diabetes_years or 0} Years", normal_style),
            Paragraph("<b>Screening Type:</b>", normal_style),
            Paragraph("Digital Retinal Fundus (DR)", normal_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[120, 150, 130, 140])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 3. Retinal Images (Original and Grad-CAM Heatmap)
    story.append(Paragraph("<b>Retinal Imagery & Attention Heatmap</b>", section_heading))
    
    upload_full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], scan.image_path)
    heatmap_full_path = os.path.join(current_app.config["HEATMAP_FOLDER"], scan.heatmap_path) if scan.heatmap_path else None

    img_elements = []
    
    # Check original image exists
    orig_img_flowable = Paragraph("Original image missing", normal_style)
    if os.path.exists(upload_full_path):
        orig_img_flowable = RLImage(upload_full_path, width=220, height=180)

    # Check heatmap image exists
    heat_img_flowable = Paragraph("Heatmap missing", normal_style)
    if heatmap_full_path and os.path.exists(heatmap_full_path):
        heat_img_flowable = RLImage(heatmap_full_path, width=220, height=180)

    image_table_data = [
        [
            Paragraph("<b>Original Retinal Fundus Photo</b>", subtitle_style),
            Paragraph("<b>Grad-CAM Explainability Heatmap</b>", subtitle_style)
        ],
        [
            orig_img_flowable,
            heat_img_flowable
        ]
    ]

    img_table = Table(image_table_data, colWidths=[270, 270])
    img_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(img_table)
    story.append(Spacer(1, 12))

    # 4. AI Diagnosis & Severity Assessment
    story.append(Paragraph("<b>AI Screening Findings & Recommendations</b>", section_heading))

    # Grade coloring
    grade_colors = {
        0: colors.HexColor("#10b981"),
        1: colors.HexColor("#06b6d4"),
        2: colors.HexColor("#f59e0b"),
        3: colors.HexColor("#ea580c"),
        4: colors.HexColor("#ef4444")
    }
    g_color = grade_colors.get(scan.predicted_grade, colors.HexColor("#0d9488"))

    results_data = [
        [
            Paragraph("<b>Diabetic Retinopathy Grade:</b>", normal_style),
            Paragraph(f"<font color='{g_color.hexval()}'><b>Grade {scan.predicted_grade} &bull; {scan.predicted_label}</b></font>", normal_style)
        ],
        [
            Paragraph("<b>Inference Confidence Score:</b>", normal_style),
            Paragraph(f"<b>{(scan.confidence or 0) * 100:.1f}%</b>", normal_style)
        ],
        [
            Paragraph("<b>Recommended Clinical Action:</b>", normal_style),
            Paragraph(GRADE_ADVICE.get(scan.predicted_grade, "Consult ophthalmologist."), normal_style)
        ]
    ]

    results_table = Table(results_data, colWidths=[180, 360])
    results_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 14))

    # 5. Mandatory Medical Disclaimer Box
    disclaimer_text = (
        "<b>MANDATORY MEDICAL DISCLAIMER:</b><br/>"
        "This is an AI screening aid, not a medical diagnosis. Please consult a qualified ophthalmologist. "
        "Automated grading is intended for preliminary screening assistance and triage in educational/demo settings. "
        "Clinical intervention or treatment decisions must be made solely by certified ophthalmic physicians."
    )
    disclaimer_p = Paragraph(disclaimer_text, disclaimer_style)
    disclaimer_table = Table([[disclaimer_p]], colWidths=[540])
    disclaimer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3b82f6")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(disclaimer_table)

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    filename = f"EyeCare_AI_Report_Scan_{scan.id}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )
