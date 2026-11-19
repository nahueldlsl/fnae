/**
 * AnimationController (SRP / DRY) - Unified frame-sequence animation runner.
 */
export class AnimationController {
  constructor(timers) {
    this.#timers = timers;
    this.#channels = new Map();
  }

  #timers;
  #channels;

  cancelChannel(channel) {
    if (!channel || !this.#channels.has(channel)) return;
    const ids = this.#channels.get(channel);
    for (const id of ids) {
      this.#timers.clearTimeout(id);
    }
    this.#channels.delete(channel);
  }

  cancelAll() {
    for (const channel of [...this.#channels.keys()]) {
      this.cancelChannel(channel);
    }
  }

  /**
   * Plays an array of frame URLs or indices sequentially or in reverse.
   * When `channel` is provided, any in-flight sequence on the same channel is cancelled first.
   */
  playSequence({ frames, frameMs = 30, reverse = false, channel = null, onFrame, onComplete }) {
    if (channel) {
      this.cancelChannel(channel);
    }

    if (!frames || frames.length === 0) {
      if (onComplete) onComplete();
      return;
    }

    const trackedIds = channel ? new Set() : null;
    if (channel) {
      this.#channels.set(channel, trackedIds);
    }

    const ordered = reverse ? [...frames].reverse() : frames;
    ordered.forEach((frame, stepIdx) => {
      const id = this.#timers.setTimeout(() => {
        if (trackedIds) trackedIds.delete(id);
        onFrame(frame, stepIdx);
      }, frameMs * (stepIdx + 1));
      if (trackedIds) trackedIds.add(id);
    });

    if (onComplete) {
      const doneId = this.#timers.setTimeout(() => {
        if (channel) this.#channels.delete(channel);
        onComplete();
      }, frameMs * (ordered.length + 1));
      if (trackedIds) trackedIds.add(doneId);
    }
  }

  playTransition(transitionEl) {
    if (!transitionEl) return;
    const frames = Array.from({ length: 8 }, (_, i) => `graphics/transition/${i}.webp`);
    transitionEl.style.display = 'block';
    this.playSequence({
      frames,
      frameMs: 65,
      channel: 'transition',
      onFrame: (src) => {
        transitionEl.src = src;
      },
      onComplete: () => {
        transitionEl.style.display = 'none';
      },
    });
  }

  playDoor(side, closing) {
    const doorEl = document.getElementById(side === 'left' ? 'doorleft' : 'doorright');
    if (!doorEl) return;
    const frames = Array.from(
      { length: 14 },
      (_, i) => `graphics/rooms/office/doors/${side}/${i}.webp`
    );
    this.playSequence({
      frames,
      frameMs: closing ? 30 : 20,
      reverse: !closing,
      channel: `door:${side}`,
      onFrame: (src) => {
        doorEl.src = src;
      },
    });
  }

  playCameraFlip(opening, onComplete) {
    const animEl = document.getElementById('camerafeedanimation');
    if (!animEl) {
      if (onComplete) onComplete();
      return;
    }
    const frames = Array.from(
      { length: 10 },
      (_, i) => `graphics/camera/camerafeedanimation/${i}.webp`
    );
    animEl.style.display = 'block';
    this.playSequence({
      frames,
      frameMs: opening ? 30 : 20,
      reverse: !opening,
      channel: 'camera:flip',
      onFrame: (src) => {
        animEl.src = src;
      },
      onComplete: () => {
        animEl.style.display = 'none';
        if (onComplete) onComplete();
      },
    });
  }

  playJumpscare(characterCfg, onFinished) {
    const officeMain = document.getElementById('officemain');
    const frames = characterCfg?.assets?.jumpscareFrames || [];
    const frameMs = characterCfg?.assets?.jumpscareFrameMs || 45;

    if (!officeMain || frames.length === 0) {
      if (onFinished) onFinished();
      return;
    }

    this.playSequence({
      frames,
      frameMs,
      channel: 'jumpscare',
      onFrame: (src) => {
        officeMain.style.backgroundImage = `url('${src}')`;
      },
      onComplete: onFinished,
    });
  }
}
