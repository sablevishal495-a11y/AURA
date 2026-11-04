# AURA — Problem Statement 1 implementation status

AURA is a property-valuation and lender-review-support prototype. It is **not** a production AVM, credit decision engine, or proof of reduced physical inspections.

## Requirement 1 — Scope Indian residential + commercial market
- Existing demo model/data: residential Apartment, Independent House, Villa in six demo cities.
- API accepts a property type string, but the current trained model is not validated for commercial properties.
- **Remaining:** commercial-specific dataset/features/model validation and a documented rollout plan for all Indian states/cities.

## Requirement 2 — Combine structured, unstructured and alternative data
- Implemented: PostgreSQL/PostGIS foundation, property/comparable tables, CSV import, source catalog endpoint (`GET /api/data-catalog/`) and a provenance/quality pipeline contract.
- **Remaining:** licensed/permissioned external connectors, document extraction, geospatial feature ingestion, operational deduplication/quarantine/freshness monitoring. Catalog entries are plans/contracts, not live feeds.

## Requirement 3 — AI/ML model and accuracy
- Implemented: LightGBM pipeline, saved artifact, training/evaluation code and API metrics.
- Current reported metrics are **synthetic-demo-only** and cannot establish real-world accuracy or superiority over existing AVMs.
- **Remaining:** verified transaction labels, temporal/geographic holdouts, baseline comparison, independent benchmark, error analysis by city/property segment.

## Requirement 4 — Explainable valuation
- Implemented: SHAP contributions, estimate/range, comparable records, evidence indicator and disclaimer in valuation API.
- Range is an illustrative MAE band, not a calibrated confidence interval. Evidence indicator is heuristic.
- **Remaining:** calibrated prediction intervals, verified comparable records, persistent model/version/data lineage per valuation, UI presentation/audit review.

## Requirement 5 — Automate and scale
- Implemented: containerized FastAPI + PostgreSQL/PostGIS + React/Vite, CSV ingestion path, source integration contract.
- **Remaining:** scheduled/retryable ingestion workers, production model registry, observability, load testing, deployment/security controls, nationwide data coverage.

## Requirement 6 — Support lending decisions and reduce physical valuations
- Implemented: lender-review API with persistent review record, conservative evidence-based routing, review listing, and explicit human-review requirement.
- Routing statuses: `DEMO_ONLY_MANUAL_REVIEW`, `PHYSICAL_VALUATION_RECOMMENDED`, `DESK_REVIEW_CANDIDATE`.
- **Remaining:** integrate frontend workflow, lender policy configuration, pilot with lender data, measure false acceptance/review outcomes and actual physical-inspection reduction. AURA does not approve/decline loans.

## Data integrity
- Synthetic/demo data must remain visibly labeled.
- Do not report market accuracy, AVM superiority, lender suitability, or inspection reduction until validated on licensed, verified real-world data and a documented pilot.
