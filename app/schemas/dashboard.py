from pydantic import BaseModel
from typing import List, Optional


class DashboardStats(BaseModel):
    total_products: int
    total_categories: int
    total_orders: int
    pending_orders: int
    total_customers: int
    unread_messages: int
    total_revenue: float
    recent_orders: List[dict] = []
