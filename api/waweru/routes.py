from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dad.session import session
from api.dad.auth import User
from api.daisy.utils.auth_utils import get_current_user
from api.waweru.service import chat_stream

waweru_router = APIRouter(prefix="/harvest", tags=["Harvest"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


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
