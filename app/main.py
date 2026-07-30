import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.redis_client import init_redis, close_redis
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.api.endpoints import auth, products, categories, orders, pages, users, chats, settings, dashboard
from app.websocket import chat as chat_websocket
from app.services.db import SupabaseDB

logger = logging.getLogger(__name__)
app_settings = get_settings()

app = FastAPI(
    title=app_settings.app_name,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    origin = request.headers.get("origin", "")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers=headers,
    )

# CORS — support multiple origins via comma-separated FRONTEND_URL
origins = [
    o.strip()
    for o in app_settings.frontend_url.split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)


@app.on_event("startup")
async def startup():
    from datetime import datetime, timedelta
    try:
        db = SupabaseDB()
        cutoff = (datetime.utcnow() - timedelta(days=15)).isoformat()
        old_orders = db.get_all("orders", columns="id", filters={"created_at": f"lt.{cutoff}"})
        for o in old_orders:
            db.delete_many("order_items", {"order_id": f"eq.{o['id']}"})
            db.delete("orders", o["id"])
        old_chats = db.get_all("chats", columns="id", filters={"created_at": f"lt.{cutoff}"})
        for c in old_chats:
            db.delete_many("messages", {"chat_id": f"eq.{c['id']}"})
            db.delete("chats", c["id"])
    except Exception:
        pass
    await init_redis()


@app.on_event("shutdown")
async def shutdown():
    await close_redis()


# Root redirect to docs
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs")


# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "app": app_settings.app_name}


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(pages.router, prefix="/api/pages", tags=["Pages"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(chats.router, prefix="/api/chats", tags=["Chats"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

# WebSocket
app.include_router(chat_websocket.router, prefix="/ws", tags=["WebSocket"])
