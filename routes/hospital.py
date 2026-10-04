from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from routes.auth import role_required
from models import db, Hospital, Procedure, HospitalProcedure, Appointment, Scan

hospital_bp = Blueprint("hospital", __name__, url_prefix="/hospital")

@hospital_bp.route("/dashboard")
@role_required("hospital")
def dashboard():
    hospital = current_user.hospital
    if not hospital:
        flash("Hospital profile not associated with this account.", "danger")
        return redirect(url_for("main.index"))

    pending_appts = Appointment.query.filter_by(hospital_id=hospital.id, status="pending").order_by(Appointment.appt_date.asc()).all()
    all_appts_count = Appointment.query.filter_by(hospital_id=hospital.id).count()
    procedures_count = HospitalProcedure.query.filter_by(hospital_id=hospital.id).count()

    return render_template(
        "hospital/dashboard.html",
        hospital=hospital,
        pending_appts=pending_appts,
        all_appts_count=all_appts_count,
        procedures_count=procedures_count
    )


@hospital_bp.route("/profile", methods=["GET", "POST"])
@role_required("hospital")
def profile():
    hospital = current_user.hospital
    if not hospital:
        abort(404)

    if request.method == "POST":
        hospital.name = request.form.get("name", "").strip() or hospital.name
        hospital.city = request.form.get("city", "").strip() or hospital.city
        hospital.address = request.form.get("address", "").strip()
        hospital.phone = request.form.get("phone", "").strip()
        hospital.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Hospital profile updated successfully.", "success")
        return redirect(url_for("hospital.profile"))

    return render_template("hospital/profile.html", hospital=hospital)


@hospital_bp.route("/procedures", methods=["GET", "POST"])
@role_required("hospital")
def procedures():
    hospital = current_user.hospital
    if not hospital:
        abort(404)

    # Server-side validation: Unapproved hospital cannot add or edit procedures
    if hospital.approved != 1:
        flash("Your hospital is awaiting admin approval. Adding or editing procedures is disabled until approved.", "warning")
        return render_template("hospital/procedures.html", hospital=hospital, procedures=[], all_master_procedures=[], disabled=True)

    if request.method == "POST":
        action = request.form.get("action", "add")
        if action == "add":
            procedure_id = request.form.get("procedure_id", type=int)
            price_min = request.form.get("price_min", type=int)
            price_max = request.form.get("price_max", type=int)

            if not procedure_id or price_min is None or price_max is None:
                flash("Procedure and valid price ranges are required.", "danger")
            elif price_min < 0 or price_max < price_min:
                flash("Invalid price range. Minimum price cannot exceed maximum price.", "danger")
            else:
                existing = HospitalProcedure.query.filter_by(hospital_id=hospital.id, procedure_id=procedure_id).first()
                if existing:
                    existing.price_min = price_min
                    existing.price_max = price_max
                    flash("Procedure price updated successfully.", "success")
                else:
                    new_hp = HospitalProcedure(
                        hospital_id=hospital.id,
                        procedure_id=procedure_id,
                        price_min=price_min,
                        price_max=price_max
                    )
                    db.session.add(new_hp)
                    flash("Procedure added to hospital offering.", "success")
                db.session.commit()
        elif action == "delete":
            hp_id = request.form.get("hospital_procedure_id", type=int)
            hp = HospitalProcedure.query.filter_by(id=hp_id, hospital_id=hospital.id).first()
            if hp:
                db.session.delete(hp)
                db.session.commit()
                flash("Procedure removed from your offerings.", "info")

        return redirect(url_for("hospital.procedures"))

    hospital_procedures = HospitalProcedure.query.filter_by(hospital_id=hospital.id).join(Procedure).order_by(Procedure.name).all()
    existing_proc_ids = [hp.procedure_id for hp in hospital_procedures]
    available_master_procedures = Procedure.query.filter(~Procedure.id.in_(existing_proc_ids) if existing_proc_ids else True).order_by(Procedure.name).all()

    return render_template(
        "hospital/procedures.html",
        hospital=hospital,
        procedures=hospital_procedures,
        all_master_procedures=available_master_procedures,
        disabled=False
    )


@hospital_bp.route("/appointments")
@role_required("hospital")
def appointments():
    hospital = current_user.hospital
    if not hospital:
        abort(404)
    appts = Appointment.query.filter_by(hospital_id=hospital.id).order_by(Appointment.appt_date.desc()).all()
    return render_template("hospital/appointments.html", appointments=appts, hospital=hospital)


@hospital_bp.route("/appointments/<int:appointment_id>/<action>", methods=["POST"])
@role_required("hospital")
def update_appointment(appointment_id, action):
    hospital = current_user.hospital
    if not hospital:
        abort(404)

    appt = Appointment.query.filter_by(id=appointment_id, hospital_id=hospital.id).first_or_404()
    if action == "accept":
        appt.status = "accepted"
        flash("Appointment has been accepted.", "success")
    elif action == "reject":
        appt.status = "rejected"
        flash("Appointment has been rejected.", "info")
    db.session.commit()
    return redirect(url_for("hospital.appointments"))


@hospital_bp.route("/scan/<int:scan_id>")
@role_required("hospital")
def view_scan(scan_id):
    hospital = current_user.hospital
    if not hospital:
        abort(404)

    # Security check: Hospitals can see a scan only if it is linked to one of their appointments
    linked_appointment = Appointment.query.filter_by(hospital_id=hospital.id, scan_id=scan_id).first()
    if not linked_appointment:
        abort(403)

    scan = Scan.query.get_or_404(scan_id)
    return render_template("patient/scan_result.html", scan=scan, is_hospital_view=True)
