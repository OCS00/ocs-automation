from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Renk paleti ────────────────────────────────────────────────────────────
BG          = (250, 250, 255)   # neredeyse beyaz, hafif mor tonu
DARK        = (12,  12,  30)    # başlık rengi
GRAY        = (110, 110, 135)   # alt yazı
PURPLE      = (107, 102, 240)   # marka rengi
PURPLE_DARK = (72,  67, 190)
PURPLE_SOFT = (224, 222, 255)   # açık mor kutu
WHITE       = (255, 255, 255)

CANVAS = (1080, 1080)
FONTS_DIR = Path("assets/fonts")


def _font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS_DIR / ("Poppins-Bold.ttf" if bold else "Poppins-Regular.ttf")
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> "list[str]":
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if font.getbbox(test)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ── Dekoratif elementler ───────────────────────────────────────────────────

def _dot_grid(draw: ImageDraw.Draw, x0: int, y0: int,
              cols: int = 6, rows: int = 6, color=PURPLE, spacing: int = 22) -> None:
    for r in range(rows):
        for c in range(cols):
            cx = x0 + c * spacing
            cy = y0 + r * spacing
            a = max(40, 200 - r * 20 - c * 10)
            draw.ellipse([(cx - 3, cy - 3), (cx + 3, cy + 3)],
                         fill=(*color, a))


def _big_circle(draw: ImageDraw.Draw, cx: int, cy: int,
                r: int, fill, outline=None) -> None:
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)],
                 fill=fill, outline=outline)


def _corner_bracket(draw: ImageDraw.Draw, x: int, y: int,
                    size: int = 40, corner: str = "tl") -> None:
    """Köşe süsleme çizgisi."""
    t = 5
    if corner == "tl":
        draw.rectangle([(x, y), (x + size, y + t)], fill=(*PURPLE, 200))
        draw.rectangle([(x, y), (x + t, y + size)], fill=(*PURPLE, 200))
    elif corner == "tr":
        draw.rectangle([(x - size, y), (x, y + t)], fill=(*PURPLE, 200))
        draw.rectangle([(x - t, y), (x, y + size)], fill=(*PURPLE, 200))
    elif corner == "br":
        draw.rectangle([(x - size, y - t), (x, y)], fill=(*PURPLE, 200))
        draw.rectangle([(x - t, y - size), (x, y)], fill=(*PURPLE, 200))
    elif corner == "bl":
        draw.rectangle([(x, y - t), (x + size, y)], fill=(*PURPLE, 200))
        draw.rectangle([(x, y - size), (x + t, y)], fill=(*PURPLE, 200))


def _tag_pill(draw: ImageDraw.Draw, x: int, y: int,
              text: str, font: ImageFont.FreeTypeFont) -> None:
    """Küçük mor etiket kutusu."""
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 20, 10
    w, h = tw + pad_x * 2, th + pad_y * 2
    draw.rounded_rectangle([(x, y), (x + w, y + h)],
                            radius=h // 2, fill=PURPLE)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text,
              font=font, fill=WHITE)


def _step_badge(draw: ImageDraw.Draw, x: int, y: int, num: int) -> None:
    size = 72
    draw.rounded_rectangle([(x, y), (x + size, y + size)],
                            radius=16, fill=PURPLE)
    font = _font(bold=True, size=36)
    text = str(num)
    bbox = font.getbbox(text)
    tx = x + (size - (bbox[2] - bbox[0])) // 2
    ty = y + (size - (bbox[3] - bbox[1])) // 2 - bbox[1] // 2
    draw.text((tx, ty), text, font=font, fill=WHITE)


def _cta_button(draw: ImageDraw.Draw, x: int, y: int,
                text: str, width: int = 440) -> None:
    h = 72
    draw.rounded_rectangle([(x, y), (x + width, y + h)],
                            radius=h // 2, fill=PURPLE)
    # Sağda ok işareti yerine küçük bir kare
    draw.rounded_rectangle([(x + width - 60, y + 16), (x + width - 16, y + h - 16)],
                            radius=10, fill=PURPLE_DARK)
    font = _font(bold=True, size=26)
    bbox = font.getbbox(text)
    tx = x + 36
    ty = y + (h - (bbox[3] - bbox[1])) // 2 - bbox[1] // 2
    draw.text((tx, ty), text, font=font, fill=WHITE)


def _divider_line(draw: ImageDraw.Draw, x: int, y: int,
                  width: int = 80, height: int = 6) -> None:
    draw.rounded_rectangle([(x, y), (x + width, y + height)],
                            radius=3, fill=PURPLE)


def _brand_bar(draw: ImageDraw.Draw) -> None:
    """Alt brand şeridi."""
    bar_h = 64
    draw.rectangle([(0, CANVAS[1] - bar_h), (CANVAS[0], CANVAS[1])],
                   fill=PURPLE)
    font = _font(bold=True, size=22)
    draw.text((40, CANVAS[1] - bar_h + 20), "@ocscreative.tr",
              font=font, fill=WHITE)
    # Sağda site adresi
    site = "ocscreative.com.tr"
    sb = font.getbbox(site)
    draw.text((CANVAS[0] - 40 - (sb[2] - sb[0]),
               CANVAS[1] - bar_h + 20), site, font=font, fill=(*WHITE, 180))


def _slide_counter(draw: ImageDraw.Draw, idx: int, total: int) -> None:
    font = _font(bold=False, size=22)
    text = f"{idx + 1} / {total}"
    bb = font.getbbox(text)
    x = CANVAS[0] - 44 - (bb[2] - bb[0])
    draw.text((x, 36), text, font=font, fill=(*GRAY, 200))


def _slide_dots(draw: ImageDraw.Draw, idx: int, total: int) -> None:
    y = CANVAS[1] - 32
    spacing = 18
    start = (CANVAS[0] - total * spacing) // 2
    for i in range(total):
        x = start + i * spacing
        if i == idx:
            draw.ellipse([(x - 6, y - 6), (x + 6, y + 6)], fill=PURPLE)
        else:
            draw.ellipse([(x - 4, y - 4), (x + 4, y + 4)],
                         fill=(*PURPLE, 80))


# ── COVER ──────────────────────────────────────────────────────────────────

def _layout_cover(draw: ImageDraw.Draw, title: str, subtitle: str) -> None:
    W = CANVAS[0]

    # Büyük dekoratif daire — sağ alt
    _big_circle(draw, W - 80, CANVAS[1] - 160, 340,
                fill=(*PURPLE_SOFT, 180))
    _big_circle(draw, W + 60, CANVAS[1] - 80, 180,
                fill=(*PURPLE, 40))

    # Küçük daire — sol üst
    _big_circle(draw, 60, 60, 90, fill=(*PURPLE_SOFT, 120))

    # Dot grid — sağ üst
    _dot_grid(draw, W - 200, 60, cols=7, rows=5)

    # Köşe brackets
    _corner_bracket(draw, 30, 30, size=50, corner="tl")
    _corner_bracket(draw, W - 30, CANVAS[1] - 94, size=50, corner="br")

    # Ana başlık — ortada büyük
    title_font = _font(bold=True, size=82)
    max_w = W - 80
    lines = _wrap(title, title_font, max_w)
    line_h = title_font.getbbox("A")[3] + 14
    total_h = len(lines[:3]) * line_h
    y = (CANVAS[1] - total_h) // 2 - 60

    for i, line in enumerate(lines[:3]):
        # Son kelimeler vurgu rengiyle
        if i == len(lines[:3]) - 1:
            draw.text((40, y), line, font=title_font, fill=PURPLE)
        else:
            draw.text((40, y), line, font=title_font, fill=DARK)
        y += line_h

    y += 14
    _divider_line(draw, 40, y, width=100, height=7)
    y += 28

    if subtitle:
        sub_font = _font(bold=False, size=32)
        for line in _wrap(subtitle, sub_font, W - 80)[:2]:
            draw.text((40, y), line, font=sub_font, fill=GRAY)
            y += sub_font.getbbox("A")[3] + 10

    # Slide sayacı
    _slide_counter(draw, 0, 1)


# ── STEP ───────────────────────────────────────────────────────────────────

def _layout_step(draw: ImageDraw.Draw, step_num: int, total_slides: int,
                 slide_index: int, title: str, subtitle: str,
                 bullets: "list[str]") -> None:
    W = CANVAS[0]

    # Arka dekorasyon — sağ taraf büyük daire
    _big_circle(draw, W + 100, 200, 380, fill=(*PURPLE_SOFT, 140))
    _dot_grid(draw, W - 180, CANVAS[1] - 230, cols=5, rows=5,
              color=PURPLE, spacing=24)

    # Sol üst köşe bracket
    _corner_bracket(draw, 30, 30, size=45, corner="tl")

    y = 52
    # Slayt sayacı
    _slide_counter(draw, slide_index, total_slides)

    # Adım badge
    _step_badge(draw, 40, y, step_num)
    y += 96

    # Başlık
    title_font = _font(bold=True, size=66)
    max_w = W - 160
    lines = _wrap(title, title_font, max_w)
    line_h = title_font.getbbox("A")[3] + 10
    for line in lines[:3]:
        draw.text((40, y), line, font=title_font, fill=DARK)
        y += line_h
    y += 6

    _divider_line(draw, 40, y, width=80, height=6)
    y += 28

    if subtitle:
        sub_font = _font(bold=False, size=30)
        for line in _wrap(subtitle, sub_font, max_w)[:2]:
            draw.text((40, y), line, font=sub_font, fill=GRAY)
            y += sub_font.getbbox("A")[3] + 8
        y += 20

    if bullets:
        b_font = _font(bold=False, size=28)
        b_lh = b_font.getbbox("A")[3]
        for b in bullets[:5]:
            blines = _wrap(b, b_font, max_w - 36)
            for j, bl in enumerate(blines[:2]):
                if j == 0:
                    # kare ikon
                    sq = 10
                    draw.rectangle([(40, y + (b_lh - sq) // 2 + 2),
                                    (40 + sq, y + (b_lh - sq) // 2 + sq + 2)],
                                   fill=PURPLE)
                    draw.text((40 + sq + 16, y), bl, font=b_font, fill=DARK)
                else:
                    draw.text((40 + sq + 16, y), bl, font=b_font,
                              fill=(*DARK, 200))
                y += b_lh + 16
            y += 6


# ── CTA ────────────────────────────────────────────────────────────────────

def _layout_cta(draw: ImageDraw.Draw, total_slides: int,
                title: str, subtitle: str, bullets: "list[str]") -> None:
    W = CANVAS[0]

    # Arka plan: beyaz, sağ alt dekoratif daire
    _big_circle(draw, W + 80, CANVAS[1] - 100, 380,
                fill=(*PURPLE_SOFT, 200))
    _big_circle(draw, -80, 120, 220, fill=(*PURPLE_SOFT, 150))
    _dot_grid(draw, W - 190, 60, cols=6, rows=5, color=PURPLE, spacing=22)
    _corner_bracket(draw, 30, 30, size=50, corner="tl")

    # Slayt sayacı
    font_cnt = _font(bold=False, size=22)
    text_cnt = f"{total_slides} / {total_slides}"
    bb = font_cnt.getbbox(text_cnt)
    draw.text((W - 44 - (bb[2] - bb[0]), 36), text_cnt,
              font=font_cnt, fill=(*GRAY, 200))

    # Büyük başlık — mor renkte
    y = 160
    title_font = _font(bold=True, size=80)
    for line in _wrap(title, title_font, W - 80)[:3]:
        draw.text((40, y), line, font=title_font, fill=PURPLE)
        y += title_font.getbbox("A")[3] + 10

    y += 10
    _divider_line(draw, 40, y, width=100, height=7)
    y += 36

    if subtitle:
        sub_font = _font(bold=False, size=30)
        for line in _wrap(subtitle, sub_font, W - 80)[:2]:
            draw.text((40, y), line, font=sub_font, fill=GRAY)
            y += sub_font.getbbox("A")[3] + 8
        y += 20

    if bullets:
        b_font = _font(bold=False, size=27)
        b_lh = b_font.getbbox("A")[3]
        for b in bullets[:4]:
            for j, bl in enumerate(_wrap(b, b_font, W - 80)[:2]):
                if j == 0:
                    sq = 10
                    draw.rectangle([(40, y + (b_lh - sq) // 2 + 2),
                                    (50, y + (b_lh - sq) // 2 + sq + 2)],
                                   fill=PURPLE)
                    draw.text((66, y), bl, font=b_font, fill=DARK)
                else:
                    draw.text((66, y), bl, font=b_font, fill=(*DARK, 180))
                y += b_lh + 14
            y += 6

    # Büyük CTA butonu
    _cta_button(draw, 40, CANVAS[1] - 160, "DM at  |  Ucretsiz Danisalim",
                width=520)


# ── ANA FONKSİYON ──────────────────────────────────────────────────────────

def compose_slide(
    slide_type: str,
    step_num: int,
    total_slides: int,
    title: str,
    subtitle: str,
    bullets: "list[str]",
    slide_index: int,
    bg_image_path: "str | None" = None,
) -> Image.Image:
    if bg_image_path:
        # FAL görselini yükle, hafif beyaz overlay ile okunabilir kıl
        bg = Image.open(bg_image_path).resize(CANVAS, Image.LANCZOS).convert("RGBA")
        overlay = Image.new("RGBA", CANVAS, (250, 250, 255, 195))
        img = Image.alpha_composite(bg, overlay)
    else:
        img = Image.new("RGBA", CANVAS, (*BG, 255))
    draw = ImageDraw.Draw(img)

    if slide_type == "cover":
        _layout_cover(draw, title, subtitle)
        _slide_dots(draw, slide_index, total_slides)
    elif slide_type == "cta":
        _layout_cta(draw, total_slides, title, subtitle, bullets)
        _slide_dots(draw, slide_index, total_slides)
    else:
        _layout_step(draw, step_num, total_slides, slide_index,
                     title, subtitle, bullets)
        _slide_dots(draw, slide_index, total_slides)

    _brand_bar(draw)
    return img.convert("RGB")


# ── STORY (1080x1920) ───────────────────────────────────────────────────────

STORY_CANVAS = (1080, 1920)


def compose_story(
    title: str,
    subtitle: str,
    stat: str = "",
    bg_image_path: "str | None" = None,
) -> Image.Image:
    """Instagram Story formatı — 1080x1920, dikey."""
    if bg_image_path:
        bg = Image.open(bg_image_path).resize(STORY_CANVAS, Image.LANCZOS).convert("RGBA")
        overlay = Image.new("RGBA", STORY_CANVAS, (250, 250, 255, 185))
        img = Image.alpha_composite(bg, overlay)
    else:
        img = Image.new("RGBA", STORY_CANVAS, (*BG, 255))

    draw = ImageDraw.Draw(img)
    W, H = STORY_CANVAS

    # Arka plan dekorasyon
    _big_circle(draw, W + 60,  H // 2 - 200, 420, fill=(*PURPLE_SOFT, 160))
    _big_circle(draw, -60,     H // 2 + 300, 300, fill=(*PURPLE_SOFT, 120))
    _dot_grid(draw, W - 220, 120, cols=7, rows=8, color=PURPLE, spacing=24)
    _corner_bracket(draw, 40, 60, size=60, corner="tl")
    _corner_bracket(draw, W - 40, H - 80, size=60, corner="br")

    # Üst marka etiketi
    tag_font = _font(bold=True, size=24)
    _tag_pill(draw, 40, 80, "ocscreative.com.tr", tag_font)

    # Orta içerik — stat büyük, başlık altında
    center_y = H // 2 - 220

    if stat:
        stat_font = _font(bold=True, size=96)
        stat_lines = _wrap(stat, stat_font, W - 80)
        stat_lh = stat_font.getbbox("A")[3] + 12
        for line in stat_lines[:2]:
            draw.text((40, center_y), line, font=stat_font, fill=PURPLE)
            center_y += stat_lh
        center_y += 16
        _divider_line(draw, 40, center_y, width=120, height=8)
        center_y += 36

    title_font = _font(bold=True, size=72)
    title_lh = title_font.getbbox("A")[3] + 12
    for line in _wrap(title, title_font, W - 80)[:3]:
        draw.text((40, center_y), line, font=title_font, fill=DARK)
        center_y += title_lh
    center_y += 16

    if subtitle:
        sub_font = _font(bold=False, size=34)
        for line in _wrap(subtitle, sub_font, W - 80)[:3]:
            draw.text((40, center_y), line, font=sub_font, fill=GRAY)
            center_y += sub_font.getbbox("A")[3] + 10

    # Alt CTA butonu
    _cta_button(draw, 40, H - 220, "Ucretsiz Analiz — DM at", width=580)

    # Alt marka şeridi
    bar_h = 80
    draw.rectangle([(0, H - bar_h), (W, H)], fill=PURPLE)
    brand_font = _font(bold=True, size=26)
    draw.text((48, H - bar_h + 26), "@ocscreative.tr", font=brand_font, fill=WHITE)
    site = "ocscreative.com.tr"
    sb = brand_font.getbbox(site)
    draw.text((W - 48 - (sb[2] - sb[0]), H - bar_h + 26), site,
              font=brand_font, fill=(*WHITE, 180))

    return img.convert("RGB")
