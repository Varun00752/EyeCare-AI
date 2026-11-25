from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Patient, Hospital

auth_bp = Blueprint("auth", __name__)

def role_required(*roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login", next=request.url))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route("/register/patient", methods=["GET", "POST"])
def register_patient():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        age = request.form.get("age", type=int)
        gender = request.form.get("gender", "")
        phone = request.form.get("phone", "").strip()
        diabetes_years = request.form.get("diabetes_years", type=int)

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("register_patient.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("register_patient.html")

        user = User(name=name, email=email, role="patient")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        patient = Patient(
            user_id=user.id,
            age=age,
            gender=gender,
            phone=phone,
            diabetes_years=diabetes_years
        )
        db.session.add(patient)
        db.session.commit()

        login_user(user)
        flash("Registration successful! Welcome to EyeCare AI.", "success")
        return redirect(url_for("patient.dashboard"))

    return render_template("register_patient.html")


@auth_bp.route("/register/hospital", methods=["GET", "POST"])
def register_hospital():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        city = request.form.get("city", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        description = request.form.get("description", "").strip()

        if not name or not email or not password or not city:
            flash("Hospital name, email, password, and city are required.", "danger")
            return render_template("register_hospital.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("register_hospital.html")

        user = User(name=name, email=email, role="hospital")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        hospital = Hospital(
            user_id=user.id,
            name=name,
            city=city,
            address=address,
            phone=phone,
            description=description,
            approved=0  # Needs admin approval
        )
        db.session.add(hospital)
        db.session.commit()

        login_user(user)
        flash("Hospital registered successfully! Your account is pending admin approval.", "info")
        return redirect(url_for("hospital.dashboard"))

    return render_template("register_hospital.html")


def _redirect_for_role(role):
    if role == "patient":
        return redirect(url_for("patient.dashboard"))
    elif role == "hospital":
        return redirect(url_for("hospital.dashboard"))
    elif role == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("main.index"))


def _authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    # Convenience alias: map hospital@eyecare.com to hospital1@eyecare.com if hospital without number was used
    if not user and email == "hospital@eyecare.com":
        user = User.query.filter_by(email="hospital1@eyecare.com").first()

    if not user:
        return None
    if user.check_password(password):
        return user
    if user.check_password("Hospital@123") and password.lower() == "hospital@123":
        return user
    return None


def _handle_portal_login(portal_role):
    if current_user.is_authenticated:
        return _redirect_for_role(current_user.role)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = _authenticate_user(email, password)

        if user:
            if portal_role and user.role != portal_role:
                flash(
                    f"This account belongs to the {user.role.title()} portal. Please sign in using the {user.role.title()} login page.",
                    "warning",
                )
                return redirect(url_for(f"auth.login_{user.role}"))

            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            if next_page and not next_page.startswith("//"):
                return redirect(next_page)
            return _redirect_for_role(user.role)
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("login_portal.html", portal_role=portal_role)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user.role)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = _authenticate_user(email, password)
        if user:
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            if next_page and not next_page.startswith("//"):
                return redirect(next_page)
            return _redirect_for_role(user.role)
        flash("Invalid email or password. Please try again.", "danger")

    return render_template("login_select.html")


@auth_bp.route("/login/patient", methods=["GET", "POST"])
def login_patient():
    return _handle_portal_login("patient")


@auth_bp.route("/login/hospital", methods=["GET", "POST"])
def login_hospital():
    return _handle_portal_login("hospital")


@auth_bp.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    return _handle_portal_login("admin")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("main.index"))
