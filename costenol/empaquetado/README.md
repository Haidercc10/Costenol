# Preparar de nuevo el portable

Desde un equipo Windows x64 con Python 3.10+ y Tcl/Tk funcional:

1. Comprueba la ventana: `python -m tkinter`.
2. Instala la herramienta de construcción:
   `python -m pip install -r empaquetado/requisitos-construccion.txt`
3. Ejecuta en PowerShell desde costenol:
   `& ./empaquetado/construir.ps1`
4. Copia TODA la carpeta dist/Costenol al otro equipo; conserva _internal y ejemplos.

El ejecutable contiene Python y Tcl/Tk, por lo que el destinatario no los instala.
La distribución elegida es una carpeta portable (onedir), no un único archivo
que extraiga librerías en cada inicio. Se incluye el icono logo/costenol.ico y
los PNG usados por los temas y la bienvenida.

La llamada multiprocessing.freeze_support() permite el arranque correcto del
proceso independiente de bienvenida dentro del ejecutable de PyInstaller.
recursos.py resuelve los ejemplos editables junto al exe y asigna la identidad
de la barra de tareas. Los recursos internos se incluyen con el paquete.

Las herramientas de empaquetado se necesitan solo para reconstruir. La aplicación
desde código utiliza únicamente la biblioteca estándar y los recursos de logo.

Autoprueba opcional (desde la carpeta del portable):

    ./Costenol.exe --autoprueba ./resultado.json

Comprueba Tk, logos, icono, pestañas, tema e interpretación con datos simulados.
El resultado debe indicar OK y todos los indicadores en true. No sustituye la
inspección visual ni la comprobación en otro equipo.
