# 🍕 Five Nights at Ezequiel's (FNAE)

[![HTML5](https://img.shields.io/badge/Engine-HTML5%20%2F%20JavaScript-orange.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Python](https://img.shields.io/badge/Tools-Python%203.10-blue.svg)](https://www.python.org/)
[![Pillow](https://img.shields.io/badge/Image%20Pipeline-Pillow-yellowgreen.svg)](https://python-pillow.org/)
[![Status](https://img.shields.io/badge/Status-100%25%20Playable-brightgreen.svg)](#)

> **Five Nights at Ezequiel's** es una adaptación personalizada, humorística y 100% jugable del clásico juego de terror *Five Nights at Freddy's* (FNAF), recreada sobre un motor web nativo en HTML5/JavaScript y transformada con fotos y expresiones de **Ezequiel** y sus amigos.

---

## 📖 Sinopsis & Lore

Bienvenido a tu nuevo trabajo de verano en la oficina de vigilancia. Tu tarea es simple: vigilar las cámaras de seguridad desde las 12 AM hasta las 6 AM sin quedarte sin batería... pero algo no anda bien con los animatrónicos de esta pizzería: **todos tienen la cara de Ezequiel**, y su mejor amigo está listo para salir a toda velocidad de la Pirate Cove para darte el susto de tu vida.

¿Podrás sobrevivir a las 5 noches, superar la Noche 6 y dominar el desafío 20/20/20/20 de la Noche Personalizada?

---

## 🎭 Personajes & Roles

| Animatrónico | Personaje en FNAE | Comportamiento & Ubicación |
|---|---|---|
| 🐻 **Freddy Fazbear** | **Ezequiel** | Comienza en el escenario (**CAM 1A**), avanza sigilosamente en la oscuridad, te acecha en la puerta derecha y canta la caja de música cuando se corta la luz. |
| 🐰 **Bonnie** | **Ezequiel (Buzo Bordó)** | Rápido y agresivo. Acecha por el pasillo izquierdo y se asoma por la puerta izquierda. Si prendes la luz y lo ves, ¡cierra la puerta de inmediato! |
| 🐥 **Chica** | **Santi** | Merodea por el lado derecho y la cocina (escucharás ollas y platos). Aparece en la puerta derecha con mirada fija. |
| 🦊 **Foxy** | **Horacio** | Escondido tras la cortina de la Pirate Cove (**CAM 1C**). Si no lo miras con frecuencia, saldrá disparado corriendo por el pasillo (**CAM 2A**) directo hacia tu puerta izquierda. |

---

## 🎮 Características de Jugabilidad

- ⚡ **Gestión Dinámica de Energía**: El uso de puertas, luces y cámaras consume electricidad progresivamente. ¡Si llega a 0%, prepárate para el show de Ezequiel en la oscuridad!
- 🚪 **Puertas & Luces Funcionales**: Animaciones de 30 FPS para apertura/cierre y luces independientes con inspección de pasillo vacío y alerta de monstruo.
- 📹 **Sistema de Cámaras Completo**: Monitor interactivo con selector de 11 salas (1A, 1B, 1C, 2A, 2B, 3, 4A, 4B, 5, 6, 7), audio ambiente y estática en video WebM.
- 😱 **Jumpscares Sin Artefactos**: Todas las animaciones de ataque cuentan con máscaras alfa difuminadas (feathering), aberración cromática, parpadeo estroboscópico y volumen sonoro real (sin cajas negras ni bordes duros).
- ⚙️ **Noche 7 (Custom Night)**: Configura la inteligencia artificial de los 4 personajes desde el nivel 0 hasta el 20 con dígitos y flechas interactivas.
- 🏆 **Sistema de Guardado & Logros**: Progreso persistente en `localStorage` con estrellas de victoria para las Noches 5, 6 y el modo 20/20/20/20.
- 🔄 **Rejugabilidad Instantánea**: Reinicio limpio de batería, hora, estados y puertas sin necesidad de refrescar el navegador.

---

## 🚀 Inicio Rápido

### Prerrequisitos
- Tener instalado **Python 3** (viene incluido en la mayoría de sistemas).
- Un navegador web moderno (Chrome, Edge, Firefox, Brave, Safari).

### Ejecución en Windows (Recomendado)
Haz doble clic en el archivo:
```bat
start.bat
```

### Ejecución mediante Terminal
1. Clona el repositorio:
   ```bash
   git clone https://github.com/nahueldlsl/fnae.git
   cd fnae
   ```
2. Inicia el servidor local:
   ```bash
   python run_game.py
   ```
3. Abre tu navegador en:
   ```
   http://localhost:8000
   ```
4. Haz clic en la pantalla de bienvenida **`[ HAZ CLIC PARA JUGAR ]`** para desbloquear el audio y sumergirte en la experiencia.

---

## 🕹️ Controles

- **Mover la vista de la oficina**: Mueve el cursor hacia los extremos izquierdo o derecho de la pantalla.
- **Puertas**: Haz clic en el botón superior rojo/verde `DOOR` (o usa las teclas **`Q`** izquierda / **`E`** derecha).
- **Luces de pasillo**: Haz clic en el botón inferior blanco `LIGHT` (o usa las teclas **`A`** izquierda / **`D`** derecha).
- **Monitor de cámaras**: Haz clic en la barra inferior blanca `[ CAMERA ]` (o presiona **`Espacio`**).
- **Cambiar de cámara**: Haz clic sobre cualquiera de los botones de la mini-guía del mapa.
- **Pausa**: Presiona **`Esc`** para pausar/reanudar la partida, ver controles o volver al menú.
- **Silenciar audio**: Presiona **`M`** en cualquier momento para silenciar o reactivar el sonido.
- **Custom Night**: Usa los presets rápidos (`20/20/20/20`, `Noche 5`, `Solo Foxy`, `Reset 0`) o **`Shift + clic`** en las flechas para saltos de ±5.

---

## 🛠️ Pipeline de Personajes y Assets (`assets_src/`)

El proyecto cuenta con una carpeta dedicada en [assets_src/](assets_src/README_ASSETS.md) para cambiar caras o agregar personajes nuevos (5to, 6to, etc.) sin editar el código del juego:
- **Fotos y configuración por personaje**: `assets_src/characters/<id>/character.json` + `source.jpeg`.
- **Plantilla para nuevos personajes**: `assets_src/characters/_template/character.json`.
- **Pipeline unificado en Python**: [tools/build_characters.py](tools/build_characters.py) genera los íconos, jumpscares, luces de puerta, overlays de cámaras y el manifiesto dinámico [config/characters.json](config/characters.json).

Para reconstruir assets o verificar la integridad:
```bash
python3 tools/build_characters.py
python3 tools/verify_assets.py
npm test
```

---

## 📁 Estructura del Proyecto

```
fnae/
├── assets_src/             # Fuentes editables de personajes, fotos y fondos base
│   ├── base_graphics/      # Fondos limpios de oficina y escenario
│   └── characters/         # Carpetas por personaje (freddy, bonnie, chica, foxy, _template)
├── config/                 # Manifiestos declarativos del motor
│   ├── characters.json     # Registro dinámico de personajes, rutas, IA y assets
│   └── game.json           # Duración de horas, consumo eléctrico, salas y audios
├── graphics/               # Texturas, animaciones y salas WebP/PNG generadas
├── sounds/                 # 27 efectos de sonido y pistas ambientales (.wav, .ogg)
├── script/                 # Motor modular ES6 (SOLID / GRASP / DRY / Singleton)
│   ├── core/               # EventBus, TimerRegistry, SaveRepository, AudioManager, AssetLoader
│   ├── systems/            # NightClock, PowerSystem, OfficeSystem, CameraSystem
│   ├── ai/                 # AnimatronicEntity, MovementStrategies, AIManager
│   ├── ui/                 # AnimationController, MenuController, CustomNightView, OfficeView, CameraView
│   ├── GameEngine.js       # Orquestador principal de partida
│   └── app.js              # Composition root
├── tests/                  # Pruebas unitarias automatizadas (`node --test`)
├── tools/                  # Herramientas en Python (build_characters.py, verify_assets.py)
├── index.html              # Estructura HTML5 limpia
├── feed.css / 1080.css     # Estilos responsivos estándar
├── run_game.py             # Servidor HTTP local con tipos MIME correctos
└── start.bat               # Lanzador rápido para Windows
```

---

## ⚖️ Créditos & Disclaimer

- **Concepto original & diseño**: Scott Cawthon (*Five Nights at Freddy's*).
- **Motor Web Base**: Port de ingeniería inversa HTML5/JS (FNAF-JS) por Sam Lynch.
- **Five Nights at Ezequiel's Edition**: Proyecto paródico y educativo desarrollado para Nahuel y Ezequiel.
- *Este proyecto es una creación sin fines de lucro con fines recreativos y educativos.*
