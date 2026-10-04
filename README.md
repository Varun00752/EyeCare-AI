# EyeCare AI &bull; Retinal Screening & Hospital Care Platform

EyeCare AI is a full-stack web platform designed to assist patients in preliminary Diabetic Retinopathy (DR) screening using deep learning explainability (Grad-CAM heatmaps), transparently compare eye procedure prices across specialized hospitals, and schedule clinical consultations.

> **Medical Disclaimer:**
> *This is an AI screening aid, not a medical diagnosis. Please consult a qualified ophthalmologist.*

---

## Tech Stack
- **Backend:** Python 3.10+ (Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug)
- **Database:** SQLite (`eyecare.db`)
- **Frontend:** Jinja2 templates, Bootstrap 5 (CDN), Chart.js (CDN), Bootstrap Icons
- **Image Processing & ML:** OpenCV, NumPy, Pillow, Lazy-loaded Keras/EfficientNet-B0 fallback
- **Reports:** ReportLab (clinical PDF generation)

---

## Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Sample Database
Populates the administrator account, 6 pre-approved partner hospitals in Bengaluru, Chennai, Hyderabad, and Mumbai with varied sample procedure price ranges, and a sample patient:
```bash
python seed.py
```

### 3. Start the Web Server
```bash
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## Test Login Accounts

| Role | Email | Password | Access & Permissions |
|---|---|---|---|
| **Admin** | `admin@eyecare.com` | `Admin@123` | Hospital approvals/rejections, master procedures catalog management, system stats dashboard |
| **Patient** | `patient@eyecare.com` | `Patient@123` | Upload retinal scans, view Grad-CAM heatmaps, download PDF reports, book & cancel appointments |
| **Hospital** | `hospital1@eyecare.com` | `Hospital@123` | Nethra Institute: Manage procedures & price ranges, review patient appointments, view attached retinal scans |
| **Hospital 2** | `hospital2@eyecare.com` | `Hospital@123` | Shankara Vision Hospital |
| **Hospital 3** | `hospital3@eyecare.com` | `Hospital@123` | Dr. Mohan Retinal Eye Foundation (Chennai) |
| **Hospital 4** | `hospital4@eyecare.com` | `Hospital@123` | Prasad Eye Institute (Hyderabad) |
| **Hospital 5** | `hospital5@eyecare.com` | `Hospital@123` | Bombay City Eye & Retina Clinic (Mumbai) |
| **Hospital 6** | `hospital6@eyecare.com` | `Hospital@123` | Metro Retina & Cornea Hospital (Mumbai) |

---

## Key Features Implemented (Tasks 1 to 9)

1. **Task 1 - Project Setup:** Modular Flask architecture, application factory pattern, environment-configurable secret key with dev fallback, responsive medical layout in `base.html` with role-aware navigation.
2. **Task 2 - Database Models & Seed Data:** Complete schema for Users, Patients, Hospitals, Master Procedures, HospitalProcedure price ranges, Scans, and Appointments.
3. **Task 3 - Authentication & Role Isolation:** Passwords hashed with `werkzeug.security`. Secure `@role_required` decorator enforcing role isolation; 403 pages returned for cross-role violations.
4. **Task 4 - Public Hospital Directory & Price Comparison:** Filter hospitals by city and procedure. `/compare` displays comparative pricing with cheapest hospital highlighted and interactive Chart.js bar charts. Only approved hospitals appear.
5. **Task 5 - ML Module & DEMO MODE Fallback:** `ml/predict.py` implements image validation (checks format, min 100x100px, low-illumination warning), black border cropping, CLAHE enhancement, and simulated Grad-CAM attention heatmaps in DEMO MODE with prominent banners.
6. **Task 6 - Retinal Scan Upload & Grading:** Drag-and-drop upload with client & server-side validation (formats, 5MB limit). Results display original retinal image alongside Grad-CAM heatmap, severity grade (0-4), confidence bar, class probabilities, clinical advice, and recommended hospitals for grade >= 2.
7. **Task 7 - Consultation Scheduling & Appointments:** Server-side future-date validation. Hospitals can only view scans attached to their appointments. Pending appointments can be cancelled by patients or accepted/rejected by hospitals.
8. **Task 8 - Hospital & Admin Management Portals:** Unapproved hospitals are locked from adding/editing procedures and hidden from public search until approved by the admin. Admin can approve/reject partner hospitals and manage the master procedure catalog.
9. **Task 9 - Clinical PDF Reports:** Downloadable PDF report generated with ReportLab featuring patient metadata, original fundus image, Grad-CAM heatmap overlay, DR grade, confidence score, clinical action text, and mandatory medical disclaimer.

---

## API Endpoints (`/api`)

- `POST /api/predict`: Multipart image upload (logged-in patient only) &rarr; returns `{grade, label, confidence, heatmap_url, demo}`.
- `GET /api/hospitals?city=&procedure=`: Returns JSON list of approved hospitals and procedure price ranges.
- `GET /api/stats`: Admin-only metrics and DR grade distribution for charting.

---

## Documented Assumptions (per AGENTS.md)
1. **DEMO MODE:** When `ml/dr_model.keras` is absent, the system operates in DEMO MODE. Predictions are simulated based on image statistics, generating consistent grades and realistic Grad-CAM heatmaps.
2. **Sample Prices:** All hospital procedure prices in the database are simulated INR estimates labeled "Sample prices for demo" throughout the UI.
3. **Privacy:** Data isolation ensures patients only see their own scans; hospitals can only view scans explicitly attached to an appointment booked with their hospital.
