# app/__init__.py
# Registers all routers
from fastapi import FastAPI
from app.api.routes.transcripts import router as transcripts_router

app = FastAPI(
    title="TaskFlow Agent",
    description="Dual-Stream Semantic Synthesis System — transforms raw transcripts into narrative notes and structured action items.",
    version="0.1.0",
)

app.include_router(transcripts_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return { "message" : "API is running" }

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
