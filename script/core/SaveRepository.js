/**
 * SaveRepository (Singleton) - Persistence layer for player progression and stars.
 */
export class SaveRepository {
  static #instance = null;
  static KEYS = {
    NIGHT: 'fnae.save.night',
    STARS: 'fnae.save.stars',
    LEGACY_NIGHT: 'fnaf-js-savegame.night',
    LEGACY_STARS: 'fnaf-js-savegame.stars',
  };

  static getInstance(storage = typeof localStorage !== 'undefined' ? localStorage : null) {
    if (!SaveRepository.#instance) {
      SaveRepository.#instance = new SaveRepository(storage);
    }
    return SaveRepository.#instance;
  }

  constructor(storage) {
    this.#storage = storage ?? this.#createMemoryStorage();
    this.#migrateLegacy();
  }

  #storage;

  #createMemoryStorage() {
    const store = new Map();
    return {
      getItem: (k) => (store.has(k) ? store.get(k) : null),
      setItem: (k, v) => store.set(k, String(v)),
    };
  }

  #migrateLegacy() {
    if (this.#storage.getItem(SaveRepository.KEYS.NIGHT) == null) {
      const legacyNight = this.#storage.getItem(SaveRepository.KEYS.LEGACY_NIGHT);
      this.#storage.setItem(SaveRepository.KEYS.NIGHT, legacyNight || '1');
    }
    if (this.#storage.getItem(SaveRepository.KEYS.STARS) == null) {
      const legacyStars = this.#storage.getItem(SaveRepository.KEYS.LEGACY_STARS);
      this.#storage.setItem(SaveRepository.KEYS.STARS, legacyStars || '0');
    }
  }

  getNight() {
    const parsed = parseInt(this.#storage.getItem(SaveRepository.KEYS.NIGHT) || '1', 10);
    return Number.isFinite(parsed) && parsed >= 1 ? parsed : 1;
  }

  setNight(night) {
    const clamped = Math.max(1, Math.min(7, Number(night) || 1));
    this.#storage.setItem(SaveRepository.KEYS.NIGHT, String(clamped));
  }

  getStars() {
    const parsed = parseInt(this.#storage.getItem(SaveRepository.KEYS.STARS) || '0', 10);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
  }

  setStars(stars) {
    const clamped = Math.max(0, Math.min(3, Number(stars) || 0));
    this.#storage.setItem(SaveRepository.KEYS.STARS, String(clamped));
  }

  recordNightVictory(completedNight, isAll20Mode = false) {
    const nightNum = Number(completedNight) || 1;
    let savedNight = this.getNight();
    let stars = this.getStars();

    if (nightNum >= 5 && stars < 1) stars = 1;
    if (nightNum >= 6 && stars < 2) stars = 2;
    if (nightNum === 7 && isAll20Mode && stars < 3) stars = 3;

    if (nightNum < 7 && nightNum + 1 > savedNight) {
      savedNight = nightNum + 1;
    }
    this.setNight(savedNight);
    this.setStars(stars);
    return { night: savedNight, stars };
  }
}
