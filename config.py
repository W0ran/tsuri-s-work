import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://dev-ai-expert.digitalplatform.kz")

USERS = {
    "applicant": {
        "login": os.getenv("APPLICANT_LOGIN"),
        "password": os.getenv("APPLICANT_PASSWORD"),
    },
    "expert": {
        "login": os.getenv("EXPERT_LOGIN"),
        "password": os.getenv("EXPERT_PASSWORD"),
    },
    "admin": {
        "login": os.getenv("ADMIN_LOGIN"),
        "password": os.getenv("ADMIN_PASSWORD"),
    },
    "predsedatel": {
        "login": os.getenv("PREDSEDATEL_LOGIN"),
        "password": os.getenv("PREDSEDATEL_PASSWORD"),
    },
    "sovet_tsuri": {
        "login": os.getenv("SOVET_TSURI_LOGIN"),
        "password": os.getenv("SOVET_TSURI_PASSWORD"),
    },
}

INVALID_PASSWORD = "wrong_password_123"
NONEXISTENT_LOGIN = "no_such_user_qa"
