from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True, "extra": "ignore"}


class ChatCreate(BaseModel):
    product_id: Optional[int] = None
    guest_identifier: Optional[str] = None


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    sender_type: str = Field(..., pattern=r"^(admin|customer)$")


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_type: str
    content: str
    is_read: Optional[bool] = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class ChatResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user: Optional[UserBrief] = None
    guest_identifier: Optional[str]
    product_id: Optional[int]
    is_active: bool = True
    created_at: Optional[datetime] = None
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True, "extra": "ignore", "coerce_numbers_to_str": True}
