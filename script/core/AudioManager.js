/**
 * AudioManager (Singleton) - Multichannel sound & seamless ambient loop controller.
 * Fixes the legacy stopSound() early-return bug and supports concurrent SFX playback.
 */
export class AudioManager {
  static #instance = null;
  static DEFAULT_VOLUME = 0.3;

  static getInstance() {
    if (!AudioManager.#instance) {
      AudioManager.#instance = new AudioManager();
    }
    return AudioManager.#instance;
  }

  constructor() {
    this.#tracks = new Map();
    this.#activeInstances = new Set();
    this.#ambientLoops = [];
    this.#unlocked = false;
    this.#debugSuppress = false;
    this.#muted = false;
    this.#ambientRunning = false;
  }

  #tracks;
  #activeInstances;
  #ambientLoops;
  #unlocked;
  #debugSuppress;
  #muted;
  #ambientRunning;

  get isMuted() {
    return this.#muted;
  }

  setDebugSuppress(flag) {
    this.#debugSuppress = Boolean(flag);
  }

  setMuted(flag) {
    this.#muted = Boolean(flag);
    for (const inst of this.#activeInstances) {
      inst.muted = this.#muted;
    }
    for (const track of this.#tracks.values()) {
      track.muted = this.#muted;
    }
    if (this.#ambientRunning) {
      for (const entry of this.#ambientLoops) {
        try {
          entry.loop.volume(this.#muted ? 0 : entry.volume);
        } catch (_e) {}
      }
    }
    return this.#muted;
  }

  toggleMute() {
    return this.setMuted(!this.#muted);
  }

  preload(soundList) {
    if (typeof Audio === 'undefined') return;
    for (const rel of soundList) {
      if (!this.#tracks.has(rel)) {
        const audio = new Audio(`sounds/${rel}`);
        audio.preload = 'auto';
        this.#tracks.set(rel, audio);
      }
    }
    if (typeof SeamlessLoop !== 'undefined' && this.#ambientLoops.length === 0) {
      try {
        const amb1 = new SeamlessLoop();
        amb1.addUri('sounds/Buzz_Fan_Florescent2.wav', 9600, 'ambiancetrack1');
        const amb2 = new SeamlessLoop();
        amb2.addUri('sounds/ambience2.wav', 60000, 'ambiancetrack2');
        this.#ambientLoops = [
          { loop: amb1, id: 'ambiancetrack1', volume: 0.3 },
          { loop: amb2, id: 'ambiancetrack2', volume: 0.3 },
        ];
      } catch (_e) {
        this.#ambientLoops = [];
      }
    }
  }

  unlock() {
    if (this.#unlocked) return;
    this.#unlocked = true;
    if (typeof window !== 'undefined') {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) {
        try {
          const ctx = new Ctx();
          if (ctx.state === 'suspended') {
            ctx.resume().catch(() => {});
          }
        } catch (_e) {}
      }
    }
  }

  play(src, volume = AudioManager.DEFAULT_VOLUME, loop = false) {
    if (this.#debugSuppress || !src || typeof Audio === 'undefined') return null;

    const template = this.#tracks.get(src);
    let instance;

    if (loop && template) {
      template.pause();
      template.currentTime = 0;
      template.loop = true;
      template.volume = volume;
      instance = template;
    } else {
      instance = template ? template.cloneNode() : new Audio(`sounds/${src}`);
      instance.loop = Boolean(loop);
      instance.volume = Math.max(0, Math.min(1, volume));
    }

    instance.muted = this.#muted;
    this.#activeInstances.add(instance);
    const cleanup = () => {
      if (!instance.loop) {
        this.#activeInstances.delete(instance);
      }
    };
    instance.addEventListener('ended', cleanup, { once: true });

    const promise = instance.play();
    if (promise && typeof promise.catch === 'function') {
      promise.catch(() => {
        this.#activeInstances.delete(instance);
      });
    }
    return instance;
  }

  playOptionalCall(path) {
    if (!path || typeof fetch === 'undefined' || typeof Audio === 'undefined') {
      return Promise.resolve(null);
    }
    return fetch(path, { method: 'HEAD' })
      .then((res) => {
        if (!res.ok) return null;
        const audio = new Audio(path);
        audio.volume = 0.65;
        audio.muted = this.#muted;
        this.#activeInstances.add(audio);
        audio.addEventListener('ended', () => this.#activeInstances.delete(audio), { once: true });
        audio.play().catch(() => {});
        return audio;
      })
      .catch(() => null);
  }

  stop(src) {
    if (!src) {
      this.stopAll();
      return;
    }
    for (const inst of [...this.#activeInstances]) {
      if (inst.src && inst.src.includes(encodeURI(src))) {
        inst.pause();
        inst.currentTime = 0;
        this.#activeInstances.delete(inst);
      }
    }
    const base = this.#tracks.get(src);
    if (base) {
      base.pause();
      base.currentTime = 0;
    }
  }

  stopAll() {
    for (const inst of [...this.#activeInstances]) {
      inst.pause();
      try {
        inst.currentTime = 0;
      } catch (_e) {}
    }
    this.#activeInstances.clear();
    for (const track of this.#tracks.values()) {
      track.pause();
      try {
        track.currentTime = 0;
      } catch (_e) {}
    }
  }

  startAmbient() {
    if (this.#debugSuppress) return;
    if (this.#ambientRunning) {
      this.stopAmbient();
    }
    this.#ambientRunning = true;
    for (const entry of this.#ambientLoops) {
      try {
        entry.loop.start(entry.id);
        entry.loop.volume(this.#muted ? 0 : entry.volume);
      } catch (_e) {}
    }
  }

  stopAmbient() {
    this.#ambientRunning = false;
    for (const entry of this.#ambientLoops) {
      try {
        entry.loop.stop();
      } catch (_e) {}
    }
  }
}
