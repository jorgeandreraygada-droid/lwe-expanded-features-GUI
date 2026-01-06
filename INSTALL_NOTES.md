# Notas de instalación y cambios realizados

Descripción breve
-----------------
He actualizado el instalador y dependencias para que la instalación sea lo más "plug-and-play" posible y documentado. A continuación tienes un resumen de lo que he cambiado, por qué y cómo revertir o ajustar las acciones.

Cambios realizados
------------------
1. `install.sh` (reemplazado por una versión más robusta)
   - Mejoras principales:
     - Detección de versión de Python (requiere 3.10+; se puede forzar continuar manualmente).
     - Soporte para opciones CLI:
       - `--skip-system-deps`: no instalar paquetes del sistema (útil en entornos controlados).
       - `--non-interactive`: no preguntar al usuario (útil para automatización).
       - `--dry-run`: simula las acciones sin ejecutarlas.
       - `--venv-path PATH`: especifica la ruta del entorno virtual (por defecto `.venv`).
       - `--install-backend`: clona `linux-wallpaperengine` si no está presente (requiere `git`).
     - Manejo de detection del gestor de paquetes (apt, pacman, dnf, zypper) y comandos para instalar **wmctrl**, **xdotool**, **python3-tk** y **python3-pillow/python3-pil**.
     - Crea y activa virtualenv, actualiza pip/setuptools/wheel e instala `requirements.txt`.
     - Marca ejecutables (`source/run.sh`, `source/core/main.sh`, `install.sh`).
     - Crea directorios estándar: `~/.local/share/linux-wallpaper-engine-features/` y `~/.config/linux-wallpaper-engine-features/`.
     - Opción para crear una entrada de escritorio (desktop entry) en `~/.local/share/applications/`.
     - Mensajes claros al final con pasos siguientes.

   - Cómo usar:
     - Instalación recomendada interactiva:
       ```bash
       chmod +x install.sh
       ./install.sh
       ```
     - Instalación no interactiva y sin instalar paquetes del sistema (por ejemplo en containers):
       ```bash
       ./install.sh --non-interactive --skip-system-deps
       ```
     - Ver qué haría (sin cambios):
       ```bash
       ./install.sh --dry-run
       ```

2. `requirements.txt` (actualizado)
   - Ahora contiene:
     - `Pillow>=9.5.0,<11` (versión fijada con rango compatible).   - **Se añadió `requirements.lock.txt`** para reproducir exactamente el `.venv` del mantenedor:
     - Contiene `pip==25.3`, `pillow==12.1.0`, `setuptools==80.9.0`, `wheel==0.45.1`.
     - `install.sh` usa `requirements.lock.txt` por defecto si existe, lo que asegura que la venv creada sea idéntica a la tuya.   - Nota: `tkinter` no se instala desde PyPI; debe ser proporcionado por paquetes del sistema (`python3-tk` / `python3-tkinter`).

3. `README.md`
   - No se han cambiado grandes secciones de contenido, pero puedes pedirme que añada un bloque de ejemplo para los flags del instalador (lo puedo actualizar si lo deseas).

4. `INSTALL_NOTES.md` (este fichero)
   - Documento explicando los cambios, instrucciones de uso y cómo revertir.

Qué probé / comprobé
--------------------
- He revisado los imports dentro de `source/` para listar dependencias PyPI y de sistema.
- Verifiqué que `GUI.py` lanza `WallpaperEngineGUI` y que las funciones usan `PIL` y `tkinter`.
- Validé que el instalador cubre los casos más comunes de gestores de paquetes.

Sugerencias / pasos adicionales recomendados
------------------------------------------
- Prueba el instalador en una máquina de prueba o VM antes de usarlo en producción, en particular la parte de instalación de paquetes del sistema.
- Si quieres, puedo añadir verificación automatizada (comprobaciones posteriores a la instalación) o un script `setup_ci.sh` para ejecutar en un contenedor docker.
- Si prefieres que el instalador instale automáticamente el backend `linux-wallpaperengine` y lo configure (más allá de clonar), puedo ampliar esa sección y testearla.

Cómo revertir
-------------
- Para revertir cambios automáticos del instalador (si ejecutaste el comando de gestor de paquetes), revisa el historial del paquete del gestor (`apt`, `dnf`, etc.).
- Para desinstalar las dependencias Python:
  ```bash
  source .venv/bin/activate
  pip uninstall -r requirements.txt
  deactivate
  rm -rf .venv
  ```
- Para borrar la entrada del escritorio:
  ```bash
  rm ~/.local/share/applications/linux-wallpaper-engine-features.desktop
  ```

¿Quieres que pruebe el instalador en modo `--dry-run` o que ejecute una instalación en un entorno controlado (si me indicas que lo haga)?

---

Si quieres, puedo ahora:
- Ejecutar un `--dry-run` (no cambia nada) y mostrar la salida aquí.
- Añadir una sección en `README.md` explicando las flags del instalador.
- Implementar comprobaciones adicionales (por ejemplo, verificar que `linux-wallpaperengine` arranca correctamente).

Si prefieres, procedo con la siguiente tarea planificada (me indicas cuál).