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
| 🐻 **Freddy Fazbear** | **Ezequiel Clásico** | Comienza en el escenario (**CAM 1A**), avanza sigilosamente en la oscuridad, te acecha en la puerta derecha y canta la caja de música cuando se corta la luz. |
| 🐰 **Bonnie** | **Ezequiel (Buzo Bordó)** | Rápido y agresivo. Acecha por el pasillo izquierdo y se asoma por la ventana de tu puerta izquierda. Si prendes la luz y lo ves, ¡cierra la puerta de inmediato! |
| 🐥 **Chica** | **Ezequiel (Escritorio)** | Merodea por el lado derecho y la cocina (escucharás ollas y platos). Aparece en la ventana de tu puerta derecha con mirada fija. |
| 🦊 **Foxy** | **El Amigo Gritando** | Escondido tras la cortina de la Pirate Cove (**CAM 1C**). Si no lo miras con frecuencia, saldrá disparado corriendo por el pasillo (**CAM 2A**) directo hacia tu puerta izquierda. |

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
- **Puertas**: Haz clic en el botón superior rojo/verde `DOOR`.
- **Luces de pasillo**: Haz clic en el botón inferior blanco `LIGHT`.
- **Monitor de cámaras**: Pasa el ratón sobre la barra inferior blanca `[ CAMERA ]`.
- **Cambiar de cámara**: Haz clic sobre cualquiera de los botones de la mini-guía del mapa.

---

## 🛠️ Pipeline de Transformación de Imágenes

El proyecto incluye scripts en Python ([tools/transform_ezequiel.py](tools/transform_ezequiel.py)) que procesan las fotos originales mediante **Pillow**:
- **Detección y recorte de rostros**: Extracción precisa de Ezequiel y su amigo en shock.
- **Máscaras Alfa Suaves (`feathered masks`)**: Bordes elípticos con desenfoque gaussiano para fusionar los rostros con la oficina sin costuras rectangulares.
- **Efectos de Terror FNAF**:
  - Filtros de contraste dinámico y reducción de brillo.
  - Scanlines CRT simuladas.
  - Efecto de aberración cromática (separación de canales R y B).
  - Ojos incandescentes con resplandor concéntrico.

Para re-ejecutar el pipeline de imágenes o verificar la integridad:
```bash
python tools/transform_ezequiel.py
python tools/verify_assets.py
```

---

## 📁 Estructura del Proyecto

```
fnae/
├── graphics/               # Más de 360 texturas, animaciones y salas WebP/PNG
│   ├── camera/             # Mapas, estática, indicadores de batería y hora
│   ├── gameover/           # Jumpscares completos de Freddy, Bonnie, Chica y Foxy
│   ├── mainmenu/           # Menú interactivo, logo, estrellas y Custom Night
│   ├── rooms/              # Fondos de salas de cámaras y oficina
│   └── transition/         # Animaciones de transición estática
├── sounds/                 # 27 efectos de sonido y pistas ambientales (.wav, .ogg)
├── script/                 # Lógica del motor del juego en JavaScript
│   ├── ai.js               # Inteligencia artificial de los 4 animatrónicos
│   ├── animation.js        # Secuencias de jumpscares y puertas
│   ├── loading.js          # Precarga de assets y sincronización
│   ├── main.js             # Bucle principal, control de noches y fin de juego
│   ├── sound.js            # Sistema de audio multicanal
│   ├── ui.js               # Botones, paneo y monitor de cámaras
│   └── variables.js        # Estados del juego, contadores y dificultad
├── tools/                  # Herramientas de automatización en Python
│   ├── transform_ezequiel.py # Pipeline de procesamiento de imágenes con Pillow
│   └── verify_assets.py    # Validador de integridad de archivos y assets
├── index.html              # Estructura principal y overlay de inicio
├── feed.css / 1080.css     # Estilos responsivos de la oficina y cámaras
├── run_game.py             # Servidor HTTP local con tipos MIME correctos
├── start.bat               # Lanzador rápido para Windows
└── README.md
```

---

## ⚖️ Créditos & Disclaimer

- **Concepto original & diseño**: Scott Cawthon (*Five Nights at Freddy's*).
- **Motor Web Base**: Port de ingeniería inversa HTML5/JS (FNAF-JS) por Sam Lynch.
- **Five Nights at Ezequiel's Edition**: Proyecto paródico y educativo desarrollado para Nahuel y Ezequiel.
- *Este proyecto es una creación sin fines de lucro con fines recreativos y educativos.*
