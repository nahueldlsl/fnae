/**
 * CameraView (SRP / DRY) - Handles monitor toggle, single delegated binding for all
 * camera map buttons, static bursts, REC blink, and Foxy sprint playback.
 */
export class CameraView {
  constructor({ engine, audio, animations, timers }) {
    this.#engine = engine;
    this.#audio = audio;
    this.#animations = animations;
    this.#timers = timers;
    this.#recordInterval = null;
    this.#flicker2aInterval = null;
  }

  #engine;
  #audio;
  #animations;
  #timers;
  #recordInterval;
  #flicker2aInterval;

  init() {
    const toggleBtn = document.getElementById('openclosecamera');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        if (this.#engine.phase !== 'playing') return;
        this.#engine.camera.toggleMonitor();
      });
    }

    // Single parameterized loop replaces 11 duplicated button blocks
    for (const room of this.#engine.camera.getAllRooms()) {
      const btn = document.getElementById(`button-${room.id}`);
      if (!btn) continue;

      btn.addEventListener('mouseenter', () => {
        btn.style.backgroundColor =
          this.#engine.camera.currentRoom === room.id ? '#107010' : '#505050';
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.backgroundColor =
          this.#engine.camera.currentRoom === room.id ? '#107010' : '#101010';
      });
      btn.addEventListener('click', () => {
        if (!this.#engine.camera.isOpen) return;
        if (this.#engine.camera.selectRoom(room.id)) {
          this.#audio.play('blip3.wav', 0.5);
          this.#refreshButtonColors(room.id);
          this.#renderActiveRoom();
        }
      });
    }

    const bus = this.#engine.eventBus;
    bus.on('game:nightStarted', () => this.#onNightStart());
    bus.on('camera:toggled', ({ open }) => this.#onMonitorToggled(open));
    bus.on('ai:moved', ({ fromRoom, toRoom }) => {
      if (!this.#engine.camera.isOpen) return;
      const active = this.#engine.camera.currentRoom;
      if (active === fromRoom || active === toRoom) {
        this.#pulseStatic(450);
        this.#renderActiveRoom();
      }
    });
    bus.on('ai:foxySprinting', () => {
      if (this.#engine.camera.isOpen && this.#engine.camera.currentRoom === '2a') {
        this.#playFoxySprint();
      }
    });
    bus.on('ai:sound', ({ sound, volume }) => {
      this.#audio.play(sound, volume ?? 0.5);
    });
    bus.on('game:nightWon', () => this.stopLoops());
    bus.on('game:jumpscare', () => this.stopLoops());
    bus.on('game:powerOutageStarted', () => this.stopLoops());
  }

  #onNightStart() {
    this.stopLoops();
    const feed = document.getElementById('camerafeed');
    const anim = document.getElementById('camerafeedanimation');
    if (feed) feed.style.display = 'none';
    if (anim) anim.style.display = 'none';
    this.#refreshButtonColors('1a');

    const recordEl = document.getElementById('record');
    if (recordEl) {
      this.#recordInterval = globalThis.setInterval(() => {
        recordEl.style.display = recordEl.style.display === 'none' ? 'block' : 'none';
      }, 900);
    }
  }

  stopLoops() {
    if (this.#recordInterval != null) {
      globalThis.clearInterval(this.#recordInterval);
      this.#recordInterval = null;
    }
    if (this.#flicker2aInterval != null) {
      globalThis.clearInterval(this.#flicker2aInterval);
      this.#flicker2aInterval = null;
    }
    const staticVid = document.getElementById('staticimg');
    if (staticVid) staticVid.pause();
  }

  #onMonitorToggled(open) {
    const feed = document.getElementById('camerafeed');
    const officeMain = document.getElementById('officemain');
    const fan = document.getElementById('fan');
    const staticVid = document.getElementById('staticimg');

    if (open) {
      this.#audio.play('CAMERA_VIDEO_LOA_60105303.wav', 0.5);
      this.#animations.playCameraFlip(true, () => {
        if (!this.#engine.camera.isOpen) return;
        if (feed) feed.style.display = 'block';
        if (officeMain) officeMain.style.display = 'none';
        if (fan) fan.style.display = 'none';
        if (staticVid) staticVid.play().catch(() => {});
        this.#renderActiveRoom();
      });
    } else {
      this.#audio.play('put_down.wav', 0.5);
      if (feed) feed.style.display = 'none';
      if (officeMain) officeMain.style.display = 'block';
      if (fan) fan.style.display = 'block';
      if (staticVid) staticVid.pause();
      this.#animations.playCameraFlip(false);
    }
  }

  #refreshButtonColors(activeRoomId) {
    for (const room of this.#engine.camera.getAllRooms()) {
      const btn = document.getElementById(`button-${room.id}`);
      if (btn) {
        btn.style.backgroundColor = room.id === activeRoomId ? '#107010' : '#101010';
      }
    }
  }

  #pulseStatic(durationMs = 200) {
    const staticDiv = document.getElementById('static');
    if (!staticDiv) return;
    staticDiv.style.transition = 'none';
    staticDiv.style.opacity = '1';
    this.#timers.setTimeout(() => {
      staticDiv.style.transition = 'opacity 0.25s ease';
      staticDiv.style.opacity = '0.25';
    }, durationMs);
  }

  #renderActiveRoom() {
    if (this.#flicker2aInterval != null) {
      globalThis.clearInterval(this.#flicker2aInterval);
      this.#flicker2aInterval = null;
    }

    const roomId = this.#engine.camera.currentRoom;
    const meta = this.#engine.camera.getRoomMeta(roomId);
    const roomImg = document.getElementById('room');
    const roomNameImg = document.getElementById('roomname');
    const disabledBanner = document.getElementById('cameradisabled');
    const staticDiv = document.getElementById('static');

    if (roomNameImg) {
      roomNameImg.src = `graphics/camera/roomnames/${roomId}.webp`;
    }

    if (meta?.audioOnly) {
      if (disabledBanner) disabledBanner.style.display = 'block';
      if (staticDiv) staticDiv.style.opacity = '1';
      return;
    }

    if (disabledBanner) disabledBanner.style.display = 'none';
    this.#pulseStatic(175);

    const src = this.#engine.camera.resolveRoomImage(roomId, this.#engine.ai.entities);
    if (roomImg && src) {
      roomImg.src = src;
      if (meta?.movingCamera) {
        roomImg.classList.add('roomtest');
      } else {
        roomImg.classList.remove('roomtest');
      }
    }

    if (roomId === '2a') {
      const foxy = this.#engine.ai.getEntity('foxy');
      if (foxy && foxy.foxyPhase === 'sprinting') {
        this.#playFoxySprint();
      } else if (src && src.endsWith('0.webp')) {
        let toggle = 0;
        this.#flicker2aInterval = globalThis.setInterval(() => {
          if (!this.#engine.camera.isOpen || this.#engine.camera.currentRoom !== '2a') return;
          toggle = toggle ^ 1;
          if (roomImg) roomImg.src = `graphics/rooms/2a/${toggle}.webp`;
        }, 120);
      }
    }
  }

  #playFoxySprint() {
    const roomImg = document.getElementById('room');
    if (!roomImg) return;
    const frames = Array.from({ length: 31 }, (_, i) => `graphics/rooms/2a/foxxy/${i}.webp`);
    this.#animations.playSequence({
      frames,
      frameMs: 35,
      onFrame: (src) => {
        if (this.#engine.camera.currentRoom === '2a') {
          roomImg.src = src;
        }
      },
    });
  }
}
