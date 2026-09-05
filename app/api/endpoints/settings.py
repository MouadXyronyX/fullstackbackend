from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
import json
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import require_admin
from app.schemas.setting import (
    SettingCreate, SettingUpdate, SettingResponse, GeneralSettings,
    DeliveryWilaya, DeliveryWilayasUpdate,
)

router = APIRouter()

PUBLIC_KEYS = ["store_name", "store_description", "facebook_url", "instagram_url",
               "whatsapp_number", "phone", "email", "address", "working_hours"]

DELIVERY_KEY = "delivery_wilayas"


def _get_delivery_wilayas(db: SupabaseDB) -> list[dict]:
    row = db.get_one("settings", {"key": f"eq.{DELIVERY_KEY}"})
    if not row or not row.get("value"):
        return []
    try:
        data = json.loads(row["value"])
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


@router.get("/delivery-wilayas", response_model=List[DeliveryWilaya])
def get_delivery_wilayas(db: SupabaseDB = Depends(get_db)):
    return _get_delivery_wilayas(db)


@router.put("/delivery-wilayas", response_model=List[DeliveryWilaya])
def update_delivery_wilayas(data: DeliveryWilayasUpdate, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_one("settings", {"key": f"eq.{DELIVERY_KEY}"})
    value = json.dumps([item.model_dump() for item in data.items], ensure_ascii=False)
    if existing:
        db.update("settings", existing["id"], {"value": value}, id_field="id")
    else:
        db.insert("settings", {"key": DELIVERY_KEY, "value": value})
    return data.items


@router.get("/public", response_model=Dict[str, str])
def get_public_settings(db: SupabaseDB = Depends(get_db)):
    keys_filter = ",".join(PUBLIC_KEYS)
    settings = db.get_all("settings", filters={"key": f"in.({keys_filter})"})
    return {s["key"]: s.get("value") or "" for s in settings}


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
