#!/usr/bin/env python3
import argparse, glob, os, sys
from num2words import num2words
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BG, INK = (250, 244, 230), (28, 28, 28)
DIV_Y, MAX_W = 700, 920

def spell(n):
    t = num2words(n, lang="en").replace(",", "").replace(" and ", " ")
    return t.upper()

def find_font():
    here = os.path.dirname(os.path.abspath(__file__))
    paths = sorted(glob.glob(os.path.join(here, "fonts", "*.ttf")))
    paths += ["/system/fonts/Roboto-Bold.ttf",
              "/system/fonts/RobotoStatic-Bold.ttf",
              "/system/fonts/Roboto-Regular.ttf",
              "/system/fonts/NotoSans-Bold.ttf",
              "/system/fonts/DroidSans-Bold.ttf"]
    paths += sorted(glob.glob("/system/fonts/*Bold*.ttf"))
    paths += sorted(glob.glob("/system/fonts/Roboto*.ttf"))
    for p in paths:
        if os.path.exists(p):
            return p
    sys.exit("No font found. Put a .ttf file in ~/numberarchive/fonts/")

def font_at(path, size):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_name("Bold")
    except Exception:
        pass
    return f

def box(d, text, f):
    return d.textbbox((0, 0), text, font=f, anchor="ls")

def draw_c(d, text, f, cx, cy):
    b = box(d, text, f)
    d.text((cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2),
           text, font=f, fill=INK, anchor="ls")

def fit_numeral(d, text, path):
    size = 560
    while size > 40:
        f = font_at(path, size)
        b = box(d, text, f)
        if b[2] - b[0] <= MAX_W and b[3] - b[1] <= 520:
            return f
        size -= 8
    return font_at(path, 40)

def wrap(d, text, f):
    lines, cur = [], ""
    for w in text.split(" "):
        trial = (cur + " " + w).strip()
        if cur and d.textlength(trial, font=f) > MAX_W:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    lines.append(cur)
    return lines

def fit_words(d, text, path):
    size = 140
    while size > 24:
        f = font_at(path, size)
        lines = wrap(d, text, f)
        widest = max(d.textlength(l, font=f) for l in lines)
        if widest <= MAX_W and len(lines) * size * 1.25 <= 480:
            return f, lines
        size -= 4
    f = font_at(path, 24)
    return f, wrap(d, text, f)

def render(n, path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    num = str(n)
    draw_c(d, num, fit_numeral(d, num, path), W / 2, 375)
    d.rectangle([160, DIV_Y - 2, W - 160, DIV_Y + 2], fill=INK)
    wf, lines = fit_words(d, spell(n), path)
    lh = wf.size * 1.25
    top = 1000 - len(lines) * lh / 2
    for i, l in enumerate(lines):
        draw_c(d, l, wf, W / 2, top + lh * i + lh / 2)
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--out", default="images")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.start < 0 or a.count < 1:
        sys.exit("start must be >= 0 and count >= 1")
    os.makedirs(a.out, exist_ok=True)
    path = find_font()
    print("Font:", path)
    made = skipped = 0
    for n in range(a.start, a.start + a.count):
        dest = os.path.join(a.out, f"{n:06d}.jpg")
        if os.path.exists(dest) and not a.force:
            skipped += 1
            continue
        tmp = dest + ".tmp"
        render(n, path).save(tmp, "JPEG", quality=92,
                             optimize=True, subsampling=0)
        os.replace(tmp, dest)
        made += 1
    print(f"Done. made={made} skipped={skipped} folder={a.out}")

if __name__ == "__main__":
    main()
