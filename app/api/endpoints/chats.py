from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.services.db import SupabaseDB, get_db
from app.core.dependencies import get_current_user, require_admin
from app.schemas.chat import ChatCreate, MessageCreate, ChatResponse, MessageResponse, UserBrief

router = APIRouter()


def _enrich_chat(chat: dict, db: SupabaseDB) -> dict:
    messages = db.get_all("messages", filters={"chat_id": f"eq.{chat['id']}"}, order="created_at.asc")
    chat["messages"] = messages
    if chat.get("user_id"):
        user = db.get_by_id("users", chat["user_id"], columns="id,name,email,phone")
        if user:
            chat["user"] = user
    return chat


@router.get("/", response_model=List[ChatResponse])
def list_chats(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    admin=Depends(require_admin),
    db: SupabaseDB = Depends(get_db),
):
    filters = {"is_active": f"eq.true"}
    if date_from:
        filters["created_at"] = f"gte.{date_from}"
    if date_to:
        filters["created_at"] = f"lte.{date_to}"
    chats = db.get_all("chats", filters=filters, order="created_at.desc")
    result = []
    for c in chats:
        result.append(ChatResponse.model_validate(_enrich_chat(c, db)))
    return result


@router.get("/my", response_model=List[ChatResponse])
def get_my_chats(user: dict = Depends(get_current_user), db: SupabaseDB = Depends(get_db)):
    chats = db.get_all("chats", filters={"user_id": f"eq.{user['id']}"}, order="created_at.desc")
    result = []
    for c in chats:
        result.append(ChatResponse.model_validate(_enrich_chat(c, db)))
    return result


@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(chat_id: int, db: SupabaseDB = Depends(get_db), user: dict = Depends(get_current_user)):
    chat = db.get_by_id("chats", chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if user.get("role_id") != 1 and chat.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="لا يمكنك الوصول إلى هذه الدردشة")
    return ChatResponse.model_validate(_enrich_chat(chat, db))


@router.post("/", response_model=ChatResponse)
def create_chat(data: ChatCreate, user: dict = Depends(get_current_user), db: SupabaseDB = Depends(get_db)):
    chat_data = {"user_id": user["id"], "is_active": True}
    if data.product_id:
        chat_data["product_id"] = data.product_id
    chat = db.insert("chats", chat_data)
    return ChatResponse.model_validate(_enrich_chat(chat, db))


@router.post("/{chat_id}/messages", response_model=MessageResponse)
def send_message(
    chat_id: int,
    data: MessageCreate,
    db: SupabaseDB = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    chat = db.get_by_id("chats", chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if user.get("role_id") != 1 and chat.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="لا يمكنك الوصول إلى هذه الدردشة")
    message = db.insert("messages", {
        "chat_id": chat_id,
        "sender_type": data.sender_type,
        "content": data.content,
        "is_read": False,
    })
    return MessageResponse.model_validate(message)
