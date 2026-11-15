"""Recursos y configuración de escritorio para ejecución desde código o portable."""
from pathlib import Path
import sys
import os


def carpeta_ejemplos():
    """Busca ejemplos editables junto al ejecutable o junto al código fuente."""
    base = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    return base / 'ejemplos'


def identidad_windows():
    """Asigna identidad propia en la barra de tareas e icono del isotipo a todas las ventanas Tk."""
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Costenol.Editor.Portable.1')
        except (AttributeError, OSError):
            pass


def icono_ventana(root):
    """Aplica el ICO incluido al escritorio Windows y sus nuevos diálogos, si está disponible."""
    if sys.platform == 'win32':
        import tkinter as tk
        ruta = Path(__file__).resolve().parent / 'logo' / 'costenol.ico'
        try:
            root.iconbitmap(default=ruta_tk(ruta))
        except (tk.TclError, OSError):
            pass


def ruta_tk(archivo):
    """Devuelve una ruta relativa para los recursos nativos de Tk cuando comparten unidad.
    Conserva la ruta absoluta si el directorio de trabajo está en otra unidad de Windows.
    """
    try:
        return os.path.relpath(archivo, Path.cwd()).replace(chr(92), '/')
    except ValueError:
        return str(archivo).replace(chr(92), '/')


def configurar_tk_portable():
    """Localiza Tcl/Tk incluidos en el portable sin depender del Python instalado ni del cwd."""
    if getattr(sys, 'frozen', False):
        base = Path(__file__).resolve().parent
        os.environ['TCL_LIBRARY'] = ruta_tk(base / '_tcl_data')
        os.environ['TK_LIBRARY'] = ruta_tk(base / '_tk_data')

