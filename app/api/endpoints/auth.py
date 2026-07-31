import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from datetime import datetime, timezone, timedelta
from app.services.db import SupabaseDB, get_db
from app.core.rate_limit import limiter
from app.core.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    decode_token, generate_totp_secret, get_totp_uri, generate_totp_qrcode, verify_totp
)
from app.core.dependencies import get_current_user, require_admin
from app.schemas.user import (
    UserCreate, UserLogin, AdminLogin, UserResponse, TokenResponse,
    RefreshRequest, TOTPSetupResponse, TOTPVerifyRequest, UserUpdate
)

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _create_tokens(user: dict, db: SupabaseDB) -> dict:
    access_token = create_access_token({"sub": str(user["id"])})
    refresh_token = create_refresh_token({"sub": str(user["id"])})
    from datetime import timedelta
    from app.core.config import get_settings
    settings = get_settings()
    db.insert("sessions", {
        "user_id": user["id"],
        "refresh_token": refresh_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)).isoformat(),
    })
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


def _safe_verify(plain: str, hashed: str) -> bool:
    try:
        return verify_password(plain, hashed)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def _register_failed_attempt(db: SupabaseDB, user: dict):
    try:
        attempts = int(user.get("failed_login_attempts") or 0) + 1
        update = {"failed_login_attempts": attempts}
        if attempts >= MAX_FAILED_ATTEMPTS:
            update["locked_until"] = (
                datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            ).isoformat()
        db.update("users", user["id"], update)
    except Exception as e:
        logger.error(f"Failed-attempt update error: {e}")


def _check_lockout(user: dict):
    locked_until = user.get("locked_until")
    if not locked_until:
        return
    if isinstance(locked_until, str):
        try:
            locked_until = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
        except ValueError:
            return
    if locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=423, detail="Account is locked. Try again later.")


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, data: UserCreate, db: SupabaseDB = Depends(get_db)):
    if not data.email and not data.phone:
        raise HTTPException(status_code=400, detail="Email or phone is required")
    if data.email:
        existing = db.get_one("users", {"email": f"eq.{data.email}"})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
    if data.phone:
        existing = db.get_one("users", {"phone": f"eq.{data.phone}"})
        if existing:
            raise HTTPException(status_code=400, detail="Phone already registered")

    role = db.get_one("roles", {"name": f"eq.customer"})
    if not role:
        role = db.insert("roles", {"name": "customer"})
    if not role:
        raise HTTPException(status_code=500, detail="Failed to create or retrieve user role")

    try:
        user = db.insert("users", {
            "name": data.name,
            "email": data.email,
            "phone": data.phone,
            "password_hash": get_password_hash(data.password),
            "role_id": role["id"] if isinstance(role, dict) else role[0]["id"],
            "is_active": True,
        })
        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        return _create_tokens(user, db)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, data: UserLogin, db: SupabaseDB = Depends(get_db)):
    user = None
    if data.email:
        user = db.get_one("users", {"email": f"eq.{data.email}"})
    elif data.phone:
        user = db.get_one("users", {"phone": f"eq.{data.phone}"})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_active", False):
        raise HTTPException(status_code=403, detail="Account is disabled")

    _check_lockout(user)

    if not _safe_verify(data.password, user.get("password_hash", "")):
        _register_failed_attempt(db, user)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        db.update("users", user["id"], {"failed_login_attempts": 0, "locked_until": None})
    except Exception as e:
        logger.error(f"Login update error: {e}")

    try:
        return _create_tokens(user, db)
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/admin-login", response_model=TokenResponse)
@limiter.limit("10/minute")
def admin_login(request: Request, data: AdminLogin, db: SupabaseDB = Depends(get_db)):
    user = db.get_one("users", {"email": f"eq.{data.email}", "role_id": f"eq.1"})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    if not user.get("is_active", False):
        raise HTTPException(status_code=403, detail="Account is disabled")

    _check_lockout(user)

    if not _safe_verify(data.password, user.get("password_hash", "")):
        _register_failed_attempt(db, user)
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    if user.get("totp_enabled", False):
        return {
            "access_token": "",
            "refresh_token": "",
            "token_type": "bearer",
            "user": UserResponse.model_validate(user),
            "totp_required": True,
        }

    try:
        db.update("users", user["id"], {"failed_login_attempts": 0, "locked_until": None})
    except Exception as e:
        logger.error(f"Admin login update error: {e}")

    try:
        return _create_tokens(user, db)
    except Exception as e:
        logger.error(f"Admin token creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Admin login failed: {str(e)}")


@router.post("/admin-login-totp", response_model=TokenResponse)
@limiter.limit("10/minute")
def admin_login_totp(request: Request, data: TOTPVerifyRequest, user_id: int, db: SupabaseDB = Depends(get_db)):
    user = db.get_by_id("users", user_id)
    if not user or not user.get("totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP not enabled")

    if not verify_totp(user.get("totp_secret", ""), data.code):
        _register_failed_attempt(db, user)
        raise HTTPException(status_code=401, detail="Invalid TOTP code")

    try:
        db.update("users", user["id"], {"failed_login_attempts": 0, "locked_until": None})
    except Exception as e:
        logger.error(f"TOTP login update error: {e}")

    return _create_tokens(user, db)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
def refresh_token(request: Request, data: RefreshRequest, db: SupabaseDB = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    session = db.get_one("sessions", {
        "user_id": f"eq.{int(user_id)}",
        "refresh_token": f"eq.{data.refresh_token}",
    })
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    expires_at = session.get("expires_at")
    if expires_at:
        if isinstance(expires_at, str):
            from datetime import datetime
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")

    user = db.get_by_id("users", int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    db.delete("sessions", session["id"])

    return _create_tokens(user, db)


@router.get("/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.post("/totp/setup", response_model=TOTPSetupResponse)
@limiter.limit("10/minute")
def setup_totp(request: Request, user: dict = Depends(require_admin), db: SupabaseDB = Depends(get_db)):
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, user.get("email") or user.get("name", ""))
    qrcode = generate_totp_qrcode(uri)
    db.update("users", user["id"], {"totp_secret": secret, "totp_enabled": False})
    return {"secret": secret, "uri": uri, "qrcode": qrcode}


@router.post("/totp/verify-enable")
def verify_enable_totp(data: TOTPVerifyRequest, user: dict = Depends(require_admin), db: SupabaseDB = Depends(get_db)):
    if not verify_totp(user.get("totp_secret", ""), data.code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    db.update("users", user["id"], {"totp_enabled": True})
    return {"detail": "TOTP enabled successfully"}


@router.post("/totp/disable")
def disable_totp(user: dict = Depends(require_admin), db: SupabaseDB = Depends(get_db)):
    db.update("users", user["id"], {"totp_enabled": False, "totp_secret": None})
    return {"detail": "TOTP disabled"}


@router.post("/admin-delete-user")
def admin_delete_user(email: str, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    user = db.get_one("users", {"email": f"eq.{email}"})
    if user:
        db.delete_many("sessions", {"user_id": f"eq.{user['id']}"})
        db.delete("users", user["id"])
        return {"detail": f"User '{email}' deleted"}
    return {"detail": f"User '{email}' not found"}
