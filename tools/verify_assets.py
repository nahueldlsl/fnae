import os
import glob
from PIL import Image

def verify_all():
    print("=== VERIFYING FIVE NIGHTS AT EZEQUIEL'S INTEGRITY ===")
    
    # 1. Check core files
    core_files = [
        "index.html",
        "feed.css",
        "jquery.min.js",
        "run_game.py",
        "start.bat",
        "script/main.js",
        "script/ai.js",
        "script/sound.js",
        "script/loading.js",
        "script/variables.js",
        "script/ui.js",
        "script/animation.js"
    ]
    
    missing_core = [f for f in core_files if not os.path.exists(f) or os.path.getsize(f) == 0]
    if missing_core:
        print(f"[FAIL] Missing core files: {missing_core}")
        return False
    print(f"[PASS] All {len(core_files)} core engine files verified.")

    # 2. Check sounds
    sound_files = glob.glob("sounds/**/*.wav", recursive=True) + glob.glob("sounds/**/*.ogg", recursive=True)
    zero_sounds = [s for s in sound_files if os.path.getsize(s) == 0]
    if zero_sounds:
        print(f"[FAIL] Empty sound files detected: {zero_sounds}")
        return False
    print(f"[PASS] Total verified audio files: {len(sound_files)}")

    # 3. Check transformed Ezequiel assets
    ezequiel_checks = [
        ("Main Menu 0", "graphics/mainmenu/0.webp"),
        ("Main Menu 1", "graphics/mainmenu/1.webp"),
        ("Main Menu 2", "graphics/mainmenu/2.webp"),
        ("Main Menu 3", "graphics/mainmenu/3.webp"),
        ("Logo", "graphics/fnaflogo.png"),
        ("Left Door Light", "graphics/rooms/office/0_lightleft.webp"),
        ("Right Door Light", "graphics/rooms/office/0_lightright.webp"),
        ("Power Out 0", "graphics/rooms/office/powerout0.webp"),
        ("Power Out 1", "graphics/rooms/office/powerout1.webp"),
        ("CAM 1A Stage", "graphics/rooms/1a/0.webp"),
        ("Game Over Screen", "graphics/gameover/gameoverimg.webp"),
        ("Custom Night Freddy", "graphics/mainmenu/customnight/freddy.png"),
        ("Custom Night Bonnie", "graphics/mainmenu/customnight/bunny.png"),
        ("Custom Night Chica", "graphics/mainmenu/customnight/chica.png"),
        ("Custom Night Foxy", "graphics/mainmenu/customnight/foxxy.png"),
        ("Freddy Jumpscare Frame 0", "graphics/gameover/freddy/0.webp"),
        ("Freddy Jumpscare Frame 19", "graphics/gameover/freddy/19.webp"),
        ("Bonnie Jumpscare Frame 0", "graphics/gameover/bonny/0.webp"),
        ("Chica Jumpscare Frame 0", "graphics/gameover/chica/0.webp"),
        ("Foxy Office Frame 0", "graphics/rooms/office/foxxy/0.webp"),
        ("Achievement Star", "graphics/mainmenu/star.png"),
    ]

    # Additional digit checks
    for i in range(10):
        cn_num = f"graphics/mainmenu/customnight/text/{i}.png"
        if not os.path.exists(cn_num):
            print(f"[FAIL] Missing Custom Night digit {i}: {cn_num}")
            return False
    for i in range(1, 8):
        lt_num = f"graphics/mainmenu/littletext/{i}.png"
        if not os.path.exists(lt_num):
            print(f"[FAIL] Missing littletext digit {i}: {lt_num}")
            return False
        ui_num = f"graphics/camera/ui/{i}.png"
        if not os.path.exists(ui_num):
            print(f"[FAIL] Missing camera UI night digit {i}: {ui_num}")
            return False

    for label, path in ezequiel_checks:
        if not os.path.exists(path):
            print(f"[FAIL] {label} not found at {path}")
            return False
        try:
            with Image.open(path) as im:
                im.verify()
        except Exception as e:
            print(f"[FAIL] {label} at {path} could not be loaded: {e}")
            return False

    print(f"[PASS] All {len(ezequiel_checks)} Ezequiel custom asset checks passed successfully.")

    # 4. Total graphics count
    all_graphics = glob.glob("graphics/**/*.*", recursive=True)
    print(f"[PASS] Total game graphics present: {len(all_graphics)}")
    print("=== ALL VERIFICATION CHECKS PASSED (100% OK) ===")
    return True

if __name__ == "__main__":
    verify_all()
