from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import API_PREFIX, APP_NAME, FRONTEND_URL
from backend.app.routers.auth import router as auth_router
from backend.app.routers.chat import router as chat_router
from backend.app.routers.hash import router as hash_router
from backend.app.routers.health import router as health_router
from leadhunter.database import init_db

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(health_router, prefix=API_PREFIX)
app.include_router(chat_router, prefix=API_PREFIX)
app.include_router(hash_router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "status": "running",
        "docs": "/docs",
    }
