
from enum import Enum
from pathlib import Path
import os

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 1400

BUFFER_SIZE = 5

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_FOLDER = "uploads" 
UPLOADS_PATH = Path(f"{BASE_DIR}/{UPLOADS_FOLDER}")
UPLOADS_PATH.mkdir(exist_ok=True)

ROLE_ACCESS = {
    "employee": ["employee_only"],
    "manager": ["employee_only", "manager_only"],
    "admin": ["employee_only", "manager_only", "admin_only"],
}

ALLOWED_MIME_TYPES = [
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text"
    ]
