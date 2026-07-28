from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import require_admin
from app.schemas.page import PageCreate, PageUpdate, PageResponse

router = APIRouter()


@router.get("/", response_model=List[PageResponse])
def list_published_pages(db: SupabaseDB = Depends(get_db)):
    pages = db.get_all("pages", filters={"is_published": f"eq.true"}, order="title.asc")
    return [PageResponse.model_validate(p) for p in pages]


@router.get("/all", response_model=List[PageResponse])
def list_all_pages(db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    pages = db.get_all("pages", order="title.asc")
    return [PageResponse.model_validate(p) for p in pages]


@router.get("/by-slug/{slug}", response_model=PageResponse)
def get_page_by_slug(slug: str, db: SupabaseDB = Depends(get_db)):
    page = db.get_one("pages", {"slug": f"eq.{slug}", "is_published": f"eq.true"})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return PageResponse.model_validate(page)


@router.get("/{page_id}", response_model=PageResponse)
def get_page(page_id: int, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    page = db.get_by_id("pages", page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return PageResponse.model_validate(page)


@router.post("/", response_model=PageResponse, status_code=201)
def create_page(data: PageCreate, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_one("pages", {"slug": f"eq.{data.slug}"})
    if existing:
        raise HTTPException(status_code=400, detail="A page with this slug already exists")
    page = db.insert("pages", data.model_dump())
    return PageResponse.model_validate(page)


@router.put("/{page_id}", response_model=PageResponse)
def update_page(page_id: int, data: PageUpdate, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("pages", page_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Page not found")
    page = db.update("pages", page_id, data.model_dump(exclude_unset=True))
    return PageResponse.model_validate(page)


@router.delete("/{page_id}")
def delete_page(page_id: int, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("pages", page_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Page not found")
    db.delete("pages", page_id)
    return {"detail": "Page deleted successfully"}
