from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import create_engine
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from lightgbm import LGBMRegressor


# --------------------------------------------------
# Configuration
# --------------------------------------------------
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "ML_DATABASE_URL",
    "postgresql+psycopg2://aura_user:aura_dev_password@db:5432/aura",
)

engine = create_engine(DATABASE_URL)

MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "property_valuation_model.joblib"


# --------------------------------------------------
# Load data
# --------------------------------------------------

query = """
SELECT
    city,
    locality,
    property_type,
    area_sqft,
    bedrooms,
    bathrooms,
    property_age_years,
    floor_number,
    furnishing_status,
    estimated_value_inr,
    data_source
FROM properties
"""

df = pd.read_sql(query, engine)

print(f"Loaded {len(df)} records")


# --------------------------------------------------
# Basic data cleaning
# --------------------------------------------------

# Train only on explicitly identified synthetic demo records.
df = df[df["data_source"] == "SYNTHETIC_DEMO"].copy()

# Remove missing or invalid target/area records.
df = df.dropna(
    subset=[
        "area_sqft",
        "estimated_value_inr",
        "city",
        "property_type",
    ]
)

df = df[
    (df["area_sqft"] > 0)
    & (df["estimated_value_inr"] > 0)
]

# Basic plausibility filters for demo data.
df = df[
    (df["bedrooms"].between(0, 10))
    & (df["bathrooms"].between(0, 10))
    & (df["property_age_years"].between(0, 100))
    & (df["floor_number"].between(0, 60))
]

print(f"Records after cleaning: {len(df)}")


# --------------------------------------------------
# Features and target
# --------------------------------------------------

FEATURES = [
    "city",
    "locality",
    "property_type",
    "area_sqft",
    "bedrooms",
    "bathrooms",
    "property_age_years",
    "floor_number",
    "furnishing_status",
]

TARGET = "estimated_value_inr"

X = df[FEATURES]
y = df[TARGET]


# --------------------------------------------------
# Train/test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
)


# --------------------------------------------------
# Preprocessing
# --------------------------------------------------

categorical_features = [
    "city",
    "locality",
    "property_type",
    "furnishing_status",
]

numeric_features = [
    "area_sqft",
    "bedrooms",
    "bathrooms",
    "property_age_years",
    "floor_number",
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        ),
        ("numeric", "passthrough", numeric_features),
    ]
)


# --------------------------------------------------
# Model
# --------------------------------------------------

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "regressor",
            LGBMRegressor(
                n_estimators=300,
                learning_rate=0.05,
                num_leaves=31,
                random_state=42,
                verbosity=-1,
            ),
        ),
    ]
)


# --------------------------------------------------
# Train and evaluate
# --------------------------------------------------

print("Training LightGBM model...")

model.fit(X_train, y_train)

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
rmse = mean_squared_error(y_test, predictions) ** 0.5
r2 = r2_score(y_test, predictions)

print("\n----- MODEL EVALUATION -----")
print(f"MAE:  ₹{mae:,.2f}")
print(f"RMSE: ₹{rmse:,.2f}")
print(f"R²:   {r2:.4f}")
print("----------------------------")


# --------------------------------------------------
# Save model and metadata
# --------------------------------------------------

joblib.dump(
    {
        "model": model,
        "features": FEATURES,
        "target": TARGET,
        "data_source": "SYNTHETIC_DEMO",
        "metrics": {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
        },
    },
    MODEL_PATH,
)

print(f"\nModel saved to: {MODEL_PATH}")
print("NOTE: This model was trained on synthetic demo data.")