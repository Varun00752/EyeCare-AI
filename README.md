# EyeCare AI &bull; Intelligent Retinal Screening & Ophthalmology Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask%203.1-teal.svg)](https://flask.palletsprojects.com/)
[![TensorFlow](https://img.shields.io/badge/ML-TensorFlow%20%2F%20Keras-orange.svg)](https://www.tensorflow.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**EyeCare AI** is a full-stack medical web platform designed to assist in early **Diabetic Retinopathy (DR)** screening using deep learning explainability (**Grad-CAM heatmaps** on EfficientNet-B0), transparently compare eye procedure prices across specialized ophthalmology hospitals, and schedule clinical consultations with attached diagnostic reports.

> **Important Medical Disclaimer:**  
> *This platform is an AI screening aid and decision-support tool, not a medical diagnosis. Clinical intervention decisions must always be made by a qualified ophthalmologist.*

---

## Key Features

1. **AI Retinal Screening (EfficientNet-B0):**
   - Upload digital fundus photography (`.png`, `.jpg`, `.jpeg`).
   - Standardized clinical preprocessing: black border cropping, bilinear resize (256&times;256), and **CLAHE** (Contrast Limited Adaptive Histogram Equalization) on the L channel in LAB color space.
   - Categorizes retinal severity across the **5 ICDR DR Grades** (Grade 0: No DR to Grade 4: Proliferative DR) with model confidence and class probability distribution.

2. **Explainable AI (Grad-CAM on `top_conv`):**
   - Visual gradient-weighted class activation mapping highlights exactly where the neural network detected microvascular lesions (microaneurysms, hemorrhages, hard exudates).
   - Generates visual JET colormap overlays, fostering clinical interpretability and trust.

3. **Transparent Procedure Price Comparison:**
   - Real-time comparative pricing for key eye procedures: **Cataract Surgery (IOL)**, **LASIK**, **Retinal Laser Photocoagulation**, **Anti-VEGF Injections**, **Vitrectomy**, and **Cornea Transplants**.
   - Filters by city (Bengaluru, Chennai, Hyderabad, Mumbai) and procedure.
   - Highlights the lowest-cost facility and displays an interactive **Chart.js** price distribution bar chart.

4. **Hospital Directory & Admin Verification:**
   - Search verified partner eye hospitals.
   - Complete hospital onboarding governance: unapproved hospital registrations remain locked and hidden from public search until verified by the system administrator.

5. **Integrated Consultation Scheduling:**
   - Patients schedule appointments with specialized hospitals.
   - Option to attach previous retinal AI scans for ophthalmologist pre-review.
   - Enforces server-side future-date scheduling and cancellation guards (only pending appointments can be cancelled).

6. **Downloadable Clinical PDF Reports:**
   - One-click print-ready diagnostic PDF reports generated with **ReportLab**.
   - Contains patient history, original fundus photography, Grad-CAM heatmap overlay, severity grade, confidence score, clinical action advice, and medical disclaimer.

7. **Multi-Role Access Control (RBAC):**
   - Dedicated portals for **Patients**, **Hospitals**, and **Administrators** with strict security isolation (patients can only see their own scans; hospitals can only view scans attached to their appointments).

---

## Tech Stack

| Layer | Technologies Used |
|---|---|
| **Backend Framework** | Python 3.10+, Flask 3.1, Jinja2 |
| **Database & ORM** | SQLite (`eyecare.db`), SQLAlchemy 2.1, Flask-SQLAlchemy |
| **Authentication & RBAC** | Flask-Login, Werkzeug (salted password hashing) |
| **AI / Machine Learning** | TensorFlow / Keras 3.x (`EfficientNet-B0`), `tf.GradientTape` |
| **Computer Vision** | OpenCV (`cv2`), NumPy, Pillow |
| **Document Generation** | ReportLab 5.0 (clinical PDF engine) |
| **Frontend UI** | Bootstrap 5 (CDN), Chart.js (CDN), Bootstrap Icons |

---

## Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Varun00752/EyeCare-AI.git
cd EyeCare-AI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed the Database
Populates default procedures, administrator credentials, sample patient, and pre-approved partner eye hospitals with realistic procedure price ranges:
```bash
python seed.py
```

### 4. Start the Application
```bash
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## Demo Login Accounts

| Role | Email Address | Password | Features & Portal Access |
|---|---|---|---|
| **Admin** | `admin@eyecare.com` | `Admin@123` | Hospital verification (Approve/Reject), master procedure catalog, disease stats |
| **Patient** | `patient@eyecare.com` | `Patient@123` | Upload retinal scans, view Grad-CAM heatmaps, download PDF, book appointments |
| **Hospital 1** | `hospital1@eyecare.com` | `Hospital@123` | Nethra Institute (Bengaluru) &ndash; manage procedures/prices, review bookings |
| **Hospital 2** | `hospital2@eyecare.com` | `Hospital@123` | Shankara Vision Hospital (Bengaluru) |
| **Hospital 3** | `hospital3@eyecare.com` | `Hospital@123` | Dr. Mohan Retinal Eye Foundation (Chennai) |
| **Hospital 4** | `hospital4@eyecare.com` | `Hospital@123` | Prasad Eye Institute & Laser Center (Hyderabad) |
| **Hospital 5** | `hospital5@eyecare.com` | `Hospital@123` | Bombay City Eye & Retina Clinic (Mumbai) |
| **Hospital 6** | `hospital6@eyecare.com` | `Hospital@123` | Metro Retina & Cornea Hospital (Mumbai) |

---

## Diabetic Retinopathy Severity Scale (ICDR)

| Grade | Severity Level | Pathological Findings | Clinical Recommendation |
|:---:|---|---|---|
| **0** | **No DR** | Normal retina, no microvascular lesions | Annual routine re-screening in 12 months |
| **1** | **Mild NPDR** | Microaneurysms only | Blood sugar control; re-screen in 6&ndash;12 months |
| **2** | **Moderate NPDR** | Multiple microaneurysms, blot hemorrhages, hard exudates | Consult ophthalmologist within 1&ndash;3 months |
| **3** | **Severe NPDR** | >20 intraretinal hemorrhages in 4 quadrants, venous beading | Urgent specialist consultation required |
| **4** | **Proliferative DR** | Neovascularization, vitreous/preretinal hemorrhage | Immediate specialist care (Laser / Anti-VEGF) |

---

## REST API Endpoints (`/api`)

- **`POST /api/predict`**: Multipart image upload (logged-in patient only). Returns predicted grade, label, confidence, and Grad-CAM heatmap URL.
- **`GET /api/hospitals?city=&procedure=`**: Returns JSON list of approved hospitals, contact info, and procedure price ranges.
- **`GET /api/stats`**: Admin-only system metrics, user counts, and DR grade distribution for analytics.

---

## Project Structure

```text
EyeCare-AI/
├── app.py                 # Flask application factory & error handlers
├── config.py              # Configuration & environment variables
├── models.py              # SQLAlchemy database models & RBAC schema
├── seed.py                # Database population script
├── requirements.txt       # Project dependencies
├── README.md              # Project documentation
│
├── ml/                    # Machine Learning Module
│   ├── dr_model.keras     # Trained EfficientNet-B0 model
│   └── predict.py         # CLAHE preprocessing, inference & Grad-CAM
│
├── routes/                # Blueprint Route Controllers
│   ├── auth.py            # Authentication, registration & role decorators
│   ├── main.py            # Public landing, hospital directory & price comparison
│   ├── patient.py         # Patient dashboard, scan upload & booking
│   ├── hospital.py        # Hospital portal, procedures & appointment review
│   ├── admin.py           # Admin console & hospital approvals
│   ├── api.py             # REST API endpoints
│   └── patient_pdf.py     # ReportLab clinical PDF generator
│
├── templates/             # Jinja2 HTML Templates
│   ├── base.html          # Global layout, responsive navbar & medical footer
│   ├── index.html         # Homepage hero & feature cards
│   ├── hospitals.html     # Directory & search filters
│   ├── compare.html       # Price comparison & Chart.js chart
│   ├── patient/           # Patient portal pages
│   ├── hospital/          # Hospital management pages
│   └── admin/             # Admin console pages
│
└── static/                # Static Media & Storage
    ├── css/style.css      # Custom medical color theme
    ├── uploads/           # Uploaded fundus scans
    ├── heatmaps/          # Generated Grad-CAM attention heatmaps
    └── reports/           # Generated PDF reports
```
