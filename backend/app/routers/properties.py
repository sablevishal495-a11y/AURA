from fastapi import APIRouter, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os

router = APIRouter(prefix="/api/properties", tags=["Properties"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aura_user:aura_dev_password@localhost:5432/aura"
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)


@router.get("/")
async def get_properties(
    city: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = """
        SELECT property_id, city, locality, property_type,
               area_sqft, bedrooms, bathrooms, property_age_years,
               floor_number, furnishing_status, rate_per_sqft_inr,
               estimated_value_inr, data_source
        FROM properties
    """
    params = {"limit": limit, "offset": offset}

    if city:
        query += " WHERE LOWER(city) = LOWER(:city)"
        params["city"] = city

    query += " ORDER BY property_id LIMIT :limit OFFSET :offset"

    async with engine.connect() as connection:
        result = await connection.execute(text(query), params)
        rows = result.mappings().all()

    return {
        "count": len(rows),
        "limit": limit,
        "offset": offset,
        "data": [dict(row) for row in rows],
    }