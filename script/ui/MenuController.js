/**
 * MenuController (SRP) - Manages start overlay, intro logo, main menu,
 * 6 AM victory screen, and Game Over screen transitions.
 */
export class MenuController {
  constructor({
    audio,
    saveRepository,
    animations,
    timers,
    onStartNight,
    onOpenCustomNight,
    onResumeNight,
    onReturnToMenu,
  }) {
    this.#audio = audio;
    this.#save = saveRepository;
    this.#animations = animations;
    this.#timers = timers;
    this.#onStartNight = onStartNight;
    this.#onOpenCustomNight = onOpenCustomNight;
    this.#onResumeNight = onResumeNight;
    this.#onReturnToMenu = onReturnToMenu;
    this.#menuAnimInterval = null;
    this.#staticFadeTimer = null;
    this.#overlayDismissed = false;
    this.#isLaunching = false;
  }

  #audio;
  #save;
  #animations;
  #timers;
  #onStartNight;
  #onOpenCustomNight;
  #onResumeNight;
  #onReturnToMenu;
  #menuAnimInterval;
  #staticFadeTimer;
  #overlayDismissed;
  #isLaunching;

  init() {
    const startOverlay = document.getElementById('startoverlay');
    if (startOverlay) {
      startOverlay.addEventListener('click', () => this.#unlockAndStart());
    }

    const menuItems = [
      { id: 'newbutton', top: '57.5%', action: () => this.#startNewGame() },
      { id: 'continuebutton', top: '65.5%', action: () => this.#continueGame() },
      { id: '6thnight', top: '75.5%', action: () => this.#startSixthNight() },
      { id: 'customnight', top: '83.5%', action: () => this.#openCustomNight() },
    ];

    const arrows = document.getElementById('selectedarrows');
    for (const item of menuItems) {
      const el = document.getElementById(item.id);
      if (!el) continue;
      el.addEventListener('mouseenter', () => {
        if (arrows) arrows.style.top = item.top;
      });
      el.addEventListener('click', item.action);
    }

    const resumeBtn = document.getElementById('pause-resume');
    if (resumeBtn) {
      resumeBtn.addEventListener('click', () => {
        if (this.#onResumeNight) this.#onResumeNight();
      });
    }
    const muteBtn = document.getElementById('pause-mute');
    if (muteBtn) {
      muteBtn.addEventListener('click', () => {
        this.#audio.toggleMute();
        this.syncMuteButton();
      });
    }
    const backMenuBtn = document.getElementById('pause-menu');
    if (backMenuBtn) {
      backMenuBtn.addEventListener('click', () => {
        this.hidePauseOverlay();
        this.#audio.stopAll();
        this.#audio.stopAmbient();
        if (this.#onReturnToMenu) this.#onReturnToMenu();
        this.showMainMenu();
      });
    }

    this.#timers.setTimeout(() => this.#playIntro(), 1200);
  }

  showPauseOverlay() {
    this.syncMuteButton();
    const el = document.getElementById('pauseoverlay');
    if (el) el.style.display = 'flex';
  }

  hidePauseOverlay() {
    const el = document.getElementById('pauseoverlay');
    if (el) el.style.display = 'none';
  }

  syncMuteButton() {
    const muteBtn = document.getElementById('pause-mute');
    if (muteBtn) {
      muteBtn.textContent = this.#audio.isMuted ? 'SONIDO: SILENCIADO (M)' : 'SONIDO: ACTIVO (M)';
    }
  }

  #unlockAndStart() {
    if (this.#overlayDismissed) return;
    this.#overlayDismissed = true;
    this.#audio.unlock();

    const ov = document.getElementById('startoverlay');
    if (ov) {
      ov.style.transition = 'opacity 0.6s ease-out';
      ov.style.opacity = '0';
      this.#timers.setTimeout(() => {
        ov.style.display = 'none';
      }, 600);
    }

    const vid = document.getElementById('mainmenustaticimg');
    if (vid) vid.play().catch(() => {});

    const menuEl = document.getElementById('mainmenu');
    if (menuEl && window.getComputedStyle(menuEl).display !== 'none') {
      this.#audio.play('static2.wav', 0.3, true);
    }
  }

  #playIntro() {
    const logo = document.getElementById('amduatlogo');
    const transitionEl = document.getElementById('transistionanimation');
    this.#animations.playTransition(transitionEl);
    if (logo) {
      logo.style.display = 'block';
      logo.style.transition = 'opacity 0.25s ease';
      logo.style.opacity = '1';
      this.#timers.setTimeout(() => {
        this.#animations.playTransition(transitionEl);
        logo.style.opacity = '0';
        this.#timers.setTimeout(() => {
          logo.style.display = 'none';
          this.showMainMenu();
        }, 1800);
      }, 4200);
    } else {
      this.showMainMenu();
    }
  }

  showMainMenu() {
    this.#isLaunching = false;
    this.#stopMenuAnimations();
    this.#hideAllScreens();

    const menuEl = document.getElementById('mainmenu');
    const menuStatic = document.getElementById('mainmenustaticimg');
    if (menuEl) menuEl.style.display = 'block';
    if (menuStatic) {
      menuStatic.style.display = 'block';
      menuStatic.play().catch(() => {});
    }

    const stars = this.#save.getStars();
    for (let i = 1; i <= 3; i++) {
      const starEl = document.getElementById(`achievement${i}`);
      if (starEl) starEl.style.display = i <= stars ? 'block' : 'none';
    }

    // TEMP: desbloqueo temporal de todas las noches (Continue Noche 5, 6th Night y Custom Night)
    const savedNight = 7;
    const continueBtn = document.getElementById('continuebutton');
    const continueNight = document.getElementById('continuebuttonnight');
    const continueNum = document.getElementById('continuebuttonnightnumber');
    const sixthBtn = document.getElementById('6thnight');
    const customBtn = document.getElementById('customnight');

    if (savedNight > 1) {
      if (continueBtn) continueBtn.style.display = 'block';
      if (continueNight) continueNight.style.display = 'block';
      if (continueNum) {
        continueNum.style.display = 'block';
        continueNum.src = `graphics/mainmenu/littletext/${Math.min(5, savedNight)}.png`;
      }
      if (savedNight >= 6 && sixthBtn) sixthBtn.style.display = 'block';
      if (savedNight >= 7 && customBtn) customBtn.style.display = 'block';
    } else {
      if (continueBtn) continueBtn.style.display = 'none';
      if (continueNight) continueNight.style.display = 'none';
      if (continueNum) continueNum.style.display = 'none';
      if (sixthBtn) sixthBtn.style.display = 'none';
      if (customBtn) customBtn.style.display = 'none';
    }

    if (this.#overlayDismissed) {
      this.#audio.play('static2.wav', 0.3, true);
    }

    this.#startMenuGlitchLoop();
    this.#animateMenuStatic();
  }

  #startMenuGlitchLoop() {
    const faceEl = document.getElementById('mainmenufazbearanim');
    if (!faceEl) return;

    const scheduleFlicker = (count, stepMs, mask) => {
      for (let i = 0; i < count; i++) {
        this.#timers.setTimeout(() => {
          faceEl.src = `graphics/mainmenu/${i & mask}.webp`;
        }, stepMs * (i + 1));
      }
    };

    this.#menuAnimInterval = this.#timers.setInterval(() => {
      const rand = Math.random();
      if (rand > 0.8) {
        scheduleFlicker(6, 65, 3);
      } else if (rand > 0.6) {
        scheduleFlicker(7, 45, 2);
      } else if (rand > 0.4) {
        scheduleFlicker(7, 25, 1);
      } else {
        faceEl.src = 'graphics/mainmenu/0.webp';
      }
    }, 1000);
  }

  #animateMenuStatic() {
    const el = document.getElementById('mainmenustaticimg');
    if (!el) return;
    let high = false;
    this.#staticFadeTimer = this.#timers.setInterval(() => {
      high = !high;
      el.style.transition = 'opacity 1.8s ease-in-out';
      el.style.opacity = high ? '0.6' : '0.28';
    }, 2000);
  }

  #stopMenuAnimations() {
    if (this.#menuAnimInterval != null) {
      this.#timers.clearInterval(this.#menuAnimInterval);
      this.#menuAnimInterval = null;
    }
    if (this.#staticFadeTimer != null) {
      this.#timers.clearInterval(this.#staticFadeTimer);
      this.#staticFadeTimer = null;
    }
  }

  #hideAllScreens() {
    const ids = [
      'mainmenu',
      'night7interface',
      'newgamebg',
      'body',
      'timekeeper',
      'openclosecamera',
      'power',
      'nightover',
      'gameover',
      'gameoverstaticimg',
      'loadingicon',
      'camerafeedanimation',
      'transistionanimation',
      'amduatlogo',
      'officecameraleft',
      'officecameraright',
      'goldenfreddy-overlay',
      'pauseoverlay',
    ];
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    }
  }

  #startNewGame() {
    if (this.#isLaunching) return;
    this.#isLaunching = true;
    this.#stopMenuAnimations();
    this.#audio.stopAll();
    this.#save.setNight(1);
    const bg = document.getElementById('newgamebg');
    if (bg) {
      bg.style.display = 'block';
      bg.style.opacity = '0';
      bg.style.transition = 'opacity 1s ease';
      requestAnimationFrame(() => {
        bg.style.opacity = '1';
      });
      this.#timers.setTimeout(() => this.#launchWithLoading(1), 4500);
    } else {
      this.#launchWithLoading(1);
    }
  }

  #continueGame() {
    if (this.#isLaunching) return;
    this.#isLaunching = true;
    this.#stopMenuAnimations();
    this.#audio.stopAll();
    // TEMP: usar noche 5 en Continue mientras esté el desbloqueo temporal
    const nightToPlay = Math.min(5, 7);
    this.#launchWithLoading(nightToPlay);
  }

  #startSixthNight() {
    if (this.#isLaunching) return;
    this.#isLaunching = true;
    this.#stopMenuAnimations();
    this.#audio.stopAll();
    this.#launchWithLoading(6);
  }

  #openCustomNight() {
    if (this.#isLaunching) return;
    this.#stopMenuAnimations();
    this.#hideAllScreens();
    const vid = document.getElementById('gameoverstaticimg');
    if (vid) vid.pause();
    this.#onOpenCustomNight();
  }

  launchNight(nightNumber, customLevels = null) {
    if (this.#isLaunching) return;
    this.#isLaunching = true;
    this.#stopMenuAnimations();
    this.#audio.stopAll();
    this.#launchWithLoading(nightNumber, customLevels);
  }

  #launchWithLoading(nightNumber, customLevels = null) {
    this.#hideAllScreens();
    const transitionEl = document.getElementById('transistionanimation');
    this.#animations.playTransition(transitionEl);

    const loadingEl = document.getElementById('loadingicon');
    if (loadingEl) {
      loadingEl.src = `graphics/loading/loading${Math.max(1, Math.min(7, nightNumber))}.png`;
      loadingEl.style.display = 'block';
    }

    this.#timers.setTimeout(() => {
      this.#isLaunching = false;
      if (loadingEl) loadingEl.style.display = 'none';
      this.#onStartNight(nightNumber, customLevels);
    }, 3000);
  }

  showNightWonScreen() {
    this.#audio.stopAll();
    this.#audio.stopAmbient();
    this.#hideAllScreens();

    const nightOverEl = document.getElementById('nightover');
    const amEl = document.getElementById('nightoveram');
    const n5El = document.getElementById('nightover5');
    const n6El = document.getElementById('nightover6');

    if (nightOverEl) nightOverEl.style.display = 'block';
    if (amEl) amEl.style.top = '80px';
    if (n5El) {
      n5El.style.transition = 'none';
      n5El.style.top = '80px';
    }
    if (n6El) {
      n6El.style.transition = 'none';
      n6El.style.top = '20px';
    }

    this.#audio.play('chimes 2.wav', 0.7);

    this.#timers.setTimeout(() => {
      if (n5El) {
        n5El.style.transition = 'top 6s linear';
        n5El.style.top = '140px';
      }
      if (n6El) {
        n6El.style.transition = 'top 6s linear';
        n6El.style.top = '80px';
      }
      this.#timers.setTimeout(() => {
        this.#audio.play('CROWD_SMALL_CHIL_EC049202.wav', 0.7);
      }, 6000);
    }, 1500);

    this.#timers.setTimeout(() => {
      this.showMainMenu();
    }, 10000);
  }

  showGameOverSequence(delayStaticMs = 950) {
    this.#timers.setTimeout(() => {
      this.#audio.stopAll();
      this.#audio.stopAmbient();
      const staticVid = document.getElementById('gameoverstaticimg');
      if (staticVid) {
        staticVid.style.display = 'block';
        staticVid.style.opacity = '1';
        staticVid.play().catch(() => {});
      }

      this.#timers.setTimeout(() => {
        if (staticVid) {
          staticVid.pause();
          staticVid.style.display = 'none';
        }
        this.#hideAllScreens();
        const goEl = document.getElementById('gameover');
        if (goEl) {
          goEl.style.display = 'block';
          goEl.style.opacity = '0';
          goEl.style.transition = 'opacity 2s ease';
          requestAnimationFrame(() => {
            goEl.style.opacity = '1';
          });
        }
        this.#timers.setTimeout(() => {
          this.showMainMenu();
        }, 5000);
      }, 5500);
    }, delayStaticMs);
  }
}
