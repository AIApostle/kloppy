"""Authentication routes."""

from fastapi import APIRouter, HTTPException, status
from ..services.auth import AuthConfigurationError, AuthProviderError, AuthSession, SupabaseAuthService
from ..schemas import AuthRequest, SessionResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthRequest) -> SessionResponse:
    """Create an account through Supabase Auth."""
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
    """Authenticate an existing account through Supabase Auth."""
    try:
        session = SupabaseAuthService.from_settings().login(str(payload.email), payload.password)
    except AuthConfigurationError as error:
        raise HTTPException(status_code=503, detail="Authentication is not configured.") from error
    except AuthProviderError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    return _response(session)


def _response(session: AuthSession) -> SessionResponse:
    """Translate the provider session without exposing provider internals."""
    auth_session = session
    return SessionResponse(
        token=auth_session.access_token,
        refresh_token=auth_session.refresh_token,
        expires_at=auth_session.expires_at,
        authenticated=auth_session.access_token is not None,
        message=(
            None
            if auth_session.access_token
            else "Account created. Check your email to confirm it before signing in."
        ),
        user={
            "id": auth_session.user_id,
            "name": auth_session.name,
            "email": auth_session.email,
            "email_confirmed": auth_session.email_confirmed,
        },
    )
