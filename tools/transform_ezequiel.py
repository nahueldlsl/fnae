import os
import math
import random
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ImageOps

P1 = "WhatsApp Image 2026-11-04 at 22.53.49.jpeg"  # Leaning smile, maroon sweatshirt
P2 = "WhatsApp Image 2026-11-09 at 19.29.15.jpeg"  # Classroom serious stare, black hoodie
P3 = "WhatsApp Image 2026-11-14 at 20.29.17.jpeg"  # Laying down, close intense stare
P4 = "WhatsApp Image 2026-11-15 at 20.05.00.jpeg"  # High angle desk shot
P5 = "WhatsApp Image 2026-11-15 at 20.05.01.jpeg"  # Ezequiel + screaming friend!

def load_and_fix_orientation(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGBA")

def make_feathered_mask(w, h, feather=25):
    """Creates a smooth elliptical alpha mask with soft feathered edges to prevent rectangular boxes."""
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    f = max(5, int(feather))
    draw.ellipse([f, f, max(f+1, w - f), max(f+1, h - f)], fill=255)
    return mask.filter(ImageFilter.GaussianBlur(f // 2))

def apply_fnaf_filter(img, darkness=0.45, contrast=1.35, vignette=False, scanlines=True):
    im = img.convert("RGBA")
    
    enhancer = ImageEnhance.Brightness(im)
    im = enhancer.enhance(darkness)
    enhancer = ImageEnhance.Contrast(im)
    im = enhancer.enhance(contrast)
    
    w, h = im.size
    
    if vignette:
        vignette_mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(vignette_mask)
        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx**2 + cy**2)
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

def add_glowing_eyes(img, eye_positions, radius=6, glow_color=(255, 255, 255)):
    im = img.copy().convert("RGBA")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for ex, ey in eye_positions:
        for r in range(radius * 3, radius, -2):
            alpha = int(55 * (1 - r / (radius * 3)))
            draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=(glow_color[0], glow_color[1], glow_color[2], alpha))
        draw.ellipse([ex - radius, ey - radius, ex + radius, ey + radius], fill=(glow_color[0], glow_color[1], glow_color[2], 255))
        draw.ellipse([ex - radius//2, ey - radius//2, ex + radius//2, ey + radius//2], fill=(255, 255, 255, 255))

    return Image.alpha_composite(im, overlay)

def create_chromatic_aberration(img, offset=6):
    r, g, b, a = img.convert("RGBA").split()
    r_shifted = Image.new("L", r.size, 0)
    r_shifted.paste(r, (offset, 0))
    b_shifted = Image.new("L", b.size, 0)
    b_shifted.paste(b, (-offset, 0))
    return Image.merge("RGBA", (r_shifted, g, b_shifted, a))

# ==========================================================
# 1. LOGO GENERATION
# ==========================================================
def generate_logo():
    print("Generating custom Five Nights at Ezequiel's logo...")
    w, h = 201, 212
    logo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo)
    font_large = ImageFont.load_default()
    
    lines = ["FIVE", "NIGHTS", "AT", "EZEQUIEL'S"]
    y_starts = [15, 60, 110, 155]
    
    for line, y in zip(lines, y_starts):
        bbox = draw.textbbox((0, 0), line, font=font_large)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x + 2, y + 2), line, fill=(180, 0, 0, 255), font=font_large)
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=font_large)

    logo.convert("1").save("graphics/fnaflogo.png")
    print("[OK] graphics/fnaflogo.png created")

# ==========================================================
# 2. MAIN MENU ANIMATIONS
# ==========================================================
def generate_main_menu():
    print("Generating Main Menu frames (graphics/mainmenu/0..3.webp)...")
    im_p2 = load_and_fix_orientation(P2)
    im_p1 = load_and_fix_orientation(P1)
    im_p3 = load_and_fix_orientation(P3)
    target_w, target_h = 1280, 720
    
    p2_crop = im_p2.crop((150, 200, 1350, 1750)).resize((target_w, target_h), Image.Resampling.LANCZOS)
    frame0 = apply_fnaf_filter(p2_crop, darkness=0.38, contrast=1.45, vignette=True)
    frame0.convert("RGB").save("graphics/mainmenu/0.webp", "WEBP", quality=90)
    
    frame1 = apply_fnaf_filter(p2_crop, darkness=0.5, contrast=1.6, vignette=True)
    frame1 = add_glowing_eyes(frame1, [(545, 312), (720, 316)], radius=6)
    frame1 = create_chromatic_aberration(frame1, offset=5)
    frame1.convert("RGB").save("graphics/mainmenu/1.webp", "WEBP", quality=90)
    
    p1_crop = im_p1.crop((100, 100, 1400, 1600)).resize((target_w, target_h), Image.Resampling.LANCZOS)
    frame2 = apply_fnaf_filter(p1_crop, darkness=0.42, contrast=1.5, vignette=True)
    frame2 = add_glowing_eyes(frame2, [(470, 240), (690, 260)], radius=7, glow_color=(255, 60, 60))
    slice_y = random.randint(200, 400)
    slice_h = random.randint(40, 90)
    region = frame2.crop((0, slice_y, target_w, slice_y + slice_h))
    frame2.paste(region, (20, slice_y))
    frame2.convert("RGB").save("graphics/mainmenu/2.webp", "WEBP", quality=90)
    
    p3_crop = im_p3.crop((80, 150, 1000, 1400)).resize((target_w, target_h), Image.Resampling.LANCZOS)
    frame3 = apply_fnaf_filter(p3_crop, darkness=0.65, contrast=1.8, vignette=True)
    frame3 = add_glowing_eyes(frame3, [(420, 340), (810, 350)], radius=9)
    frame3 = create_chromatic_aberration(frame3, offset=8)
    frame3.convert("RGB").save("graphics/mainmenu/3.webp", "WEBP", quality=90)
    print("[OK] Main Menu 0..3 generated")

# ==========================================================
# 3. CUSTOM NIGHT ICONS (200x200 PNG)
# ==========================================================
def generate_custom_night_icons():
    print("Generating Custom Night icons...")
    target_size = (200, 200)
    
    im_p2 = load_and_fix_orientation(P2)
    head_p2 = im_p2.crop((350, 300, 1150, 1100)).resize(target_size, Image.Resampling.LANCZOS)
    head_p2 = apply_fnaf_filter(head_p2, darkness=0.7, contrast=1.3, vignette=True, scanlines=False)
    head_p2.convert("RGB").save("graphics/mainmenu/customnight/freddy.png", "PNG")
    
    im_p1 = load_and_fix_orientation(P1)
    head_p1 = im_p1.crop((200, 50, 1100, 950)).resize(target_size, Image.Resampling.LANCZOS)
    head_p1 = apply_fnaf_filter(head_p1, darkness=0.7, contrast=1.3, vignette=True, scanlines=False)
    head_p1.convert("RGB").save("graphics/mainmenu/customnight/bunny.png", "PNG")
    
    im_p4 = load_and_fix_orientation(P4)
    head_p4 = im_p4.crop((400, 250, 1150, 1000)).resize(target_size, Image.Resampling.LANCZOS)
    head_p4 = apply_fnaf_filter(head_p4, darkness=0.7, contrast=1.3, vignette=True, scanlines=False)
    head_p4.convert("RGB").save("graphics/mainmenu/customnight/chica.png", "PNG")
    
    im_p5 = load_and_fix_orientation(P5)
    head_p5 = im_p5.crop((150, 950, 600, 1450)).resize(target_size, Image.Resampling.LANCZOS)
    head_p5 = apply_fnaf_filter(head_p5, darkness=0.75, contrast=1.4, vignette=True, scanlines=False)
    head_p5.convert("RGB").save("graphics/mainmenu/customnight/foxxy.png", "PNG")
    print("[OK] Custom Night icons generated")

# ==========================================================
# 4. OFFICE DOOR LIGHTS (CLEAN EMPTY LIGHTS + EZEQUIEL IN ANIMS)
# ==========================================================
def generate_door_lights():
    print("Generating Office Door Light appearances (Clean lights + Ezequiel in anims)...")
    office_base = Image.open("graphics/rooms/office/0.webp").convert("RGBA")
    w, h = office_base.size # 1600, 720
    
    # 4.1 Empty Left Light beam (NO Ezequiel)
    clean_left = office_base.copy()
    beam_left = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bdraw_l = ImageDraw.Draw(beam_left)
    bdraw_l.polygon([(50, 110), (270, 110), (310, 560), (30, 560)], fill=(255, 245, 200, 40))
    clean_left = Image.alpha_composite(clean_left, beam_left)
    
    # 4.2 Empty Right Light beam (NO Ezequiel)
    clean_right = office_base.copy()
    beam_right = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bdraw_r = ImageDraw.Draw(beam_right)
    bdraw_r.polygon([(1330, 110), (1550, 110), (1570, 560), (1290, 560)], fill=(255, 245, 200, 40))
    clean_right = Image.alpha_composite(clean_right, beam_right)
    
    # Save empty states (x_idx = 0)
    clean_left.convert("RGB").save("graphics/rooms/office/0_lightleft.webp", "WEBP", quality=90)
    clean_left.convert("RGB").save("graphics/rooms/office/2_lightleft.webp", "WEBP", quality=90)
    
    clean_right.convert("RGB").save("graphics/rooms/office/0_lightright.webp", "WEBP", quality=90)
    clean_right.convert("RGB").save("graphics/rooms/office/1_lightright.webp", "WEBP", quality=90)
    
    # 4.3 Left Door Light with Bonnie / Ezequiel (1_lightleft.webp)
    im_p1 = load_and_fix_orientation(P1)
    cut_w, cut_h = 230, 310
    head_p1 = im_p1.crop((120, 60, 1250, 1250)).resize((cut_w, cut_h), Image.Resampling.LANCZOS)
    head_p1 = apply_fnaf_filter(head_p1, darkness=0.8, contrast=1.3, vignette=False, scanlines=True)
    head_p1 = add_glowing_eyes(head_p1, [(90, 100), (155, 120)], radius=4)
    feather_mask_left = make_feathered_mask(cut_w, cut_h, feather=25)
    
    bonnie_left = clean_left.copy()
    bonnie_left.paste(head_p1, (95, 160), feather_mask_left)
    bonnie_left.convert("RGB").save("graphics/rooms/office/1_lightleft.webp", "WEBP", quality=90)
    
    # 4.4 Right Door Light with Chica / Ezequiel (2_lightright.webp)
    im_p2 = load_and_fix_orientation(P2)
    rcut_w, rcut_h = 220, 280
    head_p2 = im_p2.crop((350, 280, 1150, 1120)).resize((rcut_w, rcut_h), Image.Resampling.LANCZOS)
    head_p2 = apply_fnaf_filter(head_p2, darkness=0.8, contrast=1.3, vignette=False, scanlines=True)
    head_p2 = add_glowing_eyes(head_p2, [(95, 115), (145, 115)], radius=4)
    feather_mask_right = make_feathered_mask(rcut_w, rcut_h, feather=25)
    
    chica_right = clean_right.copy()
    chica_right.paste(head_p2, (1340, 170), feather_mask_right)
    chica_right.convert("RGB").save("graphics/rooms/office/2_lightright.webp", "WEBP", quality=90)
    
    print("[OK] Office Door Light images generated: 0 is clean empty, 1/2 have Ezequiel")

# ==========================================================
# 5. POWER OUTAGE GLOWING FACE
# ==========================================================
def generate_powerout():
    print("Generating Power Outage frames...")
    target_size = (1600, 720)
    black_bg = Image.new("RGBA", target_size, (0, 0, 0, 255))
    
    im_p2 = load_and_fix_orientation(P2)
    pw, ph = 300, 320
    face = im_p2.crop((300, 250, 1200, 1200)).resize((pw, ph), Image.Resampling.LANCZOS)
    mask = make_feathered_mask(pw, ph, feather=30)
    
    face0 = apply_fnaf_filter(face, darkness=0.08, contrast=2.2, vignette=True)
    face0 = add_glowing_eyes(face0, [(125, 135), (185, 135)], radius=4, glow_color=(255, 255, 255))
    out0 = black_bg.copy()
    out0.paste(face0, (130, 170), mask)
    out0.convert("RGB").save("graphics/rooms/office/powerout0.webp", "WEBP", quality=90)
    
    face1 = apply_fnaf_filter(face, darkness=0.28, contrast=2.2, vignette=True)
    face1 = add_glowing_eyes(face1, [(125, 135), (185, 135)], radius=6, glow_color=(255, 255, 255))
    out1 = black_bg.copy()
    out1.paste(face1, (130, 170), mask)
    out1.convert("RGB").save("graphics/rooms/office/powerout1.webp", "WEBP", quality=90)
    print("[OK] powerout0 and powerout1 generated")

# ==========================================================
# 6. ALL JUMPSCARES (WITH PROPER ALPHA FEATHERING - NO BLACK BOXES!)
# ==========================================================
def generate_jumpscares():
    print("Generating all jumpscare animation suites (clean alpha blending without boxes)...")
    im_p1 = load_and_fix_orientation(P1)
    im_p2 = load_and_fix_orientation(P2)
    im_p3 = load_and_fix_orientation(P3)
    im_p4 = load_and_fix_orientation(P4)
    im_p5 = load_and_fix_orientation(P5)
    
    office_base = Image.open("graphics/rooms/office/0.webp").convert("RGBA")
    
    # 6.1 Main Freddy Jumpscare (1600x720, 20 frames, centered)
    target_w, target_h = 1600, 720
    p3_face = im_p3.crop((120, 220, 960, 1180)) # Ezequiel intense stare
    # Friend screaming face in P5:
    p5_friend = im_p5.crop((150, 950, 600, 1450)) # Screaming friend head
    
    for i in range(20):
        prog = i / 19.0
        scale = 0.75 + 1.6 * (prog ** 1.5)
        shake_x = int(random.uniform(-1, 1) * 35 * prog)
        shake_y = int(random.uniform(-1, 1) * 35 * prog)
        
        fw = int(p3_face.width * scale)
        fh = int(p3_face.height * scale)
        rf = p3_face.resize((max(1, fw), max(1, fh)), Image.Resampling.BILINEAR)
        
        strobe = 0.5 + 0.45 * (prog ** 2) if (i % 2 == 0) else 0.3 + 0.3 * (prog ** 2)
        filtered = apply_fnaf_filter(rf, darkness=strobe, contrast=1.4 + 0.6 * prog, vignette=False)
        mask = make_feathered_mask(fw, fh, feather=int(min(fw, fh) * 0.18))
        
        bg = Image.new("RGBA", (target_w, target_h), (5, 0, 0, 255))
        
        if i >= 13:
            friend_scale = 1.3 + 1.0 * (i - 13) / 6.0
            rf_w = int(p5_friend.width * friend_scale)
            rf_h = int(p5_friend.height * friend_scale)
            rf_friend = p5_friend.resize((rf_w, rf_h), Image.Resampling.BILINEAR)
            rff = apply_fnaf_filter(rf_friend, darkness=0.8, contrast=1.8, vignette=False)
            fmask = make_feathered_mask(rf_w, rf_h, feather=int(min(rf_w, rf_h) * 0.18))
            fx = (target_w - rf_w) // 2 + shake_x
            fy = (target_h - rf_h) // 2 + shake_y
            bg.paste(rff, (fx, fy), fmask)
            
        pos_x = (target_w - fw) // 2 + shake_x
        start_y = int(target_h * 0.3 * (1.0 - prog))
        pos_y = (target_h - fh) // 2 + start_y + shake_y
        
        bg.paste(filtered, (pos_x, pos_y), mask)
        bg = create_chromatic_aberration(bg, offset=int(3 + 10 * prog))
        if i >= 10 and i % 3 == 0:
            red_flash = Image.new("RGBA", (target_w, target_h), (220, 0, 0, 65))
            bg = Image.alpha_composite(bg, red_flash)
            
        bg.convert("RGB").save(f"graphics/gameover/freddy/{i}.webp", "WEBP", quality=85)

    # 6.2 Freddy Office Jumpscare (1600x720, 31 frames)
    for i in range(31):
        prog = i / 30.0
        scale = 0.6 + 1.4 * (prog ** 1.4)
        shake_x = int(random.uniform(-1, 1) * 35 * prog)
        shake_y = int(random.uniform(-1, 1) * 35 * prog)
        
        fw = int(p3_face.width * scale)
        fh = int(p3_face.height * scale)
        rf = p3_face.resize((fw, fh), Image.Resampling.BILINEAR)
        strobe = 0.45 + 0.45 * (prog ** 2) if (i % 2 == 0) else 0.25 + 0.3 * (prog ** 2)
        rf_filt = apply_fnaf_filter(rf, darkness=strobe, contrast=1.5, vignette=False)
        mask = make_feathered_mask(fw, fh, feather=int(min(fw, fh) * 0.18))
        
        frame = office_base.copy()
        dark_dim = Image.new("RGBA", frame.size, (0, 0, 0, int(190 * prog)))
        frame = Image.alpha_composite(frame, dark_dim)
        
        px = (1600 - fw) // 2 + shake_x
        py = (720 - fh) // 2 + int(160 * (1.0 - prog)) + shake_y
        frame.paste(rf_filt, (px, py), mask)
        frame = create_chromatic_aberration(frame, offset=int(3 + 9 * prog))
        frame.convert("RGB").save(f"graphics/gameover/freddyoffice/{i}.webp", "WEBP", quality=85)

    # 6.3 Bonnie Office Jumpscare (1600x720, 22 frames)
    p1_face = im_p1.crop((180, 80, 1150, 1100))
    for i in range(22):
        prog = i / 21.0
        scale = 0.6 + 1.35 * (prog ** 1.4)
        shake_x = int(random.uniform(-1, 1) * 35 * prog)
        shake_y = int(random.uniform(-1, 1) * 35 * prog)
        
        fw = int(p1_face.width * scale)
        fh = int(p1_face.height * scale)
        rf = p1_face.resize((fw, fh), Image.Resampling.BILINEAR)
        rf_filt = apply_fnaf_filter(rf, darkness=0.6 + 0.35 * prog, contrast=1.6, vignette=False)
        mask = make_feathered_mask(fw, fh, feather=int(min(fw, fh) * 0.18))
        
        frame = office_base.copy()
        px = 300 + int(200 * prog) + shake_x # Bonnie lunges from left towards center
        py = (720 - fh) // 2 + int(180 * (1.0 - prog)) + shake_y
        frame.paste(rf_filt, (px, py), mask)
        frame = create_chromatic_aberration(frame, offset=int(4 + 8 * prog))
        frame.convert("RGB").save(f"graphics/gameover/bonny/{i}.webp", "WEBP", quality=85)

    # 6.4 Chica Office Jumpscare (1600x720, 16 frames)
    p4_face = im_p4.crop((450, 300, 1100, 1050))
    for i in range(16):
        prog = i / 15.0
        scale = 0.6 + 1.4 * (prog ** 1.4)
        shake_x = int(random.uniform(-1, 1) * 35 * prog)
        shake_y = int(random.uniform(-1, 1) * 35 * prog)
        
        fw = int(p4_face.width * scale)
        fh = int(p4_face.height * scale)
        rf = p4_face.resize((fw, fh), Image.Resampling.BILINEAR)
        rf_filt = apply_fnaf_filter(rf, darkness=0.6 + 0.35 * prog, contrast=1.6, vignette=False)
        mask = make_feathered_mask(fw, fh, feather=int(min(fw, fh) * 0.18))
        
        frame = office_base.copy()
        px = 850 - int(150 * prog) + shake_x # Chica lunges from right towards center
        py = (720 - fh) // 2 + int(180 * (1.0 - prog)) + shake_y
        frame.paste(rf_filt, (px, py), mask)
        frame = create_chromatic_aberration(frame, offset=int(4 + 8 * prog))
        frame.convert("RGB").save(f"graphics/gameover/chica/{i}.webp", "WEBP", quality=85)

    # 6.5 Foxy Office Jumpscare (1600x720, 21 frames)
    # Screaming friend from P5 emerges from left doorway!
    for i in range(21):
        prog = i / 20.0
        scale = 0.8 + 1.2 * prog
        shake_x = int(random.uniform(-1, 1) * 30 * prog)
        shake_y = int(random.uniform(-1, 1) * 30 * prog)
        
        fw = int(p5_friend.width * scale)
        fh = int(p5_friend.height * scale)
        rf = p5_friend.resize((fw, fh), Image.Resampling.BILINEAR)
        rf_filt = apply_fnaf_filter(rf, darkness=0.75 + 0.25 * (i % 2), contrast=1.7, vignette=False)
        mask = make_feathered_mask(fw, fh, feather=int(min(fw, fh) * 0.18))
        
        frame = office_base.copy()
        px = 80 + int(320 * prog) + shake_x # Peeks in from doorway and moves into view
        py = 150 + int(40 * prog) + shake_y
        frame.paste(rf_filt, (px, py), mask)
        frame = create_chromatic_aberration(frame, offset=int(3 + 8 * prog))
        frame.convert("RGB").save(f"graphics/rooms/office/foxxy/{i}.webp", "WEBP", quality=85)

    print("[OK] All jumpscare suites regenerated without black box artifacts")

# ==========================================================
# 7. GAME OVER SCREEN
# ==========================================================
def generate_gameover():
    print("Generating Game Over screen (graphics/gameover/gameoverimg.webp)...")
    target_w, target_h = 1280, 720
    im_p5 = load_and_fix_orientation(P5)
    bg = im_p5.resize((target_w, target_h), Image.Resampling.LANCZOS)
    bg = apply_fnaf_filter(bg, darkness=0.25, contrast=1.8, vignette=True, scanlines=True)
    bg = create_chromatic_aberration(bg, offset=6)
    bg.convert("RGB").save("graphics/gameover/gameoverimg.webp", "WEBP", quality=85)
    print("[OK] Game Over image generated")

# ==========================================================
# 8. SHOW STAGE (CAM 1A)
# ==========================================================
def generate_cam_1a():
    print("Generating Show Stage (CAM 1A) with Ezequiel...")
    # Clean stage background: 1.webp
    stage_ez = Image.open("graphics/rooms/1a/1.webp").convert("RGBA")
    im_p2 = load_and_fix_orientation(P2)
    
    ez_w, ez_h = 360, 420
    ez = im_p2.crop((200, 150, 1300, 1400)).resize((ez_w, ez_h), Image.Resampling.LANCZOS)
    ez = apply_fnaf_filter(ez, darkness=0.42, contrast=1.4, vignette=False, scanlines=True)
    ez = add_glowing_eyes(ez, [(150, 205), (225, 207)], radius=5)
    mask = make_feathered_mask(ez_w, ez_h, feather=35)
    
    stage_ez.paste(ez, (630, 140), mask)
    stage_ez.convert("RGB").save("graphics/rooms/1a/0.webp", "WEBP", quality=90)
    print("[OK] CAM 1A updated")

def main():
    print("=== STARTING REVISED EZEQUIEL TRANSFORMATION PIPELINE ===")
    generate_logo()
    generate_main_menu()
    generate_custom_night_icons()
    generate_door_lights()
    generate_powerout()
    generate_jumpscares()
    generate_gameover()
    generate_cam_1a()
    # Clean temporary files if any
    for t in ["test_friend.jpg", "test_head.jpg"]:
        if os.path.exists(t):
            os.remove(t)
    print("=== ALL ASSETS REGENERATED WITH HIGH QUALITY & ZERO ARTIFACTS ===")

if __name__ == "__main__":
    main()
