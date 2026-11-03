import io
import math
import os
from datetime import date

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

router = APIRouter(prefix="/api/data-import", tags=["Data Import"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aura_user:aura_dev_password@localhost:5432/aura"
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

REQUIRED_COLUMNS = {
    "city",
    "locality",
    "property_type",
    "area_sqft",
    "transaction_value_inr",
}


@router.post("/comparables-csv")
async def import_comparables_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded CSV is empty.")

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read CSV: {str(exc)}",
        )

    df.columns = [str(column).strip().lower() for column in df.columns]

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV is missing required columns.",
                "missing_columns": sorted(missing_columns),
                "required_columns": sorted(REQUIRED_COLUMNS),
            },
        )

    optional_columns = {
        "transaction_date": None,
        "source_record_id": None,
        "source_name": "CSV_UPLOAD",
    }

    for column, default_value in optional_columns.items():
        if column not in df.columns:
            df[column] = default_value

    df["city"] = df["city"].astype("string").str.strip()
    df["locality"] = df["locality"].astype("string").str.strip()
    df["property_type"] = df["property_type"].astype("string").str.strip()

    df["area_sqft"] = pd.to_numeric(df["area_sqft"], errors="coerce")
    df["transaction_value_inr"] = pd.to_numeric(
        df["transaction_value_inr"], errors="coerce"
    )

    df = df.dropna(
        subset=[
            "city",
            "locality",
            "property_type",
            "area_sqft",
            "transaction_value_inr",
        ]
    )

    df = df[
        (df["city"] != "")
        & (df["locality"] != "")
        & (df["property_type"] != "")
        & (df["area_sqft"] > 0)
        & (df["transaction_value_inr"] > 0)
    ].copy()

    df["rate_per_sqft_inr"] = (
        df["transaction_value_inr"] / df["area_sqft"]
    )

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce"
    ).dt.date

    df = df.replace({pd.NA: None})
    df = df.where(pd.notnull(df), None)

    records = df.to_dict(orient="records")

    if not records:
        raise HTTPException(
            status_code=400,
            detail="No valid records remained after cleaning.",
        )

    inserted = 0

    async with engine.begin() as connection:
        for record in records:
            source_name = str(record.get("source_name") or "CSV_UPLOAD").strip()

            source_result = await connection.execute(
                text("""
                    INSERT INTO data_sources
                        (source_name, source_type, license_notes)
                    VALUES
                        (:source_name, 'CSV_UPLOAD', 'Uploaded by AURA user; verify source rights and authenticity.')
                    RETURNING source_id
                """),
                {"source_name": source_name},
            )

            source_id = source_result.scalar_one()

            await connection.execute(
                text("""
                    INSERT INTO property_comparables (
                        source_id,
                        city,
                        locality,
                        property_type,
                        transaction_date,
                        area_sqft,
                        transaction_value_inr,
                        rate_per_sqft_inr,
                        data_source,
                        source_record_id,
                        is_verified
                    )
                    VALUES (
                        :source_id,
                        :city,
                        :locality,
                        :property_type,
                        :transaction_date,
                        :area_sqft,
                        :transaction_value_inr,
                        :rate_per_sqft_inr,
                        :data_source,
                        :source_record_id,
                        FALSE
                    )
                """),
                {
                    "source_id": source_id,
                    "city": str(record["city"]),
                    "locality": str(record["locality"]),
                    "property_type": str(record["property_type"]),
                    "transaction_date": record.get("transaction_date"),
                    "area_sqft": float(record["area_sqft"]),
                    "transaction_value_inr": float(record["transaction_value_inr"]),
                    "rate_per_sqft_inr": float(record["rate_per_sqft_inr"]),
                    "data_source": source_name,
                    "source_record_id": (
                        str(record["source_record_id"])
                        if record.get("source_record_id") is not None
                        else None
                    ),
                },
            )

            inserted += 1

    return {
        "message": "CSV import completed.",
        "filename": file.filename,
        "inserted_records": inserted,
        "verified_records": 0,
        "notice": "Imported records are unverified until their source and authenticity are checked.",
    }
