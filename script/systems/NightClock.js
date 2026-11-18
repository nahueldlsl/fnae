/**
 * NightClock (SRP) - Tracks in-game hour progression (12 AM -> 6 AM).
 * Default FNAF 1 timing: 90s for 12 AM, 89s for 1..5 AM (535s total).
 */
export class NightClock {
  constructor(eventBus, config = {}) {
    this.#eventBus = eventBus;
    this.#hourDurations = config.hourDurationsSec || [90, 89, 89, 89, 89, 89];
    this.#maxHour = config.maxHour ?? 6;
    this.reset();
  }

  #eventBus;
  #hourDurations;
  #maxHour;
  #hour = 0;
  #elapsedInHour = 0;
  #totalElapsed = 0;
  #finished = false;

  get hour() {
    return this.#hour;
  }

  get elapsedInHour() {
    return this.#elapsedInHour;
  }

  get totalElapsed() {
    return this.#totalElapsed;
  }

  get isFinished() {
    return this.#finished;
  }

  reset() {
    this.#hour = 0;
    this.#elapsedInHour = 0;
    this.#totalElapsed = 0;
    this.#finished = false;
  }

  tick(deltaSec = 1) {
    if (this.#finished) return;
    this.#elapsedInHour += deltaSec;
    this.#totalElapsed += deltaSec;

    let currentDuration = this.#hourDurations[this.#hour] ?? 89;
    while (this.#elapsedInHour >= currentDuration && !this.#finished) {
      this.#elapsedInHour -= currentDuration;
      this.#hour += 1;
      this.#eventBus.emit('clock:hourChanged', { hour: this.#hour });

      if (this.#hour >= this.#maxHour) {
        this.#finished = true;
        this.#eventBus.emit('clock:sixAM', { totalElapsed: this.#totalElapsed });
        break;
      }
      currentDuration = this.#hourDurations[this.#hour] ?? 89;
    }

    this.#eventBus.emit('clock:tick', {
      hour: this.#hour,
      elapsedInHour: this.#elapsedInHour,
      totalElapsed: this.#totalElapsed,
    });
  }
}
