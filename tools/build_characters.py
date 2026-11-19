"""
Dynamic character & asset build pipeline for Five Nights at Ezequiel's (FNAE).

Reads character manifests from `assets_src/characters/*/character.json`
(ignoring `_template`), prefers AI-composited assets when present under
`assets_src/characters/<id>/` or `assets_src/base_graphics/ai_branding/`,
falls back to a high-quality NumPy/Pillow pipeline for new characters,
generates runtime graphics under `graphics/characters/<id>/` (plus legacy paths),
and writes `config/characters.json`.
"""

import argparse
import json
import os
import random
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_SRC_DIR = ROOT_DIR / "assets_src"
CHARACTERS_SRC_DIR = ASSETS_SRC_DIR / "characters"
BASE_GRAPHICS_DIR = ASSETS_SRC_DIR / "base_graphics"
AI_BRANDING_DIR = BASE_GRAPHICS_DIR / "ai_branding"
AI_STAGE_DIR = BASE_GRAPHICS_DIR / "ai_stage"
GRAPHICS_DIR = ROOT_DIR / "graphics"
CONFIG_OUT_PATH = ROOT_DIR / "config" / "characters.json"

OFFICE_SIZE = (1600, 720)
MENU_SIZE = (1280, 720)
ICON_SIZE = (200, 200)


def _find_first_existing(base_dir: Path, stems: list[str], exts=(".png", ".webp", ".jpg", ".jpeg")) -> Path | None:
    """Return the first existing file matching any stem+ext combination."""
    for stem in stems:
        p_direct = base_dir / stem
        if p_direct.exists() and p_direct.is_file():
            return p_direct
        for ext in exts:
            candidate = base_dir / f"{stem}{ext}"
            if candidate.exists() and candidate.is_file():
                return candidate
    return None


def load_and_fix_orientation(path: Path) -> Image.Image:
    """Open an image, normalize EXIF orientation, and convert to RGBA."""
    with Image.open(path) as im:
        fixed = ImageOps.exif_transpose(im)
        return fixed.convert("RGBA")


def crop_or_center_square(im: Image.Image, crop_box) -> Image.Image:
    """Crop image to [x1, y1, x2, y2] or a centered square if crop_box is None."""
    if crop_box and len(crop_box) == 4:
        x1, y1, x2, y2 = crop_box
        x1 = max(0, min(im.width - 1, int(x1)))
        y1 = max(0, min(im.height - 1, int(y1)))
        x2 = max(x1 + 1, min(im.width, int(x2)))
        y2 = max(y1 + 1, min(im.height, int(y2)))
        return im.crop((x1, y1, x2, y2))

    side = min(im.width, im.height)
    left = (im.width - side) // 2
    top = (im.height - side) // 2
    return im.crop((left, top, left + side, top + side))


def fit_crop(
    im: Image.Image,
    crop_box,
    target_size: tuple[int, int],
    source_eyes: list[list[float]] | None = None,
) -> tuple[Image.Image, list[tuple[int, int]]]:
    """
    Crop around `crop_box` while preserving `target_size`'s exact aspect ratio
    (no face squashing), resize with LANCZOS, and project `source_eyes` into
    output pixel coordinates.
    """
    tw, th = target_size
    target_aspect = tw / max(1, th)

    if crop_box and len(crop_box) == 4:
        x1, y1, x2, y2 = [float(v) for v in crop_box]
    else:
        x1, y1, x2, y2 = 0.0, 0.0, float(im.width), float(im.height)

    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    cw = max(2.0, x2 - x1)
    ch = max(2.0, y2 - y1)

    if cw / ch > target_aspect:
        # Box is wider than target -> expand height or trim width to match aspect
        new_w = ch * target_aspect
        new_h = ch
    else:
        new_w = cw
        new_h = cw / target_aspect

    # Clamp to image bounds while preserving aspect ratio
    scale_limit = min(im.width / new_w, im.height / new_h, 1.0)
    new_w *= scale_limit
    new_h *= scale_limit

    rx1 = max(0.0, min(im.width - new_w, cx - new_w / 2.0))
    ry1 = max(0.0, min(im.height - new_h, cy - new_h / 2.0))
    rx2 = rx1 + new_w
    ry2 = ry1 + new_h

    cropped = im.crop((int(round(rx1)), int(round(ry1)), int(round(rx2)), int(round(ry2))))
    resized = cropped.resize((tw, th), Image.Resampling.LANCZOS)

    projected_eyes: list[tuple[int, int]] = []
    if source_eyes:
        sx = tw / max(1.0, (rx2 - rx1))
        sy = th / max(1.0, (ry2 - ry1))
        for ex, ey in source_eyes:
            px = int(round((float(ex) - rx1) * sx))
            py = int(round((float(ey) - ry1) * sy))
            if 0 <= px < tw and 0 <= py < th:
                projected_eyes.append((px, py))

    return resized, projected_eyes


def make_feathered_mask(w: int, h: int, feather: int = 25) -> Image.Image:
    """Create a smooth elliptical alpha mask using continuous radial distance (zero banding)."""
    y, x = np.ogrid[:h, :w]
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    rx = max(1.0, w / 2.0)
    ry = max(1.0, h / 2.0)
    dist = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)

    feather_frac = np.clip(feather / max(1.0, min(rx, ry)), 0.08, 0.75)
    inner = 1.0 - feather_frac
    t = np.clip((dist - inner) / max(1e-5, feather_frac), 0.0, 1.0)
    # Smoothstep falloff
    alpha = 1.0 - (t * t * (3.0 - 2.0 * t))
    return Image.fromarray((alpha * 255.0).astype(np.uint8), mode="L")


def extract_portrait_alpha(img: Image.Image) -> Image.Image:
    """
    Ensure an AI portrait has a clean feathered alpha channel.
    - If it already has transparency, preserve it.
    - If it is isolated on a pure pitch-black background, smoothly key out
      the outer black void while keeping dark hair/clothing inside the silhouette opaque.
    """
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba, dtype=np.float32)
    existing_alpha = arr[:, :, 3]
    if existing_alpha.min() < 245:
        return rgba

    h, w = arr.shape[:2]
    # Luminance map (0..255)
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

    # Radial distance from upper-center (where head/shoulders live)
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    nx = (xx - w * 0.50) / (w * 0.44)
    ny = (yy - h * 0.48) / (h * 0.48)
    r = np.sqrt(nx * nx + ny * ny)

    # Outer black void keying: pixels that are very dark AND outside core face region fade to 0
    lum_alpha = np.clip((lum - 8.0) / 26.0, 0.0, 1.0)
    core_protect = np.clip(1.0 - (r - 0.55) / 0.30, 0.0, 1.0)
    edge_fade = np.clip(1.0 - (r - 0.85) / 0.22, 0.0, 1.0)

    # Bottom edge soft fade so shoulders dissolve naturally into the dark office
    bottom_fade = np.clip((h - yy) / max(1.0, h * 0.16), 0.0, 1.0)

    combined = np.maximum(lum_alpha, core_protect * 0.92) * edge_fade * bottom_fade
    mask_im = Image.fromarray((np.clip(combined, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L")
    mask_im = mask_im.filter(ImageFilter.GaussianBlur(radius=max(2, min(w, h) // 70)))

    out = rgba.copy()
    out.putalpha(mask_im)
    return out


def apply_smooth_vignette(
    img: Image.Image,
    strength: float = 0.72,
    inner_radius: float = 0.48,
    power: float = 2.0,
) -> Image.Image:
    """Apply a continuous, band-free radial vignette while preserving alpha."""
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba, dtype=np.float32)
    h, w = arr.shape[:2]

    y, x = np.ogrid[:h, :w]
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    max_r = np.sqrt(cx * cx + cy * cy) + 1e-5
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max_r

    t = np.clip((dist - inner_radius) / max(1e-5, 1.0 - inner_radius), 0.0, 1.0)
    darkening = strength * (t ** power)
    factor = (1.0 - darkening)[:, :, None]

    arr[:, :, :3] = np.clip(arr[:, :, :3] * factor, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode="RGBA")


def apply_fnaf_filter(
    img: Image.Image,
    darkness: float = 0.55,
    contrast: float = 1.32,
    saturation: float = 0.80,
    tint: tuple[float, float, float] | None = None,
    vignette: bool = False,
    vignette_strength: float = 0.70,
    scanlines: bool = True,
    grain: float = 0.0,
) -> Image.Image:
    """Apply FNAF-style color grading, smooth vignette, subtle CRT scanlines, and optional grain."""
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")

    rgb = ImageEnhance.Color(rgb).enhance(saturation)
    rgb = ImageEnhance.Brightness(rgb).enhance(darkness)
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)

    arr = np.asarray(rgb, dtype=np.float32)
    if tint is not None:
        arr[:, :, 0] *= tint[0]
        arr[:, :, 1] *= tint[1]
        arr[:, :, 2] *= tint[2]

    if grain > 0.0:
        rng = np.random.default_rng(42)
        noise = rng.normal(0.0, grain * 255.0, size=(arr.shape[0], arr.shape[1], 1))
        arr += noise

    if scanlines:
        arr[::3, :, :] *= 0.87

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr, mode="RGB").convert("RGBA")
    out.putalpha(alpha)

    if vignette:
        out = apply_smooth_vignette(out, strength=vignette_strength, inner_radius=0.45, power=2.0)

    return out


def add_glowing_eyes(
    img: Image.Image,
    eye_positions,
    radius: int = 4,
    glow_color=(235, 245, 255),
    darken_sclera: bool = True,
) -> Image.Image:
    """Render realistic FNAF horror eye glow (subtle dark eye socket + Gaussian bloom pinpoint)."""
    if not eye_positions:
        return img
    im = img.copy().convert("RGBA")

    if darken_sclera:
        dark_layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ddraw = ImageDraw.Draw(dark_layer)
        sr = max(4, int(radius * 2.4))
        for ex, ey in eye_positions:
            ddraw.ellipse([ex - sr, ey - int(sr * 0.7), ex + sr, ey + int(sr * 0.7)], fill=(0, 0, 0, 175))
        dark_layer = dark_layer.filter(ImageFilter.GaussianBlur(radius=max(2, radius)))
        im = Image.alpha_composite(im, dark_layer)

    halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(halo)
    hr = max(2, int(radius * 1.6))
    for ex, ey in eye_positions:
        hdraw.ellipse(
            [ex - hr, ey - hr, ex + hr, ey + hr],
            fill=(glow_color[0], glow_color[1], glow_color[2], 165),
        )
    halo = halo.filter(ImageFilter.GaussianBlur(radius=max(2, radius * 1.8)))
    im = Image.alpha_composite(im, halo)

    core = Image.new("RGBA", im.size, (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(core)
    cr = max(1, int(radius * 0.65))
    for ex, ey in eye_positions:
        cdraw.ellipse([ex - cr, ey - cr, ex + cr, ey + cr], fill=(255, 255, 255, 235))
    core = core.filter(ImageFilter.GaussianBlur(radius=0.8))

    return Image.alpha_composite(im, core)


def create_chromatic_aberration(img: Image.Image, offset: int = 5) -> Image.Image:
    """Shift R and B channels horizontally with edge-clamping (no black border artifacts)."""
    if offset <= 0:
        return img
    arr = np.asarray(img.convert("RGBA"), dtype=np.uint8)
    h, w = arr.shape[:2]
    o = min(int(offset), max(1, w // 4))

    r_pad = np.pad(arr[:, :, 0], ((0, 0), (o, o)), mode="edge")
    b_pad = np.pad(arr[:, :, 2], ((0, 0), (o, o)), mode="edge")

    out = arr.copy()
    out[:, :, 0] = r_pad[:, :w]          # shift right
    out[:, :, 2] = b_pad[:, 2 * o:2 * o + w]  # shift left
    return Image.fromarray(out, mode="RGBA")


def save_image(img: Image.Image, dest: Path, fmt: str = "WEBP", quality: int = 90) -> None:
    """Save an image ensuring parent directory exists."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if fmt.upper() == "PNG":
        img.save(dest, "PNG")
    else:
        img.convert("RGB").save(dest, "WEBP", quality=quality)


def build_base_door_lights(office_base: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Generate soft volumetric empty left/right door light beam frames from the office base."""
    w, h = office_base.size

    def make_soft_beam(poly, cx_frac: float):
        beam = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(beam).polygon(poly, fill=(255, 240, 200, 62))
        beam = beam.filter(ImageFilter.GaussianBlur(radius=28))

        # Modulate beam with vertical falloff (brighter near top fixture, softer near floor)
        arr = np.asarray(beam, dtype=np.float32)
        yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
        v_grad = np.clip(1.15 - 0.65 * yy, 0.25, 1.0)
        xx = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
        h_grad = np.exp(-((xx - cx_frac) / 0.14) ** 2)
        arr[:, :, 3] = np.clip(arr[:, :, 3] * v_grad * (0.45 + 0.55 * h_grad), 0, 255)
        soft_beam = Image.fromarray(arr.astype(np.uint8), mode="RGBA")
        return Image.alpha_composite(office_base.copy(), soft_beam)

    clean_left = make_soft_beam([(45, 70), (275, 115), (305, 610), (20, 610)], cx_frac=0.10)
    clean_right = make_soft_beam([(1325, 115), (1555, 70), (1580, 610), (1295, 610)], cx_frac=0.90)

    save_image(clean_left, GRAPHICS_DIR / "rooms/office/0_lightleft.webp", quality=90)
    save_image(clean_left, GRAPHICS_DIR / "rooms/office/2_lightleft.webp", quality=90)
    save_image(clean_right, GRAPHICS_DIR / "rooms/office/0_lightright.webp", quality=90)
    save_image(clean_right, GRAPHICS_DIR / "rooms/office/1_lightright.webp", quality=90)
    return clean_left, clean_right


def _jumpscare_frame_transform(mode: str, prog: float, idx: int) -> dict:
    """Compute per-frame position, scale, brightness, and dimming parameters for a jumpscare mode."""
    shake_x = int(random.uniform(-1, 1) * 28 * prog)
    shake_y = int(random.uniform(-1, 1) * 24 * prog)
    strobe = 0.82 + 0.28 * prog if idx % 2 == 0 else 0.55 + 0.22 * prog

    modes = {
        "center_office": {
            "scale": 0.48 + 0.82 * (prog ** 1.25),
            "px": lambda w: (OFFICE_SIZE[0] - w) // 2 + shake_x,
            "py": lambda h: (OFFICE_SIZE[1] - h) // 2 + int(110 * (1.0 - prog)) + shake_y,
            "dim": int(185 * prog),
            "darkness": strobe,
        },
        "lunge_left": {
            "scale": 0.46 + 0.84 * (prog ** 1.25),
            "px": lambda w: int(180 + ((OFFICE_SIZE[0] - w) // 2 - 180) * prog) + shake_x,
            "py": lambda h: (OFFICE_SIZE[1] - h) // 2 + int(110 * (1.0 - prog)) + shake_y,
            "dim": int(120 * prog),
            "darkness": strobe,
        },
        "lunge_right": {
            "scale": 0.46 + 0.84 * (prog ** 1.25),
            "px": lambda w: int((OFFICE_SIZE[0] - w - 180) * (1.0 - prog) + ((OFFICE_SIZE[0] - w) // 2) * prog) + shake_x,
            "py": lambda h: (OFFICE_SIZE[1] - h) // 2 + int(110 * (1.0 - prog)) + shake_y,
            "dim": int(120 * prog),
            "darkness": strobe,
        },
        "lunge_left_doorway": {
            "scale": 0.42 + 0.88 * (prog ** 1.1),
            "px": lambda w: int(60 + ((OFFICE_SIZE[0] - w) // 2 - 60) * prog) + shake_x,
            "py": lambda h: (OFFICE_SIZE[1] - h) // 2 + int(80 * (1.0 - prog)) + shake_y,
            "dim": int(110 * prog),
            "darkness": 0.85 + 0.25 * (idx % 2),
        },
    }
    return modes.get(mode, modes["center_office"])


def render_jumpscare_sequence(
    face_src: Image.Image,
    office_base: Image.Image,
    out_dir: Path,
    legacy_dir: Path | None,
    frame_count: int,
    mode: str,
    use_native_alpha: bool = False,
) -> list[str]:
    """Generate a sharp, cinematic jumpscare animation sequence and return relative frame paths."""
    rng_state = random.getstate()
    random.seed(f"{out_dir.name}:{mode}")
    frame_paths = []

    # Normalize base face height to ~720px so scale=1.0 fills screen cleanly regardless of input resolution
    base_h = 720
    base_w = max(1, int(round(face_src.width * (base_h / max(1, face_src.height)))))
    norm_face = face_src.resize((base_w, base_h), Image.Resampling.LANCZOS)

    try:
        for i in range(frame_count):
            prog = i / max(1, frame_count - 1)
            params = _jumpscare_frame_transform(mode, prog, i)
            scale = params["scale"]
            fw = max(1, int(norm_face.width * scale))
            fh = max(1, int(norm_face.height * scale))
            rf = norm_face.resize((fw, fh), Image.Resampling.LANCZOS)

            rf_filt = apply_fnaf_filter(
                rf,
                darkness=params["darkness"],
                contrast=1.35 + 0.22 * prog,
                saturation=0.85,
                vignette=False,
                scanlines=True,
                grain=0.025,
            )

            if use_native_alpha:
                mask = rf_filt.getchannel("A")
            else:
                mask = make_feathered_mask(fw, fh, feather=int(min(fw, fh) * 0.22))

            frame = office_base.copy()
            if params["dim"] > 0:
                frame = Image.alpha_composite(
                    frame, Image.new("RGBA", frame.size, (0, 0, 0, params["dim"]))
                )

            frame.paste(rf_filt, (params["px"](fw), params["py"](fh)), mask)

            # Subtle motion blur & chromatic aberration intensify toward impact
            if prog > 0.72 and i % 2 == 1:
                frame = frame.filter(ImageFilter.GaussianBlur(radius=0.8))
            frame = create_chromatic_aberration(frame, offset=int(2 + 6 * prog))

            out_file = out_dir / f"{i}.webp"
            save_image(frame, out_file, quality=88)
            if legacy_dir is not None:
                save_image(frame, legacy_dir / f"{i}.webp", quality=88)

            frame_paths.append(str(out_file.relative_to(ROOT_DIR)).replace(os.sep, "/"))
    finally:
        random.setstate(rng_state)
    return frame_paths


def render_hallway_run(
    runner_src: Image.Image,
    hall_bg_path: Path,
    out_dir: Path,
    frame_count: int = 31,
    use_native_alpha: bool = False,
) -> None:
    """Generate Foxy/Horacio sprinting down West Hall (CAM 2A) across 31 CCTV frames."""
    if not hall_bg_path.exists():
        return
    with Image.open(hall_bg_path) as hb:
        hall_base = hb.convert("RGBA").resize(OFFICE_SIZE, Image.Resampling.LANCZOS)

    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(frame_count):
        prog = i / max(1, frame_count - 1)
        # Perspective growth from far hallway to charging close-up
        ease = prog ** 1.45
        h_size = int(110 + 490 * ease)
        w_size = max(1, int(round(h_size * (runner_src.width / max(1, runner_src.height)))))
        sprite = runner_src.resize((w_size, h_size), Image.Resampling.LANCZOS)
        sprite = apply_fnaf_filter(
            sprite,
            darkness=0.45 + 0.35 * ease,
            contrast=1.35 + 0.20 * ease,
            saturation=0.72,
            tint=(0.90, 0.98, 1.04),
            vignette=False,
            scanlines=True,
            grain=0.03,
        )

        # Running bob + slight horizontal charge toward left-center
        bob = int(np.sin(i * 1.45) * (8 + 22 * ease))
        cx = int(OFFICE_SIZE[0] * (0.48 - 0.14 * ease))
        cy = int(OFFICE_SIZE[1] * (0.42 + 0.14 * ease)) + bob
        px = cx - w_size // 2
        py = cy - h_size // 2

        mask = sprite.getchannel("A") if use_native_alpha else make_feathered_mask(
            w_size, h_size, feather=max(12, int(min(w_size, h_size) * 0.24))
        )

        frame = hall_base.copy()
        frame.paste(sprite, (px, py), mask)
        if ease > 0.35:
            frame = frame.filter(ImageFilter.GaussianBlur(radius=0.6 + 1.4 * ease))
        frame = create_chromatic_aberration(frame, offset=int(1 + 5 * ease))
        save_image(frame, out_dir / f"{i}.webp", quality=85)


def build_character(
    char_dir: Path,
    office_base: Image.Image,
    clean_left: Image.Image,
    clean_right: Image.Image,
    dry_run: bool = False,
) -> dict:
    """Process one character folder and return its runtime config entry."""
    cfg_path = char_dir / "character.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    char_id = cfg["id"]
    pipe = cfg.get("pipeline", {})
    src_name = pipe.get("sourceImage", "source.jpeg")
    src_path = char_dir / src_name
    if not src_path.exists():
        raise FileNotFoundError(f"Missing source image for character '{char_id}': {src_path}")

    out_char_dir = GRAPHICS_DIR / "characters" / char_id
    icon_rel = f"graphics/characters/{char_id}/icon.png"
    jumpscare_frames_count = int(pipe.get("jumpscareFrames", 20))

    runtime_assets = {
        "icon": icon_rel,
        "nameBanner": pipe.get("nameBanner"),
        "jumpscareFrames": [
            f"graphics/characters/{char_id}/jumpscare/{i}.webp"
            for i in range(jumpscare_frames_count)
        ],
        "jumpscareFrameMs": int(pipe.get("jumpscareFrameMs", 45)),
        "jumpscareSound": cfg.get("sounds", {}).get("jumpscare", "XSCREAM.wav"),
    }

    door_light_cfg = pipe.get("doorLight")
    if door_light_cfg and door_light_cfg.get("enabled"):
        runtime_assets["doorLightFrame"] = f"graphics/characters/{char_id}/door_light.webp"

    room_overlays_cfg = cfg.get("roomOverlays", {})
    generated_room_overlays = {}
    for room_id in room_overlays_cfg:
        generated_room_overlays[room_id] = f"graphics/characters/{char_id}/room_{room_id}.webp"
    if generated_room_overlays:
        runtime_assets["roomOverlays"] = generated_room_overlays

    if dry_run:
        return _build_runtime_entry(cfg, runtime_assets)

    src_im = load_and_fix_orientation(src_path)
    source_eyes = pipe.get("sourceEyes")

    # Check for AI-generated clean portrait / cutout
    ai_portrait_path = _find_first_existing(char_dir, ["cutout", "ai_portrait"])
    ai_portrait_im = load_and_fix_orientation(ai_portrait_path) if ai_portrait_path else None

    # 1. Custom Night icon (200x200, crisp & zero banding)
    if ai_portrait_im is not None:
        head_icon = ImageOps.fit(ai_portrait_im, ICON_SIZE, method=Image.Resampling.LANCZOS)
        head_icon = apply_fnaf_filter(
            head_icon,
            darkness=0.92,
            contrast=1.15,
            saturation=0.92,
            vignette=True,
            vignette_strength=0.45,
            scanlines=False,
        )
    else:
        head_icon, _ = fit_crop(src_im, pipe.get("iconCrop"), ICON_SIZE)
        head_icon = apply_fnaf_filter(
            head_icon,
            darkness=0.76,
            contrast=1.28,
            saturation=0.82,
            vignette=True,
            vignette_strength=0.58,
            scanlines=False,
        )
    save_image(head_icon.convert("RGB"), ROOT_DIR / icon_rel, fmt="PNG")
    if pipe.get("legacyIconPath"):
        save_image(head_icon.convert("RGB"), ROOT_DIR / pipe["legacyIconPath"], fmt="PNG")

    # 2. Jumpscare frames
    ai_js_path = _find_first_existing(char_dir, ["ai_jumpscare_portrait", "cutout", "ai_portrait"])
    if ai_js_path is not None:
        js_face = extract_portrait_alpha(load_and_fix_orientation(ai_js_path))
        use_native_alpha = True
    else:
        js_src_path = char_dir / pipe.get("jumpscareSourceImage", src_name)
        js_src = load_and_fix_orientation(js_src_path) if js_src_path.exists() else src_im
        js_face = crop_or_center_square(js_src, pipe.get("jumpscareCrop"))
        use_native_alpha = False

    legacy_js_dir = ROOT_DIR / pipe["legacyJumpscareDir"] if pipe.get("legacyJumpscareDir") else None
    render_jumpscare_sequence(
        face_src=js_face,
        office_base=office_base,
        out_dir=out_char_dir / "jumpscare",
        legacy_dir=legacy_js_dir,
        frame_count=jumpscare_frames_count,
        mode=pipe.get("jumpscareMode", "center_office"),
        use_native_alpha=use_native_alpha,
    )

    # 3. Door light frame (AI override preferred; clean fallback otherwise)
    if door_light_cfg and door_light_cfg.get("enabled"):
        ai_door_path = _find_first_existing(char_dir, ["ai_door_light"])
        if ai_door_path is not None:
            composited = load_and_fix_orientation(ai_door_path).resize(
                OFFICE_SIZE, Image.Resampling.LANCZOS
            )
        else:
            cw, ch = door_light_cfg.get("size", [230, 300])
            px, py = door_light_cfg.get("position", [95, 160])
            dl_face, proj_eyes = fit_crop(src_im, door_light_cfg.get("crop"), (cw, ch), source_eyes)
            dl_face = apply_fnaf_filter(
                dl_face,
                darkness=0.72,
                contrast=1.30,
                saturation=0.78,
                tint=(1.04, 0.99, 0.90),
                vignette=False,
                scanlines=True,
                grain=0.02,
            )
            eyes_to_use = proj_eyes if proj_eyes else door_light_cfg.get("eyes", [])
            if door_light_cfg.get("glowingEyes", False) and eyes_to_use:
                dl_face = add_glowing_eyes(dl_face, eyes_to_use, radius=3)
            dl_mask = make_feathered_mask(cw, ch, feather=30)
            base_light = clean_left if door_light_cfg.get("side") == "left" else clean_right
            composited = base_light.copy()
            composited.paste(dl_face, (px, py), dl_mask)

        save_image(composited, ROOT_DIR / runtime_assets["doorLightFrame"], quality=90)
        if door_light_cfg.get("legacyPath"):
            save_image(composited, ROOT_DIR / door_light_cfg["legacyPath"], quality=90)

    # 4. Stage overlay (CAM 1A)
    stage_cfg = pipe.get("stageOverlay")
    stage_base_path = BASE_GRAPHICS_DIR / "rooms/1a/1.webp"
    if stage_cfg and stage_cfg.get("enabled"):
        ai_stage_path = _find_first_existing(char_dir, ["ai_stage"])
        if ai_stage_path is not None:
            stage_out = load_and_fix_orientation(ai_stage_path).resize(
                OFFICE_SIZE, Image.Resampling.LANCZOS
            )
            save_image(stage_out, GRAPHICS_DIR / "rooms/1a/1.webp", quality=90)
            has_stage_all = AI_STAGE_DIR.exists() and _find_first_existing(AI_STAGE_DIR, ["stage_all"]) is not None
            if not has_stage_all:
                save_image(stage_out, GRAPHICS_DIR / "rooms/1a/0.webp", quality=90)
        elif stage_base_path.exists():
            with Image.open(stage_base_path) as st_im:
                stage_bg = st_im.convert("RGBA")
            sw, sh = stage_cfg.get("size", [360, 420])
            sx, sy = stage_cfg.get("position", [630, 140])
            ez, proj_eyes = fit_crop(src_im, stage_cfg.get("crop"), (sw, sh), source_eyes)
            ez = apply_fnaf_filter(
                ez,
                darkness=0.45,
                contrast=1.38,
                saturation=0.72,
                tint=(0.90, 0.98, 1.02),
                vignette=False,
                scanlines=True,
                grain=0.025,
            )
            eyes_to_use = proj_eyes if proj_eyes else stage_cfg.get("eyes", [])
            if stage_cfg.get("glowingEyes", False) and eyes_to_use:
                ez = add_glowing_eyes(ez, eyes_to_use, radius=4)
            stage_bg.paste(ez, (sx, sy), make_feathered_mask(sw, sh, feather=40))
            save_image(stage_bg, GRAPHICS_DIR / "rooms/1a/0.webp", quality=90)

    # 5. Power outage face
    po_cfg = pipe.get("powerout")
    if po_cfg and po_cfg.get("enabled"):
        ai_po0 = _find_first_existing(char_dir, ["ai_powerout_0"])
        ai_po1 = _find_first_existing(char_dir, ["ai_powerout_1"])
        if ai_po0 is not None and ai_po1 is not None:
            for idx, po_path in enumerate([ai_po0, ai_po1]):
                po_img = load_and_fix_orientation(po_path).resize(
                    OFFICE_SIZE, Image.Resampling.LANCZOS
                )
                save_image(po_img, GRAPHICS_DIR / f"rooms/office/powerout{idx}.webp", quality=90)
        else:
            pw, ph = po_cfg.get("size", [300, 320])
            px, py = po_cfg.get("position", [130, 170])
            face, proj_eyes = fit_crop(src_im, po_cfg.get("crop"), (pw, ph), source_eyes)
            mask = make_feathered_mask(pw, ph, feather=35)
            eyes_to_use = proj_eyes if proj_eyes else po_cfg.get("eyes", [])
            for idx, (dark, rad) in enumerate([(0.07, 3), (0.28, 4)]):
                out = Image.new("RGBA", OFFICE_SIZE, (0, 0, 0, 255))
                ff = apply_fnaf_filter(
                    face,
                    darkness=dark,
                    contrast=2.0,
                    saturation=0.55,
                    tint=(0.86, 0.94, 1.08),
                    vignette=True,
                    vignette_strength=0.65,
                )
                ff = add_glowing_eyes(ff, eyes_to_use, radius=rad)
                out.paste(ff, (px, py), mask)
                save_image(out, GRAPHICS_DIR / f"rooms/office/powerout{idx}.webp", quality=90)

    # 5b. Pirate Cove stages (CAM 1C stages 1 & 2)
    if pipe.get("coveStages"):
        for stage_idx in (1, 2):
            ai_cove = _find_first_existing(char_dir, [f"ai_cove_{stage_idx}"])
            if ai_cove is not None:
                cove_out = load_and_fix_orientation(ai_cove).resize(
                    OFFICE_SIZE, Image.Resampling.LANCZOS
                )
                save_image(cove_out, GRAPHICS_DIR / f"rooms/1c/{stage_idx}.webp", quality=90)

    # 5c. Hallway sprint sequence (CAM 2A foxxy/0..30.webp)
    run_cfg = pipe.get("hallwayRun")
    if run_cfg and run_cfg.get("enabled"):
        run_out_dir = ROOT_DIR / run_cfg.get("outDir", "graphics/rooms/2a/foxxy")
        hall_bg = GRAPHICS_DIR / "rooms/2a/0.webp"
        render_hallway_run(
            runner_src=js_face,
            hall_bg_path=hall_bg,
            out_dir=run_out_dir,
            frame_count=int(run_cfg.get("frames", 31)),
            use_native_alpha=use_native_alpha,
        )

    # 6. Optional custom room overlays (AI room override or clean CCTV fallback)
    ai_rooms_dir = char_dir / "ai_rooms"
    for room_id, ov_cfg in room_overlays_cfg.items():
        ai_room_path = _find_first_existing(ai_rooms_dir, [room_id]) if ai_rooms_dir.exists() else None
        if ai_room_path is not None:
            room_out = load_and_fix_orientation(ai_room_path).resize(
                OFFICE_SIZE, Image.Resampling.LANCZOS
            )
            save_image(room_out, ROOT_DIR / generated_room_overlays[room_id], quality=88)
            continue

        empty_room_path = GRAPHICS_DIR / "rooms" / room_id / "0.webp"
        if not empty_room_path.exists():
            continue
        with Image.open(empty_room_path) as rm_im:
            room_bg = rm_im.convert("RGBA")
        rw, rh = ov_cfg.get("size", [260, 300])
        rx, ry = ov_cfg.get("position", [(room_bg.width - rw) // 2, (room_bg.height - rh) // 2])
        if ai_portrait_im is not None:
            ov_rgba = extract_portrait_alpha(
                ImageOps.fit(ai_portrait_im, (rw, rh), method=Image.Resampling.LANCZOS)
            )
            ov_face = apply_fnaf_filter(
                ov_rgba,
                darkness=float(ov_cfg.get("darkness", 0.52)),
                contrast=1.28,
                saturation=0.68,
                tint=(0.90, 0.98, 1.04),
                vignette=False,
                scanlines=True,
                grain=0.025,
            )
            room_bg.paste(ov_face, (rx, ry), ov_face.getchannel("A"))
        else:
            ov_face, proj_eyes = fit_crop(src_im, ov_cfg.get("crop"), (rw, rh), source_eyes)
            ov_face = apply_fnaf_filter(
                ov_face,
                darkness=float(ov_cfg.get("darkness", 0.5)),
                contrast=1.35,
                saturation=0.70,
                tint=(0.90, 0.98, 1.04),
                vignette=False,
                scanlines=True,
                grain=0.025,
            )
            eyes_to_use = proj_eyes if proj_eyes else ov_cfg.get("eyes", [])
            if ov_cfg.get("glowingEyes", False) and eyes_to_use:
                ov_face = add_glowing_eyes(ov_face, eyes_to_use, radius=3)
            room_bg.paste(ov_face, (rx, ry), make_feathered_mask(rw, rh, feather=28))
        save_image(room_bg, ROOT_DIR / generated_room_overlays[room_id], quality=88)

    return _build_runtime_entry(cfg, runtime_assets)


def _build_runtime_entry(cfg: dict, runtime_assets: dict) -> dict:
    """Build normalized character schema entry consumed by the JS engine."""
    return {
        "id": cfg["id"],
        "displayName": cfg.get("displayName", cfg["id"].title()),
        "customNightOrder": cfg.get("customNightOrder", 99),
        "strategy": cfg.get("strategy", "roamer"),
        "side": cfg.get("side", "left"),
        "startRoom": cfg.get("startRoom", "1a"),
        "movementIntervalSec": cfg.get("movementIntervalSec", 4.97),
        "doorWaitChecks": cfg.get("doorWaitChecks", 2),
        "route": cfg.get("route", []),
        "retreatRoom": cfg.get("retreatRoom", "1b"),
        "roomStates": cfg.get("roomStates", {}),
        "sounds": cfg.get("sounds", {}),
        "nightLevels": cfg.get("nightLevels", {}),
        "hourlyBoost": cfg.get("hourlyBoost", {}),
        "assets": runtime_assets,
    }


def _load_source_eyes(char_name: str, key: str = "sourceEyes") -> list[list[float]] | None:
    cfg_path = CHARACTERS_SRC_DIR / char_name / "character.json"
    if not cfg_path.exists():
        return None
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("pipeline", {}).get(key)


def build_shared_branding(dry_run: bool = False) -> None:
    """Build shared menu/logo/gameover screens (preferring AI branding when present)."""
    if dry_run:
        return

    # Main Menu frames 0..3
    for idx in range(4):
        ai_mm = _find_first_existing(AI_BRANDING_DIR, [f"mainmenu_{idx}"]) if AI_BRANDING_DIR.exists() else None
        if ai_mm is not None:
            mm_img = ImageOps.fit(load_and_fix_orientation(ai_mm), MENU_SIZE, method=Image.Resampling.LANCZOS)
            save_image(mm_img, GRAPHICS_DIR / f"mainmenu/{idx}.webp", quality=90)

    # Fallback for any missing mainmenu frames using aspect-safe fit_crop + projected eyes
    freddy_src = CHARACTERS_SRC_DIR / "freddy" / "source.jpeg"
    freddy_intense = CHARACTERS_SRC_DIR / "freddy" / "source_intense.jpeg"
    bonnie_src = CHARACTERS_SRC_DIR / "bonnie" / "source.jpeg"
    foxy_src = CHARACTERS_SRC_DIR / "foxy" / "source.jpeg"

    if freddy_src.exists() and bonnie_src.exists() and freddy_intense.exists():
        if not _find_first_existing(AI_BRANDING_DIR, ["mainmenu_0"]) or not _find_first_existing(AI_BRANDING_DIR, ["mainmenu_1"]):
            im_p2 = load_and_fix_orientation(freddy_src)
            p2_crop, p2_eyes = fit_crop(im_p2, [200, 450, 1400, 1300], MENU_SIZE, _load_source_eyes("freddy"))
            if not _find_first_existing(AI_BRANDING_DIR, ["mainmenu_0"]):
                f0 = apply_fnaf_filter(p2_crop, darkness=0.42, contrast=1.40, vignette=True, grain=0.02)
                save_image(f0, GRAPHICS_DIR / "mainmenu/0.webp", quality=90)
            if not _find_first_existing(AI_BRANDING_DIR, ["mainmenu_1"]):
                f1 = apply_fnaf_filter(p2_crop, darkness=0.48, contrast=1.55, vignette=True, grain=0.025)
                f1 = add_glowing_eyes(f1, p2_eyes, radius=4)
                f1 = create_chromatic_aberration(f1, offset=5)
                save_image(f1, GRAPHICS_DIR / "mainmenu/1.webp", quality=90)

        if not _find_first_existing(AI_BRANDING_DIR, ["mainmenu_2"]):
            im_p1 = load_and_fix_orientation(bonnie_src)
            p1_crop, p1_eyes = fit_crop(im_p1, [100, 0, 1200, 950], MENU_SIZE, _load_source_eyes("bonnie"))
            f2 = apply_fnaf_filter(p1_crop, darkness=0.44, contrast=1.45, vignette=True, grain=0.025)
            f2 = add_glowing_eyes(f2, p1_eyes, radius=4, glow_color=(255, 80, 80))
            region = f2.crop((0, 280, MENU_SIZE[0], 345))
            f2.paste(region, (18, 280))
            save_image(f2, GRAPHICS_DIR / "mainmenu/2.webp", quality=90)

        if not _find_first_existing(AI_BRANDING_DIR, ["mainmenu_3"]):
            im_p3 = load_and_fix_orientation(freddy_intense)
            p3_crop, p3_eyes = fit_crop(
                im_p3, [50, 400, 1030, 1250], MENU_SIZE, _load_source_eyes("freddy", "jumpscareSourceEyes")
            )
            f3 = apply_fnaf_filter(p3_crop, darkness=0.58, contrast=1.65, vignette=True, grain=0.03)
            f3 = add_glowing_eyes(f3, p3_eyes, radius=5)
            f3 = create_chromatic_aberration(f3, offset=7)
            save_image(f3, GRAPHICS_DIR / "mainmenu/3.webp", quality=90)

    # Game Over screen
    ai_go = _find_first_existing(AI_BRANDING_DIR, ["gameover"]) if AI_BRANDING_DIR.exists() else None
    if ai_go is not None:
        go_img = ImageOps.fit(load_and_fix_orientation(ai_go), MENU_SIZE, method=Image.Resampling.LANCZOS)
        save_image(go_img, GRAPHICS_DIR / "gameover/gameoverimg.webp", quality=88)
    elif foxy_src.exists():
        im_p5 = load_and_fix_orientation(foxy_src)
        bg, _ = fit_crop(im_p5, [80, 750, 700, 1300], MENU_SIZE)
        bg = apply_fnaf_filter(bg, darkness=0.30, contrast=1.70, vignette=True, scanlines=True, grain=0.035)
        bg = create_chromatic_aberration(bg, offset=6)
        save_image(bg, GRAPHICS_DIR / "gameover/gameoverimg.webp", quality=85)


def build_stage_variants(dry_run: bool = False) -> None:
    """Build combined Show Stage (CAM 1A) character presence variants."""
    if dry_run or not AI_STAGE_DIR.exists():
        return
    mapping = {
        "stage_all": "rooms/1a/0.webp",
        "stage_freddy_chica": "rooms/1a/2.webp",
        "stage_freddy_bonnie": "rooms/1a/3.webp",
    }
    for stem, rel_out in mapping.items():
        src_path = _find_first_existing(AI_STAGE_DIR, [stem])
        if src_path is not None:
            out_img = load_and_fix_orientation(src_path).resize(
                OFFICE_SIZE, Image.Resampling.LANCZOS
            )
            save_image(out_img, GRAPHICS_DIR / rel_out, quality=90)
            print(f"[OK] Show Stage variant '{stem}' -> graphics/{rel_out}")


def main():
    parser = argparse.ArgumentParser(description="Build FNAE character assets and manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print plan without writing images.")
    args = parser.parse_args()

    office_base_path = BASE_GRAPHICS_DIR / "rooms/office/0.webp"
    if not office_base_path.exists():
        office_base_path = GRAPHICS_DIR / "rooms/office/0.webp"
        if office_base_path.exists() and not args.dry_run:
            (BASE_GRAPHICS_DIR / "rooms/office").mkdir(parents=True, exist_ok=True)
            shutil.copy2(office_base_path, BASE_GRAPHICS_DIR / "rooms/office/0.webp")

    office_base = load_and_fix_orientation(office_base_path)
    if args.dry_run:
        clean_left = office_base
        clean_right = office_base
    else:
        clean_left, clean_right = build_base_door_lights(office_base)

    character_dirs = sorted(
        p for p in CHARACTERS_SRC_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "character.json").exists()
    )

    manifest = []
    for cdir in character_dirs:
        entry = build_character(cdir, office_base, clean_left, clean_right, dry_run=args.dry_run)
        manifest.append(entry)
        print(f"[{'DRY' if args.dry_run else 'OK'}] Character '{entry['id']}' ({entry['strategy']})")

    manifest.sort(key=lambda c: c.get("customNightOrder", 99))
    build_shared_branding(dry_run=args.dry_run)
    build_stage_variants(dry_run=args.dry_run)

    if not args.dry_run:
        CONFIG_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_OUT_PATH, "w", encoding="utf-8") as f:
            json.dump({"characters": manifest}, f, indent=2, ensure_ascii=False)
        print(f"[OK] Wrote {CONFIG_OUT_PATH} ({len(manifest)} characters)")


if __name__ == "__main__":
    main()
