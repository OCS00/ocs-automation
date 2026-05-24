import os

import resend


def send_approval_email(post: dict) -> None:
    """Tek post için onay maili (geriye dönük uyumluluk)."""
    send_batch_approval_email([post])


def send_batch_approval_email(posts: list) -> None:
    """Haftalık 3 post için tek toplu onay maili."""
    resend.api_key = os.getenv("RESEND_API_KEY")
    base_url = os.getenv("APPROVAL_BASE_URL", "http://localhost:5001")

    batch_id = posts[0].get("batch_id") if len(posts) > 1 else None

    def _post_card(post: dict) -> str:
        approve_url = f"{base_url}/approve/{post['id']}"
        reject_url  = f"{base_url}/reject/{post['id']}"
        day_label   = post.get("scheduled_day", "")
        cover_path  = post.get("image_path", "")
        cover_file  = os.path.basename(cover_path) if cover_path else ""
        img_url     = f"{base_url}/images/{cover_file}" if cover_file else ""

        return f"""
        <div style="border:1px solid #e5e7eb; border-radius:10px; padding:20px; margin-bottom:24px;">
          <p style="margin:0 0 8px; font-size:13px; color:#6b7280; font-weight:600;
                    text-transform:uppercase; letter-spacing:1px;">{day_label}</p>
          <p style="margin:0 0 12px; font-size:15px; font-weight:700; color:#111;">{post['topic']}</p>
          {'<img src="' + img_url + '" style="width:100%;border-radius:8px;margin-bottom:12px;" />' if img_url else ''}
          <p style="font-size:13px; color:#374151; background:#f9fafb; padding:10px;
                    border-radius:6px; white-space:pre-line; margin:0 0 12px;">{post.get('caption','')[:200]}…</p>
          <a href="{reject_url}"
             style="font-size:13px; color:#ef4444; text-decoration:none;">✗ Bu postu reddet</a>
        </div>
        """

    cards_html = "".join(_post_card(p) for p in posts)

    if batch_id:
        approve_all_url = f"{base_url}/approve-batch/{batch_id}"
        action_block = f"""
        <div style="margin-top:32px; text-align:center;">
          <a href="{approve_all_url}"
             style="background:#22c55e; color:white; padding:16px 40px;
                    border-radius:10px; text-decoration:none; font-weight:bold; font-size:18px;
                    display:inline-block;">
            ✓ Tüm Haftayı Onayla ({len(posts)} post)
          </a>
          <p style="margin-top:12px; font-size:13px; color:#6b7280;">
            Onayladıktan sonra postlar sırasıyla zamanında yayınlanacak.
          </p>
        </div>
        """
        subject = f"[OCS] Haftalık {len(posts)} Post Onayı — {posts[0].get('scheduled_day','')}"
    else:
        post = posts[0]
        approve_url = f"{base_url}/approve/{post['id']}"
        action_block = f"""
        <div style="margin-top:32px;">
          <a href="{approve_url}"
             style="background:#22c55e; color:white; padding:14px 28px;
                    border-radius:8px; text-decoration:none; font-weight:bold; font-size:16px;">
            ✓ Onayla ve Paylaş
          </a>
        </div>
        """
        subject = f"[OCS] Post Onayı: {post['topic'][:50]}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto;
                 padding: 24px; color: #111;">
      <div style="background:#6B66F0; padding:20px 24px; border-radius:10px; margin-bottom:28px;">
        <h2 style="margin:0; color:white; font-size:20px;">OCS Creative — İçerik Onayı</h2>
        <p style="margin:6px 0 0; color:rgba(255,255,255,0.8); font-size:14px;">
          {len(posts)} post hazır, incelemenizi bekliyor.
        </p>
      </div>
      {cards_html}
      {action_block}
    </body>
    </html>
    """

    resend.Emails.send({
        "from": os.getenv("EMAIL_FROM", "OCS Creative <noreply@ocscreative.com.tr>"),
        "to": [os.getenv("EMAIL_RECIPIENT")],
        "subject": subject,
        "html": html,
    })
