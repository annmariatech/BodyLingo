"""Account-scoped conversation history and grounded chat endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.scenario import Scenario
from database import get_db
from dependencies.auth import CurrentUser
from models.chat import ChatConversation, ChatMessage
from schemas.chat import ChatConversationResponse, ChatMessageRequest, ChatMessageResponse
from services.chat_service import generate_reply, retrieve_references

router = APIRouter(prefix="/chat", tags=["chat"])


def _conversation(db: Session, user_id: str, conversation_id: str) -> ChatConversation:
    conversation = db.scalar(select(ChatConversation).where(ChatConversation.id == conversation_id, ChatConversation.user_id == user_id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _messages(db: Session, conversation_id: str) -> list[ChatMessage]:
    return db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.created_at, ChatMessage.id)).all()


@router.get("/conversations", response_model=list[ChatConversationResponse])
def list_conversations(user: CurrentUser, db: Session = Depends(get_db)):
    rows = db.scalars(select(ChatConversation).where(ChatConversation.user_id == user.id).order_by(ChatConversation.updated_at.desc())).all()
    return [ChatConversationResponse(**{**row.__dict__, "messages": []}) for row in rows]


@router.post("/conversations", response_model=ChatConversationResponse)
def create_conversation(user: CurrentUser, db: Session = Depends(get_db)):
    row = ChatConversation(user_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ChatConversationResponse(**{**row.__dict__, "messages": []})


@router.get("/conversations/{conversation_id}", response_model=ChatConversationResponse)
def get_conversation(conversation_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    row = _conversation(db, user.id, conversation_id)
    return ChatConversationResponse(**{**row.__dict__, "messages": [ChatMessageResponse.model_validate(message) for message in _messages(db, row.id)]})


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageResponse)
def send_message(conversation_id: str, payload: ChatMessageRequest, user: CurrentUser, db: Session = Depends(get_db)):
    row = _conversation(db, user.id, conversation_id)
    learner_message = ChatMessage(conversation_id=row.id, role="user", content=payload.content)
    db.add(learner_message)
    db.flush()
    references = retrieve_references(
        payload.content,
        db.scalars(select(Scenario).where(Scenario.published.is_(True))).all(),
        include_premium=user.is_premium,
    )
    history = [{"role": message.role, "content": message.content} for message in _messages(db, row.id)][-12:]
    # Only reference fields with user-facing labels are returned; content remains server-side prompt context.
    answer, _provider = generate_reply(history, references)
    reply = ChatMessage(conversation_id=row.id, role="assistant", content=answer, references=[{key: item[key] for key in ("type", "id", "title")} for item in references])
    if row.title == "New conversation":
        row.title = payload.content[:100]
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply
