"""Authenticated workspace settings routes."""

from fastapi import APIRouter, Header, HTTPException

from ..schemas.settings import ProfileUpdate
from ..services.user_settings import (
    SettingsAuthenticationError,
    SettingsStoreError,
    read_user_settings,
    save_user_settings,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    return authorization[7:].strip()


@router.get("")
def get_settings(authorization: str | None = Header(default=None)) -> dict:
    try:
        return read_user_settings(_token(authorization))
    except SettingsAuthenticationError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SettingsStoreError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.put("")
def update_settings(
    payload: ProfileUpdate,
    authorization: str | None = Header(default=None),
) -> dict:
    try:
        return save_user_settings(_token(authorization), payload)
    except SettingsAuthenticationError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SettingsStoreError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
