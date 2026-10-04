import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key from environment variable with development fallback
    SECRET_KEY = os.environ.get("SECRET_KEY", "eyecare-super-secret-development-key-2024")
    
    # SQLite Database URI
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'eyecare.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload and generated file paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    HEATMAP_FOLDER = os.path.join(BASE_DIR, "static", "heatmaps")
    REPORT_FOLDER = os.path.join(BASE_DIR, "static", "reports")
    
    # 5 MB file size limit
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
