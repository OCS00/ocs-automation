import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

from email_approval import send_batch_approval_email
from generator import TOPICS, generate_post
from instagram import post_to_instagram, post_story_to_instagram
from storage import add_post, get_approved_posts_for_today, update_post_status

REQUIRED_VARS = [
    "ANTHROPIC_API_KEY",
    "FAL_API_KEY",
    "RESEND_API_KEY",
    "EMAIL_RECIPIENT",
    "INSTAGRAM_USER_ID",
    "INSTAGRAM_ACCESS_TOKEN",
]

_INDEX_FILE = Path("posts/topic_index.txt")

# Pzt=0, Çrş=2, Cum=4
_PUBLISH_DAYS = [0, 2, 4]


def _next_topic() -> str:
    _INDEX_FILE.parent.mkdir(exist_ok=True)
    idx = int(_INDEX_FILE.read_text().strip()) if _INDEX_FILE.exists() else 0
    topic = TOPICS[idx % len(TOPICS)]
    _INDEX_FILE.write_text(str((idx + 1) % len(TOPICS)))
    return topic


def _next_weekday_at_9(weekday: int) -> datetime:
    """Haftanın belirtilen gününün 09:00'ını döndür (bugün veya sonraki hafta)."""
    now = datetime.now()
    days_ahead = weekday - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    target = now + timedelta(days=days_ahead)
    return target.replace(hour=9, minute=0, second=0, microsecond=0)


def run_weekly_batch() -> None:
    """Pazar 22:00 — haftanın 3 postunu üret, tek onay maili gönder."""
    print(f"\n{'=' * 50}")
    print(f"Toplu üretim başladı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    batch_id = str(uuid.uuid4())
    day_names = ["Pazartesi", "Çarşamba", "Cuma"]
    posts = []

    for weekday, day_name in zip(_PUBLISH_DAYS, day_names):
        topic = _next_topic()
        post_id = str(uuid.uuid4())
        scheduled_dt = _next_weekday_at_9(weekday)

        try:
            print(f"\n→ [{day_name}] {topic}")
            post_data = generate_post(topic, post_id)
            post_data["batch_id"] = batch_id
            post_data["scheduled_for"] = scheduled_dt.isoformat()
            post_data["scheduled_day"] = day_name
            post = add_post(post_data)
            posts.append(post)
            print(f"  ✓ Üretildi → {scheduled_dt.strftime('%d.%m %H:%M')}")
        except Exception as e:
            print(f"  ✗ [{day_name}] Hata: {e}")

    if posts:
        send_batch_approval_email(posts)
        print(f"\n✓ {len(posts)} post için onay maili gönderildi.")
    else:
        print("\n✗ Hiç post üretilemedi.")


def run_publish() -> None:
    """Pzt/Çrş/Cum 09:00 — bugün için onaylanmış postları yayınla."""
    print(f"\nYayın kontrolü: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    today_posts = get_approved_posts_for_today()

    if not today_posts:
        print("  Bugün için onaylı post yok.")
        return

    for post in today_posts:
        print(f"\n→ {post['topic']}")
        try:
            media_id = post_to_instagram(post)
            update_post_status(
                post["id"], "posted",
                posted_at=datetime.now().isoformat(),
                media_id=media_id,
            )
            print("  ✓ Carousel yayınlandı")

            if post.get("story_path"):
                post_story_to_instagram(post)
                print("  ✓ Story yayınlandı")
        except Exception as e:
            print(f"  ✗ Hata: {e}")


def main() -> None:
    missing = [k for k in REQUIRED_VARS if not os.getenv(k)]
    if missing:
        print(f"✗ Eksik .env değişkenleri: {', '.join(missing)}")
        sys.exit(1)

    if "--batch" in sys.argv:
        run_weekly_batch()
        return

    if "--publish" in sys.argv:
        run_publish()
        return

    # Geriye dönük: --now tek post üret ve hemen yayınla
    if "--now" in sys.argv:
        topic = _next_topic()
        post_id = str(uuid.uuid4())
        post_data = generate_post(topic, post_id)
        post = add_post(post_data)
        print(f"✓ Post üretildi: {topic}")
        from email_approval import send_batch_approval_email
        send_batch_approval_email([post])
        print("✓ Onay maili gönderildi")
        return

    scheduler = BlockingScheduler(timezone="Europe/Istanbul")
    # Pazar 22:00 — haftanın 3 postunu toplu üret
    scheduler.add_job(run_weekly_batch, "cron", day_of_week="sun", hour=22, minute=0)
    # Pzt/Çrş/Cum 09:00 — onaylı postları yayınla
    scheduler.add_job(run_publish, "cron", day_of_week="mon,wed,fri", hour=9, minute=0)

    print("Zamanlayıcı başlatıldı:")
    print("  Pazar    22:00 → Toplu üretim (3 post) + onay maili")
    print("  Pzt/Çrş/Cum 09:00 → Onaylı postları yayınla + story")
    print("\nTest komutları:")
    print("  python main.py --batch    → Hemen toplu üret")
    print("  python main.py --publish  → Onaylı postları hemen yayınla")
    print("  python main.py --now      → Tek post üret + onay maili")
    print("  python approval_server.py → Onay sunucusunu başlat")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nDurduruldu.")


if __name__ == "__main__":
    main()
