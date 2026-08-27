from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import StreamingResponse
from .. import oauth
from ..database import get_db
from .. import schemas
from sqlalchemy.orm import Session
from typing import Annotated
from .agents import run_agent, run_agent_stream

ai_router = APIRouter(
    tags=["CHAT-BOT-FUNCTIONS"],
    prefix='/chat'
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[schemas.Token, Depends(oauth.get_current_user)]

@ai_router.post("/chat", response_model=schemas.ChatResponse)
def chat(request: schemas.ChatRequest,
         db: DbSession,
         current_user: CurrentUser):
    question = request.message
    history = request.history
    return run_agent(question, history, db, current_user)


@ai_router.post("/stream")
def chat_stream(request: schemas.ChatRequest,
                db: DbSession,
                current_user: CurrentUser):
    """SSE endpoint — streams tokens as they arrive from the LLM."""
    def generator():
        yield from run_agent_stream(request.message, request.history, db, current_user)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disables nginx buffering if used
        }
    )

