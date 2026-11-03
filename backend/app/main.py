from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.properties import router as properties_router
from app.routers.valuation import router as valuation_router
from app.routers.data_import import router as data_import_router

app = FastAPI(
    title="AURA Property Intelligence API",
    description="AI-powered property valuation and lending intelligence demo.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties_router)
app.include_router(valuation_router)
app.include_router(data_import_router)


@app.get("/")
def root():
    return {
        "message": "AURA API is running",
        "mode": "demo",
        "data_notice": "Synthetic demo data only; imported records require verification.",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
