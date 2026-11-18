/**
 * AnimationController (SRP / DRY) - Unified frame-sequence animation runner.
 */
export class AnimationController {
  constructor(timers) {
    this.#timers = timers;
  }

  #timers;

  /**
   * Plays an array of frame URLs or indices sequentially or in reverse.
   */
  playSequence({ frames, frameMs = 30, reverse = false, onFrame, onComplete }) {
    if (!frames || frames.length === 0) {
      if (onComplete) onComplete();
      return;
    }

    const ordered = reverse ? [...frames].reverse() : frames;
    ordered.forEach((frame, stepIdx) => {
      this.#timers.setTimeout(() => {
        onFrame(frame, stepIdx);
      }, frameMs * (stepIdx + 1));
    });

    if (onComplete) {
      this.#timers.setTimeout(onComplete, frameMs * (ordered.length + 1));
    }
  }

  playTransition(transitionEl) {
    if (!transitionEl) return;
    const frames = Array.from({ length: 8 }, (_, i) => `graphics/transition/${i}.webp`);
    transitionEl.style.display = 'block';
    this.playSequence({
      frames,
      frameMs: 65,
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
      onFrame: (src) => {
        officeMain.style.backgroundImage = `url('${src}')`;
      },
      onComplete: onFinished,
    });
  }
}
