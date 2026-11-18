import { EventBus } from './core/EventBus.js';
import { TimerRegistry } from './core/TimerRegistry.js';
import { SaveRepository } from './core/SaveRepository.js';
import { NightClock } from './systems/NightClock.js';
import { PowerSystem } from './systems/PowerSystem.js';
import { OfficeSystem } from './systems/OfficeSystem.js';
import { CameraSystem } from './systems/CameraSystem.js';
import { AIManager } from './ai/AIManager.js';

/**
 * GameEngine (Singleton / GRASP Controller) - Central simulation orchestrator.
 * Owns game lifecycle, night transitions, power-outage survival, and clean resets.
 */
export class GameEngine {
  static #instance = null;

  static getInstance(deps = {}) {
    if (!GameEngine.#instance) {
      GameEngine.#instance = new GameEngine(deps);
    }
    return GameEngine.#instance;
  }

  static resetInstance() {
    if (GameEngine.#instance) {
      GameEngine.#instance.destroy();
      GameEngine.#instance = null;
    }
  }

  constructor({
    gameConfig = {},
    characterConfigs = [],
    eventBus = EventBus.getInstance(),
    saveRepository = SaveRepository.getInstance(),
    timers = new TimerRegistry(),
    rng = Math.random,
  } = {}) {
    this.eventBus = eventBus;
    this.saveRepository = saveRepository;
    this.timers = timers;
    this.gameConfig = gameConfig;
    this.characterConfigs = characterConfigs;
    this.rng = rng;

    this.clock = new NightClock(this.eventBus, gameConfig.night);
    this.power = new PowerSystem(this.eventBus, gameConfig.power);
    this.office = new OfficeSystem(this.eventBus);
    this.camera = new CameraSystem(this.eventBus, gameConfig.rooms || []);
    this.ai = new AIManager(this.eventBus, characterConfigs, gameConfig, {
      rng,
      officeSystem: this.office,
      cameraSystem: this.camera,
      powerSystem: this.power,
    });

    this.#currentNight = 1;
    this.#isAll20Mode = false;
    this.#phase = 'menu'; // 'menu' | 'playing' | 'powerout' | 'ended'
    this.#tickIntervalId = null;

    this.#bindDomainEvents();
  }

  #currentNight;
  #isAll20Mode;
  #phase;
  #tickIntervalId;

  get currentNight() {
    return this.#currentNight;
  }

  get phase() {
    return this.#phase;
  }

  get isAll20Mode() {
    return this.#isAll20Mode;
  }

  #bindDomainEvents() {
    this.eventBus.on('clock:hourChanged', ({ hour }) => {
      if (this.#currentNight < 7 && this.gameConfig.night?.hourlyBoostsAt?.[String(hour)]) {
        this.ai.applyHourlyBoost(hour);
      }
    });

    this.eventBus.on('clock:sixAM', () => {
      this.#handleVictory();
    });

    this.eventBus.on('power:depleted', () => {
      this.#handlePowerOutage();
    });

    this.eventBus.on('office:doorChanged', () => this.#syncPowerUsage());
    this.eventBus.on('office:lightChanged', () => this.#syncPowerUsage());
    this.eventBus.on('camera:toggled', ({ open }) => {
      this.#syncPowerUsage();
      this.ai.onMonitorStateChanged(open);
    });
    this.eventBus.on('camera:roomChanged', ({ room }) => {
      this.ai.onCameraSelected(room);
    });

    this.eventBus.on('ai:jumpscare', (payload) => {
      this.#handleJumpscare(payload);
    });

    this.eventBus.on('ai:goldenFreddyKill', ({ sound }) => {
      const freddyCfg = this.characterConfigs.find((c) => c.id === 'freddy') || this.characterConfigs[0];
      this.#handleJumpscare({
        characterId: 'golden_freddy',
        character: freddyCfg,
        overrideSound: sound,
      });
    });
  }

  #syncPowerUsage() {
    this.power.recalculateUsage({
      leftDoorClosed: this.office.isDoorClosed('left'),
      rightDoorClosed: this.office.isDoorClosed('right'),
      activeLightSide: this.office.getActiveLightSide(),
      monitorOpen: this.camera.isOpen,
    });
  }

  startNight(nightNumber = 1, customLevels = null, { autoStartLoop = true } = {}) {
    this.resetSimulation();
    this.#currentNight = Math.max(1, Math.min(7, Number(nightNumber) || 1));
    this.#phase = 'playing';

    if (customLevels && this.characterConfigs.length > 0) {
      this.#isAll20Mode = this.characterConfigs.every(
        (c) => Number(customLevels[c.id] ?? 0) === 20
      );
    } else {
      this.#isAll20Mode = false;
    }

    this.clock.reset();
    this.power.reset(this.#currentNight);
    this.office.reset();
    this.camera.reset();
    this.ai.configureForNight(this.#currentNight, customLevels);
    this.#syncPowerUsage();

    this.eventBus.emit('game:nightStarted', {
      night: this.#currentNight,
      isAll20Mode: this.#isAll20Mode,
    });

    if (autoStartLoop) {
      this.#tickIntervalId = this.timers.setInterval(() => this.step(0.25), 250);
    }
  }

  step(deltaSec = 0.25) {
    if (this.#phase === 'playing') {
      this.clock.tick(deltaSec);
      if (this.#phase !== 'playing') return;
      this.power.tick(deltaSec);
      if (this.#phase !== 'playing') return;
      this.ai.tick(deltaSec);
    } else if (this.#phase === 'powerout') {
      // Clock continues ticking so the player can still survive until 6 AM!
      this.clock.tick(deltaSec);
    }
  }

  resetSimulation() {
    if (this.#tickIntervalId != null) {
      this.timers.clearInterval(this.#tickIntervalId);
      this.#tickIntervalId = null;
    }
    this.timers.clearAll();
    this.ai.stop();
    this.clock.reset();
    this.office.reset();
    this.camera.reset();
    this.#phase = 'menu';
  }

  destroy() {
    this.resetSimulation();
  }

  #handlePowerOutage() {
    if (this.#phase !== 'playing') return;
    this.#phase = 'powerout';
    this.ai.stop();
    if (this.camera.isOpen) {
      this.camera.setMonitorOpen(false);
    }
    this.office.powerDown();

    const minDelay = this.gameConfig.power?.powerOutageMinDelaySec ?? 10;
    const maxDelay = this.gameConfig.power?.powerOutageMaxDelaySec ?? 45;
    const totalOutageSec = minDelay + this.rng() * (maxDelay - minDelay);
    const musicDelayMs = Math.round(totalOutageSec * 200);
    const killDelayMs = Math.round(totalOutageSec * 1000);

    this.eventBus.emit('game:powerOutageStarted', {
      musicDelayMs,
      killDelayMs,
    });

    this.timers.setTimeout(() => {
      if (this.#phase !== 'powerout') return;
      const freddyCfg = this.characterConfigs.find((c) => c.id === 'freddy') || this.characterConfigs[0];
      this.#handleJumpscare({
        characterId: freddyCfg?.id || 'freddy',
        character: freddyCfg,
      });
    }, killDelayMs);
  }

  #handleVictory() {
    if (this.#phase === 'ended') return;
    this.#phase = 'ended';
    this.resetSimulation();
    const saveState = this.saveRepository.recordNightVictory(
      this.#currentNight,
      this.#isAll20Mode
    );
    this.eventBus.emit('game:nightWon', {
      completedNight: this.#currentNight,
      saveState,
    });
  }

  #handleJumpscare(payload) {
    if (this.#phase === 'ended') return;
    this.#phase = 'ended';
    this.resetSimulation();
    this.eventBus.emit('game:jumpscare', payload);
  }
}
