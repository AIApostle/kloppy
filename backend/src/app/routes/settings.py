"""Workspace settings routes."""

from fastapi import APIRouter

from ..data import PROFILE
from ..schemas import ProfileUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings() -> dict:
    return PROFILE.copy()


@router.put("")
def update_settings(payload: ProfileUpdate) -> dict:
    PROFILE.update(payload.model_dump())
    return PROFILE.copy()
