from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dad.session import session
from api.dad.auth import User
from api.daisy.utils.auth_utils import get_current_user
from api.waweru.service import chat

waweru_router = APIRouter(prefix="/harvest", tags=["Harvest"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str


@waweru_router.post("/chat", response_model=ChatResponse)
def harvest_chat(
    body: ChatRequest,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return chat(
        conversation_id=body.conversation_id,
        user_message=body.message,
        db=db,
    )
