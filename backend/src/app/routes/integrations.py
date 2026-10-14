"""Third-party connection routes."""

from fastapi import APIRouter, HTTPException

from ..data import INTEGRATIONS
from ..schemas import Integration, IntegrationUpdate

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[Integration])
def list_integrations() -> list[Integration]:
    return [Integration(**item) for item in INTEGRATIONS]


@router.patch("/{integration_id}", response_model=Integration)
def update_integration(integration_id: str, payload: IntegrationUpdate) -> Integration:
    for item in INTEGRATIONS:
        if item["id"] == integration_id:
            item["connected"] = payload.connected
            item["status"] = "Connected" if payload.connected else "Available"
            return Integration(**item)
    raise HTTPException(status_code=404, detail="Integration was not found.")
