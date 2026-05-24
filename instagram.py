import os
import time

import requests

GRAPH_BASE = "https://graph.facebook.com/v18.0"


def _upload_carousel_item(user_id: str, image_url: str, access_token: str) -> str:
    res = requests.post(
        f"{GRAPH_BASE}/{user_id}/media",
        params={
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": access_token,
        },
        timeout=30,
    )
    if not res.ok:
        raise RuntimeError(f"Carousel item hatası {res.status_code}: {res.json()}")
    return res.json()["id"]


def post_to_instagram(post: dict) -> str:
    user_id = os.getenv("INSTAGRAM_USER_ID")
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    base_url = os.getenv("APPROVAL_BASE_URL", "http://localhost:5001")
    post_id = post["id"]

    if not user_id or not access_token:
        raise ValueError("INSTAGRAM_USER_ID veya INSTAGRAM_ACCESS_TOKEN eksik")

    slide_paths = post.get("slide_paths", [])
    if not slide_paths:
        raise ValueError("Paylaşılacak slayt bulunamadı")

    caption = f"{post['caption']}\n\n{post['hashtags']}"

    # Her slayt için public URL → ngrok üzerinden servis ediliyor
    child_ids = []
    for i, path in enumerate(slide_paths):
        filename = os.path.basename(path)
        image_url = f"{base_url}/images/{filename}"
        child_id = _upload_carousel_item(user_id, image_url, access_token)
        child_ids.append(child_id)
        time.sleep(1)

    # Carousel container oluştur
    carousel_res = requests.post(
        f"{GRAPH_BASE}/{user_id}/media",
        params={
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    if not carousel_res.ok:
        raise RuntimeError(f"Carousel container hatası {carousel_res.status_code}: {carousel_res.json()}")
    creation_id = carousel_res.json().get("id")

    # Yayınla
    publish_res = requests.post(
        f"{GRAPH_BASE}/{user_id}/media_publish",
        params={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    if not publish_res.ok:
        raise RuntimeError(f"Yayın hatası {publish_res.status_code}: {publish_res.json()}")

    return publish_res.json().get("id", "")


def post_story_to_instagram(post: dict) -> str:
    user_id = os.getenv("INSTAGRAM_USER_ID")
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    base_url = os.getenv("APPROVAL_BASE_URL", "http://localhost:5001")

    if not user_id or not access_token:
        raise ValueError("INSTAGRAM_USER_ID veya INSTAGRAM_ACCESS_TOKEN eksik")

    story_path = post.get("story_path")
    if not story_path:
        raise ValueError("story_path bulunamadı")

    filename = os.path.basename(story_path)
    image_url = f"{base_url}/images/{filename}"

    container_res = requests.post(
        f"{GRAPH_BASE}/{user_id}/media",
        params={
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": access_token,
        },
        timeout=30,
    )
    if not container_res.ok:
        raise RuntimeError(f"Story container hatası {container_res.status_code}: {container_res.json()}")
    creation_id = container_res.json()["id"]

    time.sleep(2)

    publish_res = requests.post(
        f"{GRAPH_BASE}/{user_id}/media_publish",
        params={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    if not publish_res.ok:
        raise RuntimeError(f"Story yayın hatası {publish_res.status_code}: {publish_res.json()}")

    return publish_res.json().get("id", "")
