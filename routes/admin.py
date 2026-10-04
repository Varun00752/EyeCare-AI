from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from routes.auth import role_required
from models import db, User, Patient, Hospital, Procedure, HospitalProcedure, Scan, Appointment

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    total_users = User.query.count()
    total_patients = Patient.query.count()
    total_hospitals = Hospital.query.count()
    approved_hospitals = Hospital.query.filter_by(approved=1).count()
    pending_hospitals = Hospital.query.filter_by(approved=0).count()
    total_scans = Scan.query.count()
    total_appointments = Appointment.query.count()

    grade_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    scans = Scan.query.filter_by(scan_type="dr").all()
    for s in scans:
        if s.predicted_grade in grade_counts:
            grade_counts[s.predicted_grade] += 1

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_patients=total_patients,
        total_hospitals=total_hospitals,
        approved_hospitals=approved_hospitals,
        pending_hospitals=pending_hospitals,
        total_scans=total_scans,
        total_appointments=total_appointments,
        grade_counts=grade_counts
    )


@admin_bp.route("/hospitals")
@role_required("admin")
def hospitals():
    pending_hospitals = Hospital.query.filter_by(approved=0).order_by(Hospital.id.desc()).all()
    approved_hospitals = Hospital.query.filter_by(approved=1).order_by(Hospital.name).all()
    rejected_hospitals = Hospital.query.filter_by(approved=2).order_by(Hospital.id.desc()).all()

    return render_template(
        "admin/hospitals.html",
        pending_hospitals=pending_hospitals,
        approved_hospitals=approved_hospitals,
        rejected_hospitals=rejected_hospitals
    )


@admin_bp.route("/hospitals/<int:hospital_id>/<action>", methods=["POST"])
@role_required("admin")
def decide_hospital(hospital_id, action):
    hospital = Hospital.query.get_or_404(hospital_id)
    if action == "approve":
        hospital.approved = 1
        flash(f"Hospital '{hospital.name}' has been approved and is now live.", "success")
    elif action == "reject":
        hospital.approved = 2
        flash(f"Hospital '{hospital.name}' registration was rejected.", "warning")
    db.session.commit()
    return redirect(url_for("admin.hospitals"))


@admin_bp.route("/procedures", methods=["GET", "POST"])
@role_required("admin")
def procedures():
    if request.method == "POST":
        action = request.form.get("action", "add")
        if action == "add":
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()

            if not name:
                flash("Procedure name is required.", "danger")
            elif Procedure.query.filter_by(name=name).first():
                flash("Procedure with this name already exists.", "danger")
            else:
                proc = Procedure(name=name, category=category, description=description)
                db.session.add(proc)
                db.session.commit()
                flash(f"Procedure '{name}' added successfully.", "success")
        elif action == "delete":
            proc_id = request.form.get("procedure_id", type=int)
            proc = Procedure.query.get(proc_id)
            if proc:
                db.session.delete(proc)
                db.session.commit()
                flash("Procedure deleted.", "info")

        return redirect(url_for("admin.procedures"))

    all_procedures = Procedure.query.order_by(Procedure.category, Procedure.name).all()
    return render_template("admin/procedures.html", procedures=all_procedures)
