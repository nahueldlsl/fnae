import os
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

BASE_URL = "https://lagged.com/games/fnaf/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://lagged.com/games/fnaf/"
}

def get_asset_list():
    assets = set()
    
    # 1. HTML static assets
    html_assets = [
        "graphics/camera/static_test5.webm",
        "graphics/logo.png",
        "graphics/nightover.png",
        "graphics/gameover/gameoverimg.webp",
        "graphics/gameover/gameover.png",
        "graphics/newgame.webp",
        "graphics/fnaflogo.png",
        "graphics/copyright.png",
        "graphics/mainmenu/newgame.png",
        "graphics/mainmenu/continue.png",
        "graphics/mainmenu/littletext/night.png",
        "graphics/mainmenu/littletext/2.png",
        "graphics/mainmenu/littletext/5.png",
        "graphics/mainmenu/6thnight.png",
        "graphics/mainmenu/customnight.png",
        "graphics/mainmenu/selected.png",
        "graphics/mainmenu/customnight/text/title.png",
        "graphics/mainmenu/customnight/text/freddy.png",
        "graphics/mainmenu/customnight/text/bonnie.png",
        "graphics/mainmenu/customnight/text/chica.png",
        "graphics/mainmenu/customnight/text/foxy.png",
        "graphics/mainmenu/customnight/text/2.png",
        "graphics/mainmenu/customnight/text/0.png",
        "graphics/mainmenu/customnight/text/ready.png",
        "graphics/mainmenu/customnight/text/difficulty.png",
        "graphics/mainmenu/customnight/ailevel.png",
        "graphics/mainmenu/customnight/arrowleft.png",
        "graphics/mainmenu/customnight/arrowright.png",
        "graphics/mainmenu/customnight/freddy.png",
        "graphics/mainmenu/customnight/bunny.png",
        "graphics/mainmenu/customnight/chica.png",
        "graphics/mainmenu/customnight/foxxy.png",
        "graphics/camera/record.png",
        "graphics/camera/ui/cameradisabled.png",
        "graphics/camera/outline.png",
        "graphics/camera/map.png",
        "graphics/camera/openclosecamera.png",
        "graphics/camera/ui/night.png",
        "graphics/camera/ui/1.png",
        "graphics/camera/ui/timeAM.png",
        "graphics/camera/powerleft.png",
        "graphics/camera/powerusage.png",
        "graphics/loadingicon.png",
        "graphics/rooms/office/cameraposition.webp"
    ]
    assets.update(html_assets)

    # Map buttons
    for b in ["1a", "1b", "1c", "2a", "2b", "3", "4a", "4b", "5", "6", "7"]:
        assets.add(f"graphics/camera/mapbuttons/{b}.png")

    # Transitions 0..7
    for i in range(8):
        assets.add(f"graphics/transition/{i}.webp")

    # Sounds
    sound_files = [
        "sounds/chimes 2.wav",
        "sounds/blip3.wav",
        "sounds/CAMERA_VIDEO_LOA_60105303.wav",
        "sounds/DOOR_POUNDING_ME_D0291401.wav",
        "sounds/knock2.wav",
        "sounds/pirate_song2.wav",
        "sounds/powerdown.wav",
        "sounds/put_down.wav",
        "sounds/run.wav",
        "sounds/SFXBible_12478.wav",
        "sounds/static2.wav",
        "sounds/windowscare.wav",
        "sounds/XSCREAM.wav",
        "sounds/XSCREAM2.wav",
        "sounds/freddy/poweroutmusic.ogg",
        "sounds/error.wav",
        "sounds/kitchen1.wav",
        "sounds/kitchen2.wav",
        "sounds/kitchen3.wav",
        "sounds/kitchen4.wav",
        "sounds/Laugh_Giggle_Girl_1d.wav",
        "sounds/Laugh_Giggle_Girl_2d.wav",
        "sounds/Laugh_Giggle_Girl_8d.wav",
        "sounds/deep steps.wav",
        "sounds/Buzz_Fan_Florescent2.wav",
        "sounds/ambience2.wav"
    ]
    assets.update(sound_files)

    # Loading icons
    for i in range(1, 8):
        assets.add(f"graphics/loading/loading{i}.png")

    # Room images
    room_counts = {
        "1a": 7, "1b": 6, "1c": 4, "2a": 3, "2b": 3,
        "5": 3, "7": 4, "3": 3, "4a": 4, "4b": 5
    }
    for r, count in room_counts.items():
        for y in range(count):
            assets.add(f"graphics/rooms/{r}/{y}.webp")

    # Room names
    for r in ["1a", "1b", "1c", "2a", "2b", "5", "7", "3", "4a", "4b", "6"]:
        assets.add(f"graphics/camera/roomnames/{r}.webp")

    # Office base
    assets.add("graphics/rooms/office/0.webp")

    # Office lights
    for x in range(3):
        for side in ["left", "right"]:
            assets.add(f"graphics/rooms/office/{x}_light{side}.webp")

    # Buttons
    for i in range(1, 5):
        assets.add(f"graphics/rooms/office/buttons/buttonleft_{i}.webp")
        assets.add(f"graphics/rooms/office/buttons/buttonright_{i}.webp")

    # Doors
    for i in range(14):
        assets.add(f"graphics/rooms/office/doors/left/{i}.webp")
        assets.add(f"graphics/rooms/office/doors/right/{i}.webp")

    # Power and time
    for i in range(1, 6):
        assets.add(f"graphics/camera/power{i}.png")
    for i in range(10):
        assets.add(f"graphics/camera/ui/powernumbers/{i}.png")
    assets.add("graphics/camera/ui/powernumbers/percent.png")
    for i in range(7):
        assets.add(f"graphics/camera/ui/time{i}.png")

    # Camera feed animation
    for i in range(10):
        assets.add(f"graphics/camera/camerafeedanimation/{i}.webp")

    # Foxy 2a anim
    for i in range(31):
        assets.add(f"graphics/rooms/2a/foxxy/{i}.webp")

    # Fan anim
    for i in range(1, 4):
        assets.add(f"graphics/rooms/office/fan_{i}.webp")

    # Foxy office anim
    for i in range(21):
        assets.add(f"graphics/rooms/office/foxxy/{i}.webp")

    # Powerout
    for i in range(2):
        assets.add(f"graphics/rooms/office/powerout{i}.webp")

    # Jumpscares
    for i in range(20):
        assets.add(f"graphics/gameover/freddy/{i}.webp")
    for i in range(31):
        assets.add(f"graphics/gameover/freddyoffice/{i}.webp")
    for i in range(22):
        assets.add(f"graphics/gameover/bonny/{i}.webp")
    for i in range(16):
        assets.add(f"graphics/gameover/chica/{i}.webp")

    # Main menu
    for i in range(4):
        assets.add(f"graphics/mainmenu/{i}.webp")

    return sorted(list(assets))

def download_one(rel_path):
    if os.path.exists(rel_path) and os.path.getsize(rel_path) > 0:
        return (rel_path, True, "Already exists")
    
    quoted_path = urllib.parse.quote(rel_path)
    url = BASE_URL + quoted_path
    
    req = urllib.request.Request(url, headers=HEADERS)
    
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
                if len(content) < 500 and (b"404 Not Found" in content or b"Not Acceptable" in content):
                    return (rel_path, False, f"Server returned error page: {content[:100]}")
                with open(rel_path, "wb") as f:
                    f.write(content)
            return (rel_path, True, f"Downloaded {len(content)} bytes")
        except Exception as e:
            if attempt == 3:
                return (rel_path, False, str(e))
            time.sleep(0.5 * (attempt + 1))

def main():
    assets = get_asset_list()
    print(f"Total assets queued to download: {len(assets)}")
    
    # Pre-create all directories sequentially to avoid Windows race conditions
    all_dirs = set(os.path.dirname(p) for p in assets if os.path.dirname(p))
    for d in sorted(all_dirs):
        os.makedirs(d, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    failures = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(download_one, path): path for path in assets}
        for future in as_completed(futures):
            path = futures[future]
            try:
                rel_path, ok, msg = future.result()
                if ok:
                    success_count += 1
                    if "Downloaded" in msg:
                        print(f"[OK] {rel_path} ({msg})")
                else:
                    fail_count += 1
                    failures.append((rel_path, msg))
                    print(f"[FAIL] {rel_path}: {msg}")
            except Exception as e:
                fail_count += 1
                failures.append((path, str(e)))
                print(f"[ERR] {path}: {e}")

    print("\n" + "="*50)
    print(f"Download complete: {success_count} succeeded, {fail_count} failed")
    if failures:
        print("Failed assets:")
        for path, err in failures:
            print(f" - {path}: {err}")

if __name__ == "__main__":
    main()
