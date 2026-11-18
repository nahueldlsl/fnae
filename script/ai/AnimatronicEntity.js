/**
 * AnimatronicEntity - Holds runtime state for a single configured character.
 */
export class AnimatronicEntity {
  constructor(config) {
    this.config = config;
    this.id = config.id;
    this.displayName = config.displayName || config.id;
    this.strategyName = config.strategy || 'roamer';
    this.side = config.side || 'left';
    this.routeMap = new Map((config.route || []).map((node) => [node.room, node.next || []]));
    this.reset(0);
  }

  reset(baseAiLevel = 0) {
    this.baseAiLevel = baseAiLevel;
    this.hourlyBonus = 0;
    this.currentRoom = this.config.startRoom || '1a';
    this.atDoor = false;
    this.insideOffice = false;
    this.coveStage = 0;
    this.foxyPhase = 'cove'; // 'cove' | 'ready' | 'sprinting'
    this.foxyAttackTimer = 0;
    this.foxySprintTimer = 0;
    this.foxyBangs = 0;
    this.foxyStallTimer = 0;
    this.movementTimer = 0;
    this.doorWaitTicks = 0;
    this.insideWaitTimer = 0;
    this.roomVariant = 0;
  }

  get effectiveAiLevel() {
    return Math.max(0, Math.min(20, this.baseAiLevel + this.hourlyBonus));
  }

  getNextRooms() {
    return this.routeMap.get(this.currentRoom) || [];
  }
}
