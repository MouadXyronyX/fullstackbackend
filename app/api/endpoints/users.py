from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import get_current_user, require_admin
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    users = db.get_all("users", order="created_at.desc")
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    user = db.get_by_id("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("users", user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    user = db.update("users", user_id, data.model_dump(exclude_unset=True))
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
def delete_user(user_id: int, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("users", user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        chats = db.get_all("chats", filters={"user_id": f"eq.{user_id}"}, columns="id")
        for c in chats:
            db.delete_many("messages", {"chat_id": f"eq.{c['id']}"})
            db.delete("chats", c["id"])
    except Exception:
        pass
    try:
        orders = db.get_all("orders", filters={"user_id": f"eq.{user_id}"}, columns="id")
        for o in orders:
            db.delete_many("order_items", {"order_id": f"eq.{o['id']}"})
            db.delete("orders", o["id"])
    except Exception:
        pass
    try:
        db.delete_many("sessions", {"user_id": f"eq.{user_id}"})
    except Exception:
        pass
    try:
        db.delete_many("notifications", {"reference_id": f"eq.{user_id}"})
    except Exception:
        pass
    try:
        db.delete("users", user_id)
    except Exception:
        db.update("users", user_id, {"is_active": False})
        return {"detail": "User disabled instead of deleted"}
    return {"detail": "User deleted successfully"}
