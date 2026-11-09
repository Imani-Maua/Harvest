import json
import logging
from datetime import datetime, timezone

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from api.dad.conversation import Conversation, Message
from api.warren.config import Settings
from api.waweru.prompt import SYSTEM_PROMPT
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


def chat(conversation_id: int | None, user_message: str, db: Session) -> dict:
    settings = Settings()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Load or create conversation
    if conversation_id:
        convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not convo:
            convo = Conversation()
            db.add(convo)
            db.flush()
    else:
        convo = Conversation()
        db.add(convo)
        db.flush()

    # Build history for Gemini
    history = [
        types.Content(role=msg.role, parts=[types.Part(text=msg.content)])
        for msg in convo.messages
    ]

    # Persist user message
    db.add(Message(conversation_id=convo.id, role="user", content=user_message))
    db.flush()

    logger.info(_log("info", "chat_turn_started", conversation_id=convo.id))

    tools = [types.Tool(function_declarations=[
        types.FunctionDeclaration(**fd) for fd in FUNCTION_DECLARATIONS
    ])]

    chat_session = client.chats.create(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=tools,
        ),
        history=history,
    )

    response = chat_session.send_message(user_message)

    reply_text = ""
    for part in response.candidates[0].content.parts:
        if part.function_call:
            fc = part.function_call
            fn_name = fc.name
            fn_args = dict(fc.args)
            logger.info(_log("info", "function_call", function=fn_name))
            fn_result = _dispatch(fn_name, fn_args, db)
            follow_up = chat_session.send_message(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fn_name,
                        response={"result": fn_result},
                    )
                )
            )
            reply_text = follow_up.text
        elif part.text:
            reply_text += part.text

    if not reply_text:
        reply_text = response.text

    # Persist model reply
    db.add(Message(conversation_id=convo.id, role="model", content=reply_text))
    db.commit()

    logger.info(_log("info", "chat_turn_complete", conversation_id=convo.id))
    return {"conversation_id": convo.id, "reply": reply_text}
