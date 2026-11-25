import os
import re
import uuid
from flask import Blueprint, request, jsonify, current_app, url_for
from flask_login import current_user
from models import db, User, Patient, Hospital, Procedure, HospitalProcedure, Scan, Appointment
from ml.predict import predict_dr, GRADE_ADVICE, LABELS

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
        return jsonify({"error": "File size exceeds 10 MB limit."}), 400

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


def _build_grade_next_steps(grade):
    if grade == 0:
        return [
            "Maintain regular blood sugar (HbA1c), blood pressure, and lipid control.",
            "Schedule a routine diabetic eye checkup in 12 months."
        ]
    elif grade == 1:
        return [
            "Tighten glycemic and blood pressure management with your physician.",
            "Repeat retinal screening in 6 to 12 months."
        ]
    elif grade == 2:
        return [
            "Book an appointment with a retina specialist / ophthalmologist within 1 to 3 months.",
            "Compare Eye Checkup & Retinal Laser prices across verified hospitals."
        ]
    elif grade == 3:
        return [
            "Consult an ophthalmologist urgently (within 1 to 2 weeks).",
            "Ask your specialist about Retinal Laser Photocoagulation or Anti-VEGF therapy."
        ]
    else:
        return [
            "Seek immediate care from a vitreoretinal specialist.",
            "Use the Hospital Directory to book an urgent appointment right away."
        ]


def _analyze_pasted_report_text(text):
    lower = text.lower()
    detected_grade = None
    for g, label in enumerate(LABELS):
        if f"grade {g}" in lower or label.lower() in lower:
            detected_grade = g
            break

    if detected_grade is None:
        return None

    conf_match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", text)
    conf_note = f" (Reported Confidence: {conf_match.group(1)}%)" if conf_match else ""
    advice = GRADE_ADVICE.get(detected_grade, "")
    steps = _build_grade_next_steps(detected_grade)

    return {
        "reply": (
            f"**Report Analysis — Grade {detected_grade}: {LABELS[detected_grade]}**{conf_note}\n\n"
            f"**Clinical Guidance:** {advice}\n\n"
            f"**Recommended Next Steps:**\n"
            + "\n".join(f"- {s}" for s in steps)
            + "\n\n*Note: This is an assistive pre-screening summary, not a formal diagnosis.*"
        ),
        "actions": [
            {"label": "Find Hospitals", "url": url_for("main.hospitals")},
            {"label": "Compare Prices", "url": url_for("main.compare")},
        ],
    }


@api_bp.route("/chat", methods=["POST"])
def api_chat():
    # Support either JSON or multipart/form-data (for direct image upload in chat)
    if request.content_type and "multipart/form-data" in request.content_type:
        message = (request.form.get("message") or "").strip()
        uploaded_file = request.files.get("file")
    else:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        uploaded_file = None

    # 1. Handle direct retinal image upload inside chat
    if uploaded_file and uploaded_file.filename:
        if not allowed_file(uploaded_file.filename):
            return jsonify({
                "reply": "Please upload a valid retinal fundus image in **PNG, JPG, or JPEG** format (under 10 MB)."
            })

        ext = uploaded_file.filename.rsplit(".", 1)[1].lower()
        unique_filename = f"chat_{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        uploaded_file.save(save_path)

        try:
            prediction = predict_dr(save_path, output_dir=current_app.config["HEATMAP_FOLDER"])
            grade = prediction["grade"]
            label = prediction["label"]
            conf_pct = round(prediction["confidence"] * 100, 1)
            advice = GRADE_ADVICE.get(grade, "")
            steps = _build_grade_next_steps(grade)

            # Save to DB if logged in as patient
            actions = [
                {"label": "Find Eye Hospitals", "url": url_for("main.hospitals")},
                {"label": "Compare Prices", "url": url_for("main.compare")},
            ]
            if current_user.is_authenticated and current_user.role == "patient" and current_user.patient:
                scan = Scan(
                    patient_id=current_user.patient.id,
                    scan_type="dr",
                    image_path=unique_filename,
                    heatmap_path=prediction["heatmap_path"],
                    predicted_grade=grade,
                    predicted_label=label,
                    confidence=prediction["confidence"],
                )
                db.session.add(scan)
                db.session.commit()
                actions.insert(0, {"label": "View Full Scan & PDF", "url": url_for("patient.scan_result", scan_id=scan.id)})

            return jsonify({
                "reply": (
                    f"**Image Analysis Complete — Grade {grade}: {label}** ({conf_pct}% confidence)\n\n"
                    f"**Clinical Guidance:** {advice}\n\n"
                    f"**Recommended Next Steps:**\n"
                    + "\n".join(f"- {s}" for s in steps)
                ),
                "actions": actions,
            })
        except ValueError as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            return jsonify({
                "reply": f"**Could not analyze image:** {str(e)}\n\nTip: Make sure you upload a circular orange-red retinal fundus photograph with dark borders."
            })
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            return jsonify({"reply": f"Sorry, something went wrong analyzing that image: {str(e)}"})

    if not message:
        return jsonify({"reply": "Hi! Ask me about your scan report, what to do next, how to get a fundus retinal image, or any Diabetic Retinopathy questions."})

    lower = message.lower()

    # 2. Check if the user pasted a report snippet to analyze
    pasted_analysis = _analyze_pasted_report_text(message)
    if pasted_analysis and len(message) > 25:
        return jsonify(pasted_analysis)

    # 3. Fetch patient context if logged in
    latest_scan = None
    upcoming_appt = None
    if current_user.is_authenticated and current_user.role == "patient" and current_user.patient:
        latest_scan = (
            Scan.query.filter_by(patient_id=current_user.patient.id)
            .order_by(Scan.created_at.desc())
            .first()
        )
        upcoming_appt = (
            Appointment.query.filter_by(patient_id=current_user.patient.id)
            .order_by(Appointment.appt_date.asc())
            .first()
        )

    # 4. Report reading & analysis intent
    if any(k in lower for k in ["report", "latest", "my scan", "analyze", "result", "read my"]):
        if latest_scan:
            grade = latest_scan.predicted_grade
            label = latest_scan.predicted_label
            conf_pct = round((latest_scan.confidence or 0) * 100, 1)
            date_str = latest_scan.created_at.strftime("%d %b %Y") if latest_scan.created_at else "Recent"
            advice = GRADE_ADVICE.get(grade, "")
            steps = _build_grade_next_steps(grade)
            return jsonify({
                "reply": (
                    f"**Your Latest Scan Report (#{latest_scan.id} • {date_str})**\n"
                    f"- **Result:** Grade {grade} — **{label}**\n"
                    f"- **Confidence:** {conf_pct}%\n"
                    f"- **Clinical Advice:** {advice}\n\n"
                    f"**What you should do next:**\n"
                    + "\n".join(f"- {s}" for s in steps)
                ),
                "actions": [
                    {"label": "Open Full Report", "url": url_for("patient.scan_result", scan_id=latest_scan.id)},
                    {"label": "Download PDF", "url": url_for("patient.download_pdf", scan_id=latest_scan.id)},
                    {"label": "Find Hospitals", "url": url_for("main.hospitals")},
                ],
            })
        elif current_user.is_authenticated and current_user.role == "patient":
            return jsonify({
                "reply": (
                    "You haven't uploaded a retinal scan yet! Here's how to get started:\n"
                    "1. Obtain a digital retinal fundus image (JPG/PNG) from an eye clinic or optometrist.\n"
                    "2. Upload it on the **New Scan** page, or attach it directly here using the paperclip icon."
                ),
                "actions": [{"label": "Upload First Scan", "url": url_for("patient.scan_new")}],
            })
        else:
            return jsonify({
                "reply": (
                    "To read your saved scan report automatically, please **sign in to the Patient Portal**.\n\n"
                    "Alternatively, you can **paste your report text** here or **attach a retinal fundus image** using the paperclip button and I will analyze it for you!"
                ),
                "actions": [{"label": "Patient Sign In", "url": url_for("auth.login_patient")}],
            })

    # 5. How to get a fundus retinal image
    if any(k in lower for k in ["fundus", "retinal image", "get image", "take photo", "camera", "where to get", "how to get"]):
        return jsonify({
            "reply": (
                "**How to Get a Retinal Fundus Image:**\n"
                "1. **Visit an Eye Clinic or Optometrist:** Ask for a *digital retinal fundus photograph* (captured with a non-mydriatic fundus camera — painless and takes ~2 minutes).\n"
                "2. **Diabetes & Ophthalmology Centers:** Most specialty eye hospitals (listed in our Hospitals directory) offer fundus photography during routine DR screening.\n"
                "3. **Request a Digital Copy:** Ask the clinic to email or share the `.jpg` or `.png` image file (under 10 MB).\n"
                "4. **Image Tips:** Make sure it shows the circular orange-red retina with dark corners and clear focus (avoid phone screenshots of a blurry monitor)."
            ),
            "actions": [
                {"label": "Find Nearby Hospitals", "url": url_for("main.hospitals")},
                {"label": "Upload Scan", "url": url_for("patient.scan_new") if current_user.is_authenticated and current_user.role == "patient" else url_for("auth.login_patient")},
            ],
        })

    # 6. What should I do next?
    if any(k in lower for k in ["next", "what should i do", "steps", "now what", "book", "appointment"]):
        if latest_scan:
            steps = _build_grade_next_steps(latest_scan.predicted_grade)
            appt_note = (
                f"\n\n*You have an appointment on {upcoming_appt.appt_date} ({upcoming_appt.status}).*"
                if upcoming_appt else ""
            )
            return jsonify({
                "reply": (
                    f"Based on your latest scan (**Grade {latest_scan.predicted_grade} — {latest_scan.predicted_label}**), here are your recommended next steps:\n"
                    + "\n".join(f"- {s}" for s in steps)
                    + appt_note
                ),
                "actions": [
                    {"label": "Compare Treatment Prices", "url": url_for("main.compare")},
                    {"label": "Book Eye Hospital", "url": url_for("main.hospitals")},
                ],
            })
        return jsonify({
            "reply": (
                "**Recommended Next Steps on EyeCare:**\n"
                "1. **Sign In / Register** as a Patient.\n"
                "2. **Upload a Retinal Fundus Photo** to get a 5-grade Diabetic Retinopathy screening & PDF report.\n"
                "3. **Compare Procedure Prices** across verified eye hospitals.\n"
                "4. **Book an Appointment** directly with a specialist."
            ),
            "actions": [
                {"label": "Patient Sign In", "url": url_for("auth.login_patient")},
                {"label": "Compare Prices", "url": url_for("main.compare")},
                {"label": "Explore Hospitals", "url": url_for("main.hospitals")},
            ],
        })

    # 7. DR grades & basic questions
    if any(k in lower for k in ["grade", "scale", "severity", "stages", "proliferative", "mild", "moderate", "severe"]):
        return jsonify({
            "reply": (
                "**Diabetic Retinopathy (DR) 5-Grade Scale:**\n"
                "- **Grade 0 (No DR):** No visible retinal abnormalities. Re-screen every 12 months.\n"
                "- **Grade 1 (Mild):** Small microaneurysms. Control blood sugar; re-screen in 6–12 months.\n"
                "- **Grade 2 (Moderate):** More microaneurysms/hemorrhages. See an ophthalmologist within 1–3 months.\n"
                "- **Grade 3 (Severe):** Significant retinal vessel blockage. Urgent specialist consultation needed.\n"
                "- **Grade 4 (Proliferative DR):** Fragile new blood vessels growing. Immediate vitreoretinal care required."
            )
        })

    if any(k in lower for k in ["diabetic retinopathy", "what is dr", "symptoms", "heatmap", "grad-cam", "cost", "price"]):
        return jsonify({
            "reply": (
                "**About Diabetic Retinopathy & EyeCare:**\n"
                "- **Diabetic Retinopathy (DR)** is a diabetes complication that damages retinal blood vessels and often has *no early symptoms* until vision is affected.\n"
                "- **Grad-CAM Heatmaps** highlight the retinal regions that most influenced the screening score.\n"
                "- **Price Comparison:** Use **Compare Prices** to check upfront ranges for Retinal Laser, Anti-VEGF Injections, Cataract Surgery, and Vitrectomy across approved clinics."
            ),
            "actions": [
                {"label": "Compare Prices", "url": url_for("main.compare")},
                {"label": "Find Hospitals", "url": url_for("main.hospitals")},
            ],
        })

    # 8. Default helpful response
    return jsonify({
        "reply": (
            "I'm your **EyeCare Assistant**! I can help you with:\n"
            "- **Analyze your report:** Ask *\"Analyze my latest report\"* or paste report text / attach a retinal image.\n"
            "- **Next steps:** Ask *\"What should I do next?\"*\n"
            "- **Getting a fundus image:** Ask *\"How do I get a retinal fundus image?\"*\n"
            "- **Basic questions:** DR grades (0–4), Grad-CAM heatmaps, symptoms, or hospital pricing."
        )
    })
