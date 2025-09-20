from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.notes import router as notes_router
from app.api.vitals import router as vitals_router
from app.api import patients, summarize, qa, documents

app = FastAPI()

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],  # Allow your frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(patients.router, prefix="/patients", tags=["patients"])
app.include_router(summarize.router, prefix="/patients", tags=["summarize"])
app.include_router(qa.router, prefix="/patients", tags=["qa"])
app.include_router(documents.router, prefix="/patients", tags=["documents"])
app.include_router(notes_router, prefix="/patients", tags=["notes"])
app.include_router(vitals_router, prefix="", tags=["vitals"])  # No prefix for /vitals endpoint

@app.get("/")
async def root():
    return {"message": "EMR AI Backend running"}
