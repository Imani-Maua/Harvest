from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from api.dad.conversation import Conversation
from api.dad.session import session
from api.dad.auth import User
from api.daisy.utils.auth_utils import get_current_user
from api.waweru.service import chat_stream

waweru_router = APIRouter(prefix="/harvest", tags=["Harvest"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationSummaryOut(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailOut(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut]

    model_config = ConfigDict(from_attributes=True)


@waweru_router.post("/chat")
def harvest_chat(
    body: ChatRequest,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return StreamingResponse(
        chat_stream(
            conversation_id=body.conversation_id,
            user_message=body.message,
            db=db,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@waweru_router.get("/conversations", response_model=list[ConversationSummaryOut])
def list_conversations(
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()


@waweru_router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(
    conversation_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo
