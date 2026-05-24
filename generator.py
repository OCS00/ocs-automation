import json
import os
import re
from pathlib import Path

import anthropic
import fal_client
import requests

from image_composer import compose_slide, compose_story

SYSTEM_PROMPT = """Sen OCS Creative'in Instagram içerik yazarısın. Görevin: web sitesi olmayan veya eski site kullanan esnaf ve KOBİ sahiplerine yönelik, @firat_ozbey_ kalitesinde eğitici, derin ve paylaşılmaya değer carousel postlar üretmek.

OCS CREATIVE:
- Slogan: "Söz Değil, İş Üretiyoruz"
- Hizmetler: Web tasarım, SEO, mobil uygulama, e-ticaret, dijital pazarlama
- Stack: Next.js 14, React, Tailwind CSS
- Rakamlar: 50+ proje, %99 memnuniyet, 12 sektör, müşterilerde %40 dönüşüm artışı
- Gerçek projeler: Glory Cord (e-ticaret), Av. Osman Özkaya (hukuk bürosu), Smmm Yavuz Şahin (mali müşavir)

HEDEF KİTLE: Web sitesi olmayan ya da eski/yavaş site kullanan esnaf, KOBİ sahibi, girişimci. B2B satış odaklı — içerik okuyucuyu DM atmaya veya ocscreative.com.tr'ye gitmeye ikna etmeli.

--- FİNANSAL ETKİ ÇERÇEVESI (EN KRİTİK KURAL) ---
Teknik bilgi değil, PARA konuş. Her istatistiği TL/müşteri/ciro kaybına çevir.
- YANLIŞ: "3 saniyede açılmayan site bounce rate'i artırır"
- DOĞRU: "Siteniz 3 sn'de açılmazsa ziyaretçinin %53'ü çıkıyor — ayda 100 ziyaretçiyse 53 müşteri adayı çöpe gidiyor"
- Tablolar ve karşılaştırmalar ekle: "Yavaş site vs. hızlı site — yıllık fark"
- B2B alıcıya konuş: ciro etkisi, dönüşüm farkı, rakipten geri kalma maliyeti

--- İÇERİK KALİTESİ STANDARDI ---
@firat_ozbey_ tarzında yaz. Bu ne demek:
- Her slayt tek bir güçlü fikir taşısın, generik olmasın
- Somut rakamlar, gerçek senaryolar, "sen de yaşadın mı?" anları
- "Sık yapılan hatalar", "3 farklı yol", "karşılaştırma", "adım adım" formatları kullan
- Pro ipuçları serpiştir
- Okuyucu slaytı bitirince bir şey öğrenmiş olsun, sadece "evet doğru" demesin
- Her bullet max 10 kelime, spesifik ve aksiyon odaklı

--- 3 İÇERİK SÜTUNU ---
Konu türüne göre uygun formatta yaz:
1. FİNANSAL ETKİ konuları → Başlıkta rakam, içerikte maliyet/kazanç karşılaştırması
2. SEKTÖREL/VAKA konuları → "X işletmesi için ne yaptık, sonuç ne oldu" formatı, gerçek proje referansları
3. KURUCU GÜNLÜĞÜ konuları → Kişisel, sahici, "sahne arkası" tonu; "50+ proje sonunda gördük ki..." şeklinde

--- CAROUSEL YAPISI ---
Slide sayısını konunun derinliğine göre 5-8 arasında seç.

SLIDE TİPLERİ ve AMAÇLARI:
- cover (ilk slayt): Scroll durduran hook. Rakam odaklı başlık veya acı veren soru
- step (ara slaytlar): Her slayt farklı açı — problem, finansal etki, çözüm yolu, vaka, karşılaştırma, pro ipucu
- cta (son slayt): Net B2B yönlendirme — "Sitenizi ücretsiz analiz ediyoruz, DM atın"

SLIDE_TYPE KURALI:
- cover → step_num: 0
- step → step_num: 1, 2, 3... sırayla
- cta → son step_num + 1

--- BULLET KURALI ---
- Her step slaytında 3-4 bullet
- Max 10 kelime/bullet, hiç generik cümle yok
- Örnek iyi: "Sayfa 3 sn'de açılmazsa kullanıcının %53'ü çıkıyor"
- Örnek kötü: "Hızlı site önemlidir"

--- CAPTION ---
3-4 cümle. Finansal etki veya sahici bir hikaye ile aç. OCS rakamlarını doğal kullan. Son cümle yorum daveti veya soru.

--- HASHTAGS ---
20-25 adet. Niş + orta + geniş karışım. Türkçe ve İngilizce."""

# ── İÇERİK SÜTUNLARI ──────────────────────────────────────────────────────────
# Sütun 1: Finansal Etki / Hız Verileri (teknik değil, maliyet odaklı)
# Sütun 2: Niş Sektörel Çözümler / Vaka Analizleri
# Sütun 3: Kurucu Günlüğü / Süreç Arkası
# Döngü sırası: 1 → 2 → 3 → 1 → 2 → 3 ...
TOPICS = [
    # SÜTUN 1 — Finansal Etki
    "Web siteniz 1 saniye yavaşsa yılda ne kadar para kaybediyorsunuz?",
    "Web sitesi olmayan işletmenin her gün kaybettiği gerçek para",
    "Siteniz mobil uyumlu değilse müşterinizin %60'ı rakibinize gidiyor",
    "Eski web sitesi mi? İşte rakamlarla gerçek maliyet",
    "Tüketicilerin %75'i güvenmeden önce siteye bakıyor — bu sizi nasıl etkiliyor?",
    "Google'da çıkmayan işletme yılda kaç müşteri kaçırıyor?",
    "Yavaş site = düşen satış: 3 saniyede ne olduğunu biliyor musunuz?",
    "Web sitesi yatırımı ortalama kaç ayda geri döner? Gerçek rakamlar",

    # SÜTUN 2 — Niş Sektörel Vaka Analizleri
    "Restoran web sitesi nasıl olmalı? Rezervasyon ve menü stratejisi",
    "E-ticaret sitesi kurarken yaptığımız 3 kritik tercih — Glory Cord örneği",
    "Hukuk bürosu web sitesi nasıl olmalı? Av. Osman Özkaya projemizden öğrendiklerimiz",
    "Mali müşavir için yaptığımız web sitesi: Smmm Yavuz Şahin projesi",
    "Güzellik salonu için dönüşüm odaklı web sitesi nasıl kurulur?",
    "Yerel esnaf için Google Maps + web sitesi kombinasyonu nasıl çalışır?",
    "Ucuz web sitesi mi profesyonel web sitesi mi — müşteri kaybı riski açısından",
    "Web sitesi yaptırırken ajandan sormalısın şu 5 soru",

    # SÜTUN 3 — Kurucu Günlüğü / Süreç Arkası
    "50+ proje sonunda öğrendiklerimiz — dürüst bir özet",
    "Bir müşteri projesinin perde arkası: başlangıçtan yayına 4 hafta",
    "Bize iş veren müşteriler ne istedi, biz ne yaptık",
    "Neden bazı web siteleri 3 ayda kapanıyor? Gördüklerimiz",
    "Fiyat mı kalite mi? Müşterilerin en sık sorduğu soru ve cevabı",
    "2026'da web tasarımında değişen 3 şey — biz nasıl uyum sağladık",
]

IMAGES_DIR = Path("images")


def generate_content(topic: str) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Konu: {topic}\n\n"
                    "Bu konu için üst düzey, kreatif ve dönüşüm odaklı bir Instagram carousel postu oluştur.\n"
                    "SADECE ve SADECE aşağıdaki JSON formatında çıktı ver, asla markdown veya ekstra açıklama ekleme:\n"
                    "{\n"
                    '  "slides": [\n'
                    '    {\n'
                    '      "slide_type": "cover",\n'
                    '      "step_num": 0,\n'
                    '      "title": "Vurucu başlık (max 6 kelime)",\n'
                    '      "subtitle": "Merak uyandıran alt başlık (1 cümle)",\n'
                    '      "bullets": []\n'
                    '    },\n'
                    '    {\n'
                    '      "slide_type": "step",\n'
                    '      "step_num": 1,\n'
                    '      "title": "Slayt Başlığı (max 6 kelime)",\n'
                    '      "subtitle": "Kısa açıklama veya can alıcı soru",\n'
                    '      "bullets": ["Madde 1 (max 9 kelime)", "Madde 2 (max 9 kelime)"]\n'
                    '    },\n'
                    '    {\n'
                    '      "slide_type": "cta",\n'
                    '      "step_num": 2,\n'
                    '      "title": "Harekete Geç (max 5 kelime)",\n'
                    '      "subtitle": "Net CTA cümlesi",\n'
                    '      "bullets": ["Profildeki linke tıklayın", "DM üzerinden iletişime geçin"]\n'
                    '    }\n'
                    "  ],\n"
                    '  "image_prompt": "Tüm slaytlar için ortak arka plan. İngilizce. Minimalist, soft texture, subtle purple tones, white/light background, NO text, safe for text overlay. Cinematic quality.",\n'
                    '  "story_image_prompt": "Instagram Story arka planı. İngilizce. Same brand mood but portrait feel, 9:16 ratio composition, soft light background, purple accent details, NO text.",\n'
                    '  "story_stat": "En çarpıcı istatistik veya rakam (max 6 kelime, Türkçe)",\n'
                    '  "caption": "Instagram zengin açıklama metni",\n'
                    '  "hashtags": "#tag1 #tag2 #tag3"\n'
                    "}\n\n"
                    "Slayt sayısını konunun derinliğine ve kalitesine göre 4-7 arasında belirle."
                ),
            }
        ],
    )

    content = message.content[0].text
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        raw = json_match.group()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Tek tırnak ve kontrol karakterlerini temizle
            raw = raw.replace("\\'", "'").replace("\\n", " ")
            raw = re.sub(r",\s*([}\]])", r"\1", raw)  # trailing comma
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass

    # Fallback mekanizması (Hata durumunda güvenli çıktı)
    return {
        "slides": [
            {
                "slide_type": "cover",
                "step_num": 0,
                "title": "Dijitalde Yok Olmak Mı?",
                "subtitle": "İşletmenizin geleceğini değiştirecek o adım.",
                "bullets": [],
                "image_prompt": "Minimalist digital network, pure black background, glowing purple line art, empty center space, cinematic tech, 8k.",
            }
        ],
        "caption": topic,
        "hashtags": "#ocscreative #webdesign",
    }


def _generate_bg_image(prompt: str, path: Path) -> None:
    os.environ["FAL_KEY"] = os.getenv("FAL_API_KEY", "")
    result = fal_client.run(
        "fal-ai/flux-pro",
        arguments={"prompt": prompt, "num_images": 1, "image_size": "square"},
    )
    img_data = requests.get(result["images"][0]["url"], timeout=60)
    img_data.raise_for_status()
    path.write_bytes(img_data.content)


def _generate_story_bg_image(prompt: str, path: Path) -> None:
    os.environ["FAL_KEY"] = os.getenv("FAL_API_KEY", "")
    result = fal_client.run(
        "fal-ai/flux-pro",
        arguments={"prompt": prompt, "num_images": 1, "image_size": "portrait_4_3"},
    )
    img_data = requests.get(result["images"][0]["url"], timeout=60)
    img_data.raise_for_status()
    path.write_bytes(img_data.content)


def generate_post(topic: str, post_id: str) -> dict:
    content = generate_content(topic)
    slides = content.get("slides", [])
    total = len(slides)

    IMAGES_DIR.mkdir(exist_ok=True)
    slide_paths = []

    # Tüm slaytlar için tek bir arka plan üret (FAL maliyetini düşür)
    carousel_bg_path = IMAGES_DIR / f"{post_id}_bg.jpg"
    image_prompt = content.get("image_prompt", "")
    if image_prompt:
        _generate_bg_image(image_prompt, carousel_bg_path)
    bg_arg = str(carousel_bg_path) if carousel_bg_path.exists() else None

    for i, slide in enumerate(slides):
        composed_path = IMAGES_DIR / f"{post_id}_slide{i}.jpg"
        composed = compose_slide(
            slide_type=slide.get("slide_type", "step"),
            step_num=slide.get("step_num", i),
            total_slides=total,
            title=slide["title"],
            subtitle=slide.get("subtitle", ""),
            bullets=slide.get("bullets", []),
            slide_index=i,
            bg_image_path=bg_arg,
        )
        composed.save(str(composed_path), "JPEG", quality=95)
        slide_paths.append(str(composed_path))

    # Story üret
    story_path_str = ""
    cover = slides[0] if slides else {}
    story_bg_path = IMAGES_DIR / f"{post_id}_story_bg.jpg"
    story_prompt = content.get("story_image_prompt", "")
    if story_prompt:
        _generate_story_bg_image(story_prompt, story_bg_path)
    story_bg_arg = str(story_bg_path) if story_bg_path.exists() else None

    story_composed_path = IMAGES_DIR / f"{post_id}_story.jpg"
    story_img = compose_story(
        title=cover.get("title", topic),
        subtitle=cover.get("subtitle", ""),
        stat=content.get("story_stat", ""),
        bg_image_path=story_bg_arg,
    )
    story_img.save(str(story_composed_path), "JPEG", quality=95)
    story_path_str = str(story_composed_path)

    return {
        "id": post_id,
        "topic": topic,
        "caption": content.get("caption", ""),
        "hashtags": content.get("hashtags", ""),
        "slide_paths": slide_paths,
        "story_path": story_path_str,
        "image_url": "",
        "image_path": slide_paths[0] if slide_paths else "",
    }