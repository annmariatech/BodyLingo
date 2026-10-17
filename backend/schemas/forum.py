from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ForumPost(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    excerpt: str
    author_display_name: str
    created_at: datetime
    category: str
    topic_tags: list[str]
    fictional: bool = True


class ForumFeed(BaseModel):
    posts: list[ForumPost]
    categories: list[str]
    classification: str
