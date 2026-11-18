/**
 * PowerSystem (SRP) - Manages FNAF 1 battery units (999 = 99.9%),
 * active usage bars (1..5), passive night drain, and power outage trigger.
 */
export class PowerSystem {
  constructor(eventBus, config = {}) {
    this.#eventBus = eventBus;
    this.#initialUnits = config.initialUnits ?? 999;
    this.#usageUnitPerBarPerSec = config.usageUnitPerBarPerSec ?? 1.04;
    this.#passiveDrainIntervalSec = config.passiveDrainIntervalSec || {
      1: 0,
      2: 6,
      3: 5,
      4: 4,
      5: 3,
      6: 3,
      7: 3,
    };
    this.reset(1);
  }

  #eventBus;
  #initialUnits;
  #usageUnitPerBarPerSec;
  #passiveDrainIntervalSec;
  #units = 999;
  #usageBars = 1;
  #night = 1;
  #passiveTimer = 0;
  #depleted = false;

  get units() {
    return this.#units;
  }

  get percent() {
    if (this.#units <= 0) return 0;
    return Math.min(100, Math.ceil(this.#units / 10));
  }

  get usageBars() {
    return this.#usageBars;
  }

  get isDepleted() {
    return this.#depleted;
  }

  reset(night = 1) {
    this.#night = Number(night) || 1;
    this.#units = this.#initialUnits;
    this.#usageBars = 1;
    this.#passiveTimer = 0;
    this.#depleted = false;
    this.#emitUpdate();
  }

  setUsageBars(bars) {
    const clamped = Math.max(1, Math.min(5, Math.round(bars)));
    if (clamped !== this.#usageBars) {
      this.#usageBars = clamped;
      this.#eventBus.emit('power:usageChanged', { usageBars: this.#usageBars });
    }
  }

  recalculateUsage({ leftDoorClosed, rightDoorClosed, activeLightSide, monitorOpen }) {
    const activeDevices =
      (leftDoorClosed ? 1 : 0) +
      (rightDoorClosed ? 1 : 0) +
      (activeLightSide ? 1 : 0) +
      (monitorOpen ? 1 : 0);
    this.setUsageBars(1 + activeDevices);
  }

  consumePercent(percentAmount) {
    if (this.#depleted) return;
    this.#units = Math.max(0, this.#units - percentAmount * 10);
    this.#emitUpdate();
    this.#checkDepletion();
  }

  tick(deltaSec = 1) {
    if (this.#depleted) return;

    const activeDrain = this.#usageBars * this.#usageUnitPerBarPerSec * deltaSec;
    this.#units -= activeDrain;

    const passiveInterval = this.#passiveDrainIntervalSec[String(this.#night)] ?? 0;
    if (passiveInterval > 0) {
      this.#passiveTimer += deltaSec;
      while (this.#passiveTimer >= passiveInterval) {
        this.#passiveTimer -= passiveInterval;
        this.#units -= 1;
      }
    }

    if (this.#units < 0) this.#units = 0;
    this.#emitUpdate();
    this.#checkDepletion();
  }

  #emitUpdate() {
    this.#eventBus.emit('power:updated', {
      units: this.#units,
      percent: this.percent,
      usageBars: this.#usageBars,
    });
  }

  #checkDepletion() {
    if (!this.#depleted && this.#units <= 0) {
      this.#depleted = true;
      this.#eventBus.emit('power:depleted', {});
    }
  }
}
