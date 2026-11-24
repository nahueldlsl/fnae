# 🎨 Carpeta de Assets y Personajes (`assets_src/`)

Esta carpeta centraliza las fotos originales, los fondos base y la configuración de cada personaje para que puedas **reemplazar caras existentes** o **agregar personajes nuevos** sin editar el código JavaScript ni HTML del juego.

## 📁 Estructura

```text
assets_src/
├── base_graphics/       # Fondos limpios de oficina y salas (no editar salvo que quieras cambiar el escenario)
└── characters/
    ├── freddy/          # Personaje 1 (Ezequiel)
    ├── bonnie/          # Personaje 2 (Sebastián)
    ├── chica/           # Personaje 3 (Santi)
    ├── foxy/            # Personaje 4 (Horacio)
    └── _template/       # Plantilla lista para copiar y crear un 5to+ personaje
```

## 🔄 Cómo cambiar la foto de un personaje existente

1. Entra a `assets_src/characters/<personaje>/` (por ejemplo, `bonnie/`).
2. Reemplaza `source.jpeg` por tu nueva foto (puedes usar `.jpg`, `.jpeg`, `.png` o `.webp` actualizando `"sourceImage"` en `character.json`).
3. Si quieres ajustar el recorte, cambia `"iconCrop"`, `"jumpscareCrop"` o `"doorLight.crop"` (`[x1, y1, x2, y2]`), o pon `null` para usar un recorte cuadrado centrado automático.
4. Ejecuta desde la raíz del proyecto:
   ```bash
   python3 tools/build_characters.py
   python3 tools/verify_assets.py
   ```

## ➕ Cómo agregar un personaje nuevo (5to, 6to, etc.)

1. Copia la carpeta `assets_src/characters/_template/` a un nuevo nombre, por ejemplo `assets_src/characters/juan/`.
2. Coloca dentro su foto como `source.jpeg`.
3. Edita `assets_src/characters/juan/character.json`:
   - Cambia `"id"` a `"juan"`, `"displayName"` a `"Juan"`, y `"customNightOrder"` a `5` (o el orden que prefieras).
   - Elige su `"strategy"`:
     - `"roamer"`: merodea por `route` hacia la puerta `"left"` o `"right"` y aparece en la luz de la puerta.
     - `"freddy"`: avanza sigilosamente y se congela si miras la cámara `4b`.
     - `"cove_rusher"`: espera en `1c` y corre hacia la puerta izquierda si no revisas las cámaras.
   - Configura `"roomOverlays"` para indicar en qué salas (`"1b"`, `"2a"`, `"2b"`, etc.) quieres que se genere una imagen con su rostro superpuesto automáticamente.
4. Ejecuta:
   ```bash
   python3 tools/build_characters.py
   python3 tools/verify_assets.py
   ```
5. ¡Listo! El motor leerá `config/characters.json` automáticamente, precargará sus frames, lo añadirá a la partida y generará su tarjeta en **Custom Night** sin tocar código.
