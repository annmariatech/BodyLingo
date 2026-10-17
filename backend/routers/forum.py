"""Read-only fictional forum feed with search and topic filtering."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import CurrentUser
from schemas.forum import ForumFeed
from services.forum_service import search_posts

router = APIRouter(prefix="/forum", tags=["forum"])


@router.get("/posts", response_model=ForumFeed)
def get_posts(
    user: CurrentUser,
    query: str = Query(default="", max_length=120),
    category: str = Query(default="", max_length=80),
    db: Session = Depends(get_db),
) -> dict:
    del user, db  # Sample content is shared; authentication follows the app's private learning area.
    return search_posts(query, category)
