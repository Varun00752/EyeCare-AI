"""
seed.py - Populates sample data for EyeCare AI.
Run once: python seed.py
"""

from models import db, User, Patient, Hospital, Procedure, HospitalProcedure

def populate_seed_data():
    """
    Populates seed data within an active Flask application context.
    Safe to call during initial startup or manual command.
    """
    db.create_all()

    print("Seeding database...")

    # 1. Admin User
    admin_email = "admin@eyecare.com"
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        admin_user = User(
            name="System Administrator",
            email=admin_email,
            role="admin"
        )
        admin_user.set_password("Admin@123")
        db.session.add(admin_user)
        print("  Created Admin:", admin_email)
    else:
        print("  Admin already exists.")

    # 2. Sample Patient
    patient_email = "patient@eyecare.com"
    patient_user = User.query.filter_by(email=patient_email).first()
    if not patient_user:
        patient_user = User(
            name="Ramesh Kumar",
            email=patient_email,
            role="patient"
        )
        patient_user.set_password("Patient@123")
        db.session.add(patient_user)
        db.session.flush()

        patient_profile = Patient(
            user_id=patient_user.id,
            age=54,
            gender="Male",
            phone="+91 98450 12345",
            diabetes_years=8
        )
        db.session.add(patient_profile)
        print("  Created Patient:", patient_email)
    else:
        print("  Patient already exists.")

    # 3. Master Procedures List
    procedures_data = [
        {
            "name": "Eye Checkup",
            "category": "Checkup",
            "description": "Comprehensive vision testing, intraocular pressure measurement, and dilated retinal examination."
        },
        {
            "name": "Diabetic Retinopathy Screening",
            "category": "Checkup",
            "description": "Digital fundus photography and specialized retinal evaluation for diabetic microvascular complications."
        },
        {
            "name": "Cataract Surgery (Lens Replacement / IOL)",
            "category": "Surgery",
            "description": "Phacoemulsification with foldable monofocal or multifocal intraocular lens (IOL) implantation."
        },
        {
            "name": "LASIK",
            "category": "Surgery",
            "description": "Custom wavefront blade-free laser refractive surgery for myopia, hyperopia, and astigmatism."
        },
        {
            "name": "Cornea Transplant",
            "category": "Surgery",
            "description": "Keratoplasty (full-thickness PK or endothelial DMEK/DSAEK) for severe corneal disease."
        },
        {
            "name": "Retinal Laser Photocoagulation",
            "category": "Laser",
            "description": "Panretinal or focal green laser treatment to halt proliferation of leaking retinal blood vessels."
        },
        {
            "name": "Anti-VEGF Injection",
            "category": "Injection",
            "description": "Intravitreal injection (Ranibizumab / Aflibercept / Bevacizumab) for macular edema and proliferative DR."
        },
        {
            "name": "Vitrectomy",
            "category": "Surgery",
            "description": "Microsurgical vitreoretinal procedure to remove vitreous blood hemorrhage and peel tractional retinal membranes."
        },
        {
            "name": "Glaucoma Treatment",
            "category": "Laser",
            "description": "Laser trabeculoplasty (SLT/ALT) or filtration surgery for intraocular pressure reduction."
        },
        {
            "name": "Conjunctivitis Treatment",
            "category": "Checkup",
            "description": "Targeted clinical diagnosis, antimicrobial drops, and therapeutic relief for viral or bacterial ocular infections."
        }
    ]

    proc_lookup = {}
    for pdata in procedures_data:
        proc = Procedure.query.filter_by(name=pdata["name"]).first()
        if not proc:
            proc = Procedure(
                name=pdata["name"],
                category=pdata["category"],
                description=pdata["description"]
            )
            db.session.add(proc)
            db.session.flush()
        proc_lookup[pdata["name"]] = proc
    print(f"  Initialized {len(procedures_data)} master procedures.")

    # 4. Six Real-Named Eye Hospitals with Realistic Procedures and Pricing
    hospitals_data = [
        {
            "name": "Narayana Nethralaya",
            "email": "contact@narayananethralaya.org",
            "city": "Bengaluru",
            "address": "121/C, Chord Road, 1st R Block, Rajajinagar, Bengaluru, Karnataka 560010",
            "phone": "+91 80 6612 1641",
            "description": "Super-specialty eye hospital renowned for advanced vitreoretinal surgery, diabetic retinopathy management, and femto-cataract care.",
            "procedures": {
                "Eye Checkup": (500, 1000),
                "Diabetic Retinopathy Screening": (800, 1500),
                "Cataract Surgery (Lens Replacement / IOL)": (20000, 65000),
                "LASIK": (35000, 85000),
                "Retinal Laser Photocoagulation": (6000, 14000),
                "Anti-VEGF Injection": (15000, 32000),
                "Vitrectomy": (45000, 95000),
                "Glaucoma Treatment": (8000, 25000)
            }
        },
        {
            "name": "Sankara Eye Hospital",
            "email": "info@sankaraeye.com",
            "city": "Bengaluru",
            "address": "Varthur Main Road, Kundalahalli Gate, Bengaluru, Karnataka 560037",
            "phone": "+91 80 2854 2727",
            "description": "NABH-accredited non-profit tertiary eye institute delivering high-quality retinal, cataract, and refractive surgeries.",
            "procedures": {
                "Eye Checkup": (400, 800),
                "Diabetic Retinopathy Screening": (700, 1200),
                "Cataract Surgery (Lens Replacement / IOL)": (18000, 55000),
                "LASIK": (30000, 75000),
                "Cornea Transplant": (50000, 110000),
                "Retinal Laser Photocoagulation": (5000, 12000),
                "Anti-VEGF Injection": (12000, 28000),
                "Conjunctivitis Treatment": (300, 700)
            }
        },
        {
            "name": "Aravind Eye Hospital",
            "email": "patientcare@aravind.org",
            "city": "Chennai",
            "address": "Poonamallee High Road, Noombal, Chennai, Tamil Nadu 600077",
            "phone": "+91 44 4095 6100",
            "description": "World-famous ophthalmic network specializing in cost-effective high-volume cataract and vitreoretinal clinical treatments.",
            "procedures": {
                "Eye Checkup": (300, 600),
                "Diabetic Retinopathy Screening": (600, 1000),
                "Cataract Surgery (Lens Replacement / IOL)": (15000, 48000),
                "Cornea Transplant": (45000, 90000),
                "Retinal Laser Photocoagulation": (4500, 10000),
                "Anti-VEGF Injection": (10000, 25000),
                "Vitrectomy": (40000, 80000)
            }
        },
        {
            "name": "Dr. Agarwal's Eye Hospital",
            "email": "support@dragarwal.com",
            "city": "Chennai",
            "address": "19, Cathedral Road, Gopalapuram, Chennai, Tamil Nadu 600086",
            "phone": "+91 44 4344 2400",
            "description": "Pioneering ophthalmic institution renowned for Glued IOL, PDEK cornea surgery, and dedicated Diabetic Retinopathy treatment units.",
            "procedures": {
                "Eye Checkup": (600, 1200),
                "Diabetic Retinopathy Screening": (900, 1800),
                "Cataract Surgery (Lens Replacement / IOL)": (22000, 70000),
                "LASIK": (40000, 90000),
                "Cornea Transplant": (60000, 125000),
                "Retinal Laser Photocoagulation": (7000, 15000),
                "Anti-VEGF Injection": (16000, 35000),
                "Vitrectomy": (50000, 105000)
            }
        },
        {
            "name": "LV Prasad Eye Institute (LVPEI)",
            "email": "appointment@lvpei.org",
            "city": "Hyderabad",
            "address": "Kallam Anji Reddy Campus, Road No 2, Banjara Hills, Hyderabad, Telangana 500034",
            "phone": "+91 40 6810 2020",
            "description": "WHO Collaborating Centre for Prevention of Blindness; global leader in retinal research, cornea transplants, and pediatric eye care.",
            "procedures": {
                "Eye Checkup": (500, 1100),
                "Diabetic Retinopathy Screening": (850, 1600),
                "Cataract Surgery (Lens Replacement / IOL)": (20000, 60000),
                "LASIK": (38000, 80000),
                "Cornea Transplant": (55000, 120000),
                "Retinal Laser Photocoagulation": (6500, 13500),
                "Anti-VEGF Injection": (14000, 30000),
                "Vitrectomy": (48000, 100000),
                "Glaucoma Treatment": (9000, 28000)
            }
        },
        {
            "name": "Dr. Shroff's Charity Eye Hospital",
            "email": "info@sceh.net",
            "city": "Delhi",
            "address": "5027, Kedar Nath Road, Daryaganj, New Delhi, Delhi 110002",
            "phone": "+91 11 4352 4444",
            "description": "Historic, prestigious eye and ENT hospital in Old Delhi offering advanced subspecialty ophthalmic and vitreoretinal laser treatment.",
            "procedures": {
                "Eye Checkup": (400, 750),
                "Diabetic Retinopathy Screening": (700, 1300),
                "Cataract Surgery (Lens Replacement / IOL)": (17000, 52000),
                "LASIK": (32000, 78000),
                "Cornea Transplant": (48000, 95000),
                "Retinal Laser Photocoagulation": (5500, 11500),
                "Anti-VEGF Injection": (13000, 27000),
                "Conjunctivitis Treatment": (350, 650)
            }
        }
    ]

    for hdata in hospitals_data:
        h_user = User.query.filter_by(email=hdata["email"]).first()
        if not h_user:
            h_user = User(
                name=hdata["name"],
                email=hdata["email"],
                role="hospital"
            )
            h_user.set_password("Hospital@123")
            db.session.add(h_user)
            db.session.flush()

            hospital = Hospital(
                user_id=h_user.id,
                name=hdata["name"],
                city=hdata["city"],
                address=hdata["address"],
                phone=hdata["phone"],
                description=hdata["description"],
                approved=1  # Pre-approved sample hospital
            )
            db.session.add(hospital)
            db.session.flush()

            # Add procedures and prices
            for proc_name, (pmin, pmax) in hdata["procedures"].items():
                if proc_name in proc_lookup:
                    hp = HospitalProcedure(
                        hospital_id=hospital.id,
                        procedure_id=proc_lookup[proc_name].id,
                        price_min=pmin,
                        price_max=pmax
                    )
                    db.session.add(hp)
            print(f"  Created Hospital: {hdata['name']} ({hdata['city']})")
        else:
            print(f"  Hospital {hdata['name']} already exists.")

    db.session.commit()
    print("Database seeded successfully!")

def seed_database():
    from app import create_app
    app = create_app()
    with app.app_context():
        populate_seed_data()

if __name__ == "__main__":
    seed_database()
