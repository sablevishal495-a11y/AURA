"""AURA lender-review support workflow. It assists review; it does not approve/decline loans."""
import os
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

router = APIRouter(prefix="/api/lender-review", tags=["Lender Review"])
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aura_user:aura_dev_password@localhost:5432/aura",
)
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)


class ReviewCreate(BaseModel):
    property_input: dict = Field(description="Property inputs used for valuation")
    estimated_value_inr: float = Field(gt=0)
    low_estimate_inr: float = Field(ge=0)
    high_estimate_inr: float = Field(gt=0)
    data_source: str = Field(min_length=1, max_length=100)
    comparable_count: int = Field(ge=0)
    verified_comparable_count: int = Field(ge=0)
    evidence_quality: Literal["Higher", "Moderate", "Low", "Unavailable"]
    reviewer_note: str = Field(default="", max_length=2000)


@router.on_event("startup")
async def create_review_table():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lender_valuation_reviews (
                review_id VARCHAR(36) PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                property_input JSONB NOT NULL,
                estimated_value_inr DOUBLE PRECISION NOT NULL,
                low_estimate_inr DOUBLE PRECISION NOT NULL,
                high_estimate_inr DOUBLE PRECISION NOT NULL,
                data_source VARCHAR(100) NOT NULL,
                comparable_count INTEGER NOT NULL,
                verified_comparable_count INTEGER NOT NULL,
                evidence_quality VARCHAR(20) NOT NULL,
                review_status VARCHAR(40) NOT NULL,
                routing_reason TEXT NOT NULL,
                reviewer_note TEXT NOT NULL DEFAULT ''
            )
        """))


def route_review(payload: ReviewCreate) -> tuple[str, str]:
    # Conservative demo routing rules. Not a credit decision or calibrated risk score.
    if payload.data_source.upper() == "SYNTHETIC_DEMO":
        return "DEMO_ONLY_MANUAL_REVIEW", "Synthetic model data cannot support a real lending decision."
    if payload.verified_comparable_count < 3:
        return "PHYSICAL_VALUATION_RECOMMENDED", "Fewer than 3 verified comparable records are available."
    if payload.evidence_quality in {"Low", "Unavailable"}:
        return "PHYSICAL_VALUATION_RECOMMENDED", "Evidence quality is insufficient for desk-review reliance."
    if payload.high_estimate_inr < payload.low_estimate_inr:
        raise HTTPException(status_code=422, detail="High estimate must be >= low estimate.")
    return "DESK_REVIEW_CANDIDATE", "Sufficient verified comparable evidence for reviewer assessment; human approval remains required."


@router.post("/", status_code=201)
async def create_lender_review(payload: ReviewCreate):
    status, reason = route_review(payload)
    review_id = str(uuid4())
    created_at = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO lender_valuation_reviews (
                review_id, created_at, property_input, estimated_value_inr,
                low_estimate_inr, high_estimate_inr, data_source,
                comparable_count, verified_comparable_count, evidence_quality,
                review_status, routing_reason, reviewer_note
            ) VALUES (
                :review_id, :created_at, CAST(:property_input AS JSONB), :estimated,
                :low, :high, :source, :count, :verified, :quality, :status, :reason, :note
            )
        """), {
            "review_id": review_id,
            "created_at": created_at,
            "property_input": __import__("json").dumps(payload.property_input),
            "estimated": payload.estimated_value_inr,
            "low": payload.low_estimate_inr,
            "high": payload.high_estimate_inr,
            "source": payload.data_source,
            "count": payload.comparable_count,
            "verified": payload.verified_comparable_count,
            "quality": payload.evidence_quality,
            "status": status,
            "reason": reason,
            "note": payload.reviewer_note,
        })
    return {
        "review_id": review_id,
        "created_at": created_at.isoformat(),
        "review_status": status,
        "routing_reason": reason,
        "human_review_required": True,
        "notice": "AURA provides valuation-review support only; this endpoint does not approve or decline credit.",
    }


@router.get("/")
async def list_lender_reviews(limit: int = 50):
    if not 1 <= limit <= 200:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 200")
    async with engine.connect() as conn:
        rows = (await conn.execute(text("""
            SELECT review_id, created_at, property_input, estimated_value_inr,
                   low_estimate_inr, high_estimate_inr, data_source,
                   comparable_count, verified_comparable_count, evidence_quality,
                   review_status, routing_reason, reviewer_note
            FROM lender_valuation_reviews ORDER BY created_at DESC LIMIT :limit
        """), {"limit": limit})).mappings().all()
    return {"count": len(rows), "reviews": [dict(row) for row in rows]}
