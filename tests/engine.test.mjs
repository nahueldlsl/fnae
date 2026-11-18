import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

import { EventBus } from '../script/core/EventBus.js';
import { SaveRepository } from '../script/core/SaveRepository.js';
import { GameEngine } from '../script/GameEngine.js';

const ROOT = path.resolve(import.meta.dirname, '..');
const gameConfig = JSON.parse(fs.readFileSync(path.join(ROOT, 'config/game.json'), 'utf8'));
const { characters: characterConfigs } = JSON.parse(
  fs.readFileSync(path.join(ROOT, 'config/characters.json'), 'utf8')
);

function createMemoryStorage(initial = {}) {
  const map = new Map(Object.entries(initial));
  return {
    getItem: (k) => (map.has(k) ? map.get(k) : null),
    setItem: (k, v) => map.set(k, String(v)),
  };
}

function createTestEngine({ rng = () => 0.0, extraCharacters = [], storageInitial = {} } = {}) {
  const eventBus = new EventBus();
  const saveRepo = new SaveRepository(createMemoryStorage(storageInitial));
  const engine = new GameEngine({
    gameConfig,
    characterConfigs: [...characterConfigs, ...extraCharacters],
    eventBus,
    saveRepository: saveRepo,
    rng,
  });
  return { engine, eventBus, saveRepo };
}

test('NightClock follows FNAF 1 535s schedule (90s + 5*89s) and emits 6 AM', () => {
  const { engine, eventBus } = createTestEngine();
  const hoursSeen = [];
  let won = false;
  eventBus.on('clock:hourChanged', ({ hour }) => hoursSeen.push(hour));
  eventBus.on('game:nightWon', () => {
    won = true;
  });

  engine.startNight(1, null, { autoStartLoop: false });
  // Step 89s -> still 12 AM (hour 0)
  for (let i = 0; i < 89; i++) engine.clock.tick(1);
  assert.equal(engine.clock.hour, 0);
  // +1s = 90s -> 1 AM
  engine.clock.tick(1);
  assert.equal(engine.clock.hour, 1);

  // Remaining 5 hours * 89s = 445s -> 6 AM
  for (let i = 0; i < 444; i++) engine.clock.tick(1);
  assert.equal(engine.clock.hour, 5);
  assert.equal(won, false);

  engine.clock.tick(1);
  assert.equal(engine.clock.hour, 0); // resetSimulation runs on victory
  assert.equal(won, true);
  assert.deepEqual(hoursSeen, [1, 2, 3, 4, 5, 6]);
});

test('Night 1 AI starts at 0 and scales at 2 AM, 3 AM, 4 AM', () => {
  const { engine } = createTestEngine({ rng: () => 0.01 });
  engine.startNight(1, null, { autoStartLoop: false });

  const bonnie = engine.ai.getEntity('bonnie');
  const chica = engine.ai.getEntity('chica');
  const foxy = engine.ai.getEntity('foxy');
  const freddy = engine.ai.getEntity('freddy');

  assert.equal(bonnie.baseAiLevel, 0);
  assert.equal(chica.baseAiLevel, 0);
  assert.equal(foxy.baseAiLevel, 0);
  assert.equal(freddy.baseAiLevel, 0);

  // Advance to 2 AM (90 + 89 = 179s)
  for (let i = 0; i < 179; i++) engine.step(1);
  assert.equal(engine.clock.hour, 2);
  assert.equal(bonnie.hourlyBonus, 1);
  assert.equal(bonnie.effectiveAiLevel, 1);
  assert.equal(freddy.effectiveAiLevel, 0);
});

test('PowerSystem calculates usage bars (1..5), passive drain, and allows 6 AM save during powerout', () => {
  const { engine, eventBus } = createTestEngine({ rng: () => 0.99 }); // 45s outage delay
  let outageStarted = false;
  let nightWon = false;
  eventBus.on('game:powerOutageStarted', () => {
    outageStarted = true;
  });
  eventBus.on('game:nightWon', () => {
    nightWon = true;
  });

  engine.startNight(5, null, { autoStartLoop: false });
  assert.equal(engine.power.usageBars, 1);

  engine.office.toggleDoor('left');
  assert.equal(engine.power.usageBars, 2);
  engine.office.toggleLight('right');
  assert.equal(engine.power.usageBars, 3);
  engine.camera.toggleMonitor();
  assert.equal(engine.power.usageBars, 4);

  // Turning on left light automatically turns off right light (keeps bars at 4)
  engine.office.toggleLight('left');
  assert.equal(engine.office.isLightOn('right'), false);
  assert.equal(engine.office.isLightOn('left'), true);
  assert.equal(engine.power.usageBars, 4);

  // Deplete remaining power
  engine.power.consumePercent(100);
  assert.equal(outageStarted, true);
  assert.equal(engine.phase, 'powerout');
  assert.equal(engine.office.isDoorClosed('left'), false);
  assert.equal(engine.camera.isOpen, false);

  // Clock must still tick in powerout phase and reach 6 AM!
  for (let i = 0; i < 535; i++) {
    if (nightWon) break;
    engine.step(1);
  }
  assert.equal(nightWon, true);
  engine.destroy();
});

test('Freddy freezes when CAM 4B is watched and moves when unwatched', () => {
  const { engine } = createTestEngine({ rng: () => 0.0 });
  engine.startNight(7, { freddy: 20, bonnie: 0, chica: 0, foxy: 0 }, { autoStartLoop: false });

  const freddy = engine.ai.getEntity('freddy');

  // Watch CAM 4B -> Freddy should not leave 1a
  engine.camera.setMonitorOpen(true);
  engine.camera.selectRoom('4b');
  for (let i = 0; i < 20; i++) engine.ai.tick(1);
  assert.equal(freddy.currentRoom, '1a');

  // Close monitor -> Freddy advances along his route
  engine.camera.setMonitorOpen(false);
  for (let i = 0; i < 10; i++) engine.ai.tick(1);
  assert.notEqual(freddy.currentRoom, '1a');
});

test('Foxy stalls on any camera and drains escalating power (1%, 6%, 11%) on closed door', () => {
  const { engine } = createTestEngine({ rng: () => 0.0 });
  engine.startNight(7, { freddy: 0, bonnie: 0, chica: 0, foxy: 20 }, { autoStartLoop: false });

  const foxy = engine.ai.getEntity('foxy');

  // Viewing any camera (even 1A) stalls Foxy
  engine.camera.setMonitorOpen(true);
  for (let i = 0; i < 20; i++) engine.ai.tick(1);
  assert.equal(foxy.coveStage, 0);

  // Close monitor and let Foxy advance through stages (0 -> 1 -> 2 -> 3)
  engine.camera.setMonitorOpen(false);
  foxy.foxyStallTimer = 0;
  for (let i = 0; i < 17; i++) engine.ai.tick(1);
  assert.equal(foxy.coveStage, 3);
  assert.equal(foxy.foxyPhase, 'ready');

  // Close left door -> 1st bang drains 1% (10 units)
  engine.office.toggleDoor('left');
  const powerBeforeFirstBang = engine.power.units;
  for (let i = 0; i < 26; i++) engine.ai.tick(1);
  assert.equal(foxy.foxyBangs, 1);
  assert.equal(powerBeforeFirstBang - engine.power.units, 10);

  // 2nd bang -> drains 6% (60 units)
  foxy.foxyStallTimer = 0;
  for (let i = 0; i < 45; i++) {
    if (foxy.foxyBangs === 2) break;
    engine.ai.tick(1);
  }
  assert.equal(foxy.foxyBangs, 2);
});

test('CameraSystem clears previous room state (no ghosting) and supports 5th custom character (OCP)', () => {
  const customChar = {
    id: 'shadow_friend',
    displayName: 'Shadow Friend',
    customNightOrder: 5,
    strategy: 'roamer',
    side: 'left',
    startRoom: '1b',
    movementIntervalSec: 1,
    route: [
      { room: '1b', next: ['2a'] },
      { room: '2a', next: ['office'] },
    ],
    retreatRoom: '1b',
    roomStates: {},
    nightLevels: { 7: 20 },
    assets: {
      roomOverlays: {
        '1b': 'graphics/characters/shadow_friend/room_1b.webp',
        '2a': 'graphics/characters/shadow_friend/room_2a.webp',
      },
    },
  };

  const { engine } = createTestEngine({ rng: () => 0.0, extraCharacters: [customChar] });
  engine.startNight(7, { freddy: 0, bonnie: 0, chica: 0, foxy: 0, shadow_friend: 20 }, { autoStartLoop: false });

  // Initially in 1b -> resolves custom overlay
  assert.equal(
    engine.camera.resolveRoomImage('1b', engine.ai.entities),
    'graphics/characters/shadow_friend/room_1b.webp'
  );

  // Tick once -> moves to 2a -> 1b must revert cleanly to empty 0.webp!
  engine.ai.tick(1);
  assert.equal(engine.camera.resolveRoomImage('1b', engine.ai.entities), 'graphics/rooms/1b/0.webp');
  assert.equal(
    engine.camera.resolveRoomImage('2a', engine.ai.entities),
    'graphics/characters/shadow_friend/room_2a.webp'
  );
});

test('SaveRepository migrates legacy keys and awards stars accurately', () => {
  const repo = new SaveRepository(
    createMemoryStorage({
      'fnaf-js-savegame.night': '5',
      'fnaf-js-savegame.stars': '0',
    })
  );
  assert.equal(repo.getNight(), 5);
  assert.equal(repo.getStars(), 0);

  repo.recordNightVictory(5, false);
  assert.equal(repo.getNight(), 6);
  assert.equal(repo.getStars(), 1);

  repo.recordNightVictory(6, false);
  assert.equal(repo.getNight(), 7);
  assert.equal(repo.getStars(), 2);

  repo.recordNightVictory(7, true);
  assert.equal(repo.getStars(), 3);
});
