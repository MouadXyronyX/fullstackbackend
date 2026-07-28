from fastapi import APIRouter, Depends
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import require_admin
from app.schemas.dashboard import DashboardStats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(admin=Depends(require_admin), db: SupabaseDB = Depends(get_db)):
    total_products = db.count("products")
    total_categories = db.count("categories")
    total_orders = db.count("orders")
    pending_orders = db.count("orders", {"status": f"eq.pending"})
    total_customers = db.count("users", {"role_id": f"eq.2"})
    unread_messages = db.count("messages", {"is_read": f"eq.false", "sender_type": f"eq.customer"})
    total_revenue = db.sum("orders", "total_price",
                           filters={"status": f"in.(delivered,shipped)"})

    recent_orders_raw = db.get_all("orders", order="created_at.desc", limit=5)
    recent_orders = []
    for o in recent_orders_raw:
        recent_orders.append({
            "id": o["id"],
            "order_code": o.get("order_code", ""),
            "customer": o.get("guest_name") or "زبون مسجل",
            "total_price": float(o.get("total_price", 0)),
            "status": o.get("status", ""),
            "created_at": o.get("created_at"),
        })

    return DashboardStats(
        total_products=total_products,
        total_categories=total_categories,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_customers=total_customers,
        unread_messages=unread_messages,
        total_revenue=total_revenue,
        recent_orders=recent_orders,
    )
