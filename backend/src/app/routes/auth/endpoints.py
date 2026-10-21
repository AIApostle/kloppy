"""Supabase authentication endpoints."""

from fastapi import APIRouter, Header, HTTPException, status

from ...schemas.auth import AuthRequest, SessionResponse
from ...services.auth import (
    AuthConfigurationError,
    AuthProviderError,
    AuthSession,
    SupabaseAuthService,
)
from ...services.user_settings import (
    SettingsAuthenticationError,
    SettingsStoreError,
    _user_id,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/session")
def verify_session(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    access_token = authorization[7:].strip()
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    try:
        return {"user_id": _user_id(access_token)}
    except SettingsAuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication could not be verified.",
        ) from error
    except SettingsStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication could not be verified right now.",
        ) from error


@router.post("/signup", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthRequest) -> SessionResponse:
    try:
        session = SupabaseAuthService.from_settings().signup(
            str(payload.email), payload.password, payload.name
        )
    except AuthConfigurationError as error:
        raise HTTPException(status_code=503, detail="Authentication is not configured.") from error
    except AuthProviderError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _response(session)


@router.post("/login", response_model=SessionResponse)
def login(payload: AuthRequest) -> SessionResponse:
    try:
        session = SupabaseAuthService.from_settings().login(str(payload.email), payload.password)
    except AuthConfigurationError as error:
        raise HTTPException(status_code=503, detail="Authentication is not configured.") from error
    except AuthProviderError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    return _response(session)


def _response(session: AuthSession) -> SessionResponse:
    return SessionResponse(
        token=session.access_token,
        refresh_token=session.refresh_token,
        expires_at=session.expires_at,
        authenticated=session.access_token is not None,
        message=None if session.access_token else "Account created. Check your email to confirm it before signing in.",
        user={
            "id": session.user_id,
            "name": session.name,
            "email": session.email,
            "email_confirmed": session.email_confirmed,
        },
    )
