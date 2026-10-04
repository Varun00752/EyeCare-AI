import os
import uuid
from flask import Blueprint, request, jsonify, current_app, url_for
from flask_login import current_user
from models import db, User, Patient, Hospital, Procedure, HospitalProcedure, Scan, Appointment
from ml.predict import predict_dr

api_bp = Blueprint("api", __name__, url_prefix="/api")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

@api_bp.route("/predict", methods=["POST"])
def api_predict():
    # Only logged-in patient
    if not current_user.is_authenticated or current_user.role != "patient":
        return jsonify({"error": "Unauthorized. Patient login required."}), 401

    if "image" not in request.files:
        return jsonify({"error": "No image file provided in request."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid format. Allowed: PNG, JPG, JPEG."}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > current_app.config["MAX_CONTENT_LENGTH"]:
        return jsonify({"error": "File size exceeds 5 MB limit."}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(save_path)

    try:
        prediction = predict_dr(save_path, output_dir=current_app.config["HEATMAP_FOLDER"])
    except ValueError as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"error": "Prediction failed", "details": str(e)}), 500

    scan = Scan(
        patient_id=current_user.patient.id,
        scan_type="dr",
        image_path=unique_filename,
        heatmap_path=prediction["heatmap_path"],
        predicted_grade=prediction["grade"],
        predicted_label=prediction["label"],
        confidence=prediction["confidence"]
    )
    db.session.add(scan)
    db.session.commit()

    return jsonify({
        "scan_id": scan.id,
        "grade": prediction["grade"],
        "label": prediction["label"],
        "confidence": prediction["confidence"],
        "heatmap_url": url_for("static", filename="heatmaps/" + prediction["heatmap_path"]),
        "demo": prediction["demo"]
    }), 200


@api_bp.route("/hospitals", methods=["GET"])
def api_hospitals():
    city = request.args.get("city", "").strip()
    procedure_id = request.args.get("procedure", type=int)

    # Only approved hospitals
    query = Hospital.query.filter_by(approved=1)
    if city:
        query = query.filter(Hospital.city.ilike(f"%{city}%"))

    if procedure_id:
        query = query.join(HospitalProcedure).filter(HospitalProcedure.procedure_id == procedure_id)

    hospitals_list = query.all()
    results = []
    for h in hospitals_list:
        procs = []
        for hp in h.hospital_procedures:
            if not procedure_id or hp.procedure_id == procedure_id:
                procs.append({
                    "procedure_id": hp.procedure_id,
                    "procedure_name": hp.procedure.name,
                    "price_min": hp.price_min,
                    "price_max": hp.price_max
                })
        results.append({
            "id": h.id,
            "name": h.name,
            "city": h.city,
            "address": h.address,
            "phone": h.phone,
            "procedures": procs
        })

    return jsonify({"hospitals": results, "count": len(results), "disclaimer": "Sample prices for demo"})


@api_bp.route("/stats", methods=["GET"])
def api_stats():
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Admin access required."}), 403

    grade_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    scans = Scan.query.filter_by(scan_type="dr").all()
    for s in scans:
        if s.predicted_grade in grade_counts:
            grade_counts[s.predicted_grade] += 1

    return jsonify({
        "total_users": User.query.count(),
        "total_patients": Patient.query.count(),
        "total_hospitals": Hospital.query.count(),
        "approved_hospitals": Hospital.query.filter_by(approved=1).count(),
        "pending_hospitals": Hospital.query.filter_by(approved=0).count(),
        "total_scans": Scan.query.count(),
        "total_appointments": Appointment.query.count(),
        "grade_distribution": grade_counts
    })
