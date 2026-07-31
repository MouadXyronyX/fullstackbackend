from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from app.services.db import get_db, SupabaseDB
from app.core.security import decode_token

router = APIRouter()

active_connections: dict[int, list[WebSocket]] = {}
admin_connections: list[WebSocket] = []

MAX_MESSAGE_LENGTH = 2000


async def notify_admin(message: str):
    for conn in admin_connections[:]:
        try:
            await conn.send_text(message)
        except Exception:
            admin_connections.remove(conn)


def _authenticate(token: str) -> dict | None:
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    db = SupabaseDB()
    try:
        user = db.get_by_id("users", int(user_id))
    except Exception:
        return None
    if user is None or not user.get("is_active", False):
        return None
    return user


async def _receive_auth(websocket: WebSocket, timeout_seconds: int = 10) -> dict | None:
    import asyncio
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=timeout_seconds)
        data = json.loads(raw)
        token = data.get("token", "") if isinstance(data, dict) else ""
        if not token:
            return None
        return _authenticate(token)
    except Exception:
        return None


@router.websocket("/chat/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: int):
    await websocket.accept()

    user = await _receive_auth(websocket)
    if user is None:
        await websocket.close(code=4401)
        return

    db = get_db()
    try:
        chat = db.get_by_id("chats", chat_id)
    except Exception:
        chat = None
    if not chat:
        await websocket.close(code=4404)
        return

    is_admin = user.get("role_id") == 1
    if not is_admin and chat.get("user_id") != user["id"]:
        await websocket.close(code=4403)
        return

    if chat_id not in active_connections:
        active_connections[chat_id] = []
    active_connections[chat_id].append(websocket)

    await websocket.send_text(json.dumps({"type": "ready"}))

    await notify_admin(json.dumps({
        "type": "chat_active",
        "chat_id": chat_id,
    }))

    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)

            sender_type = "admin" if is_admin else "customer"
            content = str(msg_data.get("content", ""))[:MAX_MESSAGE_LENGTH]
            if not content.strip():
                continue

            message = db.insert("messages", {
                "chat_id": chat_id,
                "sender_type": sender_type,
                "content": content,
                "is_read": False,
            })

            response = json.dumps({
                "type": "message",
                "id": message["id"],
                "chat_id": chat_id,
                "sender_type": message["sender_type"],
                "content": message["content"],
                "created_at": message.get("created_at"),
            })

            for conn in active_connections.get(chat_id, []):
                try:
                    await conn.send_text(response)
                except Exception:
                    pass

            for conn in admin_connections[:]:
                try:
                    await conn.send_text(json.dumps({
                        "type": "new_message",
                        "chat_id": chat_id,
                        **json.loads(response),
                    }))
                except Exception:
                    pass

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if chat_id in active_connections:
            if websocket in active_connections[chat_id]:
                active_connections[chat_id].remove(websocket)
            if not active_connections[chat_id]:
                del active_connections[chat_id]


@router.websocket("/admin")
async def admin_websocket(websocket: WebSocket):
    await websocket.accept()

    user = await _receive_auth(websocket)
    if user is None or user.get("role_id") != 1:
        await websocket.close(code=4403)
        return

    admin_connections.append(websocket)
    await websocket.send_text(json.dumps({"type": "ready"}))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if websocket in admin_connections:
            admin_connections.remove(websocket)


@router.websocket("/notifications")
async def notifications_websocket(websocket: WebSocket):
    await websocket.accept()

    user = await _receive_auth(websocket)
    if user is None or user.get("role_id") != 1:
        await websocket.close(code=4403)
        return

    await websocket.send_text(json.dumps({"type": "ready"}))

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            db = get_db()
            try:
                db.insert("notifications", {
                    "type": str(msg.get("type", "message"))[:50],
                    "reference_id": msg.get("reference_id"),
                    "message": str(msg.get("message", ""))[:MAX_MESSAGE_LENGTH],
                })
            except Exception:
                pass

            for conn in admin_connections[:]:
                try:
                    await conn.send_text(json.dumps({
                        "type": "notification",
                        "data": msg,
                    }))
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
