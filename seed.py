"""
seed.py - Populates sample data for EyeCare AI.
Run once: python seed.py
"""

from app import create_app
from models import db, User, Patient, Hospital, Procedure, HospitalProcedure

def seed_database():
    app = create_app()
    with app.app_context():
        # Create all database tables
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
            proc_lookup[proc.name] = proc
        print(f"  Ensured {len(proc_lookup)} master procedures.")

        # 4. 6 Sample Hospitals across Bengaluru, Chennai, Hyderabad, Mumbai (approved = 1)
        hospitals_data = [
            {
                "email": "hospital1@eyecare.com",
                "name": "Nethra Institute of Vitreo-Retina & Eye Care",
                "city": "Bengaluru",
                "address": "100 Feet Road, Indiranagar, Bengaluru, Karnataka",
                "phone": "+91 80 2521 4455",
                "description": "Super-specialty eye hospital renowned for advanced vitreoretinal surgeries and diabetic eye care.",
                "procedures": {
                    "Eye Checkup": (500, 1000),
                    "Diabetic Retinopathy Screening": (800, 1800),
                    "Cataract Surgery (Lens Replacement / IOL)": (18000, 55000),
                    "Retinal Laser Photocoagulation": (6000, 16000),
                    "Anti-VEGF Injection": (10000, 26000),
                    "Vitrectomy": (45000, 95000),
                    "Glaucoma Treatment": (4000, 15000)
                }
            },
            {
                "email": "hospital2@eyecare.com",
                "name": "Shankara Vision Hospital",
                "city": "Bengaluru",
                "address": "Varthur Road, Whitefield, Bengaluru, Karnataka",
                "phone": "+91 80 4112 8899",
                "description": "State-of-the-art refractive, laser, and diabetic retinopathy care center with community outreach.",
                "procedures": {
                    "Eye Checkup": (400, 800),
                    "Diabetic Retinopathy Screening": (700, 1500),
                    "Cataract Surgery (Lens Replacement / IOL)": (15000, 48000),
                    "LASIK": (22000, 65000),
                    "Anti-VEGF Injection": (9000, 22000),
                    "Conjunctivitis Treatment": (500, 1200)
                }
            },
            {
                "email": "hospital3@eyecare.com",
                "name": "Dr. Mohan Retinal Eye Foundation",
                "city": "Chennai",
                "address": "Cathedral Road, Gopalapuram, Chennai, Tamil Nadu",
                "phone": "+91 44 2811 7733",
                "description": "Premier eye foundation in South India specializing in diabetic macular edema and retinal laser therapies.",
                "procedures": {
                    "Eye Checkup": (600, 1200),
                    "Diabetic Retinopathy Screening": (900, 2000),
                    "Retinal Laser Photocoagulation": (5500, 14000),
                    "Anti-VEGF Injection": (8500, 24000),
                    "Vitrectomy": (42000, 90000),
                    "Cornea Transplant": (50000, 120000),
                    "Cataract Surgery (Lens Replacement / IOL)": (16000, 52000)
                }
            },
            {
                "email": "hospital4@eyecare.com",
                "name": "Prasad Eye Institute & Laser Center",
                "city": "Hyderabad",
                "address": "Road No. 2, Banjara Hills, Hyderabad, Telangana",
                "phone": "+91 40 3061 2345",
                "description": "Internationally accredited tertiary eye institute dedicated to corneal, vitreoretinal, and refractive innovation.",
                "procedures": {
                    "Eye Checkup": (500, 1000),
                    "Diabetic Retinopathy Screening": (750, 1600),
                    "Cataract Surgery (Lens Replacement / IOL)": (17000, 58000),
                    "LASIK": (25000, 80000),
                    "Cornea Transplant": (45000, 110000),
                    "Retinal Laser Photocoagulation": (6500, 15500),
                    "Anti-VEGF Injection": (9500, 25000),
                    "Vitrectomy": (48000, 105000)
                }
            },
            {
                "email": "hospital5@eyecare.com",
                "name": "Bombay City Eye & Retina Clinic",
                "city": "Mumbai",
                "address": "Victor Mansion, Babulnath Road, Chowpatty, Mumbai, Maharashtra",
                "phone": "+91 22 2367 1010",
                "description": "Modern ophthalmic surgical hospital with expertise in minimally invasive vitrectomy and advanced IOLs.",
                "procedures": {
                    "Eye Checkup": (700, 1500),
                    "Diabetic Retinopathy Screening": (1000, 2200),
                    "Cataract Surgery (Lens Replacement / IOL)": (22000, 75000),
                    "LASIK": (30000, 85000),
                    "Anti-VEGF Injection": (12000, 28000),
                    "Vitrectomy": (55000, 120000),
                    "Glaucoma Treatment": (5000, 18000)
                }
            },
            {
                "email": "hospital6@eyecare.com",
                "name": "Metro Retina & Cornea Hospital",
                "city": "Mumbai",
                "address": "Linking Road, Bandra West, Mumbai, Maharashtra",
                "phone": "+91 22 2640 5566",
                "description": "Comprehensive eye care hospital with specialized diabetic retinopathy clinics and cornea transplantation unit.",
                "procedures": {
                    "Eye Checkup": (600, 1200),
                    "Diabetic Retinopathy Screening": (850, 1800),
                    "Cataract Surgery (Lens Replacement / IOL)": (20000, 68000),
                    "Cornea Transplant": (48000, 115000),
                    "Retinal Laser Photocoagulation": (7000, 17000),
                    "Anti-VEGF Injection": (11000, 27000),
                    "Conjunctivitis Treatment": (600, 1500)
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

if __name__ == "__main__":
    seed_database()
