import os
from flask import Flask, render_template, flash, redirect, request, send_from_directory
from flask_login import LoginManager
from config import Config
from models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to access this page."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Ensure required static/runtime folders exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["HEATMAP_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)

    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.patient import patient_bp
    from routes.hospital import hospital_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(hospital_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Custom media routes to serve runtime uploads / heatmaps / reports
    # (Uses /media/... so Flask's built-in /static/ handler does not intercept /tmp files on Vercel)
    @app.route("/media/uploads/<path:filename>")
    @app.route("/static/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/media/heatmaps/<path:filename>")
    @app.route("/static/heatmaps/<path:filename>")
    def serve_heatmap(filename):
        return send_from_directory(app.config["HEATMAP_FOLDER"], filename)

    @app.route("/media/reports/<path:filename>")
    @app.route("/static/reports/<path:filename>")
    def serve_report(filename):
        return send_from_directory(app.config["REPORT_FOLDER"], filename)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        flash("File is too large. Maximum allowed size is 10 MB.", "danger")
        return redirect(request.referrer or "/")

    # Ensure database schema is created and auto-seed if empty
    with app.app_context():
        db.create_all()
        try:
            from models import User
            if User.query.first() is None:
                from seed import populate_seed_data
                populate_seed_data()
                print("[EyeCare AI] Database initialized & seeded with default hospitals and procedures.")
        except Exception as e:
            print(f"[EyeCare AI] Auto-seed status: {e}")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=port)
