from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import secrets
import string
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate, OrderTrackRequest
from app.core.redis_client import get_redis

router = APIRouter()


def generate_order_code() -> str:
    return "AQ-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: SupabaseDB = Depends(get_db),
    admin=Depends(require_admin),
):
    filters = {}
    if status:
        filters["status"] = f"eq.{status}"
    orders = db.get_all("orders", filters=filters if filters else None,
                        order="created_at.desc", limit=limit, offset=skip)
    result = []
    for o in orders:
        items = db.get_all("order_items", filters={"order_id": f"eq.{o['id']}"})
        o["items"] = items
        result.append(OrderResponse.model_validate(o))
    return result


@router.get("/my-orders", response_model=List[OrderResponse])
def get_my_orders(user: dict = Depends(get_current_user), db: SupabaseDB = Depends(get_db)):
    orders = db.get_all("orders", filters={"user_id": f"eq.{user['id']}"},
                        order="created_at.desc")
    result = []
    for o in orders:
        items = db.get_all("order_items", filters={"order_id": f"eq.{o['id']}"})
        o["items"] = items
        result.append(OrderResponse.model_validate(o))
    return result


@router.get("/track", response_model=OrderResponse)
def track_order(data: OrderTrackRequest = Depends(), db: SupabaseDB = Depends(get_db)):
    order = db.get_one("orders", {"order_code": f"eq.{data.order_code}", "guest_phone": f"eq.{data.phone}"})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or phone mismatch")
    items = db.get_all("order_items", filters={"order_id": f"eq.{order['id']}"})
    order["items"] = items
    return OrderResponse.model_validate(order)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    order = db.get_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    items = db.get_all("order_items", filters={"order_id": f"eq.{order_id}"})
    order["items"] = items
    return OrderResponse.model_validate(order)


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(data: OrderCreate, db: SupabaseDB = Depends(get_db)):
    total_price = 0.0
    order_items_data = []
    for item in data.items:
        product = db.get_by_id("products", item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if not product.get("is_available", False):
            raise HTTPException(status_code=400, detail=f"Product '{product['name']}' is not available")
        total_price += item.price_at_order * item.quantity
        order_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price_at_order": item.price_at_order,
        })

    order = db.insert("orders", {
        "order_code": generate_order_code(),
        "guest_name": data.guest_name,
        "guest_phone": data.guest_phone,
        "guest_email": data.guest_email,
        "wilaya": data.wilaya,
        "commune": data.commune,
        "address": data.address,
        "note": data.note,
        "status": "pending",
        "total_price": total_price,
    })

    for oi in order_items_data:
        oi["order_id"] = order["id"]
    db.insert("order_items", order_items_data)

    db.insert("notifications", {
        "type": "new_order",
        "reference_id": str(order["id"]),
        "message": f"طلب جديد #{order['order_code']} بقيمة {total_price:.2f} د.ج",
    })

    redis = get_redis()
    if redis:
        try:
            import asyncio, json
            asyncio.create_task(redis.publish("notifications", json.dumps({
                "type": "new_order",
                "order_id": order["id"],
                "order_code": order["order_code"],
                "message": f"طلب جديد #{order['order_code']}",
            })))
        except Exception:
            pass

    items = db.get_all("order_items", filters={"order_id": f"eq.{order['id']}"})
    order["items"] = items
    return OrderResponse.model_validate(order)


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: SupabaseDB = Depends(get_db),
    admin=Depends(require_admin),
):
    existing = db.get_by_id("orders", order_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    db.update("orders", order_id, {"status": data.status})
    order = db.get_by_id("orders", order_id)
    items = db.get_all("order_items", filters={"order_id": f"eq.{order_id}"})
    order["items"] = items
    return OrderResponse.model_validate(order)


@router.delete("/{order_id}")
def delete_order(order_id: int, db: SupabaseDB = Depends(get_db), admin=Depends(require_admin)):
    existing = db.get_by_id("orders", order_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete_many("order_items", {"order_id": f"eq.{order_id}"})
    db.delete("orders", order_id)
    return {"detail": "Order deleted successfully"}
