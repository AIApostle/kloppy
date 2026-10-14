"""Dashboard and campaign routes."""

from fastapi import APIRouter

from ..data import dashboard_payload
from ..schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    return DashboardResponse(**dashboard_payload())
