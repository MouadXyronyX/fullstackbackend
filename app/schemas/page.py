from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PageCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    title: str = Field(..., min_length=1, max_length=255)
    content: str = ""
    is_published: bool = True


class PageUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None


class PageResponse(BaseModel):
    id: int
    slug: str
    title: str
    content: Optional[str]
    is_published: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True, "extra": "ignore"}
