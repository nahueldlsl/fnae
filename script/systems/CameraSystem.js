/**
 * CameraSystem (SRP) - Manages monitor open/close, active room selection,
 * and computes room image states cleanly from occupant presence (no ghosting).
 */
export class CameraSystem {
  constructor(eventBus, rooms = []) {
    this.#eventBus = eventBus;
    this.#rooms = new Map(rooms.map((r) => [r.id, r]));
    this.reset();
  }

  #eventBus;
  #rooms;
  #monitorOpen = false;
  #currentRoom = '1a';
  #staticLocked = false;
  #goldenFreddyActive = false;

  get isOpen() {
    return this.#monitorOpen;
  }

  get currentRoom() {
    return this.#currentRoom;
  }

  get isStaticLocked() {
    return this.#staticLocked;
  }

  getRoomMeta(roomId) {
    return this.#rooms.get(roomId) || null;
  }

  getAllRooms() {
    return [...this.#rooms.values()];
  }

  reset() {
    this.#monitorOpen = false;
    this.#currentRoom = '1a';
    this.#staticLocked = false;
    this.#goldenFreddyActive = false;
  }

  setMonitorOpen(open) {
    const next = Boolean(open);
    if (next === this.#monitorOpen) return;
    this.#monitorOpen = next;
    this.#eventBus.emit('camera:toggled', {
      open: this.#monitorOpen,
      room: this.#currentRoom,
    });
  }

  toggleMonitor() {
    this.setMonitorOpen(!this.#monitorOpen);
    return this.#monitorOpen;
  }

  selectRoom(roomId) {
    if (!this.#rooms.has(roomId)) return false;
    if (roomId === this.#currentRoom) return false;
    this.#currentRoom = roomId;
    this.#eventBus.emit('camera:roomChanged', {
      room: roomId,
      meta: this.#rooms.get(roomId),
    });
    return true;
  }

  setStaticLocked(locked) {
    this.#staticLocked = Boolean(locked);
  }

  /**
   * Computes the image path for any room from live animatronic states,
   * avoiding stale state corruption and supporting custom roomOverlays.
   */
  resolveRoomImage(roomId, entities) {
    const meta = this.#rooms.get(roomId);
    if (!meta || meta.audioOnly) return null;

    const occupants = entities.filter((e) => e.currentRoom === roomId && !e.atDoor);

    if (roomId === '1a') {
      const hasFreddy = occupants.some((e) => e.id === 'freddy');
      const hasBonnie = occupants.some((e) => e.id === 'bonnie');
      const hasChica = occupants.some((e) => e.id === 'chica');
      if (hasFreddy && hasBonnie && hasChica) return 'graphics/rooms/1a/0.webp';
      if (hasFreddy && hasChica && !hasBonnie) return 'graphics/rooms/1a/2.webp';
      if (hasFreddy && hasBonnie && !hasChica) return 'graphics/rooms/1a/3.webp';
      if (hasFreddy && !hasBonnie && !hasChica) return 'graphics/rooms/1a/1.webp';
      return 'graphics/rooms/1a/5.webp';
    }

    if (roomId === '1c') {
      const foxy = entities.find((e) => e.id === 'foxy');
      const stage = foxy ? Math.max(0, Math.min(3, foxy.coveStage)) : 0;
      return `graphics/rooms/1c/${stage}.webp`;
    }

    // Support custom overlays for 5th+ characters first when occupying a room
    for (const occ of occupants) {
      const overlay = occ.config.assets?.roomOverlays?.[roomId];
      if (overlay) return overlay;
    }

    // Priority order matches FNAF 1 visibility: Freddy > Chica > Bonnie
    const priority = ['freddy', 'chica', 'bonnie'];
    occupants.sort((a, b) => {
      const ia = priority.indexOf(a.id);
      const ib = priority.indexOf(b.id);
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    });

    for (const occ of occupants) {
      const states = occ.config.roomStates?.[roomId];
      if (Array.isArray(states) && states.length > 0) {
        const chosen = occ.roomVariant % states.length;
        return `graphics/rooms/${roomId}/${states[chosen]}.webp`;
      }
    }

    return `graphics/rooms/${roomId}/0.webp`;
  }
}
