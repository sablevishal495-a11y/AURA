from pathlib import Path
import os

import joblib
import pandas as pd
import shap
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

router = APIRouter(prefix="/api/valuation", tags=["Valuation"])

MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "ml"
    / "artifacts"
    / "property_valuation_model.joblib"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aura_user:aura_dev_password@localhost:5432/aura",
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

# Load the trained model and initialize SHAP.
try:
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    FEATURES = artifact["features"]
    METRICS = artifact["metrics"]

    # The artifact is an sklearn Pipeline.
    # SHAP must explain the LightGBM estimator inside it.
    preprocessor = model.named_steps["preprocessor"]
    regressor = model.named_steps["regressor"]
    explainer = shap.TreeExplainer(regressor)

except Exception as exc:
    model = None
    preprocessor = None
    regressor = None
    explainer = None
    FEATURES = []
    METRICS = {}
    artifact = {}
    print(f"Could not load valuation model or SHAP explainer: {exc}")


class ValuationRequest(BaseModel):
    city: str
    locality: str
    property_type: str = "Apartment"
    area_sqft: float = Field(gt=0)
    bedrooms: int = Field(ge=0)
    bathrooms: int = Field(ge=0, default=1)
    property_age_years: int = Field(ge=0, default=0)
    floor_number: int = Field(ge=0, default=0)
    furnishing_status: str = "Unfurnished"


def get_shap_explanation(input_df: pd.DataFrame):
    """
    Explain the prediction using SHAP values from the transformed
    input features and the LightGBM estimator.
    """
    if explainer is None or preprocessor is None:
        return {
            "method": "SHAP TreeExplainer",
            "available": False,
            "top_factors": [],
            "notice": "SHAP explanation is currently unavailable.",
        }

    try:
        # Apply the exact preprocessing used by the trained pipeline.
        transformed_input = preprocessor.transform(input_df)

        # OneHotEncoder may return a sparse CSR matrix.
        # Convert it to a dense array for SHAP.
        if hasattr(transformed_input, "toarray"):
            transformed_input = transformed_input.toarray()

        shap_values = explainer.shap_values(transformed_input)

        # Normalize SHAP output format.
        if isinstance(shap_values, list):
            shap_values = shap_values[0]

        values = shap_values[0]

        transformed_feature_names = preprocessor.get_feature_names_out()

        base_value = explainer.expected_value
        if hasattr(base_value, "__len__"):
            base_value = base_value[0]

        factors = []

        for index, transformed_feature in enumerate(transformed_feature_names):
            impact = float(values[index])
            feature_name = str(transformed_feature)

            if feature_name.startswith("categorical__"):
                readable_name = feature_name.replace("categorical__", "")
            elif feature_name.startswith("numeric__"):
                readable_name = feature_name.replace("numeric__", "")
            else:
                readable_name = feature_name

            readable_name = readable_name.replace("_", " ").title()

            factors.append(
                {
                    "feature": feature_name,
                    "label": readable_name,
                    "impact_inr": round(impact, 2),
                    "direction": (
                        "increases_estimate"
                        if impact > 0
                        else "decreases_estimate"
                        if impact < 0
                        else "neutral"
                    ),
                    "absolute_impact": abs(impact),
                }
            )

        # Return the five strongest feature contributions.
        factors.sort(
            key=lambda item: item["absolute_impact"],
            reverse=True,
        )

        top_factors = factors[:5]

        for factor in top_factors:
            factor.pop("absolute_impact", None)

        return {
            "method": "SHAP TreeExplainer",
            "available": True,
            "base_value_inr": round(float(base_value), 2),
            "top_factors": top_factors,
            "notice": (
                "SHAP values explain how model features influence this estimate. "
                "They do not prove causal effects or guarantee real-world market value."
            ),
        }

    except Exception as exc:
        print(f"SHAP explanation failed: {exc}")

        return {
            "method": "SHAP TreeExplainer",
            "available": False,
            "top_factors": [],
            "notice": f"SHAP explanation failed: {str(exc)}",
        }


@router.post("/")
async def estimate_valuation(request: ValuationRequest):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Valuation model is not available. Check the model artifact.",
        )

    property_data = request.model_dump()
    input_df = pd.DataFrame([property_data], columns=FEATURES)

    try:
        predicted_value = float(model.predict(input_df)[0])
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Valuation prediction failed: {str(exc)}",
        )

    # Generate SHAP explanations for this prediction.
    explainability = get_shap_explanation(input_df)

    mae = float(METRICS.get("mae", 0))
    low_estimate = max(0, predicted_value - mae)
    high_estimate = predicted_value + mae

    # Fetch comparable records for the same city, locality, and property type.
    comparable_query = text(
        """
        SELECT
            city,
            locality,
            property_type,
            area_sqft,
            transaction_value_inr,
            rate_per_sqft_inr,
            data_source,
            is_verified
        FROM property_comparables
        WHERE LOWER(city) = LOWER(:city)
          AND LOWER(locality) = LOWER(:locality)
          AND LOWER(property_type) = LOWER(:property_type)
          AND area_sqft > 0
          AND transaction_value_inr > 0
        ORDER BY comparable_id DESC
        LIMIT 10
        """
    )

    async with engine.connect() as connection:
        result = await connection.execute(
            comparable_query,
            {
                "city": request.city,
                "locality": request.locality,
                "property_type": request.property_type,
            },
        )
        comparable_rows = result.mappings().all()

    comparables = []

    for row in comparable_rows:
        comparables.append(
            {
                "city": row["city"],
                "locality": row["locality"],
                "property_type": row["property_type"],
                "area_sqft": row["area_sqft"],
                "transaction_value_inr": row["transaction_value_inr"],
                "rate_per_sqft_inr": row["rate_per_sqft_inr"],
                "data_source": row["data_source"],
                "is_verified": row["is_verified"],
            }
        )

    comparable_count = len(comparables)

    if comparable_count:
        average_rate = sum(
            float(item["rate_per_sqft_inr"]) for item in comparables
        ) / comparable_count

        comparable_estimate = average_rate * request.area_sqft

        difference_inr = predicted_value - comparable_estimate

        difference_percentage = (
            (difference_inr / comparable_estimate) * 100
            if comparable_estimate > 0
            else None
        )

        verified_count = sum(
            1 for item in comparables if item["is_verified"]
        )

        if verified_count >= 5:
            evidence_quality = "Higher"
        elif verified_count >= 1:
            evidence_quality = "Moderate"
        else:
            evidence_quality = "Low"

    else:
        average_rate = None
        comparable_estimate = None
        difference_inr = None
        difference_percentage = None
        verified_count = 0
        evidence_quality = "Unavailable"

    return {
        "estimated_value_inr": round(predicted_value, 2),
        "low_estimate_inr": round(low_estimate, 2),
        "high_estimate_inr": round(high_estimate, 2),
        "model": "LightGBM",
        "data_source": artifact.get("data_source", "UNKNOWN"),

        "evaluation_metrics": {
            "mae_inr": round(mae, 2),
            "rmse_inr": round(float(METRICS.get("rmse", 0)), 2),
            "r2": round(float(METRICS.get("r2", 0)), 4),
            "evaluation_data": "Synthetic demo data",
        },

        "explainability": explainability,

        "model_vs_comparable": {
            "model_estimate_inr": round(predicted_value, 2),
            "comparable_estimate_inr": (
                round(comparable_estimate, 2)
                if comparable_estimate is not None
                else None
            ),
            "difference_inr": (
                round(difference_inr, 2)
                if difference_inr is not None
                else None
            ),
            "difference_percentage": (
                round(difference_percentage, 2)
                if difference_percentage is not None
                else None
            ),
            "notice": (
                "Comparison uses imported comparable records, which may be unverified."
            ),
        },

        "evidence_quality": {
            "quality": evidence_quality,
            "comparable_count": comparable_count,
            "verified_comparable_count": verified_count,
            "notice": (
                "Evidence quality is a simple demo indicator based on comparable "
                "record verification and count. It is not a calibrated confidence score."
            ),
        },

        "comparable_insights": {
            "comparable_count": comparable_count,
            "average_rate_per_sqft_inr": (
                round(average_rate, 2)
                if average_rate is not None
                else None
            ),
            "comparable_estimate_inr": (
                round(comparable_estimate, 2)
                if comparable_estimate is not None
                else None
            ),
            "records": comparables,
            "notice": (
                "Comparable records are imported demo data and may be unverified."
                if comparable_count
                else "No matching comparable records found for this location and property type."
            ),
        },

        "disclaimer": (
            "Demo estimate trained on synthetic data. "
            "Comparable records are not necessarily verified transactions. "
            "Not a verified market valuation or lending decision. "
            "The displayed range is illustrative, not a calibrated confidence interval."
        ),
    }
