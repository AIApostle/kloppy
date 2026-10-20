"""Authenticated routes for Qloo cultural-intelligence capabilities."""

from fastapi import APIRouter, Header, HTTPException

from ..schemas.qloo import QlooCapabilityRequest
from ..services.qloo import QlooConfigurationError, QlooProviderError, run_capability
from ..services.user_settings import SettingsAuthenticationError, SettingsStoreError, read_user_settings

router = APIRouter(prefix="/qloo", tags=["qloo"])


def _access_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    return authorization[7:].strip()


@router.post("/run")
def run_qloo(
    payload: QlooCapabilityRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    token = _access_token(authorization)
    try:
        read_user_settings(token)
        return run_capability(payload)
    except SettingsAuthenticationError as error:
        raise HTTPException(status_code=401, detail="Authentication could not be verified.") from error
    except SettingsStoreError as error:
        raise HTTPException(status_code=503, detail="User settings could not be verified.") from error
    except QlooConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except QlooProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
