"""Source catalog and provenance contract for AURA's multi-source ingestion pipeline.

This endpoint documents/configures source classes. It does not imply that external
feeds are connected or licensed; connectors must be implemented and credentials
provided per source before ingestion can be marked live.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/data-catalog", tags=["Data Catalog"])

SOURCES = [
    {
        "source_id": "registered_transactions",
        "category": "structured",
        "examples": ["licensed registered-sale/transaction datasets", "verified bank valuation records"],
        "ingestion_mode": "licensed connector or validated CSV",
        "required_provenance": ["provider", "license_or_permission", "record_id", "transaction_date", "ingested_at"],
        "status": "connector_required",
        "usage": "Primary transaction labels; use only when source rights and authenticity are verified.",
    },
    {
        "source_id": "listing_and_property_documents",
        "category": "unstructured",
        "examples": ["property listings", "sale documents", "valuation reports"],
        "ingestion_mode": "permitted API/file ingestion followed by extraction and human QA",
        "required_provenance": ["provider", "source_url_or_document_id", "license_or_permission", "ingested_at", "extraction_version"],
        "status": "connector_required",
        "usage": "Extract property attributes; listings are asking prices, not confirmed transaction prices.",
    },
    {
        "source_id": "geospatial_and_infrastructure",
        "category": "alternative",
        "examples": ["permitted GIS layers", "road/transit/amenity proximity", "land-use and hazard layers"],
        "ingestion_mode": "licensed geospatial API or versioned GIS files",
        "required_provenance": ["provider", "layer_name", "license_or_permission", "geography_version", "ingested_at"],
        "status": "connector_required",
        "usage": "Contextual features only; apply spatial validation and avoid sensitive/inappropriate proxies.",
    },
]


@router.get("/")
def get_data_catalog():
    return {
        "sources": SOURCES,
        "pipeline_contract": [
            "validate source rights and provenance",
            "normalize city/locality/property-type vocabulary and units",
            "validate ranges and required fields; quarantine invalid rows",
            "deduplicate by provider record ID and fallback fingerprints",
            "retain source lineage, timestamps, and transformation version",
            "separate verified transactions from asking-price and synthetic records",
            "monitor freshness, missingness, drift, and ingestion failures",
        ],
        "status_notice": "Catalog and ingestion contract are implemented; external source connectors and credentials are not included.",
    }
