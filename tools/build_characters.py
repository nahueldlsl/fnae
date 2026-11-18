"""
Dynamic character & asset build pipeline for Five Nights at Ezequiel's (FNAE).

Reads character manifests from `assets_src/characters/*/character.json`
(ignoring `_template`), generates runtime graphics under `graphics/characters/<id>/`
(plus legacy paths where configured), and writes `config/characters.json`.
"""

import argparse
import json
import math
import os
import random
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_SRC_DIR = ROOT_DIR / "assets_src"
CHARACTERS_SRC_DIR = ASSETS_SRC_DIR / "characters"
BASE_GRAPHICS_DIR = ASSETS_SRC_DIR / "base_graphics"
GRAPHICS_DIR = ROOT_DIR / "graphics"
CONFIG_OUT_PATH = ROOT_DIR / "config" / "characters.json"

OFFICE_SIZE = (1600, 720)
MENU_SIZE = (1280, 720)
ICON_SIZE = (200, 200)


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


def make_feathered_mask(w: int, h: int, feather: int = 25) -> Image.Image:
    """Create a smooth elliptical alpha mask with soft feathered edges."""
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    f = max(5, int(feather))
    draw.ellipse([f, f, max(f + 1, w - f), max(f + 1, h - f)], fill=255)
    return mask.filter(ImageFilter.GaussianBlur(max(1, f // 2)))


def apply_fnaf_filter(
    img: Image.Image,
    darkness: float = 0.45,
    contrast: float = 1.35,
    vignette: bool = False,
    scanlines: bool = True,
) -> Image.Image:
    """Apply FNAF-style darkness, contrast, CRT scanlines, and optional vignette."""
    im = ImageEnhance.Brightness(img.convert("RGBA")).enhance(darkness)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    w, h = im.size

    if vignette:
        vignette_mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(vignette_mask)
        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx ** 2 + cy ** 2)
        for r in range(int(max_dist), 0, -10):
            factor = r / max_dist
            alpha = int(255 * (1.0 - math.pow(1.0 - factor, 2.2)))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=min(255, alpha))
        black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        im.paste(black, (0, 0), vignette_mask)

    if scanlines:
        scan_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(scan_overlay)
        for y in range(0, h, 3):
            sdraw.line([(0, y), (w, y)], fill=(0, 0, 0, 35))
        im = Image.alpha_composite(im, scan_overlay)

    return im


def add_glowing_eyes(
    img: Image.Image,
    eye_positions,
    radius: int = 6,
    glow_color=(255, 255, 255),
) -> Image.Image:
    """Render soft concentric eye glow overlays at specified (x, y) coordinates."""
    if not eye_positions:
        return img
    im = img.copy().convert("RGBA")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for ex, ey in eye_positions:
        for r in range(radius * 3, radius, -2):
            alpha = int(55 * (1 - r / (radius * 3)))
            draw.ellipse(
                [ex - r, ey - r, ex + r, ey + r],
                fill=(glow_color[0], glow_color[1], glow_color[2], alpha),
            )
        draw.ellipse(
            [ex - radius, ey - radius, ex + radius, ey + radius],
            fill=(glow_color[0], glow_color[1], glow_color[2], 255),
        )
        draw.ellipse(
            [ex - radius // 2, ey - radius // 2, ex + radius // 2, ey + radius // 2],
            fill=(255, 255, 255, 255),
        )

    return Image.alpha_composite(im, overlay)


def create_chromatic_aberration(img: Image.Image, offset: int = 6) -> Image.Image:
    """Shift R and B channels horizontally for CRT chromatic aberration."""
    r, g, b, a = img.convert("RGBA").split()
    r_shifted = Image.new("L", r.size, 0)
    r_shifted.paste(r, (offset, 0))
    b_shifted = Image.new("L", b.size, 0)
    b_shifted.paste(b, (-offset, 0))
    return Image.merge("RGBA", (r_shifted, g, b_shifted, a))


def save_image(img: Image.Image, dest: Path, fmt: str = "WEBP", quality: int = 88) -> None:
    """Save an image ensuring parent directory exists."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if fmt.upper() == "PNG":
        img.save(dest, "PNG")
    else:
        img.convert("RGB").save(dest, "WEBP", quality=quality)


def build_base_door_lights(office_base: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Generate clean empty left/right door light beam frames from the office base."""
    w, h = office_base.size

    def make_beam(poly):
        beam = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(beam).polygon(poly, fill=(255, 245, 200, 40))
        return Image.alpha_composite(office_base.copy(), beam)

    clean_left = make_beam([(50, 110), (270, 110), (310, 560), (30, 560)])
    clean_right = make_beam([(1330, 110), (1550, 110), (1570, 560), (1290, 560)])

    save_image(clean_left, GRAPHICS_DIR / "rooms/office/0_lightleft.webp", quality=90)
    save_image(clean_left, GRAPHICS_DIR / "rooms/office/2_lightleft.webp", quality=90)
    save_image(clean_right, GRAPHICS_DIR / "rooms/office/0_lightright.webp", quality=90)
    save_image(clean_right, GRAPHICS_DIR / "rooms/office/1_lightright.webp", quality=90)
    return clean_left, clean_right


def _jumpscare_frame_transform(mode: str, prog: float, fw: int, fh: int, idx: int) -> dict:
    """Compute per-frame position, brightness, and dimming parameters for a jumpscare mode."""
    shake_x = int(random.uniform(-1, 1) * 32 * prog)
    shake_y = int(random.uniform(-1, 1) * 32 * prog)
    strobe = 0.55 + 0.35 * prog if idx % 2 == 0 else 0.35 + 0.3 * prog

    modes = {
        "center_office": {
            "scale": 0.6 + 1.4 * (prog ** 1.4),
            "px": lambda w: (OFFICE_SIZE[0] - w) // 2 + shake_x,
            "py": lambda h: (OFFICE_SIZE[1] - h) // 2 + int(160 * (1.0 - prog)) + shake_y,
            "dim": int(190 * prog),
            "darkness": strobe,
        },
        "lunge_left": {
            "scale": 0.6 + 1.35 * (prog ** 1.4),
            "px": lambda _w: 300 + int(200 * prog) + shake_x,
            "py": lambda h: (OFFICE_SIZE[1] - h) // 2 + int(180 * (1.0 - prog)) + shake_y,
            "dim": 0,
            "darkness": 0.6 + 0.35 * prog,
        },
        "lunge_right": {
            "scale": 0.6 + 1.4 * (prog ** 1.4),
            "px": lambda _w: 850 - int(150 * prog) + shake_x,
            "py": lambda h: (OFFICE_SIZE[1] - h) // 2 + int(180 * (1.0 - prog)) + shake_y,
            "dim": 0,
            "darkness": 0.6 + 0.35 * prog,
        },
        "lunge_left_doorway": {
            "scale": 0.8 + 1.2 * prog,
            "px": lambda _w: 80 + int(320 * prog) + shake_x,
            "py": lambda _h: 150 + int(40 * prog) + shake_y,
            "dim": 0,
            "darkness": 0.75 + 0.25 * (idx % 2),
        },
    }
    params = modes.get(mode, modes["center_office"])
    return params


def render_jumpscare_sequence(
    face_src: Image.Image,
    office_base: Image.Image,
    out_dir: Path,
    legacy_dir: Path | None,
    frame_count: int,
    mode: str,
) -> list[str]:
    """Generate a feathered jumpscare animation sequence and return relative frame paths."""
    rng_state = random.getstate()
    random.seed(f"{out_dir.name}:{mode}")
    frame_paths = []
    try:
        for i in range(frame_count):
            prog = i / max(1, frame_count - 1)
            params = _jumpscare_frame_transform(mode, prog, face_src.width, face_src.height, i)
            scale = params["scale"]
            fw = max(1, int(face_src.width * scale))
            fh = max(1, int(face_src.height * scale))
            rf = face_src.resize((fw, fh), Image.Resampling.BILINEAR)
            rf_filt = apply_fnaf_filter(
                rf,
                darkness=params["darkness"],
                contrast=1.5 + 0.2 * prog,
                vignette=False,
            )
            mask = make_feathered_mask(fw, fh, feather=int(min(fw, fh) * 0.18))

            frame = office_base.copy()
            if params["dim"] > 0:
                frame = Image.alpha_composite(
                    frame, Image.new("RGBA", frame.size, (0, 0, 0, params["dim"]))
                )

            frame.paste(rf_filt, (params["px"](fw), params["py"](fh)), mask)
            frame = create_chromatic_aberration(frame, offset=int(3 + 8 * prog))

            out_file = out_dir / f"{i}.webp"
            save_image(frame, out_file, quality=85)
            if legacy_dir is not None:
                save_image(frame, legacy_dir / f"{i}.webp", quality=85)

            frame_paths.append(str(out_file.relative_to(ROOT_DIR)).replace(os.sep, "/"))
    finally:
        random.setstate(rng_state)
    return frame_paths


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

    # 1. Custom Night icon
    head_icon = crop_or_center_square(src_im, pipe.get("iconCrop")).resize(
        ICON_SIZE, Image.Resampling.LANCZOS
    )
    head_icon = apply_fnaf_filter(head_icon, darkness=0.72, contrast=1.3, vignette=True, scanlines=False)
    save_image(head_icon.convert("RGB"), ROOT_DIR / icon_rel, fmt="PNG")
    if pipe.get("legacyIconPath"):
        save_image(head_icon.convert("RGB"), ROOT_DIR / pipe["legacyIconPath"], fmt="PNG")

    # 2. Jumpscare frames
    js_src_path = char_dir / pipe.get("jumpscareSourceImage", src_name)
    js_src = load_and_fix_orientation(js_src_path) if js_src_path.exists() else src_im
    js_face = crop_or_center_square(js_src, pipe.get("jumpscareCrop"))
    legacy_js_dir = ROOT_DIR / pipe["legacyJumpscareDir"] if pipe.get("legacyJumpscareDir") else None
    render_jumpscare_sequence(
        face_src=js_face,
        office_base=office_base,
        out_dir=out_char_dir / "jumpscare",
        legacy_dir=legacy_js_dir,
        frame_count=jumpscare_frames_count,
        mode=pipe.get("jumpscareMode", "center_office"),
    )

    # 3. Door light frame (if applicable)
    if door_light_cfg and door_light_cfg.get("enabled"):
        cw, ch = door_light_cfg.get("size", [230, 300])
        px, py = door_light_cfg.get("position", [95, 160])
        dl_face = crop_or_center_square(src_im, door_light_cfg.get("crop")).resize(
            (cw, ch), Image.Resampling.LANCZOS
        )
        dl_face = apply_fnaf_filter(dl_face, darkness=0.8, contrast=1.3, vignette=False, scanlines=True)
        dl_face = add_glowing_eyes(dl_face, door_light_cfg.get("eyes", []), radius=4)
        dl_mask = make_feathered_mask(cw, ch, feather=25)
        base_light = clean_left if door_light_cfg.get("side") == "left" else clean_right
        composited = base_light.copy()
        composited.paste(dl_face, (px, py), dl_mask)
        save_image(composited, ROOT_DIR / runtime_assets["doorLightFrame"], quality=90)
        if door_light_cfg.get("legacyPath"):
            save_image(composited, ROOT_DIR / door_light_cfg["legacyPath"], quality=90)

    # 4. Stage overlay (CAM 1A)
    stage_cfg = pipe.get("stageOverlay")
    stage_base_path = BASE_GRAPHICS_DIR / "rooms/1a/1.webp"
    if stage_cfg and stage_cfg.get("enabled") and stage_base_path.exists():
        with Image.open(stage_base_path) as st_im:
            stage_bg = st_im.convert("RGBA")
        sw, sh = stage_cfg.get("size", [360, 420])
        sx, sy = stage_cfg.get("position", [630, 140])
        ez = crop_or_center_square(src_im, stage_cfg.get("crop")).resize(
            (sw, sh), Image.Resampling.LANCZOS
        )
        ez = apply_fnaf_filter(ez, darkness=0.42, contrast=1.4, vignette=False, scanlines=True)
        ez = add_glowing_eyes(ez, stage_cfg.get("eyes", []), radius=5)
        stage_bg.paste(ez, (sx, sy), make_feathered_mask(sw, sh, feather=35))
        save_image(stage_bg, GRAPHICS_DIR / "rooms/1a/0.webp", quality=90)

    # 5. Power outage face
    po_cfg = pipe.get("powerout")
    if po_cfg and po_cfg.get("enabled"):
        pw, ph = po_cfg.get("size", [300, 320])
        px, py = po_cfg.get("position", [130, 170])
        face = crop_or_center_square(src_im, po_cfg.get("crop")).resize(
            (pw, ph), Image.Resampling.LANCZOS
        )
        mask = make_feathered_mask(pw, ph, feather=30)
        for idx, (dark, rad) in enumerate([(0.08, 4), (0.28, 6)]):
            out = Image.new("RGBA", OFFICE_SIZE, (0, 0, 0, 255))
            ff = apply_fnaf_filter(face, darkness=dark, contrast=2.2, vignette=True)
            ff = add_glowing_eyes(ff, po_cfg.get("eyes", []), radius=rad)
            out.paste(ff, (px, py), mask)
            save_image(out, GRAPHICS_DIR / f"rooms/office/powerout{idx}.webp", quality=90)

    # 6. Optional custom room overlays (for 5th+ characters or room customization)
    for room_id, ov_cfg in room_overlays_cfg.items():
        empty_room_path = GRAPHICS_DIR / "rooms" / room_id / "0.webp"
        if not empty_room_path.exists():
            continue
        with Image.open(empty_room_path) as rm_im:
            room_bg = rm_im.convert("RGBA")
        rw, rh = ov_cfg.get("size", [260, 300])
        rx, ry = ov_cfg.get("position", [(room_bg.width - rw) // 2, (room_bg.height - rh) // 2])
        ov_face = crop_or_center_square(src_im, ov_cfg.get("crop")).resize(
            (rw, rh), Image.Resampling.LANCZOS
        )
        ov_face = apply_fnaf_filter(
            ov_face,
            darkness=float(ov_cfg.get("darkness", 0.5)),
            contrast=1.4,
            vignette=False,
            scanlines=True,
        )
        ov_face = add_glowing_eyes(ov_face, ov_cfg.get("eyes", []), radius=4)
        room_bg.paste(ov_face, (rx, ry), make_feathered_mask(rw, rh, feather=25))
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


def build_shared_branding(dry_run: bool = False) -> None:
    """Build shared menu/logo/gameover screens when base character photos exist."""
    if dry_run:
        return

    freddy_src = CHARACTERS_SRC_DIR / "freddy" / "source.jpeg"
    freddy_intense = CHARACTERS_SRC_DIR / "freddy" / "source_intense.jpeg"
    bonnie_src = CHARACTERS_SRC_DIR / "bonnie" / "source.jpeg"
    foxy_src = CHARACTERS_SRC_DIR / "foxy" / "source.jpeg"

    if freddy_src.exists() and bonnie_src.exists() and freddy_intense.exists():
        im_p2 = load_and_fix_orientation(freddy_src)
        im_p1 = load_and_fix_orientation(bonnie_src)
        im_p3 = load_and_fix_orientation(freddy_intense)

        p2_crop = crop_or_center_square(im_p2, [150, 200, 1350, 1750]).resize(
            MENU_SIZE, Image.Resampling.LANCZOS
        )
        f0 = apply_fnaf_filter(p2_crop, darkness=0.38, contrast=1.45, vignette=True)
        save_image(f0, GRAPHICS_DIR / "mainmenu/0.webp", quality=90)

        f1 = apply_fnaf_filter(p2_crop, darkness=0.5, contrast=1.6, vignette=True)
        f1 = add_glowing_eyes(f1, [(545, 312), (720, 316)], radius=6)
        f1 = create_chromatic_aberration(f1, offset=5)
        save_image(f1, GRAPHICS_DIR / "mainmenu/1.webp", quality=90)

        p1_crop = crop_or_center_square(im_p1, [100, 100, 1400, 1600]).resize(
            MENU_SIZE, Image.Resampling.LANCZOS
        )
        f2 = apply_fnaf_filter(p1_crop, darkness=0.42, contrast=1.5, vignette=True)
        f2 = add_glowing_eyes(f2, [(470, 240), (690, 260)], radius=7, glow_color=(255, 60, 60))
        region = f2.crop((0, 280, MENU_SIZE[0], 345))
        f2.paste(region, (20, 280))
        save_image(f2, GRAPHICS_DIR / "mainmenu/2.webp", quality=90)

        p3_crop = crop_or_center_square(im_p3, [80, 150, 1000, 1400]).resize(
            MENU_SIZE, Image.Resampling.LANCZOS
        )
        f3 = apply_fnaf_filter(p3_crop, darkness=0.65, contrast=1.8, vignette=True)
        f3 = add_glowing_eyes(f3, [(420, 340), (810, 350)], radius=9)
        f3 = create_chromatic_aberration(f3, offset=8)
        save_image(f3, GRAPHICS_DIR / "mainmenu/3.webp", quality=90)

    if foxy_src.exists():
        im_p5 = load_and_fix_orientation(foxy_src)
        bg = im_p5.resize(MENU_SIZE, Image.Resampling.LANCZOS)
        bg = apply_fnaf_filter(bg, darkness=0.25, contrast=1.8, vignette=True, scanlines=True)
        bg = create_chromatic_aberration(bg, offset=6)
        save_image(bg, GRAPHICS_DIR / "gameover/gameoverimg.webp", quality=85)


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

    if not args.dry_run:
        CONFIG_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_OUT_PATH, "w", encoding="utf-8") as f:
            json.dump({"characters": manifest}, f, indent=2, ensure_ascii=False)
        print(f"[OK] Wrote {CONFIG_OUT_PATH} ({len(manifest)} characters)")


if __name__ == "__main__":
    main()
