# AURA PS1 — Run and verify newly added backend endpoints

From the project root in PowerShell:

```powershell
docker compose up -d --build backend
docker compose ps
docker compose logs --tail=60 backend
```

Open Swagger: `http://localhost:8000/docs`

## Data source catalog
- `GET /api/data-catalog/`
- Shows structured, unstructured and alternative data source classes, required provenance and pipeline quality gates.
- It is a connector contract, not evidence that external data feeds are live.

## Lender review workflow
1. Run a valuation in the frontend.
2. In Swagger, call `POST /api/lender-review/` with a body like:

```json
{
  "property_input": {
    "city": "Indore",
    "locality": "Vijay Nagar",
    "property_type": "Apartment",
    "area_sqft": 1200,
    "bedrooms": 2,
    "property_age_years": 5
  },
  "estimated_value_inr": 8000000,
  "low_estimate_inr": 7000000,
  "high_estimate_inr": 9000000,
  "data_source": "SYNTHETIC_DEMO",
  "comparable_count": 0,
  "verified_comparable_count": 0,
  "evidence_quality": "Unavailable",
  "reviewer_note": "Demo review; verify all source data before use."
}
```

3. Confirm response is `DEMO_ONLY_MANUAL_REVIEW` and `human_review_required` is `true`.
4. `GET /api/lender-review/` lists persisted review records.

**Do not use synthetic data to make actual lending decisions.**
