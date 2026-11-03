from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
ROWS = 2000

rng = np.random.default_rng(SEED)

# Synthetic Indian city/locality examples for demo purposes only.
localities = {
    "Mumbai": ["Andheri", "Powai", "Borivali", "Thane"],
    "Pune": ["Hinjewadi", "Wakad", "Kothrud", "Baner"],
    "Bengaluru": ["Whitefield", "Electronic City", "Indiranagar", "Hebbal"],
    "Delhi": ["Dwarka", "Rohini", "Saket", "Vasant Kunj"],
    "Hyderabad": ["Gachibowli", "Kukatpally", "Miyapur", "HITEC City"],
    "Indore": ["Vijay Nagar", "Rau", "Palasia", "Super Corridor"],
}

city_base_rate = {
    "Mumbai": 18000,
    "Pune": 8500,
    "Bengaluru": 10000,
    "Delhi": 12000,
    "Hyderabad": 7500,
    "Indore": 4500,
}

cities = rng.choice(list(localities.keys()), size=ROWS)

records = []

for i, city in enumerate(cities):
    locality = rng.choice(localities[city])

    area_sqft = int(rng.integers(350, 3500))
    bedrooms = int(rng.integers(1, 6))
    property_age_years = int(rng.integers(0, 35))
    floor_number = int(rng.integers(0, 25))
    total_floors = int(max(floor_number, rng.integers(1, 30)))

    property_type = rng.choice(
        ["Apartment", "Independent House", "Villa"],
        p=[0.70, 0.20, 0.10],
    )

    furnishing = rng.choice(
        ["Unfurnished", "Semi-Furnished", "Furnished"],
        p=[0.35, 0.40, 0.25],
    )

    locality_multiplier = rng.uniform(0.85, 1.25)
    age_multiplier = max(0.65, 1 - property_age_years * 0.008)
    floor_multiplier = 1 + min(floor_number, 15) * 0.003
    furnishing_multiplier = {
        "Unfurnished": 1.00,
        "Semi-Furnished": 1.05,
        "Furnished": 1.12,
    }[furnishing]

    rate_per_sqft = (
        city_base_rate[city]
        * locality_multiplier
        * age_multiplier
        * floor_multiplier
        * furnishing_multiplier
        * rng.uniform(0.90, 1.10)
    )

    estimated_value_inr = round(area_sqft * rate_per_sqft, 2)

    records.append(
        {
            "property_id": f"AURA-DEMO-{i + 1:05d}",
            "city": city,
            "locality": locality,
            "property_type": property_type,
            "area_sqft": area_sqft,
            "bedrooms": bedrooms,
            "property_age_years": property_age_years,
            "floor_number": floor_number,
            "total_floors": total_floors,
            "furnishing": furnishing,
            "rate_per_sqft_inr": round(rate_per_sqft, 2),
            "estimated_value_inr": estimated_value_inr,
            "data_source": "SYNTHETIC_DEMO",
        }
    )

df = pd.DataFrame(records)

output_dir = Path("/app/data/demo")
output_dir = Path("/app/data/demo")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "synthetic_properties.csv"
df.to_csv(output_file, index=False)

print(f"Generated {len(df)} synthetic property records.")
print(f"Saved to: {output_file}")
print(df.head())