import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://ai-expert.digitalplatform.kz")

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
    "chairman": {
        "login": os.getenv("CHAIRMAN_LOGIN"),
        "password": os.getenv("CHAIRMAN_PASSWORD"),
    },
    "board_member": {
        "login": os.getenv("BOARDMEMB_LOGIN"),
        "password": os.getenv("BOARDMEMB_PASSWORD"),
    },
}

INVALID_PASSWORD = "wrong_password_123"
NONEXISTENT_LOGIN = "no_such_user_qa"