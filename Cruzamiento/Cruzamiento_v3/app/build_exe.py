import PyInstaller.__main__
import os
import shutil

def build():
    print("Iniciando construccion de ejecutables...")

    # Limpiar carpetas de build anteriores
    try:
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("build"):
            shutil.rmtree("build")
    except Exception as e:
        print(f"Advertencia: No se pudo limpiar carpeta dist/build completamente: {e}")

    # Definir separador de ruta para add-data (; para Windows, : para Unix)
    sep = ";" 
    
    # Datos comunes a incluir
    # config_camera.json (por defecto), carpeta assets (iconos), modelos
    add_data = [
        f"config_camera.json{sep}.",
        f"assets{sep}assets",
        f"models{sep}models",
    ]

    # --- 1. Construir App Principal (CruzamientoApp) ---
    print("\nConstruyendo App Principal (CruzamientoApp)...")
    
    # Usamos src/main.py como punto de entrada para asegurar paths correctos
    PyInstaller.__main__.run([
        'src/main.py',
        '--name=CruzamientoApp',
        '--noconsole',  # Ocultar consola (usar --console para debug)
        '--icon=assets/icono.ico',
        # Incluir paths de datos
        *[f'--add-data={d}' for d in add_data],
        # Imports ocultos que PyInstaller podría perder
        '--hidden-import=pyside6',
        '--hidden-import=ultralytics',
        '--hidden-import=opencv-python',
        # Asegurar que src esta en el path
        '--paths=src',
        '--clean',
        '--noconfirm', # Overwrite output directory
    ])

    # --- 2. Construir Monitor PLC (plc_monitor.py) ---
    print("\nConstruyendo Monitor PLC...")
    
    PyInstaller.__main__.run([
        'src/services/plc_monitor.py',
        '--name=plc_monitor',
        '--console',  # Monitor NECESITA consola
        '--icon=assets/icono.ico',
        '--clean',
        '--noconfirm',
    ])

    print("\nConstruccion completada.")
    print("Organizando salida...")
    
    # Mover el exe del monitor a la carpeta de la app principal para portabilidad
    # Al usar onedir (default), tenemos dist/CruzamientoApp/ y dist/plc_monitor/
    # Queremos todo en dist/CruzamientoApp/
    
    source_monitor = os.path.join("dist", "plc_monitor", "plc_monitor.exe")
    dest_dir = os.path.join("dist", "CruzamientoApp")
    
    if os.path.exists(source_monitor):
        shutil.copy(source_monitor, dest_dir)
        print(f"   Copiado plc_monitor.exe a {dest_dir}")
    else:
        print("Advertencia: No se encontro plc_monitor.exe para mover.")

    print(f"\nListo! La aplicacion portable esta en: {os.path.abspath(dest_dir)}")

if __name__ == "__main__":
    build()
