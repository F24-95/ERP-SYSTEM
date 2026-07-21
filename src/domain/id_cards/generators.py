import os
from datetime import date
from typing import Any


def generate_qr_image(data: str, output_path: str) -> str:
    """Generate a QR image. Uses `qrcode` if available; otherwise a
    placeholder image. Ported verbatim from legacy `id_card_qr_generator.py`.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        return output_path
    except Exception:
        from PIL import Image

        img = Image.new("RGB", (512, 512), "white")
        img.save(output_path)
        return output_path


def render_student_id_pdf(card: dict[str, Any], output_pdf_path: str) -> str:
    """Render a front-side student ID card as a PDF. Ported verbatim from
    legacy `id_card_pdf_generator.py`, including its reportlab-or-placeholder
    fallback behavior.
    """
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(output_pdf_path, pagesize=A4)
        width, height = A4

        c.rect(10, 10, width - 20, height - 20)
        y = height - 30

        logo_path = card.get("institute_logo_path")
        if logo_path and os.path.exists(logo_path):
            img = ImageReader(logo_path)
            c.drawImage(
                img,
                20,
                y - 35,
                width=35 * mm / 1.0,
                height=35 * mm / 1.0,
                mask="auto",
            )
        c.setFont("Helvetica-Bold", 14)
        c.drawString(70, y - 10, str(card.get("institute_name", "")))

        y -= 55
        c.setFont("Helvetica", 10)
        c.drawString(20, y, f"Contact: {card.get('institute_contact_number', '')}")
        y -= 16
        c.drawString(
            20,
            y,
            f"Academic Session: {card.get('academic_session_label', '')}",
        )

        photo_path = card.get("student_photo_path")
        if photo_path and os.path.exists(photo_path):
            c.drawImage(
                ImageReader(photo_path),
                width - 90,
                y - 120,
                60,
                80,
                mask="auto",
            )

        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20, y, "Student Details")
        y -= 18

        c.setFont("Helvetica", 10)
        c.drawString(20, y, f"Name: {card.get('student_name', '')}")
        y -= 14
        c.drawString(20, y, f"Parent Name: {card.get('parent_name', '')}")
        y -= 14
        c.drawString(20, y, f"Class: {card.get('class_display_name', '')}")
        y -= 14

        doj: date = card.get("date_of_joining")
        valid_till: date = card.get("valid_till")
        c.drawString(20, y, f"DOJ: {doj.isoformat() if isinstance(doj, date) else ''}")
        y -= 14
        c.drawString(
            20,
            y,
            f"Valid Till: {valid_till.isoformat() if isinstance(valid_till, date) else ''}",
        )
        y -= 14

        c.setFont("Helvetica-Bold", 12)
        c.drawString(20, y, f"Student ID: {card.get('student_id_business', '')}")

        qr_path = card.get("qr_code_path")
        if qr_path and os.path.exists(qr_path):
            c.drawImage(ImageReader(qr_path), width - 110, 55, 80, 80, mask="auto")

        c.setFont("Helvetica", 9)
        c.drawString(width - 110, 40, "Scan to verify")

        c.showPage()
        c.save()
        return output_pdf_path

    except Exception:
        with open(output_pdf_path, "wb") as f:
            f.write(("Student ID Card placeholder\n" + str(card)).encode("utf-8"))
        return output_pdf_path


def load_institute_asset():
    """Return institute logo path, name, and contact number. Ported verbatim
    from legacy `institute_assets.py` — this project also has no dedicated
    institute-settings table, so the same env-var + optional-file-on-disk
    approach is preserved.
    """
    institute_name = os.environ.get("INSTITUTE_NAME", "SCHOOL-ERP Institute")
    institute_contact = os.environ.get("INSTITUTE_CONTACT", "0000000000")

    logo_candidates = [
        os.path.join("uploads", "institute", "logo.png"),
        os.path.join("uploads", "institute_logo.png"),
    ]
    logo_path = None
    for p in logo_candidates:
        if os.path.exists(p):
            logo_path = p
            break

    return logo_path, institute_name, institute_contact
