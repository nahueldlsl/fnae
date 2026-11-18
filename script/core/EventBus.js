/**
 * EventBus (Singleton) - Decoupled publish/subscribe hub (GRASP Pure Fabrication / DIP).
 */
export class EventBus {
  static #instance = null;

  static getInstance() {
    if (!EventBus.#instance) {
      EventBus.#instance = new EventBus();
    }
    return EventBus.#instance;
  }

  constructor() {
    this.#listeners = new Map();
  }

  #listeners;

  /**
   * Subscribe to an event name. Returns an unsubscribe function.
   */
  on(event, handler) {
    if (!this.#listeners.has(event)) {
      this.#listeners.set(event, new Set());
    }
    this.#listeners.get(event).add(handler);
    return () => this.off(event, handler);
  }

  off(event, handler) {
    const set = this.#listeners.get(event);
    if (set) {
      set.delete(handler);
    }
  }

  emit(event, payload) {
    const set = this.#listeners.get(event);
    if (!set) return;
    for (const handler of [...set]) {
      handler(payload);
    }
  }

  clearAll() {
    this.#listeners.clear();
  }
}
