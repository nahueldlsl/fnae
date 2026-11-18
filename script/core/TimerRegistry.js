/**
 * TimerRegistry - Centralized lifecycle manager for timeouts and intervals.
 * Prevents orphaned timers across night transitions, game overs, and resets.
 */
export class TimerRegistry {
  #timeouts = new Set();
  #intervals = new Set();

  setTimeout(fn, delayMs) {
    const id = globalThis.setTimeout(() => {
      this.#timeouts.delete(id);
      fn();
    }, delayMs);
    this.#timeouts.add(id);
    return id;
  }

  clearTimeout(id) {
    if (id == null) return;
    globalThis.clearTimeout(id);
    this.#timeouts.delete(id);
  }

  setInterval(fn, intervalMs) {
    const id = globalThis.setInterval(fn, intervalMs);
    this.#intervals.add(id);
    return id;
  }

  clearInterval(id) {
    if (id == null) return;
    globalThis.clearInterval(id);
    this.#intervals.delete(id);
  }

  clearAll() {
    for (const id of this.#timeouts) {
      globalThis.clearTimeout(id);
    }
    for (const id of this.#intervals) {
      globalThis.clearInterval(id);
    }
    this.#timeouts.clear();
    this.#intervals.clear();
  }
}
