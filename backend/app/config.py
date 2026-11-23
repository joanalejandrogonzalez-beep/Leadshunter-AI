import os

APP_NAME = os.getenv("APP_NAME", "LeadHunter API")
APP_ENV = os.getenv("APP_ENV", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
API_PREFIX = os.getenv("API_PREFIX", "/api")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
