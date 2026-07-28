from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductImageSchema(BaseModel):
    id: Optional[int] = None
    image_url: str
    order: int = 0

    model_config = {"from_attributes": True, "extra": "ignore"}


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_available: bool = True
    images: List[ProductImageSchema] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_available: Optional[bool] = None
    images: Optional[List[ProductImageSchema]] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str]
    category_id: Optional[int]
    is_available: bool
    created_at: Optional[datetime]
    images: List[ProductImageSchema] = []

    model_config = {"from_attributes": True, "extra": "ignore"}


class ProductFilter(BaseModel):
    category_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_available: Optional[bool] = None
    search: Optional[str] = None
