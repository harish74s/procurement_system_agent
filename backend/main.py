from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import get_db_connection
from routes.procurement import router as procurement_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(
    title="Enterprise Procurement AI Agent",
    description="AI-powered enterprise procurement management system",
    version="1.0.0"
)
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(procurement_router)

@app.get("/")
def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html")

@app.get("/")
def root():
    return {
        "message": "Enterprise Procurement AI Agent is running"
    }


@app.get("/health")
def health_check():
    try:
        connection = get_db_connection()

        if connection.is_connected():
            connection.close()

            return {
                "status": "healthy",
                "database": "connected"
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }