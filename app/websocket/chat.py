from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from app.services.db import get_db, SupabaseDB

router = APIRouter()

active_connections: dict[int, list[WebSocket]] = {}
admin_connections: list[WebSocket] = []


async def notify_admin(message: str):
    for conn in admin_connections[:]:
        try:
            await conn.send_text(message)
        except Exception:
            admin_connections.remove(conn)


@router.websocket("/chat/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: int):
    await websocket.accept()

    if chat_id not in active_connections:
        active_connections[chat_id] = []
    active_connections[chat_id].append(websocket)

    await notify_admin(json.dumps({
        "type": "chat_active",
        "chat_id": chat_id,
    }))

    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)

            db = get_db()
            try:
                message = db.insert("messages", {
                    "chat_id": chat_id,
                    "sender_type": msg_data.get("sender_type", "customer"),
                    "content": msg_data.get("content", ""),
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

            except Exception:
                pass

    except WebSocketDisconnect:
        if chat_id in active_connections:
            active_connections[chat_id].remove(websocket)
            if not active_connections[chat_id]:
                del active_connections[chat_id]
    except Exception:
        if chat_id in active_connections:
            active_connections[chat_id].remove(websocket)
            if not active_connections[chat_id]:
                del active_connections[chat_id]


@router.websocket("/admin")
async def admin_websocket(websocket: WebSocket):
    await websocket.accept()
    admin_connections.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in admin_connections:
            admin_connections.remove(websocket)
    except Exception:
        if websocket in admin_connections:
            admin_connections.remove(websocket)


@router.websocket("/notifications")
async def notifications_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            db = get_db()
            try:
                db.insert("notifications", {
                    "type": msg.get("type", "message"),
                    "reference_id": msg.get("reference_id"),
                    "message": msg.get("message", ""),
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
