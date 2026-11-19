/**
 * CustomNightView (OCP / DRY) - Dynamically generates character difficulty cards
 * from config/characters.json so adding a 5th+ character requires zero UI code changes.
 */
export class CustomNightView {
  constructor(characterConfigs = [], { onReady, onBack } = {}) {
    this.#characters = [...characterConfigs].sort(
      (a, b) => (a.customNightOrder ?? 99) - (b.customNightOrder ?? 99)
    );
    this.#onReady = onReady;
    this.#onBack = onBack;
    this.#levels = new Map();
    this.#initialized = false;
  }

  #characters;
  #onReady;
  #onBack;
  #levels;
  #initialized;

  show() {
    const root = document.getElementById('night7interface');
    if (!root) return;
    if (!this.#initialized) {
      this.#render();
      this.#initialized = true;
    }
    for (const ch of this.#characters) {
      this.#setLevel(ch.id, 20);
    }
    root.style.display = 'block';
  }

  hide() {
    const root = document.getElementById('night7interface');
    if (root) root.style.display = 'none';
  }

  #render() {
    const grid = document.getElementById('customnight-grid');
    if (!grid) return;
    grid.innerHTML = '';

    for (const ch of this.#characters) {
      this.#levels.set(ch.id, 20);

      const card = document.createElement('div');
      card.className = 'cn-card';
      card.dataset.characterId = ch.id;

      const header = ch.assets?.nameBanner
        ? `<img class="cn-name-banner" src="${ch.assets.nameBanner}" alt="${ch.displayName}" /><div class="cn-name-sub">${ch.displayName}</div>`
        : `<div class="cn-name-text">${ch.displayName}</div>`;

      card.innerHTML = `
        ${header}
        <img class="cn-portrait" src="${ch.assets?.icon || ''}" alt="${ch.displayName}" />
        <img class="cn-ailevel-label" src="graphics/mainmenu/customnight/ailevel.png" alt="AI Level" />
        <div class="cn-controls">
          <img class="cn-arrow cn-arrow-left" src="graphics/mainmenu/customnight/arrowleft.png" alt="-" />
          <div class="cn-digits">
            <img class="cn-digit cn-digit-tens" src="graphics/mainmenu/customnight/text/2.png" alt="2" />
            <img class="cn-digit cn-digit-ones" src="graphics/mainmenu/customnight/text/0.png" alt="0" />
          </div>
          <img class="cn-arrow cn-arrow-right" src="graphics/mainmenu/customnight/arrowright.png" alt="+" />
        </div>
      `;

      card.querySelector('.cn-arrow-left').addEventListener('click', (e) => {
        const step = e.shiftKey ? 5 : 1;
        this.#setLevel(ch.id, (this.#levels.get(ch.id) ?? 0) - step);
      });
      card.querySelector('.cn-arrow-right').addEventListener('click', (e) => {
        const step = e.shiftKey ? 5 : 1;
        this.#setLevel(ch.id, (this.#levels.get(ch.id) ?? 0) + step);
      });

      grid.appendChild(card);
    }

    const presetsRoot = document.getElementById('customnight-presets');
    if (presetsRoot) {
      presetsRoot.innerHTML = '';
      const presets = [
        { label: '20/20/20/20', map: () => 20 },
        { label: 'Noche 5', map: (ch) => Number(ch.nightLevels?.['5'] ?? 5) },
        { label: 'Solo Foxy', map: (ch) => (ch.id === 'foxy' ? 20 : 0) },
        { label: 'Reset 0', map: () => 0 },
      ];
      for (const preset of presets) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cn-preset-btn';
        btn.textContent = preset.label;
        btn.addEventListener('click', () => {
          for (const ch of this.#characters) {
            this.#setLevel(ch.id, preset.map(ch));
          }
        });
        presetsRoot.appendChild(btn);
      }
    }

    const readyBtn = document.getElementById('ready');
    if (readyBtn) {
      readyBtn.addEventListener('click', () => {
        const snapshot = Object.fromEntries(this.#levels.entries());
        this.hide();
        if (this.#onReady) this.#onReady(snapshot);
      });
    }

    const backBtn = document.getElementById('customnight-back');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        this.hide();
        if (this.#onBack) this.#onBack();
      });
    }
  }

  #setLevel(charId, value) {
    const clamped = Math.max(0, Math.min(20, value));
    this.#levels.set(charId, clamped);

    const card = document.querySelector(`.cn-card[data-character-id="${charId}"]`);
    if (!card) return;
    const tensEl = card.querySelector('.cn-digit-tens');
    const onesEl = card.querySelector('.cn-digit-ones');
    const str = String(clamped);

    if (str.length === 2) {
      tensEl.style.display = 'inline-block';
      tensEl.src = `graphics/mainmenu/customnight/text/${str[0]}.png`;
      onesEl.src = `graphics/mainmenu/customnight/text/${str[1]}.png`;
    } else {
      tensEl.style.display = 'none';
      onesEl.src = `graphics/mainmenu/customnight/text/${str[0]}.png`;
    }
  }
}
