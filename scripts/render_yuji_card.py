#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    # 优先使用系统中文字体，保证海报中文稳定显示。
    candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def cover_crop(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = img.resize((int(src_w * scale), int(src_h * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def gradient_overlay(size: tuple[int, int]) -> Image.Image:
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    pix = overlay.load()
    for y in range(h):
        for x in range(w):
            left = int(180 * (1 - min(x / (w * 0.86), 1)))
            bottom = int(125 * max((y - h * 0.55) / (h * 0.45), 0))
            top = int(70 * max((h * 0.28 - y) / (h * 0.28), 0))
            alpha = min(230, left + bottom + top + 25)
            pix[x, y] = (5, 9, 12, alpha)
    return overlay


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, fill, bold: bool = False, anchor=None):
    draw.text(xy, value, font=font(size, bold), fill=fill, anchor=anchor)


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def render(background: Path, output: Path) -> None:
    size = (1200, 1600)
    bg = Image.open(background).convert("RGB")
    card = cover_crop(bg, size).convert("RGBA")
    card = card.filter(ImageFilter.GaussianBlur(radius=0.2))
    card.alpha_composite(gradient_overlay(size))

    draw = ImageDraw.Draw(card)
    cream = (245, 238, 222, 255)
    muted = (188, 198, 188, 255)
    gold = (210, 183, 105, 255)
    green = (160, 220, 170, 255)
    line = (245, 238, 222, 55)

    # 轻量球场线条，呼应羽毛球地胶。
    draw.line((88, 235, 88, 1368), fill=line, width=2)
    draw.line((88, 1368, 1110, 1368), fill=line, width=2)
    draw.line((88, 890, 540, 890), fill=(245, 238, 222, 35), width=2)

    text(draw, (88, 96), "YUJI CARD", 38, (225, 232, 217, 230), bold=True)
    text(draw, (88, 146), "羽迹卡", 64, cream, bold=True)
    draw.line((88, 232, 310, 232), fill=gold, width=4)

    text(draw, (88, 302), "AN SE YOUNG", 64, cream, bold=True)
    text(draw, (88, 382), "截至 2026.05.31", 34, muted)
    text(draw, (88, 448), "赛季前五个月", 58, cream, bold=True)
    text(draw, (88, 520), "六个冠军节点", 58, cream, bold=True)
    text(draw, (88, 592), "4 个女单冠军 + 2 个女团冠军", 32, green, bold=True)

    events = [
        ("01", "马来西亚公开赛 S1000", "女单冠军"),
        ("02", "印度公开赛 S750", "女单冠军"),
        ("03", "亚洲团体锦标赛", "女团冠军"),
        ("04", "亚洲锦标赛", "女单冠军"),
        ("05", "尤伯杯", "女团冠军"),
        ("06", "新加坡公开赛 S750", "女单冠军"),
    ]
    y = 675
    for idx, name, result in events:
        rounded(draw, (88, y - 14, 682, y + 56), 18, (8, 13, 15, 120), outline=(245, 238, 222, 42))
        text(draw, (116, y), idx, 28, gold, bold=True)
        text(draw, (176, y - 2), name, 31, cream, bold=True)
        text(draw, (176, y + 34), result, 23, muted)
        y += 92

    quote = "不是战报，\n是一串被训练、赛程和关键分写下的痕迹。"
    rounded(draw, (88, 1198, 760, 1342), 26, (8, 13, 15, 145), outline=(210, 183, 105, 70))
    text(draw, (126, 1230), quote, 34, cream, bold=False)

    rounded(draw, (88, 1394, 1078, 1518), 24, (245, 238, 222, 230))
    text(draw, (126, 1422), "如果你也有一场想留下的球", 34, (12, 18, 18, 255), bold=True)
    text(draw, (126, 1470), "评论「羽迹卡」+ 一句话，我先免费帮 5 个球友做一张", 25, (28, 42, 38, 255))

    text(draw, (88, 1540), "YUJI / 羽迹  ·  让热爱有一张可以被保存的样子", 24, (245, 238, 222, 175))
    output.parent.mkdir(parents=True, exist_ok=True)
    card.convert("RGB").save(output, quality=96)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    render(args.background, args.output)


if __name__ == "__main__":
    main()
