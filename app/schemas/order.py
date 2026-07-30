from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    price_at_order: float
    variant_id: Optional[int] = None
    variant_name: Optional[str] = None


class OrderCreate(BaseModel):
    guest_name: Optional[str] = Field(None, min_length=2)
    guest_phone: Optional[str] = Field(None, min_length=8)
    guest_email: Optional[str] = None
    wilaya: str = Field(..., min_length=1)
    commune: str = Field(..., min_length=1)
    address: Optional[str] = Field(None, min_length=5)
    note: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_length=1)
    captcha_token: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_order: float
    product_name: Optional[str] = None
    variant_id: Optional[int] = None
    variant_name: Optional[str] = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class OrderResponse(BaseModel):
    id: int
    order_code: str
    user_id: Optional[int]
    guest_name: Optional[str]
    guest_phone: Optional[str]
    guest_email: Optional[str]
    wilaya: str
    commune: str
    address: Optional[str]
    note: Optional[str]
    status: str
    total_price: float
    created_at: Optional[datetime]
    items: List[OrderItemResponse] = []

    model_config = {"from_attributes": True, "extra": "ignore"}


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(pending|accepted|preparing|shipped|delivered|cancelled)$")


class OrderTrackRequest(BaseModel):
    order_code: str
