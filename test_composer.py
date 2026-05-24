"""
Tasarımı hızlı test et — fal.ai veya API kullanmaz.
Çalıştır: python test_composer.py
Çıktı:    images/test_slide_*.jpg
"""
import subprocess
from pathlib import Path

from image_composer import compose_slide

# Mevcut bg görsellerinden ilkini bul
slides = [
    dict(
        slide_type="cover",
        step_num=0,
        title="Rakibinizin sitesi var, sizinki yok.",
        subtitle="Müşteri hangisini seçiyor? Cevabı zaten biliyorsunuz.",
        bullets=[],
        slide_index=0,
    ),
    dict(
        slide_type="step",
        step_num=1,
        title="Müşteri önce Google'a bakıyor.",
        subtitle="Satın almadan önce işletmeyi araştırıyor — bu artık bir alışkanlık.",
        bullets=[
            "Tüketicilerin %75'i güvenmeden önce siteye bakıyor",
            "Google'da bulunamayan işletme, yok sayılıyor",
            "İlk izlenim artık kapıda değil, ekranda oluşuyor",
        ],
        slide_index=1,
    ),
    dict(
        slide_type="step",
        step_num=2,
        title="Eski site, kaybeden site.",
        subtitle="2010'dan kalma tasarım güven öldürüyor.",
        bullets=[
            "Yavaş yükleme: ziyaretçi 3 saniyede çıkıyor",
            "Mobil uyumsuz: kullanıcının %60'ı telefonda",
            "Eski görünüm: 'bu şirket hâlâ açık mı?' sorusu",
        ],
        slide_index=2,
    ),
    dict(
        slide_type="cta",
        step_num=3,
        title="Web sitenizi bugün kuralım.",
        subtitle="50+ proje, %99 memnuniyet. İlk görüşme ücretsiz.",
        bullets=[
            "ocscreative.com.tr'den iletişime geç",
            "DM'den yazın, hemen dönelim",
        ],
        slide_index=3,
    ),
]

total = len(slides)
out_paths = []

for s in slides:
    img = compose_slide(
        total_slides=total,
        **s,
    )
    out = f"images/test_slide_{s['slide_index']}.jpg"
    img.save(out, "JPEG", quality=95)
    out_paths.append(out)
    print(f"  ✓ {out}")

print(f"\n{total} slayt oluşturuldu.")

# Mac'te otomatik aç
try:
    subprocess.run(["open"] + out_paths, check=False)
except Exception:
    pass
