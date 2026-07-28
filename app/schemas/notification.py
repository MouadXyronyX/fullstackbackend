from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    type: str
    reference_id: Optional[str]
    message: str
    is_read: Optional[bool] = False
    created_at: Optional[datetime]

    model_config = {"from_attributes": True, "extra": "ignore"}


class NotificationCountResponse(BaseModel):
    count: int
