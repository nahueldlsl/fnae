import { AnimatronicEntity } from './AnimatronicEntity.js';
import { StrategyFactory } from './MovementStrategies.js';

/**
 * AIManager (GRASP Controller / Creator / OCP) - Coordinates all configured
 * animatronics, hourly AI boosts, and rare Golden Freddy hallucination events.
 */
export class AIManager {
  constructor(eventBus, characterConfigs = [], gameConfig = {}, deps = {}) {
    this.#eventBus = eventBus;
    this.#rng = deps.rng || Math.random;
    this.#goldenFreddyCfg = gameConfig.goldenFreddy || { enabled: false };
    this.#entities = characterConfigs.map((cfg) => new AnimatronicEntity(cfg));
    this.#officeSystem = deps.officeSystem;
    this.#cameraSystem = deps.cameraSystem;
    this.#powerSystem = deps.powerSystem;
    this.#active = false;
    this.#goldenTimer = 0;
    this.#goldenPending = false;
  }

  #eventBus;
  #rng;
  #goldenFreddyCfg;
  #entities;
  #officeSystem;
  #cameraSystem;
  #powerSystem;
  #active;
  #goldenTimer;
  #goldenPending;

  get entities() {
    return this.#entities;
  }

  getEntity(id) {
    return this.#entities.find((e) => e.id === id) || null;
  }

  configureForNight(night, customLevels = null) {
    this.#active = true;
    this.#goldenPending = false;
    this.#goldenTimer = 0;
    const nightKey = String(night);

    for (const entity of this.#entities) {
      let level = 0;
      if (customLevels && Object.prototype.hasOwnProperty.call(customLevels, entity.id)) {
        level = Number(customLevels[entity.id]) || 0;
      } else {
        level = Number(entity.config.nightLevels?.[nightKey] ?? 0);
      }
      entity.reset(level);
    }
  }

  applyHourlyBoost(hour) {
    const key = String(hour);
    for (const entity of this.#entities) {
      const delta = Number(entity.config.hourlyBoost?.[key] ?? 0);
      if (delta !== 0) {
        entity.hourlyBonus += delta;
      }
    }
  }

  onMonitorStateChanged(open) {
    if (!this.#active) return;
    const ctx = this.#buildContext();
    for (const entity of this.#entities) {
      const strat = StrategyFactory.get(entity.strategyName);
      if (typeof strat.onMonitorStateChanged === 'function') {
        strat.onMonitorStateChanged(entity, open, ctx);
      }
    }
    if (open && this.#goldenPending) {
      this.#goldenPending = false;
      this.#goldenTimer = 0;
      this.#eventBus.emit('ai:goldenFreddyDismissed', {});
    }
  }

  onCameraSelected(roomId) {
    if (!this.#active) return;
    const ctx = this.#buildContext();
    for (const entity of this.#entities) {
      const strat = StrategyFactory.get(entity.strategyName);
      if (typeof strat.onCameraSelected === 'function') {
        strat.onCameraSelected(entity, roomId, ctx);
      }
    }

    if (
      this.#goldenFreddyCfg.enabled &&
      roomId === this.#goldenFreddyCfg.triggerRoom &&
      !this.#goldenPending &&
      this.#rng() < (this.#goldenFreddyCfg.chance ?? 0.015)
    ) {
      this.#goldenPending = true;
      this.#goldenTimer = (this.#goldenFreddyCfg.reactionWindowMs ?? 4500) / 1000;
      this.#eventBus.emit('ai:goldenFreddyAppeared', {
        sound: this.#goldenFreddyCfg.sound || 'XSCREAM2.wav',
      });
    }
  }

  stop() {
    this.#active = false;
    this.#goldenPending = false;
  }

  tick(dt = 1) {
    if (!this.#active) return;

    if (this.#goldenPending && !this.#cameraSystem.isOpen) {
      this.#goldenTimer -= dt;
      if (this.#goldenTimer <= 0) {
        this.#goldenPending = false;
        this.#active = false;
        this.#eventBus.emit('ai:goldenFreddyKill', {
          sound: this.#goldenFreddyCfg.sound || 'XSCREAM2.wav',
        });
        return;
      }
    }

    const ctx = this.#buildContext();
    for (const entity of this.#entities) {
      if (!this.#active) break;
      const strat = StrategyFactory.get(entity.strategyName);
      strat.tick(entity, dt, ctx);
    }
  }

  #buildContext() {
    return {
      rng: this.#rng,
      monitorOpen: this.#cameraSystem.isOpen,
      currentCameraRoom: this.#cameraSystem.currentRoom,
      isDoorClosed: (side) => this.#officeSystem.isDoorClosed(side),
      getDoorOccupant: (side) => this.#officeSystem.getDoorOccupant(side),
      setDoorOccupant: (side, charId) => this.#officeSystem.setDoorOccupant(side, charId),
      jamSide: (side) => this.#officeSystem.jamSide(side),
      consumePowerPercent: (pct) => this.#powerSystem.consumePercent(pct),
      forceCloseMonitor: () => {
        if (this.#cameraSystem.isOpen) {
          this.#cameraSystem.setMonitorOpen(false);
        }
      },
      emit: (evt, payload) => this.#eventBus.emit(evt, payload),
      notifyMoved: (entity, fromRoom, toRoom) => {
        this.#eventBus.emit('ai:moved', {
          characterId: entity.id,
          fromRoom,
          toRoom,
          coveStage: entity.coveStage,
        });
      },
      triggerJumpscare: (entity) => {
        if (!this.#active) return;
        this.#active = false;
        this.#eventBus.emit('ai:jumpscare', {
          characterId: entity.id,
          character: entity.config,
        });
      },
    };
  }
}
