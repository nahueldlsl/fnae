import { EventBus } from './core/EventBus.js';
import { TimerRegistry } from './core/TimerRegistry.js';
import { SaveRepository } from './core/SaveRepository.js';
import { AudioManager } from './core/AudioManager.js';
import { AssetLoader } from './core/AssetLoader.js';
import { GameEngine } from './GameEngine.js';
import { AnimationController } from './ui/AnimationController.js';
import { MenuController } from './ui/MenuController.js';
import { CustomNightView } from './ui/CustomNightView.js';
import { OfficeView } from './ui/OfficeView.js';
import { CameraView } from './ui/CameraView.js';

/**
 * Application Composition Root (DIP / Singleton orchestration).
 */
async function bootstrap() {
  const [gameRes, charRes] = await Promise.all([
    fetch('config/game.json'),
    fetch('config/characters.json'),
  ]);
  const gameConfig = await gameRes.json();
  const { characters: characterConfigs } = await charRes.json();

  if (gameConfig.title) {
    document.title = gameConfig.title;
  }

  const eventBus = EventBus.getInstance();
  const timers = new TimerRegistry();
  const saveRepository = SaveRepository.getInstance();
  const audio = AudioManager.getInstance();
  const assetLoader = AssetLoader.getInstance();
  const animations = new AnimationController(timers);

  audio.preload(gameConfig.sounds || []);

  const engine = GameEngine.getInstance({
    gameConfig,
    characterConfigs,
    eventBus,
    saveRepository,
    timers,
  });

  const officeView = new OfficeView({ engine, audio, animations, timers });
  const cameraView = new CameraView({ engine, audio, animations, timers });

  let menuController;
  const customNightView = new CustomNightView(characterConfigs, {
    onReady: (levels) => menuController.launchNight(7, levels),
    onBack: () => menuController.showMainMenu(),
  });

  menuController = new MenuController({
    audio,
    saveRepository,
    animations,
    timers,
    onOpenCustomNight: () => customNightView.show(),
    onStartNight: (nightNumber, customLevels) => {
      assetLoader.preloadGameAssets(gameConfig, characterConfigs);
      engine.startNight(nightNumber, customLevels);
      audio.startAmbient();
      const callPath = gameConfig.calls?.[String(nightNumber)];
      if (callPath) {
        audio.playOptionalCall(callPath);
      }
    },
  });

  eventBus.on('game:nightWon', () => {
    officeView.stopLoops();
    cameraView.stopLoops();
    menuController.showNightWonScreen();
  });

  eventBus.on('game:jumpscare', (payload) => {
    const frames = payload?.character?.assets?.jumpscareFrames?.length || 20;
    const frameMs = payload?.character?.assets?.jumpscareFrameMs || 45;
    menuController.showGameOverSequence(frames * frameMs + 150);
  });

  officeView.init();
  cameraView.init();
  menuController.init();
}

bootstrap().catch((err) => {
  console.error('[FNAE] Failed to initialize game:', err);
});
