/**
 * AssetLoader (Singleton) - Preloads and caches images from a manifest.
 */
export class AssetLoader {
  static #instance = null;

  static getInstance() {
    if (!AssetLoader.#instance) {
      AssetLoader.#instance = new AssetLoader();
    }
    return AssetLoader.#instance;
  }

  constructor() {
    this.#cache = new Map();
  }

  #cache;

  preloadImage(src) {
    if (!src) return null;
    if (this.#cache.has(src)) return this.#cache.get(src);
    if (typeof Image === 'undefined') {
      this.#cache.set(src, { src });
      return this.#cache.get(src);
    }
    const img = new Image();
    img.src = src;
    this.#cache.set(src, img);
    return img;
  }

  preloadBatch(paths) {
    for (const p of paths) {
      this.preloadImage(p);
    }
  }

  preloadGameAssets(gameConfig, characterConfigs) {
    const paths = [
      'graphics/rooms/office/0.webp',
      'graphics/rooms/office/0_lightleft.webp',
      'graphics/rooms/office/0_lightright.webp',
      'graphics/rooms/office/powerout0.webp',
      'graphics/rooms/office/powerout1.webp',
      'graphics/rooms/2a/0.webp',
      'graphics/rooms/2a/1.webp',
    ];

    for (let i = 0; i < 8; i++) paths.push(`graphics/transition/${i}.webp`);
    for (let i = 0; i < 10; i++) paths.push(`graphics/camera/camerafeedanimation/${i}.webp`);
    for (let i = 0; i < 14; i++) {
      paths.push(`graphics/rooms/office/doors/left/${i}.webp`);
      paths.push(`graphics/rooms/office/doors/right/${i}.webp`);
    }
    for (let i = 1; i <= 4; i++) {
      paths.push(`graphics/rooms/office/buttons/buttonleft_${i}.webp`);
      paths.push(`graphics/rooms/office/buttons/buttonright_${i}.webp`);
    }
    for (let i = 1; i <= 3; i++) paths.push(`graphics/rooms/office/fan_${i}.webp`);
    for (let i = 1; i <= 5; i++) paths.push(`graphics/camera/power${i}.png`);
    for (let i = 0; i < 10; i++) paths.push(`graphics/camera/ui/powernumbers/${i}.png`);
    for (let i = 0; i < 7; i++) paths.push(`graphics/camera/ui/time${i}.png`);
    for (let i = 0; i < 31; i++) paths.push(`graphics/rooms/2a/foxxy/${i}.webp`);
    for (let i = 0; i < 4; i++) paths.push(`graphics/mainmenu/${i}.webp`);

    for (const room of gameConfig.rooms || []) {
      paths.push(`graphics/camera/roomnames/${room.id}.webp`);
      for (let i = 0; i < (room.images || 0); i++) {
        paths.push(`graphics/rooms/${room.id}/${i}.webp`);
      }
    }

    for (const ch of characterConfigs || []) {
      const assets = ch.assets || {};
      if (assets.icon) paths.push(assets.icon);
      if (assets.doorLightFrame) paths.push(assets.doorLightFrame);
      if (Array.isArray(assets.jumpscareFrames)) paths.push(...assets.jumpscareFrames);
      if (assets.roomOverlays) paths.push(...Object.values(assets.roomOverlays));
    }

    this.preloadBatch(paths);
  }
}
