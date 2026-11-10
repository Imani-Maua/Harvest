import json
import logging
from datetime import datetime, timezone
from typing import Generator

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from api.dad.conversation import Conversation, Message
from api.warren.config import Settings
from api.waweru.prompt import build_system_prompt
from api.waweru.functions import FUNCTION_DECLARATIONS, add_to_watchlist, get_watchlist, find_contacts_and_draft_email

logger = logging.getLogger(__name__)


def _log(level: str, event: str, **kwargs) -> str:
    return json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "logger": "api.waweru.service",
        "event": event,
        **kwargs,
    })


def _extract_error_message(exc: Exception) -> str:
    try:
        from google.genai import errors as genai_errors
        if isinstance(exc, genai_errors.APIError):
            msg = exc.message if hasattr(exc, "message") else str(exc)
            # Pull just the human-readable message from the JSON if present
            if isinstance(exc.details, dict):
                msg = exc.details.get("error", {}).get("message", msg)
            return msg
    except Exception:
        pass
    return str(exc)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _dispatch(fn_name: str, fn_args: dict, db: Session) -> str:
    if fn_name == "add_to_watchlist":
        result = add_to_watchlist(db=db, **fn_args)
    elif fn_name == "get_watchlist":
        result = get_watchlist(db=db)
    elif fn_name == "find_contacts_and_draft_email":
        result = find_contacts_and_draft_email(db=db, **fn_args)
    else:
        result = {"error": f"Unknown function: {fn_name}"}
    return json.dumps(result)


def _get_or_create_conversation(conversation_id: int | None, db: Session) -> Conversation:
    if conversation_id:
        convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if convo:
            return convo
    convo = Conversation()
    db.add(convo)
    db.flush()
    return convo


def chat_stream(conversation_id: int | None, user_message: str, db: Session) -> Generator[str, None, None]:
    settings = Settings()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    convo = _get_or_create_conversation(conversation_id, db)

    history = [
        types.Content(role=msg.role, parts=[types.Part(text=msg.content)])
        for msg in convo.messages
    ]

    db.add(Message(conversation_id=convo.id, role="user", content=user_message))
    db.flush()

    logger.info(_log("info", "chat_stream_started", conversation_id=convo.id))

    tools = [types.Tool(function_declarations=[
        types.FunctionDeclaration(**fd) for fd in FUNCTION_DECLARATIONS
    ])]

    chat_session = client.chats.create(
        model="gemini-3.8-flash",
        config=types.GenerateContentConfig(
            system_instruction=build_system_prompt(),
            tools=tools,
        ),
        history=history,
    )

    full_reply = ""

    try:
        stream = chat_session.send_message_stream(user_message)

        pending_fn_call = None
        pending_fn_name = None
        pending_fn_args = None

        for chunk in stream:
            if not chunk.candidates:
                continue
            for part in chunk.candidates[0].content.parts:
                if part.function_call:
                    pending_fn_call = part.function_call
                    pending_fn_name = part.function_call.name
                    pending_fn_args = dict(part.function_call.args)
                elif part.text:
                    full_reply += part.text
                    yield _sse({"token": part.text})

        # Handle function call after stream completes
        if pending_fn_call:
            logger.info(_log("info", "function_call", function=pending_fn_name))
            fn_result = _dispatch(pending_fn_name, pending_fn_args, db)

            follow_stream = chat_session.send_message_stream(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=pending_fn_name,
                        response={"result": fn_result},
                    )
                )
            )
            for chunk in follow_stream:
                if not chunk.candidates:
                    continue
                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        full_reply += part.text
                        yield _sse({"token": part.text})

        db.add(Message(conversation_id=convo.id, role="model", content=full_reply))
        db.commit()

        logger.info(_log("info", "chat_stream_complete", conversation_id=convo.id))
        yield _sse({"conversation_id": convo.id, "done": True})

    except Exception as exc:
        logger.error(_log("error", "chat_stream_failed", error=str(exc)))
        db.rollback()
        error_msg = _extract_error_message(exc)
        yield _sse({"error": error_msg, "done": True})
