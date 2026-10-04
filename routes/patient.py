import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from routes.auth import role_required
from models import db, User, Patient, Hospital, Procedure, HospitalProcedure, Scan, Appointment
from ml.predict import predict_dr, GRADE_ADVICE

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


@patient_bp.route("/dashboard")
@role_required("patient")
def dashboard():
    patient = current_user.patient
    recent_scans = []
    upcoming_appts = []
    if patient:
        recent_scans = Scan.query.filter_by(patient_id=patient.id).order_by(Scan.created_at.desc()).limit(5).all()
        upcoming_appts = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.appt_date.asc()).all()

    return render_template(
        "patient/dashboard.html",
        recent_scans=recent_scans,
        upcoming_appts=upcoming_appts
    )


@patient_bp.route("/scan/new", methods=["GET", "POST"])
@role_required("patient")
def scan_new():
    if request.method == "POST":
        if "image" not in request.files:
            flash("No file part provided.", "danger")
            return redirect(request.url)

        file = request.files["image"]
        if file.filename == "":
            flash("No image selected for upload.", "danger")
            return redirect(request.url)

        # Server-side validation: file extension
        if not allowed_file(file.filename):
            flash("Invalid file format. Allowed formats: PNG, JPG, JPEG.", "danger")
            return redirect(request.url)

        # Server-side validation: 5 MB size limit
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > current_app.config["MAX_CONTENT_LENGTH"]:
            flash(f"File too large ({(file_size / (1024*1024)):.2f} MB). Maximum allowed size is 5 MB.", "danger")
            return redirect(request.url)

        # Secure unique filename
        ext = file.filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(save_path)

        # Run AI prediction via ML module
        try:
            prediction = predict_dr(save_path, output_dir=current_app.config["HEATMAP_FOLDER"])
        except ValueError as e:
            # Clean up uploaded file if invalid image
            if os.path.exists(save_path):
                os.remove(save_path)
            flash(f"Image validation failed: {str(e)}", "danger")
            return redirect(request.url)
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            flash(f"An unexpected error occurred during image analysis: {str(e)}", "danger")
            return redirect(request.url)

        # Save scan to database
        scan = Scan(
            patient_id=current_user.patient.id,
            scan_type=request.form.get("scan_type", "dr"),
            image_path=unique_filename,
            heatmap_path=prediction["heatmap_path"],
            predicted_grade=prediction["grade"],
            predicted_label=prediction["label"],
            confidence=prediction["confidence"],
            is_demo=prediction.get("demo", False)
        )
        db.session.add(scan)
        db.session.commit()

        if prediction.get("warning"):
            flash(prediction["warning"], "warning")

        flash("Scan analyzed successfully!", "success")
        return redirect(url_for("patient.scan_result", scan_id=scan.id))

    from ml.predict import is_demo_mode
    return render_template("patient/scan_new.html", is_demo=is_demo_mode())


@patient_bp.route("/scan/<int:scan_id>")
@role_required("patient")
def scan_result(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    # Security: A patient can only see their own scans
    if scan.patient.user_id != current_user.id:
        abort(403)

    advice = GRADE_ADVICE.get(scan.predicted_grade, "Please consult an ophthalmologist.")
    
    # If grade >= 2, recommend approved hospitals offering DR care
    recommended_hospitals = []
    if scan.predicted_grade >= 2:
        # Match hospitals with procedures related to Retinal laser, Anti-VEGF, or DR
        recommended_hospitals = Hospital.query.filter_by(approved=1).join(HospitalProcedure).join(Procedure).filter(
            Procedure.name.in_([
                "Diabetic Retinopathy Screening",
                "Retinal Laser Photocoagulation",
                "Anti-VEGF Injection",
                "Vitrectomy"
            ])
        ).distinct().all()

    return render_template(
        "patient/scan_result.html",
        scan=scan,
        advice=advice,
        recommended_hospitals=recommended_hospitals,
        is_demo=getattr(scan, "is_demo", False),
        is_hospital_view=False
    )


@patient_bp.route("/scans")
@role_required("patient")
def scans():
    patient = current_user.patient
    all_scans = Scan.query.filter_by(patient_id=patient.id).order_by(Scan.created_at.desc()).all() if patient else []
    return render_template("patient/scans.html", scans=all_scans)


@patient_bp.route("/scan/<int:scan_id>/pdf")
@role_required("patient")
def download_pdf(scan_id):
    # Implemented in Task 9
    from routes.patient_pdf import generate_scan_pdf
    scan = Scan.query.get_or_404(scan_id)
    if scan.patient.user_id != current_user.id:
        abort(403)
    return generate_scan_pdf(scan)


@patient_bp.route("/book/<int:hospital_id>", methods=["GET", "POST"])
@role_required("patient")
def book_appointment(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    if hospital.approved != 1:
        flash("Cannot book an appointment with an unapproved hospital.", "warning")
        return redirect(url_for("main.hospitals"))

    patient = current_user.patient
    if request.method == "POST":
        procedure_id = request.form.get("procedure_id", type=int)
        appt_date_str = request.form.get("appt_date", "").strip()
        scan_id = request.form.get("scan_id", type=int)
        notes = request.form.get("notes", "").strip()

        if not procedure_id or not appt_date_str:
            flash("Procedure and date are required.", "danger")
            return redirect(request.url)

        # Server-side validation: future-date rule
        try:
            appt_date = datetime.strptime(appt_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(request.url)

        if appt_date <= datetime.utcnow().date():
            flash("Appointment date must be in the future.", "danger")
            return redirect(request.url)

        # Validate scan belongs to patient if provided
        if scan_id:
            s = Scan.query.filter_by(id=scan_id, patient_id=patient.id).first()
            if not s:
                scan_id = None

        new_appt = Appointment(
            patient_id=patient.id,
            hospital_id=hospital.id,
            procedure_id=procedure_id,
            scan_id=scan_id,
            appt_date=appt_date,
            notes=notes,
            status="pending"
        )
        db.session.add(new_appt)
        db.session.commit()

        flash(f"Appointment request submitted to {hospital.name}. Awaiting hospital confirmation.", "success")
        return redirect(url_for("patient.appointments"))

    procedures_offered = HospitalProcedure.query.filter_by(hospital_id=hospital.id).join(Procedure).all()
    patient_scans = Scan.query.filter_by(patient_id=patient.id).order_by(Scan.created_at.desc()).all()
    preselected_proc = request.args.get("procedure", type=int)
    preselected_scan = request.args.get("scan_id", type=int)

    return render_template(
        "patient/book.html",
        hospital=hospital,
        procedures=procedures_offered,
        scans=patient_scans,
        preselected_proc=preselected_proc,
        preselected_scan=preselected_scan
    )


@patient_bp.route("/appointments")
@role_required("patient")
def appointments():
    patient = current_user.patient
    appts = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.appt_date.desc()).all() if patient else []
    return render_template("patient/appointments.html", appointments=appts)


@patient_bp.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
@role_required("patient")
def cancel_appointment(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.patient.user_id != current_user.id:
        abort(403)
    # Server-side validation: Only pending appointments can be cancelled
    if appt.status != "pending":
        flash("Only pending appointments can be cancelled.", "warning")
        return redirect(url_for("patient.appointments"))
    appt.status = "cancelled"
    db.session.commit()
    flash("Appointment cancelled successfully.", "info")
    return redirect(url_for("patient.appointments"))
