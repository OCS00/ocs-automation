import json
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional

POSTS_FILE = Path("posts/posts.json")


def load_posts() -> list:
    if not POSTS_FILE.exists():
        return []
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_posts(posts: list) -> None:
    POSTS_FILE.parent.mkdir(exist_ok=True)
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(post: dict) -> dict:
    if "id" not in post:
        post["id"] = str(uuid.uuid4())
    post.setdefault("status", "pending")
    post.setdefault("created_at", datetime.now().isoformat())
    posts = load_posts()
    posts.append(post)
    save_posts(posts)
    return post


def get_post(post_id: str) -> Optional[dict]:
    return next((p for p in load_posts() if p["id"] == post_id), None)


def update_post_status(post_id: str, status: str, **kwargs) -> Optional[dict]:
    posts = load_posts()
    for post in posts:
        if post["id"] == post_id:
            post["status"] = status
            post.update(kwargs)
            save_posts(posts)
            return post
    return None


def get_batch_posts(batch_id: str) -> "list[dict]":
    return [p for p in load_posts() if p.get("batch_id") == batch_id]


def approve_batch(batch_id: str) -> "list[dict]":
    posts = load_posts()
    updated = []
    for post in posts:
        if post.get("batch_id") == batch_id and post["status"] == "pending":
            post["status"] = "approved"
            post["approved_at"] = datetime.now().isoformat()
            updated.append(post)
    save_posts(posts)
    return updated


def get_approved_posts_for_today() -> "list[dict]":
    """Return approved posts scheduled for today (by date prefix match)."""
    today_str = date.today().isoformat()
    result = []
    for p in load_posts():
        if p.get("status") == "approved":
            scheduled = p.get("scheduled_for", "")
            if scheduled.startswith(today_str):
                result.append(p)
    return result
