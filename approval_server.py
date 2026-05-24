import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, send_from_directory

load_dotenv()

from instagram import post_to_instagram, post_story_to_instagram
from storage import approve_batch, get_batch_posts, get_post, update_post_status

app = Flask(__name__)

_HTML = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>
  body {{ font-family: Arial, sans-serif; display: flex; justify-content: center;
         align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
  .card {{ background: white; padding: 40px; border-radius: 12px;
           text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,.1); }}
  h2 {{ color: {color}; }}
</style></head>
<body><div class="card"><h2>{icon} {message}</h2><p>{detail}</p></div></body>
</html>
"""


def _render(color: str, icon: str, message: str, detail: str = "", status: int = 200):
    html = _HTML.format(color=color, icon=icon, message=message, detail=detail)
    return html, status


@app.route("/images/<filename>")
def serve_image(filename: str):
    return send_from_directory("images", filename)


def _publish_post(post: dict):
    """Carousel'i ve story'yi Instagram'a gönder."""
    media_id = post_to_instagram(post)
    update_post_status(
        post["id"],
        "posted",
        posted_at=datetime.now().isoformat(),
        media_id=media_id,
    )
    if post.get("story_path"):
        try:
            post_story_to_instagram(post)
        except Exception as e:
            print(f"  Story yayın uyarısı: {e}")


@app.route("/approve/<post_id>")
def approve(post_id: str):
    post = get_post(post_id)
    if not post:
        return _render("#ef4444", "✗", "Post bulunamadı.", status=404)
    if post["status"] not in ("pending", "approved"):
        return _render("#6b7280", "ℹ", "Zaten işlendi.", f"Durum: {post['status']}")

    try:
        _publish_post(post)
        return _render("#22c55e", "✓", "Instagram'a gönderildi!", post["topic"])
    except Exception as e:
        return _render("#ef4444", "✗", "Hata oluştu.", str(e), status=500)


@app.route("/approve-batch/<batch_id>")
def approve_batch_route(batch_id: str):
    posts = get_batch_posts(batch_id)
    if not posts:
        return _render("#ef4444", "✗", "Batch bulunamadı.", status=404)

    approved = approve_batch(batch_id)
    if not approved:
        return _render("#6b7280", "ℹ", "Tüm postlar zaten işlendi.")

    return _render(
        "#22c55e", "✓",
        f"{len(approved)} post onaylandı.",
        "Postlar zamanında otomatik yayınlanacak.",
    )


@app.route("/reject/<post_id>")
def reject(post_id: str):
    post = get_post(post_id)
    if not post:
        return _render("#ef4444", "✗", "Post bulunamadı.", status=404)

    update_post_status(post_id, "rejected", rejected_at=datetime.now().isoformat())
    return _render("#6b7280", "✗", "Post reddedildi.", post["topic"])


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5001))
    print(f"Onay sunucusu başlatıldı → http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)
