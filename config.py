import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://ai-expert.digitalplatform.kz")
APPLICANT_LOGIN = os.getenv("APPLICANT_LOGIN")
APPLICANT_PASSWORD = os.getenv("APPLICANT_PASSWORD")