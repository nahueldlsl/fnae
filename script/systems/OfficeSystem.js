/**
 * DoorSideController - Reusable controller for one office side (left or right).
 * Eliminates left/right DRY duplication.
 */
class DoorSideController {
  constructor(side) {
    this.side = side;
    this.doorClosed = false;
    this.lightOn = false;
    this.jammed = false;
    this.occupant = null;
  }

  reset() {
    this.doorClosed = false;
    this.lightOn = false;
    this.jammed = false;
    this.occupant = null;
  }
}

/**
 * OfficeSystem (SRP) - Manages office doors, hall lights, jamming, and power usage bars.
 */
export class OfficeSystem {
  constructor(eventBus) {
    this.#eventBus = eventBus;
    this.#sides = {
      left: new DoorSideController('left'),
      right: new DoorSideController('right'),
    };
    this.#poweredOff = false;
  }

  #eventBus;
  #sides;
  #poweredOff;

  reset() {
    this.#sides.left.reset();
    this.#sides.right.reset();
    this.#poweredOff = false;
    this.#eventBus.emit('office:reset', {});
  }

  isDoorClosed(side) {
    return this.#sides[side]?.doorClosed ?? false;
  }

  isLightOn(side) {
    return this.#sides[side]?.lightOn ?? false;
  }

  getActiveLightSide() {
    if (this.#sides.left.lightOn) return 'left';
    if (this.#sides.right.lightOn) return 'right';
    return null;
  }

  getDoorOccupant(side) {
    return this.#sides[side]?.occupant ?? null;
  }

  setDoorOccupant(side, characterId) {
    const ctrl = this.#sides[side];
    if (!ctrl) return;
    const prev = ctrl.occupant;
    ctrl.occupant = characterId;
    if (prev !== characterId || ctrl.lightOn) {
      this.#eventBus.emit('office:occupantChanged', {
        side,
        occupant: characterId,
        lightOn: ctrl.lightOn,
      });
    }
  }

  jamSide(side) {
    const ctrl = this.#sides[side];
    if (!ctrl) return;
    ctrl.jammed = true;
    ctrl.lightOn = false;
    this.#eventBus.emit('office:jammed', { side });
  }

  toggleDoor(side) {
    const ctrl = this.#sides[side];
    if (!ctrl || this.#poweredOff) return false;
    if (ctrl.jammed) {
      this.#eventBus.emit('office:jammedAction', { side, action: 'door' });
      return false;
    }
    ctrl.doorClosed = !ctrl.doorClosed;
    this.#eventBus.emit('office:doorChanged', {
      side,
      closed: ctrl.doorClosed,
      lightOn: ctrl.lightOn,
    });
    return true;
  }

  toggleLight(side) {
    const ctrl = this.#sides[side];
    if (!ctrl || this.#poweredOff) return false;
    if (ctrl.jammed) {
      this.#eventBus.emit('office:jammedAction', { side, action: 'light' });
      return false;
    }

    const otherSide = side === 'left' ? 'right' : 'left';
    if (!ctrl.lightOn && this.#sides[otherSide].lightOn) {
      this.#sides[otherSide].lightOn = false;
      this.#eventBus.emit('office:lightChanged', {
        side: otherSide,
        on: false,
        doorClosed: this.#sides[otherSide].doorClosed,
        occupant: this.#sides[otherSide].occupant,
      });
    }

    ctrl.lightOn = !ctrl.lightOn;
    this.#eventBus.emit('office:lightChanged', {
      side,
      on: ctrl.lightOn,
      doorClosed: ctrl.doorClosed,
      occupant: ctrl.occupant,
    });
    return true;
  }

  turnOffLights() {
    for (const side of ['left', 'right']) {
      if (this.#sides[side].lightOn) {
        this.#sides[side].lightOn = false;
        this.#eventBus.emit('office:lightChanged', {
          side,
          on: false,
          doorClosed: this.#sides[side].doorClosed,
          occupant: this.#sides[side].occupant,
        });
      }
    }
  }

  powerDown() {
    this.#poweredOff = true;
    this.turnOffLights();
    for (const side of ['left', 'right']) {
      if (this.#sides[side].doorClosed) {
        this.#sides[side].doorClosed = false;
        this.#eventBus.emit('office:doorChanged', {
          side,
          closed: false,
          lightOn: false,
        });
      }
    }
  }
}
