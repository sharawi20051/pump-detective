"""Draw the Pump Detective logo files in assets/ (run once: python scripts/make_logo.py).

icon.png      square app icon: magnifying glass over a water drop on the brand gradient
logo_wide.png icon + "Pump Detective" wordmark for the sidebar (st.logo)
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
NAVY, BLUE, TEAL = (10, 37, 64), (11, 92, 173), (14, 147, 132)
S = 1024  # drawn large, then downsampled for smooth edges


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def icon(size):
    grad = Image.new("RGB", (S, S))
    px = grad.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * S)
            px[x, y] = mix(NAVY, BLUE, t / 0.6) if t < 0.6 else mix(BLUE, TEAL, (t - 0.6) / 0.4)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=S // 4.5, fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    cx, cy, r, w = 430, 430, 250, 70
    # Handle first, so the ring sits on top of it.
    d.line((cx + 200, cy + 200, 830, 830), fill="white", width=120)
    d.ellipse((830 - 60, 830 - 60, 830 + 60, 830 + 60), fill="white")  # round end cap
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline="white", width=w)
    # Water drop inside the lens.
    dx, dy = cx, cy + 40
    d.ellipse((dx - 95, dy - 70, dx + 95, dy + 120), fill=(130, 220, 205))
    d.polygon([(dx - 82, dy - 20), (dx, dy - 185), (dx + 82, dy - 20)], fill=(130, 220, 205))
    return img.resize((size, size), Image.LANCZOS)


def wide(height):
    scale = 4
    h = height * scale
    font = ImageFont.truetype(os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf"), int(h * 0.52))
    text = "Pump Detective"
    tw = int(font.getlength(text))
    img = Image.new("RGBA", (h + int(h * 0.28) + tw + 8, h), (0, 0, 0, 0))
    img.paste(icon(h), (0, 0))
    ImageDraw.Draw(img).text((h + int(h * 0.28), h // 2), text, font=font, fill=NAVY, anchor="lm")
    return img.resize((img.width // scale, height), Image.LANCZOS)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    icon(256).save(os.path.join(OUT, "icon.png"))
    wide(96).save(os.path.join(OUT, "logo_wide.png"))
    print("wrote", OUT)
