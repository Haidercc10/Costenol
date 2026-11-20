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


def tema_barra_windows():
    """Consulta el tono del sistema usado por la barra de tareas, independiente del tema del editor."""
    if sys.platform == 'win32':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as clave:
                valor, _ = winreg.QueryValueEx(clave, 'SystemUsesLightTheme')
                return 'Claro' if valor else 'Oscuro'
        except OSError:
            pass
    return 'Oscuro'


def icono_ventana(root, vigilar=False):
    """Aplica el isotipo con contraste para la barra de tareas y lo actualiza si cambia Windows.
    La barra oscura usa símbolo claro; la barra clara usa símbolo oscuro. Conserva referencias Tk.
    """
    import tkinter as tk
    tema = tema_barra_windows()
    if getattr(root, '_tema_icono_sistema', None) != tema:
        base = Path(__file__).resolve().parent / 'logo'
        nombre = 'isotipo_oscuro' if tema == 'Claro' else 'isotipo_claro'
        aplicado = False
        # El icono nativo se aplica tanto a esta ventana como a los futuros diálogos.
        # Su carga es independiente del PNG para que un fallo no deje el icono genérico de Tk.
        if sys.platform == 'win32':
            try:
                ruta = ruta_tk(base / (nombre + '.ico'))
                root.iconbitmap(ruta)
                root.iconbitmap(default=ruta)
                aplicado = True
            except (tk.TclError, OSError):
                pass
        try:
            original = tk.PhotoImage(master=root, file=ruta_tk(base / (nombre + '.png')))
            factor = max(1, (max(original.width(), original.height()) + 127) // 128)
            root._logo_sistema = original.subsample(factor, factor)
            # En Windows el ICO conserva sus tamaños específicos para título y barra de tareas.
            if not aplicado:
                root.iconphoto(True, root._logo_sistema)
                aplicado = True
        except (tk.TclError, OSError):
            pass
        if aplicado:
            root._tema_icono_sistema = tema
    if vigilar and not getattr(root, '_vigila_icono', False):
        root._vigila_icono = True
        def comprobar():
            """Revisa el tema del sistema cada cuatro segundos mientras existe la ventana."""
            if root.winfo_exists():
                icono_ventana(root)
                root._tarea_icono = root.after(4000, comprobar)
        def liberar(evento):
            """Cancela la vigilancia al destruir la raíz para no dejar callbacks pendientes."""
            if evento.widget is root and getattr(root, '_tarea_icono', None):
                root.after_cancel(root._tarea_icono)
                root._tarea_icono = None
        root.bind('<Destroy>', liberar, add='+')
        root._tarea_icono = root.after(4000, comprobar)
    return getattr(root, '_logo_sistema', None)


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

