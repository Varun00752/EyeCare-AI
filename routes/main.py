from flask import Blueprint, render_template, request, abort
from models import db, Hospital, Procedure, HospitalProcedure

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/hospitals")
def hospitals():
    city = request.args.get("city", "").strip()
    procedure_id = request.args.get("procedure", type=int)

    # Only show approved hospitals
    query = Hospital.query.filter_by(approved=1)

    if city:
        query = query.filter(Hospital.city.ilike(f"%{city}%"))

    if procedure_id:
        query = query.join(HospitalProcedure).filter(HospitalProcedure.procedure_id == procedure_id)

    hospital_list = query.all()

    # Get distinct cities and all available procedures for filter dropdowns
    available_cities = [c[0] for c in db.session.query(Hospital.city).filter(Hospital.approved == 1).distinct().all()]
    all_procedures = Procedure.query.order_by(Procedure.name).all()

    return render_template(
        "hospitals.html",
        hospitals=hospital_list,
        cities=available_cities,
        procedures=all_procedures,
        selected_city=city,
        selected_procedure=procedure_id
    )


@main_bp.route("/hospitals/<int:hospital_id>")
def hospital_detail(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    if hospital.approved != 1:
        # Only allow admin or the hospital owner to preview unapproved hospital page
        from flask_login import current_user
        if not (current_user.is_authenticated and (current_user.role == "admin" or (current_user.role == "hospital" and current_user.hospital and current_user.hospital.id == hospital.id))):
            abort(404)

    # Fetch procedures offered by this hospital
    procedures_offered = HospitalProcedure.query.filter_by(hospital_id=hospital.id).join(Procedure).order_by(Procedure.name).all()

    return render_template(
        "hospital_detail.html",
        hospital=hospital,
        procedures_offered=procedures_offered
    )


@main_bp.route("/compare")
def compare():
    procedure_id = request.args.get("procedure", type=int)
    city = request.args.get("city", "").strip()

    all_procedures = Procedure.query.order_by(Procedure.name).all()
    available_cities = [c[0] for c in db.session.query(Hospital.city).filter(Hospital.approved == 1).distinct().all()]

    comparison_results = []
    selected_procedure_obj = None

    if procedure_id:
        selected_procedure_obj = Procedure.query.get(procedure_id)
        # Query only approved hospitals offering this procedure
        query = HospitalProcedure.query.join(Hospital).filter(
            Hospital.approved == 1,
            HospitalProcedure.procedure_id == procedure_id
        )

        if city:
            query = query.filter(Hospital.city.ilike(f"%{city}%"))

        # Sort by minimum price ascending so cheapest comes first
        comparison_results = query.order_by(HospitalProcedure.price_min.asc()).all()

    return render_template(
        "compare.html",
        procedures=all_procedures,
        cities=available_cities,
        selected_procedure=procedure_id,
        selected_procedure_obj=selected_procedure_obj,
        selected_city=city,
        results=comparison_results
    )
