from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import require_admin
from app.schemas.setting import SettingCreate, SettingUpdate, SettingResponse, GeneralSettings

router = APIRouter()

PUBLIC_KEYS = ["store_name", "store_description", "facebook_url", "instagram_url",
               "whatsapp_number", "phone", "email", "address", "working_hours"]


@router.get("/public", response_model=Dict[str, str])
def get_public_settings(db: SupabaseDB = Depends(get_db)):
    settings = db.get_all("settings")
    result = {}
    keys_set = set(PUBLIC_KEYS)
    for s in settings:
        if s.get("key") in keys_set:
            result[s["key"]] = s.get("value") or ""
    return result


@router.get("/", response_model=List[SettingResponse])
def get_all_settings(admin=Depends(require_admin), db: SupabaseDB = Depends(get_db)):
    settings = db.get_all("settings", order="key.asc")
    return [SettingResponse.model_validate(s) for s in settings]


@router.get("/general", response_model=GeneralSettings)
def get_general_settings(db: SupabaseDB = Depends(get_db)):
    settings = db.get_all("settings")
    result = {k: "" for k in PUBLIC_KEYS}
    keys_set = set(PUBLIC_KEYS)
    for s in settings:
        if s.get("key") in keys_set:
            result[s["key"]] = s.get("value") or ""
    return GeneralSettings(**result)


@router.put("/general", response_model=GeneralSettings)
def update_general_settings(data: GeneralSettings, admin=Depends(require_admin), db: SupabaseDB = Depends(get_db)):
    for key, value in data.model_dump().items():
        existing = db.get_one("settings", {"key": f"eq.{key}"})
        if existing:
            db.update("settings", existing["id"], {"value": str(value)}, id_field="id")
        else:
            db.insert("settings", {"key": key, "value": str(value)})
    return data
