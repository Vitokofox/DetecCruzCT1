# Sistema de Detección de Cruzamiento (Versión 3)

Este proyecto es una aplicación de escritorio avanzada para la detección de defectos y cruzamiento en líneas de producción, utilizando visión por computadora (YOLO) e integración con PLC vía Modbus TCP.

## Estructura del Proyecto

El proyecto ha sido refactorizado para seguir una arquitectura modular:

*   **app/**: Directorio raíz de la aplicación.
    *   **src/**: Código fuente organizado en módulos.
        *   **ui/**: Componentes de interfaz gráfica (Ventanas, Alertas).
        *   **services/**: Servicios de backend (Cámaras, Detección, PLC, Grabación).
        *   **utils/**: Utilidades generales y análisis de piezas.
        *   **main.py**: Punto de entrada de la aplicación.
        *   **config.py**: Gestión centralizada de configuración.
    *   **assets/**: Recursos gráficos (iconos, logos).
    *   **models/**: Modelos de Inteligencia Artificial (YOLO .pt).
    *   **dist/**: Carpeta de salida para el ejecutable portable.
    *   **logs/**: Archivos de registro de eventos y errores.
    *   **detecciones/**: Imágenes guardadas de detecciones.
    *   **grabaciones/**: Videos grabados automáticamente.

## Requisitos Previos

*   Sistema Operativo: Windows 10 u 11 (64-bits recomendado).
*   Hardware: Cámara USB/Industrial conectada, Conexión Ethernet a PLC (opcional).
*   Software (solo para desarrollo): Python 3.10 o superior (recomendado 3.11+).

---

## 1. Instalación y Configuración (Para Desarrolladores)

Si deseas ejecutar la aplicación desde el código fuente o modificarla, sigue estos pasos:

### Paso 1: Configurar el Entorno
Hemos incluido un script automático para facilitar este proceso.

1.  Navega a la carpeta `app`.
2.  Ejecuta el archivo **`setup_env.bat`** (doble clic).
    *   Este script creará un entorno virtual aislado (`.venv`).
    *   Instalará automáticamente todas las librerías necesarias (`PySide6`, `ultralytics`, `opencv`, etc.) desde `requirements.txt`.

### Paso 2: Ejecutar la Aplicación
Una vez configurado el entorno, tienes dos opciones:

*   **Opción A (Fácil)**: Ejecuta el archivo **`run_app.bat`**.
    *   Este script activa el entorno virtual y lanza `src/main.py` automáticamente sin mostrar consola negra.
*   **Opción B (Manual)**:
    1.  Abre una terminal en la carpeta `app`.
    2.  Activa el entorno: `.venv\Scripts\activate`
    3.  Ejecuta: `python src/main.py`

---

## 2. Generar Versión Portable (Para USB / Producción)

Para desplegar la aplicación en los computadores de operación (que no tienen Python instalado), debes generar un ejecutable "portable".

1.  Asegúrate de haber completado la configuración del entorno (Paso 1).
2.  Abre una terminal en la carpeta `app` y activa el entorno (`.venv\Scripts\activate`).
3.  Ejecuta el script de construcción:
    ```bash
    python build_exe.py
    ```
4.  El proceso puede tardar unos minutos. Construirá tanto la **App Principal** como el **Monitor PLC**.

### ¿Dónde está el ejecutable?
El resultado se guardará en la carpeta:
`Cruzamiento_v3\app\dist\CruzamientoApp`

Esta carpeta contendrá:
*   `CruzamientoApp.exe`: La aplicación principal.
*   `plc_monitor.exe`: Herramienta de diagnóstico PLC incluida.
*   Carpeta `models`: Modelos YOLO necesarios.
*   Carpeta `assets`: Iconos y recursos.
*   `config_camera.json`: Archivo de configuración por defecto.

---

## 3. Ejecutar desde USB (Modo Operador)

Para usar la aplicación en un PC de planta:

1.  Copia la **carpeta completa** `CruzamientoApp` (ubicada en `dist`) a tu memoria USB o disco duro del PC destino.
    *   ⚠️ **IMPORTANTE**: No copies solo el archivo `.exe`. Debes copiar la carpeta entera, ya que contiene dependencias, modelos y configuraciones.
2.  En el PC destino, abre la carpeta `CruzamientoApp`.
3.  Ejecuta el archivo **`CruzamientoApp.exe`** (icono del sistema).

El sistema arrancará automáticamente, cargará los modelos y conectará las cámaras.

---

## Solución de Problemas Comunes

### La aplicación no inicia o se cierra inmediatamente
*   Revise la carpeta `logs` (se crea automáticamente en la carpeta de ejecución) para ver detalles del error.
*   Verifique que los drivers de la cámara estén instalados.

### Error: "Model not found"
*   Asegúrese de que copió la carpeta completa `CruzamientoApp` y no solo el ejecutable.
*   Verifique que dentro de la carpeta exista la subcarpeta `models` con archivos `.pt`.

### Error de Conexión PLC
*   Verifique el cable de red y la IP configurada en el botón "Configuración" de la aplicación.
*   Asegúrese de que el PLC esté encendido y alcanzable (pinchen la IP desde la terminal con `ping <IP>`).
*   Puede usar la herramienta `plc_monitor.exe` incluida en la carpeta para diagnosticar la conexión independientemente de la app principal.
