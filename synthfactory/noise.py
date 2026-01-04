from __future__ import annotations
import random, io
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

def apply_noise_pipeline(path: Path,
                         rotate_deg_max: float,
                         blur_radius_max: float,
                         contrast_jitter: float,
                         brightness_jitter: float,
                         speckle_amount: float,
                         jpeg_recompress: bool,
                         jpeg_quality_min: int,
                         jpeg_quality_max: int,
                         partial_crop_prob: float,
                         crop_margin_max: float,
                         smudge_prob: float,
                         smudge_strength: float,
                         downsample_prob: float,
                         downsample_min_scale: float,
                         downsample_max_scale: float,
                         text_damage_prob: float,
                         text_damage_zones_min: int,
                         text_damage_zones_max: int,
                         text_damage_strength: float,
                         text_damage_box_min_px: int,
                         text_damage_box_max_px: int):
    img = Image.open(path).convert("RGB")

    if random.random() < partial_crop_prob:
        w, h = img.size
        mx = int(w * random.uniform(0.0, crop_margin_max))
        my = int(h * random.uniform(0.0, crop_margin_max))
        left = random.randint(0, mx)
        top = random.randint(0, my)
        right = w - random.randint(0, mx)
        bottom = h - random.randint(0, my)
        img = img.crop((left, top, right, bottom)).resize((w, h), Image.Resampling.BICUBIC)

    if random.random() < downsample_prob:
        scale = random.uniform(downsample_min_scale, downsample_max_scale)
        w, h = img.size
        img = img.resize((max(8, int(w*scale)), max(8, int(h*scale))), Image.Resampling.BILINEAR)                 .resize((w, h), Image.Resampling.BICUBIC)

    deg = random.uniform(-rotate_deg_max, rotate_deg_max)
    img = img.rotate(deg, expand=False, fillcolor="white")

    if blur_radius_max > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0, blur_radius_max)))

    if contrast_jitter:
        img = ImageEnhance.Contrast(img).enhance(1.0 + random.uniform(-contrast_jitter, contrast_jitter))
    if brightness_jitter:
        img = ImageEnhance.Brightness(img).enhance(1.0 + random.uniform(-brightness_jitter, brightness_jitter))

    if random.random() < smudge_prob:
        img = _smudge(img, strength=smudge_strength)

    if random.random() < text_damage_prob:
        zones = random.randint(text_damage_zones_min, text_damage_zones_max)
        img = _text_damage(img, zones, text_damage_strength, text_damage_box_min_px, text_damage_box_max_px)

    if speckle_amount and speckle_amount > 0:
        img = _speckle(img, speckle_amount)

    if jpeg_recompress:
        q = random.randint(jpeg_quality_min, jpeg_quality_max)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")

    img.save(path, format="JPEG", quality=92)

def _speckle(img: Image.Image, amount: float) -> Image.Image:
    if img is None:
        return img
    px = img.load()
    w, h = img.size
    n = int(w*h*amount)
    for _ in range(n):
        x = random.randrange(w); y = random.randrange(h)
        v = random.choice([0, 255])
        px[x, y] = (v, v, v)
    return img

def _smudge(img: Image.Image, strength: float) -> Image.Image:
    w,h = img.size
    out = img.copy()
    for _ in range(random.randint(2,6)):
        y = random.randint(int(h*0.28), int(h*0.86))
        strip_h = random.randint(18, 55)
        x = random.randint(int(w*0.35), int(w*0.95))
        strip_w = random.randint(160, 480)
        box = (max(0, x-strip_w), max(0, y-strip_h//2), min(w, x), min(h, y+strip_h//2))
        region = out.crop(box)
        s = 1.0 - min(0.85, strength) * random.uniform(0.35, 0.7)
        rw,rh = region.size
        region = region.resize((max(8,int(rw*s)), rh), Image.Resampling.BILINEAR).resize((rw,rh), Image.Resampling.BICUBIC)
        region = region.filter(ImageFilter.GaussianBlur(radius=0.6 + strength*1.4))
        out.paste(region, box)
    return out

def _text_damage(img: Image.Image, zones: int, strength: float, box_min: int, box_max: int) -> Image.Image:
    w,h = img.size
    out = img.copy()
    for _ in range(zones):
        x = random.randint(int(w*0.08), int(w*0.78))
        y = random.randint(int(h*0.18), int(h*0.82))
        bw = random.randint(box_min, min(box_max, w-1))
        bh = random.randint(int(box_min*0.5), min(int(box_max*0.6), h-1))
        bw = min(bw, w-x-1); bh = min(bh, h-y-1)
        if bw < 30 or bh < 18:
            continue
        box = (x, y, x+bw, y+bh)
        region = out.crop(box)
        pscale = 1.0 - (0.60 * strength) * random.uniform(0.6, 1.0)
        rw,rh = region.size
        region = region.resize((max(8,int(rw*pscale)), max(8,int(rh*pscale))), Image.Resampling.BILINEAR)
        region = region.resize((rw,rh), Image.Resampling.NEAREST)
        region = region.filter(ImageFilter.GaussianBlur(radius=0.8 + 1.8*strength))
        out.paste(region, box)
    return out
