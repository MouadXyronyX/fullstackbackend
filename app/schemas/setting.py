from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SettingCreate(BaseModel):
    key: str
    value: str


class SettingUpdate(BaseModel):
    value: str


class SettingResponse(BaseModel):
    id: int
    key: str
    value: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True, "extra": "ignore"}


class GeneralSettings(BaseModel):
    store_name: str = "اثاث القدس"
    store_description: str = ""
    facebook_url: str = ""
    instagram_url: str = ""
    whatsapp_number: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    working_hours: str = ""
