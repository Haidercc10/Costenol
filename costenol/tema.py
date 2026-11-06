"""Tema oscuro y diálogos de la aplicación, sin dependencias externas."""
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, filedialog

OSCURO = {'fondo': '#0d1117', 'panel': '#161b22', 'elevado': '#212936',
           'texto': '#e6edf3', 'suave': '#9daabc', 'borde': '#303b4b',
           'acento': '#78aaff', 'seleccion': '#29456c',
           'error': '#ff929b', 'ok': '#7ee2ac'}

CLARO = {'fondo': '#edf1f7', 'panel': '#ffffff', 'elevado': '#e0e6ef',
         'texto': '#172337', 'suave': '#4b5c73', 'borde': '#bdc9d8',
         'acento': '#245b9a', 'seleccion': '#c6dcf7',
         'error': '#a72035', 'ok': '#166b42'}
PALETAS = {'Oscuro': OSCURO, 'Claro': CLARO}
COLORES = dict(OSCURO)
TEMA_ACTUAL = 'Oscuro'


def barra_oscura(ventana):
    """Solicita una barra de título oscura en Windows; otros sistemas conservan su decoración."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        ventana.update_idletasks()
        handle = ctypes.windll.user32.GetParent(ventana.winfo_id())
        valor = ctypes.c_int(TEMA_ACTUAL == 'Oscuro')
        for atributo in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(handle, atributo, ctypes.byref(valor), ctypes.sizeof(valor)) == 0:
                break
    except (AttributeError, OSError):
        pass


def aplicar_tema(root, nombre='Oscuro'):
    """Aplica Claro u Oscuro a los estilos y a los futuros diálogos.
    Actualiza COLORES sin reemplazar el diccionario compartido por la interfaz."""
    global TEMA_ACTUAL
    paleta = PALETAS[nombre]
    TEMA_ACTUAL = nombre
    COLORES.clear()
    COLORES.update(paleta)
    c = COLORES
    root.configure(bg=c['fondo'])
    for opcion, valor in {'background': c['panel'], 'foreground': c['texto'],
                          'activeBackground': c['seleccion'], 'activeForeground': c['texto'],
                          'selectBackground': c['seleccion'], 'selectForeground': c['texto'],
                          'insertBackground': c['texto'], 'highlightBackground': c['borde'],
                          'highlightColor': c['acento'], 'troughColor': c['fondo'],
                          'disabledForeground': '#68768a', 'font': '{Segoe UI} 10'}.items():
        root.option_add('*' + opcion, valor)
    estilo = ttk.Style(root)
    estilo.theme_use('clam')
    estilo.configure('.', background=c['fondo'], foreground=c['texto'], font=('Segoe UI', 10))
    estilo.configure('TFrame', background=c['fondo'])
    estilo.configure('TLabel', background=c['fondo'], foreground=c['suave'])
    estilo.configure('Titulo.TLabel', foreground=c['texto'], font=('Segoe UI', 21, 'bold'))
    estilo.configure('TButton', background=c['elevado'], foreground=c['texto'],
                     bordercolor=c['borde'], lightcolor=c['elevado'], darkcolor=c['elevado'],
                     padding=(12, 8), focusthickness=1, focuscolor=c['acento'])
    estilo.map('TButton', background=[('disabled', c['panel']), ('pressed', c['seleccion']), ('active', '#303d50' if nombre == 'Oscuro' else '#cbd7e8')],
               foreground=[('disabled', '#68768a')])
    estilo.configure('Accion.TButton', background='#244a75', foreground='#f0f6ff')
    estilo.map('Accion.TButton', background=[('disabled', c['panel']), ('pressed', '#1c3e65'), ('active', '#305e92')])
    estilo.configure('TEntry', fieldbackground=c['panel'], foreground=c['texto'], insertcolor=c['texto'], bordercolor=c['borde'], padding=7)
    estilo.map('TEntry', fieldbackground=[('focus', c['panel'])], bordercolor=[('focus', c['acento'])])
    estilo.configure('TPanedwindow', background=c['borde'])
    for orientacion in ('Vertical', 'Horizontal'):
        nombre = orientacion + '.TScrollbar'
        estilo.configure(nombre, background=c['elevado'], troughcolor=c['fondo'],
                         arrowcolor=c['suave'], bordercolor=c['fondo'], lightcolor=c['elevado'], darkcolor=c['elevado'])
        estilo.map(nombre, background=[('active', '#40516a'), ('pressed', '#506886')])
    estilo.configure('TCombobox', fieldbackground=c['panel'], background=c['elevado'],
                     foreground=c['texto'], arrowcolor=c['texto'], padding=5)
    estilo.map('TCombobox', fieldbackground=[('readonly', c['panel'])],
               foreground=[('readonly', c['texto'])], selectbackground=[('readonly', c['panel'])],
               selectforeground=[('readonly', c['texto'])])
    barra_oscura(root)


def dialogo(parent, titulo, mensaje, opciones, entrada=False):
    """Muestra un diálogo modal oscuro; devuelve el valor elegido o None al cancelar.\n    En modo entrada devuelve texto, incluida la cadena vacía, al aceptar.
    """
    ventana = tk.Toplevel(parent)
    ventana.withdraw()
    ventana.title(titulo)
    ventana.configure(bg=COLORES['fondo'])
    ventana.resizable(False, False)
    ventana.transient(parent)
    resultado = [None]
    marco = ttk.Frame(ventana, padding=24)
    marco.pack(fill='both', expand=True)
    ttk.Label(marco, text=titulo, style='Titulo.TLabel').pack(anchor='w', pady=(0, 12))
    ttk.Label(marco, text=mensaje, wraplength=460, justify='left').pack(anchor='w', pady=(0, 18))
    campo = None
    if entrada:
        campo = ttk.Entry(marco, width=48)
        campo.pack(fill='x', pady=(0, 18))
    botones = ttk.Frame(marco)
    botones.pack(fill='x')

    def elegir(valor):
        """Guarda la opción o entrada elegida y cierra el diálogo modal."""
        resultado[0] = campo.get() if entrada and valor is True else valor
        ventana.destroy()

    for texto, valor in opciones:
        ttk.Button(botones, text=texto, command=lambda v=valor: elegir(v)).pack(side='right', padx=(8, 0))
    ventana.bind('<Escape>', lambda e: elegir(None))
    ventana.protocol('WM_DELETE_WINDOW', lambda: elegir(None))
    if entrada:
        ventana.bind('<Return>', lambda e: elegir(True))
    ventana.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - ventana.winfo_reqwidth()) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - ventana.winfo_reqheight()) // 2)
    ventana.geometry(f'+{x}+{y}')
    ventana.deiconify()
    barra_oscura(ventana)
    ventana.wait_visibility()
    ventana.grab_set()
    (campo or ventana).focus_set()
    parent.wait_window(ventana)
    # Si este diálogo se abrió desde otro modal, restablecer su captura de teclado.
    if parent.winfo_exists() and isinstance(parent, tk.Toplevel):
        parent.grab_set()
    return resultado[0]


def avisar(parent, titulo, mensaje):
    """Presenta un mensaje de archivo o validación mediante una ventana oscura."""
    dialogo(parent, titulo, mensaje, [('Aceptar', True)])


class SelectorArchivo(filedialog.FileDialog):
    """Selector Tk oscuro para evitar los diálogos claros del sistema operativo."""
    def __init__(self, parent, guardar=False):
        """Construye un selector de archivos con navegación y filtro de extensiones."""
        self.guardar = guardar
        super().__init__(parent, title='Guardar programa' if guardar else 'Abrir programa')
        self.top.geometry('800x480')
        self.top.minsize(640, 380)
        self.top.configure(bg=COLORES['fondo'])
        self.ok_button.configure(text='Guardar' if guardar else 'Abrir', padx=16, pady=7, relief='flat')
        self.filter_button.configure(text='Aplicar filtro', padx=16, pady=7, relief='flat')
        self.cancel_button.configure(text='Cancelar', padx=16, pady=7, relief='flat')
        for lista in (self.files, self.dirs):
            lista.configure(bg=COLORES['panel'], fg=COLORES['texto'], relief='flat',
                            selectbackground=COLORES['seleccion'], selectforeground=COLORES['texto'])
        for campo in (self.filter, self.selection):
            campo.configure(bg=COLORES['fondo'], fg=COLORES['texto'], relief='flat')
        ttk.Label(self.top, text='Carpetas a la izquierda · Archivos a la derecha\nFiltro: *.pqek, *.cost o * para todos', padding=8).pack(side='top', fill='x')
        barra_oscura(self.top)

    def ok_command(self):
        """Valida la selección y confirma sobrescrituras; devuelve la ruta al cerrar."""
        archivo = Path(self.get_selection())
        if not self.guardar:
            if archivo.is_file():
                self.quit(str(archivo))
            else:
                avisar(self.top, 'Archivo no válido', 'Selecciona un archivo existente.')
            return
        if not archivo.suffix:
            archivo = archivo.with_suffix('.pqek')
        if archivo.is_dir() or not archivo.parent.is_dir():
            avisar(self.top, 'Ruta no válida', 'Elige un nombre de archivo y una carpeta existente.')
            return
        if archivo.exists():
            respuesta = dialogo(self.top, 'Reemplazar archivo', f'¿Reemplazar {archivo.name}?', [('Reemplazar', True), ('Cancelar', None)])
            if respuesta is not True:
                return
        self.quit(str(archivo))


def seleccionar_archivo(parent, archivo=None, guardar=False):
    """Abre el selector oscuro y devuelve una ruta o None si se cancela.\n    Inicia en ejemplos o en la carpeta del documento actual.
    """
    carpeta = archivo.parent if archivo else Path(__file__).parent / 'ejemplos'
    if not carpeta.is_dir():
        carpeta = Path(__file__).parent
    nombre = (archivo.with_suffix('.pqek').name if archivo else 'programa.pqek') if guardar else ''
    return SelectorArchivo(parent, guardar).go(str(carpeta), pattern='*', default=nombre)
