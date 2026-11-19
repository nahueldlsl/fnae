/**
 * OfficeView (SRP / DRY) - Controls office panning, left/right door & light buttons,
 * fan animation, power/clock HUD, and power outage visuals.
 */
export class OfficeView {
  constructor({ engine, audio, animations, timers }) {
    this.#engine = engine;
    this.#audio = audio;
    this.#animations = animations;
    this.#timers = timers;
    this.#officeX = 0;
    this.#panDirection = 0;
    this.#panRafId = null;
    this.#fanInterval = null;
    this.#powerOutageInterval = null;
    this.#scaredOccupant = { left: null, right: null };
    this.#characterAssets = new Map(
      (engine.characterConfigs || []).map((c) => [c.id, c])
    );
  }

  #engine;
  #audio;
  #animations;
  #timers;
  #officeX;
  #panDirection;
  #panRafId;
  #fanInterval;
  #powerOutageInterval;
  #scaredOccupant;
  #characterAssets;

  init() {
    for (const side of ['left', 'right']) {
      const doorBtn = document.getElementById(`doorbuttons${side}_door`);
      const lightBtn = document.getElementById(`doorbuttons${side}_light`);
      if (doorBtn) {
        doorBtn.addEventListener('click', () => {
          if (this.#engine.phase !== 'playing' || this.#engine.camera.isOpen) return;
          if (this.#engine.office.toggleDoor(side)) {
            this.#audio.play('SFXBible_12478.wav', 0.25);
          } else {
            this.#audio.play('error.wav', 0.5);
          }
        });
      }
      if (lightBtn) {
        lightBtn.addEventListener('click', () => {
          if (this.#engine.phase !== 'playing' || this.#engine.camera.isOpen) return;
          if (!this.#engine.office.toggleLight(side)) {
            this.#audio.play('error.wav', 0.5);
          }
        });
      }
    }

    const leftZone = document.getElementById('officecameraleft');
    const rightZone = document.getElementById('officecameraright');
    if (leftZone) {
      leftZone.addEventListener('mouseenter', () => {
        if (this.#engine.phase === 'playing' || this.#engine.phase === 'powerout') {
          this.#setPanDirection(-1);
        }
      });
      leftZone.addEventListener('mouseleave', () => this.#setPanDirection(0));
    }
    if (rightZone) {
      rightZone.addEventListener('mouseenter', () => {
        if (this.#engine.phase === 'playing' || this.#engine.phase === 'powerout') {
          this.#setPanDirection(1);
        }
      });
      rightZone.addEventListener('mouseleave', () => this.#setPanDirection(0));
    }

    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      const key = e.key.toLowerCase();

      if (key === 'escape') {
        if (this.#engine.phase === 'playing' || this.#engine.phase === 'paused') {
          e.preventDefault();
          this.#engine.togglePause();
        }
        return;
      }

      if (key === 'm') {
        const muted = this.#audio.toggleMute();
        this.#engine.eventBus.emit('audio:muteChanged', { muted });
        return;
      }

      if (this.#engine.phase !== 'playing') return;

      if (e.code === 'Space') {
        e.preventDefault();
        this.#engine.camera.toggleMonitor();
        return;
      }

      if (this.#engine.camera.isOpen) return;

      if (key === 'q') {
        if (this.#engine.office.toggleDoor('left')) {
          this.#audio.play('SFXBible_12478.wav', 0.25);
        } else {
          this.#audio.play('error.wav', 0.5);
        }
      } else if (key === 'e') {
        if (this.#engine.office.toggleDoor('right')) {
          this.#audio.play('SFXBible_12478.wav', 0.25);
        } else {
          this.#audio.play('error.wav', 0.5);
        }
      } else if (key === 'a') {
        if (!this.#engine.office.toggleLight('left')) {
          this.#audio.play('error.wav', 0.5);
        }
      } else if (key === 'd') {
        if (!this.#engine.office.toggleLight('right')) {
          this.#audio.play('error.wav', 0.5);
        }
      }
    });

    const bus = this.#engine.eventBus;
    bus.on('game:nightStarted', ({ night }) => this.showForNight(night));
    bus.on('game:paused', () => this.#setPanDirection(0));
    bus.on('game:returnedToMenu', () => this.stopLoops());
    bus.on('office:doorChanged', ({ side, closed, lightOn }) => {
      this.#animations.playDoor(side, closed);
      this.#updateButtonPanel(side, closed, lightOn);
    });
    bus.on('office:lightChanged', ({ side, on, doorClosed, occupant }) => {
      this.#updateButtonPanel(side, doorClosed, on);
      this.#renderOfficeBackground(side, on, occupant);
    });
    bus.on('office:occupantChanged', ({ side, occupant, lightOn }) => {
      if (!occupant || this.#scaredOccupant[side] !== occupant) {
        this.#scaredOccupant[side] = null;
      }
      if (lightOn) {
        this.#renderOfficeBackground(side, true, occupant);
      }
    });
    bus.on('power:updated', ({ percent, usageBars }) => this.#renderPower(percent, usageBars));
    bus.on('power:usageChanged', ({ usageBars }) => this.#renderPowerUsage(usageBars));
    bus.on('clock:hourChanged', ({ hour }) => this.#renderHour(hour));
    bus.on('game:powerOutageStarted', (payload) => this.#startPowerOutage(payload));
    bus.on('ai:goldenFreddyAppeared', ({ sound }) => {
      this.#audio.play(sound, 0.7);
      const gfOverlay = document.getElementById('goldenfreddy-overlay');
      if (gfOverlay) gfOverlay.style.display = 'block';
    });
    bus.on('ai:goldenFreddyDismissed', () => {
      const gfOverlay = document.getElementById('goldenfreddy-overlay');
      if (gfOverlay) gfOverlay.style.display = 'none';
    });
    bus.on('game:jumpscare', (payload) => this.#playJumpscare(payload));
  }

  showForNight(night) {
    this.stopLoops();
    this.#officeX = 0;
    this.#scaredOccupant = { left: null, right: null };
    const officeEl = document.getElementById('office');
    if (officeEl) officeEl.style.transform = 'translateX(0px)';

    const showIds = [
      'body',
      'timekeeper',
      'openclosecamera',
      'power',
      'fan',
      'doorbuttonsleft',
      'doorbuttonsright',
      'doorleft',
      'doorright',
      'officecameraright',
    ];
    for (const id of showIds) {
      const el = document.getElementById(id);
      if (el) el.style.display = 'block';
    }
    const leftPanZone = document.getElementById('officecameraleft');
    if (leftPanZone) leftPanZone.style.display = 'none';

    const gfOverlay = document.getElementById('goldenfreddy-overlay');
    if (gfOverlay) gfOverlay.style.display = 'none';

    const officeMain = document.getElementById('officemain');
    if (officeMain) {
      officeMain.style.display = 'block';
      officeMain.style.backgroundImage = "url('graphics/rooms/office/0.webp')";
    }

    const doorLeft = document.getElementById('doorleft');
    const doorRight = document.getElementById('doorright');
    if (doorLeft) doorLeft.src = 'graphics/rooms/office/doors/left/0.webp';
    if (doorRight) doorRight.src = 'graphics/rooms/office/doors/right/0.webp';

    this.#updateButtonPanel('left', false, false);
    this.#updateButtonPanel('right', false, false);

    const nightImg = document.getElementById('timenightnumber');
    if (nightImg) {
      nightImg.src = `graphics/camera/ui/${Math.max(1, Math.min(7, night))}.png`;
    }
    this.#renderHour(0);
    this.#renderPower(100, 1);
    this.#startFan();
  }

  stopLoops() {
    this.#setPanDirection(0);
    if (this.#fanInterval != null) {
      globalThis.clearInterval(this.#fanInterval);
      this.#fanInterval = null;
    }
    if (this.#powerOutageInterval != null) {
      globalThis.clearInterval(this.#powerOutageInterval);
      this.#powerOutageInterval = null;
    }
  }

  #setPanDirection(dir) {
    this.#panDirection = dir;
    if (dir === 0 && this.#panRafId != null) {
      cancelAnimationFrame(this.#panRafId);
      this.#panRafId = null;
      return;
    }
    if (dir !== 0 && this.#panRafId == null) {
      const step = () => {
        const maxPan = Math.max(120, Math.round(window.innerWidth * 0.22));
        this.#officeX = Math.max(0, Math.min(maxPan, this.#officeX + this.#panDirection * 12));
        const officeEl = document.getElementById('office');
        if (officeEl) {
          officeEl.style.transform = `translateX(-${this.#officeX}px)`;
        }
        const leftZone = document.getElementById('officecameraleft');
        const rightZone = document.getElementById('officecameraright');
        if (leftZone) leftZone.style.display = this.#officeX <= 0 ? 'none' : 'block';
        if (rightZone) rightZone.style.display = this.#officeX >= maxPan ? 'none' : 'block';

        if (this.#panDirection !== 0) {
          this.#panRafId = requestAnimationFrame(step);
        } else {
          this.#panRafId = null;
        }
      };
      this.#panRafId = requestAnimationFrame(step);
    }
  }

  #startFan() {
    const fanEl = document.getElementById('fan');
    if (!fanEl) return;
    let frame = 1;
    this.#fanInterval = globalThis.setInterval(() => {
      frame = (frame % 3) + 1;
      fanEl.src = `graphics/rooms/office/fan_${frame}.webp`;
    }, 35);
  }

  #updateButtonPanel(side, closed, lightOn) {
    const panel = document.getElementById(`doorbuttons${side}`);
    if (!panel) return;
    // 1: open/off, 2: open/light, 3: closed/off, 4: closed/light
    const stateIdx = (closed ? 2 : 0) + (lightOn ? 1 : 0) + 1;
    panel.style.backgroundImage = `url('graphics/rooms/office/buttons/button${side}_${stateIdx}.webp')`;
  }

  #renderOfficeBackground(side, lightOn, occupantId) {
    const officeMain = document.getElementById('officemain');
    if (!officeMain) return;
    if (!lightOn) {
      officeMain.style.backgroundImage = "url('graphics/rooms/office/0.webp')";
      return;
    }

    if (occupantId) {
      const charCfg = this.#characterAssets.get(occupantId);
      const customLight = charCfg?.assets?.doorLightFrame;
      if (customLight) {
        officeMain.style.backgroundImage = `url('${customLight}')`;
        if (this.#scaredOccupant[side] !== occupantId) {
          this.#scaredOccupant[side] = occupantId;
          this.#audio.play(charCfg.sounds?.windowscare || 'windowscare.wav', 0.65);
        }
        return;
      }
    }
    officeMain.style.backgroundImage = `url('graphics/rooms/office/0_light${side}.webp')`;
  }

  #renderPower(percent, usageBars) {
    const d1 = document.getElementById('numberone');
    const d2 = document.getElementById('numbertwo');
    const d3 = document.getElementById('numberthree');
    const blank = 'graphics/rooms/office/cameraposition.webp';
    const clamped = Math.max(0, Math.min(100, Math.round(percent)));
    const str = String(clamped);

    if (d1 && d2 && d3) {
      if (clamped >= 100) {
        d1.src = 'graphics/camera/ui/powernumbers/1.png';
        d2.src = 'graphics/camera/ui/powernumbers/0.png';
        d3.src = 'graphics/camera/ui/powernumbers/0.png';
      } else if (clamped >= 10) {
        d1.src = `graphics/camera/ui/powernumbers/${str[0]}.png`;
        d2.src = `graphics/camera/ui/powernumbers/${str[1]}.png`;
        d3.src = blank;
      } else {
        d1.src = `graphics/camera/ui/powernumbers/${str[0]}.png`;
        d2.src = blank;
        d3.src = blank;
      }
    }
    this.#renderPowerUsage(usageBars);
  }

  #renderPowerUsage(usageBars) {
    const usageEl = document.getElementById('powerusage');
    if (usageEl) {
      const clamped = Math.max(1, Math.min(5, usageBars));
      usageEl.src = `graphics/camera/power${clamped}.png`;
    }
  }

  #renderHour(hour) {
    const hourEl = document.getElementById('timehour');
    const extraEl = document.getElementById('timehourextra');
    if (!hourEl || !extraEl) return;

    if (hour <= 0) {
      hourEl.style.display = 'block';
      hourEl.src = 'graphics/camera/ui/time1.png';
      extraEl.src = 'graphics/camera/ui/time2.png';
    } else {
      hourEl.style.display = 'none';
      extraEl.src = `graphics/camera/ui/time${Math.min(6, hour)}.png`;
    }
  }

  #startPowerOutage({ musicDelayMs }) {
    this.stopLoops();
    this.#audio.stopAmbient();
    this.#audio.play('powerdown.wav', 0.7);

    const hideIds = [
      'fan',
      'timekeeper',
      'power',
      'doorbuttonsleft',
      'doorbuttonsright',
      'openclosecamera',
    ];
    for (const id of hideIds) {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    }

    const officeMain = document.getElementById('officemain');
    if (officeMain) {
      officeMain.style.backgroundImage = "url('graphics/rooms/office/powerout0.webp')";
    }

    this.#timers.setTimeout(() => {
      if (this.#engine.phase !== 'powerout') return;
      this.#audio.play('freddy/poweroutmusic.ogg', 0.65);
      let toggle = 0;
      this.#powerOutageInterval = globalThis.setInterval(() => {
        if (this.#engine.phase !== 'powerout') return;
        toggle = toggle ^ 1;
        if (officeMain) {
          officeMain.style.backgroundImage = `url('graphics/rooms/office/powerout${toggle}.webp')`;
        }
      }, 380);
    }, musicDelayMs);
  }

  #playJumpscare(payload) {
    this.stopLoops();
    this.#audio.stopAll();
    this.#audio.stopAmbient();

    const hideIds = [
      'fan',
      'doorbuttonsleft',
      'doorbuttonsright',
      'doorright',
      'doorleft',
      'officecameraleft',
      'officecameraright',
      'openclosecamera',
      'timekeeper',
      'power',
      'camerafeed',
      'goldenfreddy-overlay',
    ];
    for (const id of hideIds) {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    }

    const officeMain = document.getElementById('officemain');
    if (officeMain) officeMain.style.display = 'block';

    const charCfg = payload?.character;
    const scream = payload?.overrideSound || charCfg?.assets?.jumpscareSound || 'XSCREAM.wav';
    this.#audio.play(scream, 0.85);
    this.#animations.playJumpscare(charCfg);
  }
}
