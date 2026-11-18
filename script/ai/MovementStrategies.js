/**
 * MovementStrategies - Polymorphic AI strategies (OCP / Strategy / LSP).
 */

function rollAiOpportunity(aiLevel, rng) {
  if (aiLevel <= 0) return false;
  const roll = Math.floor(rng() * 20) + 1;
  return roll <= aiLevel;
}

function pickRandom(items, rng) {
  if (!items || items.length === 0) return null;
  return items[Math.floor(rng() * items.length)];
}

/**
 * Standard Roamer Strategy (Bonnie, Chica, and custom roaming characters).
 */
export class RoamerStrategy {
  tick(entity, dt, ctx) {
    if (entity.insideOffice) {
      if (!ctx.monitorOpen) {
        ctx.triggerJumpscare(entity);
        return;
      }
      entity.insideWaitTimer += dt;
      if (entity.insideWaitTimer >= 25) {
        ctx.forceCloseMonitor();
        ctx.triggerJumpscare(entity);
      }
      return;
    }

    const interval = entity.config.movementIntervalSec ?? 4.97;
    entity.movementTimer += dt;
    if (entity.movementTimer < interval) return;
    entity.movementTimer -= interval;

    if (entity.atDoor) {
      this.#handleAtDoor(entity, ctx);
      return;
    }

    if (!rollAiOpportunity(entity.effectiveAiLevel, ctx.rng)) return;

    const candidates = entity.getNextRooms();
    const target = pickRandom(candidates, ctx.rng);
    if (!target) return;

    if (target === 'office') {
      if (ctx.isDoorClosed(entity.side)) {
        const retreat = entity.config.retreatRoom || '1b';
        this.#moveToRoom(entity, retreat, ctx);
      } else {
        entity.atDoor = true;
        entity.doorWaitTicks = 0;
        ctx.setDoorOccupant(entity.side, entity.id);
        ctx.notifyMoved(entity, entity.currentRoom, 'door');
      }
      return;
    }

    this.#moveToRoom(entity, target, ctx);
  }

  #moveToRoom(entity, targetRoom, ctx) {
    const prevRoom = entity.currentRoom;
    entity.currentRoom = targetRoom;
    entity.roomVariant = ctx.rng() < 0.2 ? 1 : 0;
    ctx.notifyMoved(entity, prevRoom, targetRoom);

    if (targetRoom === '6' && entity.config.sounds?.kitchen?.length) {
      const snd = pickRandom(entity.config.sounds.kitchen, ctx.rng);
      ctx.emit('ai:sound', { sound: snd, volume: 0.6 });
    }
  }

  #handleAtDoor(entity, ctx) {
    if (ctx.isDoorClosed(entity.side)) {
      entity.atDoor = false;
      entity.doorWaitTicks = 0;
      ctx.setDoorOccupant(entity.side, null);
      const retreat = entity.config.retreatRoom || '1b';
      this.#moveToRoom(entity, retreat, ctx);
      return;
    }

    entity.doorWaitTicks += 1;
    const maxWait = entity.config.doorWaitChecks ?? 2;
    if (entity.doorWaitTicks >= maxWait) {
      if (ctx.monitorOpen) {
        entity.atDoor = false;
        entity.insideOffice = true;
        entity.insideWaitTimer = 0;
        ctx.setDoorOccupant(entity.side, null);
        ctx.jamSide(entity.side);
      } else {
        ctx.triggerJumpscare(entity);
      }
    }
  }
}

/**
 * Freddy Strategy - Stalls when watched or when CAM 4B is selected;
 * sneaks in from 4B if right door is open and monitor isn't holding him.
 */
export class FreddyStrategy {
  tick(entity, dt, ctx) {
    if (entity.insideOffice) {
      if (!ctx.monitorOpen) {
        ctx.triggerJumpscare(entity);
      }
      return;
    }

    const interval = entity.config.movementIntervalSec ?? 3.02;
    entity.movementTimer += dt;
    if (entity.movementTimer < interval) return;
    entity.movementTimer -= interval;

    if (!rollAiOpportunity(entity.effectiveAiLevel, ctx.rng)) return;

    const beingWatched =
      ctx.monitorOpen &&
      (ctx.currentCameraRoom === entity.currentRoom || ctx.currentCameraRoom === '4b');

    if (beingWatched) return;

    if (entity.currentRoom === '4b') {
      if (ctx.isDoorClosed(entity.side)) {
        const prev = entity.currentRoom;
        entity.currentRoom = '4a';
        ctx.notifyMoved(entity, prev, '4a');
      } else if (ctx.monitorOpen && ctx.currentCameraRoom !== '4b') {
        entity.insideOffice = true;
        ctx.notifyMoved(entity, '4b', 'office');
      } else if (!ctx.monitorOpen && ctx.rng() < 0.35) {
        ctx.triggerJumpscare(entity);
      }
      return;
    }

    const next = pickRandom(entity.getNextRooms(), ctx.rng);
    if (!next || next === 'office') return;

    const prev = entity.currentRoom;
    entity.currentRoom = next;
    ctx.notifyMoved(entity, prev, next);

    if (next === '6' && entity.config.sounds?.kitchen?.length) {
      ctx.emit('ai:sound', { sound: pickRandom(entity.config.sounds.kitchen, ctx.rng), volume: 0.6 });
    } else if (entity.config.sounds?.move?.length) {
      ctx.emit('ai:sound', { sound: pickRandom(entity.config.sounds.move, ctx.rng), volume: 0.5 });
    }
  }
}

/**
 * Cove Rusher Strategy (Foxy) - Stalled by ANY camera usage + random post-camera cooldown;
 * runs down CAM 2A and drains escalating power on closed left door.
 */
export class CoveRusherStrategy {
  onMonitorStateChanged(entity, monitorOpen, ctx) {
    if (!monitorOpen && entity.foxyPhase === 'cove') {
      entity.foxyStallTimer = 0.83 + ctx.rng() * 10.0;
    }
  }

  onCameraSelected(entity, roomId, ctx) {
    if (roomId === '2a' && entity.foxyPhase === 'ready') {
      this.#startSprint(entity, ctx);
    }
  }

  tick(entity, dt, ctx) {
    if (entity.foxyPhase === 'sprinting') {
      entity.foxySprintTimer -= dt;
      if (entity.foxySprintTimer <= 0) {
        this.#arriveAtDoor(entity, ctx);
      }
      return;
    }

    if (entity.foxyPhase === 'ready') {
      if (ctx.monitorOpen && ctx.currentCameraRoom === '2a') {
        this.#startSprint(entity, ctx);
        return;
      }
      entity.foxyAttackTimer -= dt;
      if (entity.foxyAttackTimer <= 0) {
        this.#arriveAtDoor(entity, ctx);
      }
      return;
    }

    // Stalled while monitor is up or during post-monitor lock
    if (ctx.monitorOpen) return;
    if (entity.foxyStallTimer > 0) {
      entity.foxyStallTimer = Math.max(0, entity.foxyStallTimer - dt);
      return;
    }

    const interval = entity.config.movementIntervalSec ?? 5.01;
    entity.movementTimer += dt;
    if (entity.movementTimer < interval) return;
    entity.movementTimer -= interval;

    if (!rollAiOpportunity(entity.effectiveAiLevel, ctx.rng)) return;

    if (entity.coveStage < 2) {
      entity.coveStage += 1;
      ctx.notifyMoved(entity, '1c', '1c');
      if (entity.config.sounds?.pirateSong && ctx.rng() < 0.45) {
        ctx.emit('ai:sound', { sound: entity.config.sounds.pirateSong, volume: 0.12 });
      }
    } else if (entity.coveStage === 2) {
      entity.coveStage = 3;
      entity.foxyPhase = 'ready';
      entity.foxyAttackTimer = 25;
      ctx.notifyMoved(entity, '1c', '2a');
    }
  }

  #startSprint(entity, ctx) {
    if (entity.foxyPhase === 'sprinting') return;
    entity.foxyPhase = 'sprinting';
    entity.foxySprintTimer = 1.8;
    ctx.emit('ai:foxySprinting', { characterId: entity.id });
    if (entity.config.sounds?.run) {
      ctx.emit('ai:sound', { sound: entity.config.sounds.run, volume: 0.85 });
    }
  }

  #arriveAtDoor(entity, ctx) {
    if (ctx.isDoorClosed(entity.side)) {
      const drainPercent = 1 + 5 * entity.foxyBangs;
      entity.foxyBangs += 1;
      ctx.consumePowerPercent(drainPercent);
      if (entity.config.sounds?.knock) {
        ctx.emit('ai:sound', { sound: entity.config.sounds.knock, volume: 0.85 });
      }
      entity.foxyPhase = 'cove';
      entity.coveStage = ctx.rng() < 0.5 ? 0 : 1;
      entity.currentRoom = '1c';
      entity.movementTimer = 0;
      ctx.notifyMoved(entity, '2a', '1c');
    } else {
      ctx.forceCloseMonitor();
      ctx.triggerJumpscare(entity);
    }
  }
}

export class StrategyFactory {
  static #registry = new Map([
    ['roamer', new RoamerStrategy()],
    ['freddy', new FreddyStrategy()],
    ['cove_rusher', new CoveRusherStrategy()],
  ]);

  static register(name, strategyInstance) {
    StrategyFactory.#registry.set(name, strategyInstance);
  }

  static get(name) {
    return StrategyFactory.#registry.get(name) || StrategyFactory.#registry.get('roamer');
  }
}
