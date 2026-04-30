# app/__init__.py
# Main application factory and entry point.

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes.transcripts import router as transcripts_router

app = FastAPI(
    title="TaskFlow Agent",
    description="Dual-Stream Semantic Synthesis System — transforms raw transcripts into narrative notes and structured action items.",
    version="1.0.0",
)

app.include_router(transcripts_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


# Serve the frontend — must be mounted last so API routes take priority
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
