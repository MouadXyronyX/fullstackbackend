from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import require_admin
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductFilter

router = APIRouter()


def _load_variants(product_id: int, db: SupabaseDB) -> list:
    try:
        return db.get_all("product_variants", filters={"product_id": f"eq.{product_id}"}, order="name.asc")
    except Exception:
        return []


@router.get("/", response_model=List[ProductResponse])
def list_products(
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    is_available: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: SupabaseDB = Depends(get_db),
):
    filters = {}
    if category_id is not None:
        filters["category_id"] = f"eq.{category_id}"
    if min_price is not None:
        filters["price"] = f"gte.{min_price}"
    if max_price is not None:
        filters["price"] = f"lte.{max_price}"
    if is_available is not None:
        filters["is_available"] = f"eq.{str(is_available).lower()}"
    if search:
        filters["name"] = f"ilike.%{search}%"

    products = db.get_all("products", columns="*",
                          filters=filters if filters else None,
                          order="created_at.desc",
                          limit=limit, offset=skip)
    result = []
    for p in products:
        images = db.get_all("product_images", filters={"product_id": f"eq.{p['id']}"}, order="order.asc")
        p["images"] = images
        p["variants"] = _load_variants(p["id"], db)
        result.append(ProductResponse.model_validate(p))
    return result


@router.get("/count")
def count_products(
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: SupabaseDB = Depends(get_db),
):
    filters = {}
    if category_id is not None:
        filters["category_id"] = f"eq.{category_id}"
    if search:
        filters["name"] = f"ilike.%{search}%"
    count = db.count("products", filters=filters if filters else None)
    return {"count": count}


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: SupabaseDB = Depends(get_db)):
    product = db.get_by_id("products", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    images = db.get_all("product_images", filters={"product_id": f"eq.{product_id}"}, order="order.asc")
    product["images"] = images
    product["variants"] = _load_variants(product_id, db)
    return ProductResponse.model_validate(product)


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    product_data = data.model_dump(exclude={"images", "variants"})
    product = db.insert("products", product_data)
    images_data = []
    for idx, img in enumerate(data.images):
        images_data.append({
            "product_id": product["id"],
            "image_url": img.image_url,
            "order": img.order or idx,
        })
    if images_data:
        db.insert("product_images", images_data)
    try:
        for v in data.variants:
            db.insert("product_variants", {
                "product_id": product["id"],
                "name": v.name,
                "price": v.price,
                "image_url": v.image_url,
                "is_available": v.is_available,
            })
    except Exception:
        pass
    images = db.get_all("product_images", filters={"product_id": f"eq.{product['id']}"}, order="order.asc")
    product["images"] = images
    product["variants"] = _load_variants(product["id"], db)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("products", product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = data.model_dump(exclude={"images", "variants"}, exclude_unset=True)
    if update_data:
        db.update("products", product_id, update_data)
    if data.images is not None:
        db.delete_many("product_images", {"product_id": f"eq.{product_id}"})
        images_data = []
        for idx, img in enumerate(data.images):
            images_data.append({
                "product_id": product_id,
                "image_url": img.image_url,
                "order": img.order or idx,
            })
        if images_data:
            db.insert("product_images", images_data)
    if data.variants is not None:
        try:
            db.delete_many("product_variants", {"product_id": f"eq.{product_id}"})
            for v in data.variants:
                db.insert("product_variants", {
                    "product_id": product_id,
                    "name": v.name,
                    "price": v.price,
                    "image_url": v.image_url,
                    "is_available": v.is_available,
                })
        except Exception:
            pass
    product = db.get_by_id("products", product_id)
    images = db.get_all("product_images", filters={"product_id": f"eq.{product_id}"}, order="order.asc")
    product["images"] = images
    product["variants"] = _load_variants(product_id, db)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}")
def delete_product(product_id: int, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("products", product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete_many("product_images", {"product_id": f"eq.{product_id}"})
    try:
        db.delete_many("product_variants", {"product_id": f"eq.{product_id}"})
    except Exception:
        pass
    db.delete("products", product_id)
    return {"detail": "Product deleted successfully"}
