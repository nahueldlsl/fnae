import glob
import json
import os
from pathlib import Path
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent


def verify_all() -> bool:
    print("=== VERIFYING FIVE NIGHTS AT EZEQUIEL'S INTEGRITY ===")

    core_files = [
        "index.html",
        "feed.css",
        "1080.css",
        "640.css",
        "run_game.py",
        "start.bat",
        "config/game.json",
        "config/characters.json",
        "script/app.js",
        "script/core/EventBus.js",
        "script/core/TimerRegistry.js",
        "script/core/SaveRepository.js",
        "script/core/AudioManager.js",
        "script/core/AssetLoader.js",
        "script/systems/NightClock.js",
        "script/systems/PowerSystem.js",
        "script/systems/CameraSystem.js",
        "script/systems/OfficeSystem.js",
        "script/ai/MovementStrategies.js",
        "script/ai/AnimatronicEntity.js",
        "script/ai/AIManager.js",
        "script/GameEngine.js",
        "script/ui/AnimationController.js",
        "script/ui/MenuController.js",
        "script/ui/CustomNightView.js",
        "script/ui/OfficeView.js",
        "script/ui/CameraView.js",
    ]

    missing_core = [
        f for f in core_files
        if not (ROOT_DIR / f).exists() or (ROOT_DIR / f).stat().st_size == 0
    ]
    if missing_core:
        print(f"[FAIL] Missing core files: {missing_core}")
        return False
    print(f"[PASS] All {len(core_files)} core engine & config files verified.")

    with open(ROOT_DIR / "config/game.json", "r", encoding="utf-8") as f:
        game_cfg = json.load(f)
    with open(ROOT_DIR / "config/characters.json", "r", encoding="utf-8") as f:
        char_cfg = json.load(f)

    # Check configured sounds
    for snd in game_cfg.get("sounds", []):
        snd_path = ROOT_DIR / "sounds" / snd
        if not snd_path.exists() or snd_path.stat().st_size == 0:
            print(f"[FAIL] Missing or empty configured sound: {snd_path}")
            return False

    sound_files = glob.glob(str(ROOT_DIR / "sounds/**/*.wav"), recursive=True) + glob.glob(
        str(ROOT_DIR / "sounds/**/*.ogg"), recursive=True
    )
    print(f"[PASS] Total verified audio files: {len(sound_files)}")

    # Check dynamic character assets
    characters = char_cfg.get("characters", [])
    if not characters:
        print("[FAIL] No characters configured in config/characters.json")
        return False

    checked_images = 0
    for ch in characters:
        assets = ch.get("assets", {})
        paths_to_check = [assets.get("icon"), assets.get("doorLightFrame")]
        paths_to_check.extend(assets.get("jumpscareFrames", []))
        paths_to_check.extend((assets.get("roomOverlays") or {}).values())

        for rel in filter(None, paths_to_check):
            img_path = ROOT_DIR / rel
            if not img_path.exists():
                print(f"[FAIL] Missing asset for character '{ch['id']}': {rel}")
                return False
            try:
                with Image.open(img_path) as im:
                    im.verify()
                checked_images += 1
            except Exception as e:
                print(f"[FAIL] Corrupted image {rel}: {e}")
                return False

    # Check base UI & room images
    static_checks = [
        "graphics/mainmenu/0.webp",
        "graphics/mainmenu/1.webp",
        "graphics/mainmenu/2.webp",
        "graphics/mainmenu/3.webp",
        "graphics/fnaflogo.png",
        "graphics/rooms/office/0.webp",
        "graphics/rooms/office/0_lightleft.webp",
        "graphics/rooms/office/0_lightright.webp",
        "graphics/rooms/office/powerout0.webp",
        "graphics/rooms/office/powerout1.webp",
        "graphics/rooms/1a/0.webp",
        "graphics/rooms/1a/1.webp",
        "graphics/rooms/1a/2.webp",
        "graphics/rooms/1a/3.webp",
        "graphics/rooms/1a/5.webp",
        "graphics/rooms/1c/0.webp",
        "graphics/rooms/1c/1.webp",
        "graphics/rooms/1c/2.webp",
        "graphics/rooms/1c/3.webp",
        "graphics/gameover/gameoverimg.webp",
        "graphics/mainmenu/star.png",
    ]
    for i in range(31):
        static_checks.append(f"graphics/rooms/2a/foxxy/{i}.webp")
    for i in range(10):
        static_checks.append(f"graphics/mainmenu/customnight/text/{i}.png")
    for i in range(1, 8):
        static_checks.append(f"graphics/mainmenu/littletext/{i}.png")
        static_checks.append(f"graphics/camera/ui/{i}.png")

    for rel in static_checks:
        p = ROOT_DIR / rel
        if not p.exists():
            print(f"[FAIL] Missing static asset: {rel}")
            return False
        with Image.open(p) as im:
            im.verify()
        checked_images += 1

    print(
        f"[PASS] Verified {len(characters)} characters and {checked_images} image integrity checks."
    )
    all_graphics = glob.glob(str(ROOT_DIR / "graphics/**/*.*"), recursive=True)
    print(f"[PASS] Total game graphics present: {len(all_graphics)}")
    print("=== ALL VERIFICATION CHECKS PASSED (100% OK) ===")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if verify_all() else 1)
