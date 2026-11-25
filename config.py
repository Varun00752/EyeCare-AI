import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IS_VERCEL = bool(os.environ.get("VERCEL"))

class Config:
    # Secret key from environment variable with development fallback
    SECRET_KEY = os.environ.get("SECRET_KEY", "eyecare-super-secret-development-key-2024")

    # On Vercel, the root /var/task filesystem is read-only.
    # Therefore, SQLite database and runtime upload directories must use /tmp.
    if IS_VERCEL:
        db_path = "/tmp/eyecare.db"
        # If a pre-seeded eyecare.db exists in project root, copy it to /tmp if not already present
        source_db = os.path.join(BASE_DIR, "eyecare.db")
        if os.path.exists(source_db) and not os.path.exists(db_path):
            try:
                import shutil
                shutil.copy2(source_db, db_path)
            except Exception:
                pass

        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
        UPLOAD_FOLDER = "/tmp/uploads"
        HEATMAP_FOLDER = "/tmp/heatmaps"
        REPORT_FOLDER = "/tmp/reports"
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'eyecare.db')}"
        )
        UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
        HEATMAP_FOLDER = os.path.join(BASE_DIR, "static", "heatmaps")
        REPORT_FOLDER = os.path.join(BASE_DIR, "static", "reports")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 10 MB file size limit
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
