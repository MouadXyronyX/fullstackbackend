import httpx
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import require_admin
from app.core.cache import cache_get, cache_set, cache_delete_pattern
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
def list_categories(db: SupabaseDB = Depends(get_db)):
    cache_key = "categories:all"
    cached = cache_get(cache_key)
    if cached is not None:
        return [CategoryResponse.model_validate(c) for c in cached]
    categories = db.get_all("categories", order="name.asc")
    cache_set(cache_key, categories, ttl=120)
    return [CategoryResponse.model_validate(c) for c in categories]


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: SupabaseDB = Depends(get_db)):
    category = db.get_by_id("categories", category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse.model_validate(category)


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(data: CategoryCreate, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    category = db.insert("categories", data.model_dump())
    cache_delete_pattern("categories:*")
    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, data: CategoryUpdate, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("categories", category_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    category = db.update("categories", category_id, data.model_dump(exclude_unset=True))
    cache_delete_pattern("categories:*")
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}")
def delete_category(category_id: int, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("categories", category_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    try:
        db.delete("categories", category_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            raise HTTPException(
                status_code=400,
                detail="لا يمكن حذف هذا القسم لأنه يحتوي على منتجات. قم بنقل المنتجات أو حذفها أولاً."
            )
        raise
    cache_delete_pattern("categories:*")
    return {"detail": "Category deleted successfully"}
