"""Editor de escritorio para Costeñol. Ejecutar: python interfaz.py"""
from pathlib import Path
import re
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from tema import aplicar_tema, COLORES, dialogo, avisar, seleccionar_archivo
from capturas import FORMATOS
from revision import RevisionAutomatica, EditorObservable
from inicio import InicioIndependiente
from componentes import InterruptorTema
from resaltado import rangos_sintaxis, PALETAS_SINTAXIS
from archivos import ruta_guardado
from recursos import identidad_windows, icono_ventana, ruta_tk, configurar_tk_portable
from lexer import ErrorLexico
from parser import ErrorSintactico
from semantico import analizar_semantica, ErrorSemantico
from interprete import ejecutar, ErrorEjecucion

ERRORES = (ErrorLexico, ErrorSintactico, ErrorSemantico, ErrorEjecucion)
NOMBRES = {ErrorLexico: 'Error léxico', ErrorSintactico: 'Error sintáctico',
           ErrorSemantico: 'Error semántico', ErrorEjecucion: 'Error de ejecución'}
EJEMPLO = 'nombre Texto;\nMensaje.Texto("¿Como te llamas?");\nnombre = Captura.Texto();\nMensaje.Texto("Hola, " + nombre);\n'


class Aplicacion:
    def __init__(self, root):
        """Recibe la ventana raíz y construye editor, números de línea, botones y resultados.
        Conecta eventos y atajos, inicializa el estado y carga un programa de ejemplo.
        """
        self.root = root
        self.archivo = None
        self.documentos = {}
        self.activa = None
        self.cambiando_documento = False
        self.contador_documentos = 0
        self.ocupada = False
        self.ultimo_codigo = None
        self.linea_error = None
        self.detalle_error = None
        self.diagnostico = tk.StringVar(value='')
        self.revision = RevisionAutomatica(root.after, root.after_cancel, self.publicar_diagnostico)
        root.title('Costeñol — Editor')
        root.geometry('1050x760')
        root.minsize(920, 560)
        root.protocol('WM_DELETE_WINDOW', self.cerrar)
        aplicar_tema(root)
        self.crear_menus()
        cabecera = ttk.Frame(root, padding=(16, 12))
        cabecera.pack(fill='x')
        self.cargar_logo(cabecera)
        ttk.Label(cabecera, text='Editor y ejecución de programas', padding=(20, 0)).pack(side='left')
        selector_tema = ttk.Frame(cabecera)
        selector_tema.pack(side='right')
        ttk.Label(selector_tema, text='Tema', padding=(0, 0, 8, 0)).pack(side='left')
        self.tema = tk.StringVar(value='Oscuro')
        self.selector_tema = InterruptorTema(selector_tema, self.tema, self.cambiar_tema)
        self.selector_tema.pack(side='left')
        barra = ttk.Frame(root, padding=(16, 0, 16, 10))
        barra.pack(fill='x')
        self.botones = []
        for texto, funcion in [('Analizar · F5', self.analizar), ('Ejecutar · F6', self.ejecutar),
                               ('Cerrar pestaña · Ctrl+W', self.cerrar_pestana)]:
            boton = ttk.Button(barra, text=texto, command=funcion,
                               style='Accion.TButton' if funcion in (self.analizar, self.ejecutar) else 'TButton')
            boton.pack(side='left', padx=(0, 6))
            self.botones.append(boton)
        paneles = ttk.Panedwindow(root, orient='vertical')
        self.paneles = paneles
        paneles.pack(fill='both', expand=True, padx=16)
        self.panel_diagnostico = ttk.Label(root, textvariable=self.diagnostico,
                                           foreground=COLORES['error'], wraplength=850,
                                           justify='left', padding=(10, 8))
        self.pestanas = ttk.Notebook(paneles, style='Documentos.TNotebook')
        paneles.add(self.pestanas, weight=3)
        self.pestanas.bind('<<NotebookTabChanged>>', self.cambiar_documento)
        self.pestanas.bind('<Button-2>', self.cerrar_con_raton)
        self.pestanas.bind('<ButtonRelease-1>', self.cerrar_desde_icono)
        salida = ttk.Frame(paneles)
        paneles.add(salida, weight=1)
        encabezado = ttk.Frame(salida)
        encabezado.pack(fill='x')
        ttk.Label(encabezado, text='RESULTADOS', padding=(0, 6)).pack(side='left')
        ttk.Button(encabezado, text='Limpiar', command=self.limpiar).pack(side='right')
        self.salida = tk.Text(salida, height=10, wrap='word', state='disabled',
                              font=('Consolas', 11), bg=COLORES['panel'], fg=COLORES['texto'],
                              selectbackground=COLORES['seleccion'], selectforeground=COLORES['texto'],
                              relief='flat', padx=12, pady=12)
        scroll_salida = ttk.Scrollbar(salida, command=self.salida.yview)
        scroll_salida.pack(side='right', fill='y')
        self.salida.configure(yscrollcommand=scroll_salida.set)
        self.salida.pack(fill='both', expand=True)
        self.salida.tag_configure('error', foreground=COLORES['error'])
        self.salida.tag_configure('ok', foreground=COLORES['ok'])
        self.estado = tk.StringVar(value='Listo · F5 analiza · F6 ejecuta')
        self.barra_estado = ttk.Label(root, textvariable=self.estado, padding=(16, 8))
        self.barra_estado.pack(side='bottom', fill='x', before=self.paneles)
        for tecla, funcion in [('<Control-n>', self.nuevo), ('<Control-o>', self.abrir),
                               ('<Control-s>', self.guardar), ('<F5>', self.analizar), ('<F6>', self.ejecutar)]:
            root.bind(tecla, lambda e, f=funcion: self.atajo(f))
        self.root.bind('<Control-w>', lambda e: self.atajo(self.cerrar_pestana))
        self.root.bind('<Control-Tab>', lambda e: self.atajo(self.siguiente_pestana))
        self.root.bind('<Control-Shift-S>', lambda e: self.atajo(self.guardar_como))
        self.nueva_pestana(EJEMPLO)

    def crear_menus(self):
        """Construye una barra de menús estilo editor con acciones reales y atajos visibles."""
        self.barra_menus = ttk.Frame(self.root, padding=(6, 2))
        self.barra_menus.pack(fill='x')
        self.menus = []
        self.botones_menu = []
        grupos = [
            ('Archivo', [('Nuevo', self.nuevo, 'Ctrl+N'), ('Abrir…', self.abrir, 'Ctrl+O'),
                         ('Guardar', self.guardar, 'Ctrl+S'), ('Guardar como…', self.guardar_como, 'Ctrl+Shift+S'),
                         ('Cerrar pestaña', self.cerrar_pestana, 'Ctrl+W'), ('Salir', self.cerrar, '')]),
            ('Editar', [('Deshacer', lambda: self.evento_editor('<<Undo>>'), 'Ctrl+Z'),
                        ('Rehacer', lambda: self.evento_editor('<<Redo>>'), 'Ctrl+Y'),
                        ('Cortar', lambda: self.evento_editor('<<Cut>>'), 'Ctrl+X'),
                        ('Copiar', lambda: self.evento_editor('<<Copy>>'), 'Ctrl+C'),
                        ('Pegar', lambda: self.evento_editor('<<Paste>>'), 'Ctrl+V')]),
            ('Selección', [('Seleccionar todo', self.seleccionar_todo, 'Ctrl+A')]),
            ('Ver', [('Cambiar claro / oscuro', lambda: self.selector_tema.alternar(), ''),
                     ('Siguiente archivo', self.siguiente_pestana, 'Ctrl+Tab')]),
            ('Ejecutar', [('Analizar archivo activo', self.analizar, 'F5'),
                         ('Ejecutar archivo activo', self.ejecutar, 'F6')]),
            ('Ayuda', [('Acerca de Costeñol', self.acerca_de, '')]),
        ]
        for nombre, acciones in grupos:
            boton = tk.Button(self.barra_menus, text=nombre, relief='flat', overrelief='flat',
                              borderwidth=0, highlightthickness=0, padx=8, pady=4,
                              font=('Segoe UI', 10), cursor='hand2', takefocus=True)
            menu = tk.Menu(boton, tearoff=False)
            for texto, funcion, atajo in acciones:
                menu.add_command(label=texto, command=lambda f=funcion: self.atajo(f), accelerator=atajo)
            boton.configure(command=lambda b=boton, m=menu: self.desplegar_menu(b, m))
            boton.pack(side='left', padx=0)
            self.botones_menu.append(boton)
            self.menus.append(menu)
        self.colorear_menus()

    def desplegar_menu(self, boton, menu):
        """Abre las opciones bajo la palabra pulsada; pasar el ratón no despliega ningún menú."""
        try:
            menu.tk_popup(boton.winfo_rootx(), boton.winfo_rooty() + boton.winfo_height())
        finally:
            menu.grab_release()

    def colorear_menus(self):
        """Adapta los menús desplegables a la paleta activa, sin usar el menú nativo claro."""
        for boton in self.botones_menu:
            boton.configure(bg=COLORES['fondo'], fg=COLORES['texto'],
                             activebackground=COLORES['elevado'], activeforeground=COLORES['texto'])
        for menu in self.menus:
            menu.configure(bg=COLORES['panel'], fg=COLORES['texto'],
                           activebackground=COLORES['seleccion'], activeforeground=COLORES['texto'],
                           relief='flat', borderwidth=1)

    def evento_editor(self, evento):
        """Envía acciones de edición al documento activo sin intervenir en otros archivos."""
        self.editor.focus_set()
        self.editor.event_generate(evento)

    def seleccionar_todo(self):
        """Selecciona el código del documento activo y mantiene el foco en su editor."""
        self.editor.tag_add('sel', '1.0', 'end-1c')
        self.editor.focus_set()

    def acerca_de(self):
        """Muestra una descripción breve del editor y sus acciones principales."""
        avisar(self.root, 'Costeñol', 'Editor y ejecución del lenguaje Costeñol.\n'
               'Abre varios archivos en pestañas. F5 analiza y F6 ejecuta el archivo activo.')

    def guardar_contexto(self):
        """Conserva ruta, salida y referencias del editor; cada widget retiene su historial y cursor."""
        if self.activa not in self.documentos:
            return
        datos = self.documentos[self.activa]
        datos.update(archivo=self.archivo, ultimo_codigo=self.ultimo_codigo,
                     salida=self.salida.get('1.0', 'end-1c'),
                     etiquetas={tag: tuple(str(i) for i in self.salida.tag_ranges(tag)) for tag in ('error', 'ok')})

    def nueva_pestana(self, codigo='', archivo=None):
        """Crea y selecciona un documento con editor e historial independientes, sin descartar otros."""
        if self.ocupada:
            return
        self.guardar_contexto()
        self.revision.detener()
        if self.activa is not None:
            self.publicar_diagnostico(None)
        self.cambiando_documento = True
        zona = ttk.Frame(self.pestanas)
        self.contador_documentos += 1
        self.pestanas.add(zona, text=archivo.name if archivo else f'Sin título {self.contador_documentos}')
        self.pestanas.select(zona)
        self.crear_editor(zona)
        self.activa = str(zona)
        self.documentos[self.activa] = dict(editor=self.editor, numeros=self.numeros,
                                           diagnostico_inline=self.diagnostico_inline,
                                           archivo=archivo, ultimo_codigo=codigo, salida='', etiquetas={},
                                           nombre=f'Sin título {self.contador_documentos}')
        self.cargar(codigo, archivo)
        self.cambiando_documento = False

    def cambiar_documento(self, evento=None):
        """Activa otra pestaña restaurando su editor y resultados; cancela diagnósticos del archivo anterior."""
        if self.cambiando_documento:
            return
        destino = self.pestanas.select()
        if destino == self.activa or destino not in self.documentos:
            return
        if self.ocupada:
            self.pestanas.select(self.activa)
            return
        self.guardar_contexto()
        self.revision.detener()
        if self.editor.winfo_exists():
            self.publicar_diagnostico(None)
        else:
            self.cerrar_detalle_error()
            self.linea_error = None
            self.diagnostico.set('')
            self.panel_diagnostico.pack_forget()
        self.activa = destino
        datos = self.documentos[destino]
        for atributo in ('editor', 'numeros', 'diagnostico_inline', 'archivo', 'ultimo_codigo'):
            setattr(self, atributo, datos[atributo])
        self.limpiar()
        self.salida.configure(state='normal')
        self.salida.insert('1.0', datos['salida'])
        for tag, indices in datos['etiquetas'].items():
            for inicio, fin in zip(indices[::2], indices[1::2]):
                self.salida.tag_add(tag, inicio, fin)
        self.salida.configure(state='disabled')
        self.actualizar_colores_editor(self.editor, self.numeros)
        self.configurar_resaltado()
        self.titulo()
        self.revision.solicitar(self.codigo())
        self.editor.focus_set()
        self.dibujar_numeros()

    def siguiente_pestana(self):
        """Selecciona el siguiente documento abierto y vuelve al primero al llegar al final."""
        pestañas = list(self.pestanas.tabs())
        if pestañas and not self.ocupada:
            self.pestanas.select(pestañas[(pestañas.index(self.activa) + 1) % len(pestañas)])
            self.cambiar_documento()

    def cerrar_con_raton(self, evento):
        """Cierra con el botón central la pestaña pulsada, consultando sus cambios pendientes."""
        try:
            indice = self.pestanas.index(f'@{evento.x},{evento.y}')
        except tk.TclError:
            return
        if not self.ocupada:
            self.pestanas.select(indice)
            self.cambiar_documento()
            self.cerrar_pestana()

    def cerrar_desde_icono(self, evento):
        """Cierra una pestaña al pulsar su icono de cierre, sin ejecutar el código."""
        if self.pestanas.identify(evento.x, evento.y) == 'Cerrar':
            self.cerrar_con_raton(evento)

    def cerrar_pestana(self):
        """Cierra el archivo activo tras guardar, descartar o cancelar; mantiene los otros documentos."""
        if self.ocupada or not self.confirmar_cambios():
            return
        self.revision.detener()
        self.publicar_diagnostico(None)
        identificador = self.activa
        widget = self.pestanas.nametowidget(identificador)
        self.pestanas.forget(identificador)
        del self.documentos[identificador]
        self.activa = None
        widget.destroy()
        if self.documentos:
            self.cambiar_documento()
        else:
            self.nueva_pestana('')

    def actualizar_colores_editor(self, editor, numeros):
        """Actualiza la paleta de un editor abierto sin alterar texto ni historial de deshacer."""
        c = COLORES
        numeros.configure(bg=c['panel'])
        editor.configure(bg=c['panel'], fg=c['texto'], insertbackground=c['acento'],
                         selectbackground=c['seleccion'], selectforeground=c['texto'],
                         highlightbackground=c['borde'], highlightcolor=c['acento'])

    def crear_editor(self, zona):
        """Construye un editor independiente con sus barras, historial y resaltado por documento."""
        ttk.Label(zona, text='CÓDIGO · Costeñol', padding=(0, 4)).pack(anchor='w')
        marco = ttk.Frame(zona)
        marco.pack(fill='both', expand=True)
        self.numeros = tk.Canvas(marco, width=52, bg=COLORES['panel'], highlightthickness=0)
        self.numeros.pack(side='left', fill='y')
        self.editor = EditorObservable(marco, wrap='none', undo=True, font=('Consolas', 12),
                              bg=COLORES['panel'], fg=COLORES['texto'], insertbackground=COLORES['acento'],
                              relief='flat', highlightthickness=1, highlightbackground=COLORES['borde'], highlightcolor=COLORES['acento'],
                              selectbackground=COLORES['seleccion'], selectforeground=COLORES['texto'], padx=10, pady=8, tabstyle='wordprocessor')
        self.diagnostico_inline = tk.Label(self.editor, anchor='w', font=('Consolas', 10),
                                             cursor='hand2', padx=6, pady=0, borderwidth=0)
        self.diagnostico_inline.bind('<Enter>', self.abrir_detalle_error)
        self.diagnostico_inline.bind('<Leave>', self.cerrar_detalle_error)
        self.diagnostico_inline.bind('<Button-1>', self.abrir_detalle_error)
        vertical = ttk.Scrollbar(marco, orient='vertical', command=self.editor.yview)
        vertical.pack(side='right', fill='y')
        self.editor.pack(fill='both', expand=True)
        def desplazar(inicio, fin):
            """Recibe las fracciones visibles del editor, sincroniza la barra vertical y redibuja números."""
            vertical.set(inicio, fin)
            self.dibujar_numeros()
        self.editor.configure(yscrollcommand=desplazar)
        horizontal = ttk.Scrollbar(zona, orient='horizontal', command=self.editor.xview)
        horizontal.pack(fill='x')
        def desplazar_horizontal(inicio, fin):
            """Sincroniza el desplazamiento horizontal y recoloca el diagnóstico junto al código."""
            horizontal.set(inicio, fin)
            self.ubicar_diagnostico()
        self.editor.configure(xscrollcommand=desplazar_horizontal)
        self.configurar_resaltado()
        for evento in ('<KeyRelease>', '<ButtonRelease-1>', '<B1-Motion>', '<FocusIn>'):
            self.editor.bind(evento, self.resaltar_linea_actual, add='+')
        self.editor.bind('<<Modified>>', self.modificado)
        self.editor.bind('<<ContenidoCambiado>>', self.modificado)
        self.editor.bind('<Configure>', lambda e: self.dibujar_numeros())
        self.editor.bind('<Tab>', self.tabular)

    def cargar_logo(self, cabecera):
        """Carga las dos variantes transparentes de cabecera y el isotipo de ventana.
        Conserva las referencias de Tkinter y usa el logo claro al iniciar en modo oscuro.
        Si falta un recurso, el resto de imágenes sigue disponible y se conserva texto alternativo.
        """
        carpeta = Path(__file__).resolve().parent / 'logo'
        variantes = {
            'Claro': 'Logo costeñol con fondo transparente.png',
            'Oscuro': 'Logo costeñol blanco sobre fondo transparente.png',
        }
        self.logos_cabecera = {}
        for tema, nombre in variantes.items():
            try:
                imagen = self.imagen_logo(nombre)
                factor = max(1, (imagen.width() + 279) // 280,
                             (imagen.height() + 79) // 80)
                self.logos_cabecera[tema] = imagen.subsample(factor, factor)
            except (tk.TclError, OSError):
                # Una variante ausente no debe impedir iniciar la aplicación.
                continue
        self.logo_etiqueta = ttk.Label(cabecera, style='Titulo.TLabel')
        self.logo_etiqueta.pack(side='left', padx=(0, 8))
        self.actualizar_logo('Oscuro')
        try:
            isotipo = self.imagen_logo('Puente, sol y ondas_ isotipo costero.png')
            factor = max(1, (max(isotipo.width(), isotipo.height()) + 127) // 128)
            self.logo_icono = isotipo.subsample(factor, factor)
            # True propaga el símbolo sin letras a los nuevos diálogos de la aplicación.
            self.root.iconphoto(True, self.logo_icono)
        except (tk.TclError, OSError):
            self.logo_icono = None

    def imagen_logo(self, nombre):
        """Reutiliza la precarga del inicio o lee el recurso al construir directamente la aplicación."""
        cache = getattr(self.root, '_imagenes_precargadas', {})
        if nombre in cache:
            return cache[nombre]
        return tk.PhotoImage(master=self.root,
                             file=ruta_tk(Path(__file__).resolve().parent / 'logo' / nombre))

    def actualizar_logo(self, tema):
        """Selecciona logo oscuro para fondo claro y logo blanco para fondo oscuro.
        Solo cambia la imagen de cabecera; el icono sin letras permanece fijo.
        """
        self.logo_cabecera = self.logos_cabecera.get(tema)
        if self.logo_cabecera is not None:
            self.logo_etiqueta.configure(image=self.logo_cabecera, text='')
        else:
            self.logo_etiqueta.configure(image='', text='Costeñol')

    def cambiar_tema(self, evento=None):
        """Aplica el tema seleccionado sin reconstruir ni borrar el contenido de los paneles.
        Actualiza los widgets clásicos y las etiquetas de error; los diálogos heredan la paleta.
        """
        aplicar_tema(self.root, self.tema.get())
        self.selector_tema.dibujar()
        self.colorear_menus()
        for datos in self.documentos.values():
            self.actualizar_colores_editor(datos['editor'], datos['numeros'])
        self.actualizar_logo(self.tema.get())
        c = COLORES
        self.numeros.configure(bg=c['panel'])
        self.editor.configure(bg=c['panel'], fg=c['texto'], insertbackground=c['acento'],
                              selectbackground=c['seleccion'], selectforeground=c['texto'],
                              highlightbackground=c['borde'], highlightcolor=c['acento'])
        self.salida.configure(bg=c['panel'], fg=c['texto'],
                              selectbackground=c['seleccion'], selectforeground=c['texto'])
        oscuro = self.tema.get() == 'Oscuro'
        self.configurar_resaltado()
        self.panel_diagnostico.configure(foreground=c['error'])
        self.cerrar_detalle_error()
        self.ubicar_diagnostico()
        self.salida.tag_configure('error', foreground=c['error'])
        self.salida.tag_configure('ok', foreground=c['ok'])
        self.dibujar_numeros()

    def configurar_resaltado(self):
        """Define colores y prioridad de línea activa, error y selección para el tema actual.
        La selección siempre queda por encima del sombreado para distinguir el texto seleccionado.
        """
        oscuro = self.tema.get() == 'Oscuro'
        self.editor.tag_configure('linea_actual', background='#202d3e' if oscuro else '#e7effa')
        self.editor.tag_configure('error', background='#542c39' if oscuro else '#ffe1e5',
                                  foreground='#ffe4e7' if oscuro else '#8c1326')
        self.editor.tag_configure('error_actual', background='#734152' if oscuro else '#f8c2ce',
                                  foreground='#fff0f3' if oscuro else '#761426')
        self.editor.tag_configure('sel', background='#4877b0' if oscuro else '#9ac4f5',
                                  foreground='#ffffff' if oscuro else '#102b4b')
        self.editor.configure(inactiveselectbackground='#395a80' if oscuro else '#bad3ef',
                              exportselection=False)
        self.resaltar_palabras()
        self.editor.tag_lower('linea_actual')
        self.editor.tag_raise('error')
        self.editor.tag_raise('error_actual')
        self.editor.tag_raise('sel')
        self.resaltar_linea_actual()

    def resaltar_palabras(self):
        """Aplica colores por categoría y tema, sin alterar código, selección o historial.
        Todas las categorías usan peso normal y conservan los colores de su tema.
        """
        if not hasattr(self.editor, '_fuente_reservadas'):
            self.editor._fuente_reservadas = tkfont.Font(font=self.editor.cget('font'))
            self.editor._fuente_reservadas.configure(weight='normal')
        paleta = PALETAS_SINTAXIS[self.tema.get()]
        for categoria, color in paleta.items():
            fuente = (self.editor._fuente_reservadas if categoria == 'funcion'
                      else self.editor.cget('font'))
            self.editor.tag_configure(categoria, foreground=color, font=fuente)
            self.editor.tag_remove(categoria, '1.0', 'end')
            self.editor.tag_lower(categoria, 'error')
        for categoria, inicio, fin in rangos_sintaxis(self.codigo()):
            self.editor.tag_add(categoria, inicio, fin)
        self.editor.tag_raise('sel')

    def resaltar_linea_actual(self, evento=None):
        """Sombrea la línea del cursor y acentúa su error sin borrar selección ni modificar código."""
        self.editor.tag_remove('linea_actual', '1.0', 'end')
        self.editor.tag_remove('error_actual', '1.0', 'end')
        inicio = self.editor.index('insert linestart')
        fin = self.editor.index('insert lineend+1c')
        self.editor.tag_add('linea_actual', inicio, fin)
        # Un error puede señalar una columna al final de la línea: se compara toda la línea.
        if self.editor.tag_nextrange('error', inicio, fin):
            self.editor.tag_add('error_actual', inicio, fin)
        self.editor.tag_raise('sel')

    def atajo(self, funcion):
        """Ejecuta la acción recibida si la aplicación está libre.
        Devuelve break para evitar que Tkinter siga procesando el mismo atajo.
        """
        if not self.ocupada:
            funcion()
        return 'break'

    def tabular(self, evento):
        """Atiende el evento Tab insertando cuatro espacios; devuelve break para consumirlo."""
        self.editor.insert('insert', '    ')
        return 'break'

    def dibujar_numeros(self):
        """Redibuja en el lienzo los números de las líneas actualmente visibles en el editor."""
        self.numeros.delete('all')
        indice = self.editor.index('@0,0')
        while True:
            info = self.editor.dlineinfo(indice)
            if info is None:
                break
            numero = indice.split('.')[0]
            self.numeros.create_text(42, info[1], text=numero, anchor='ne',
                                     font=('Consolas', 12), fill=COLORES['suave'])
            indice = self.editor.index(f'{indice}+1line')
        self.ubicar_diagnostico()

    def titulo(self):
        """Actualiza el título con el nombre del archivo y un asterisco si hay cambios sin guardar."""
        marca = '*' if self.editor.edit_modified() else ''
        nombre = self.archivo.name if self.archivo else self.documentos.get(self.activa, {}).get('nombre', 'Sin título')
        self.root.title(f'{marca}{nombre} — Costeñol')
        if self.activa in self.documentos:
            self.pestanas.tab(self.activa, text=f'{marca}{nombre}')

    def modificado(self, evento=None):
        """Detecta cambios reales, conserva la marca de guardado y programa la revisión automática.
        Ignora eventos de selección, guardado y notificaciones duplicadas del mismo contenido.
        """
        if self.cambiando_documento or (evento is not None and evento.widget is not self.editor):
            return
        self.titulo()
        codigo = self.codigo()
        if codigo == self.ultimo_codigo:
            return
        self.ultimo_codigo = codigo
        self.resaltar_palabras()
        self.dibujar_numeros()
        self.publicar_diagnostico(None)
        if not self.ocupada:
            self.revision.solicitar(codigo)

    def publicar_diagnostico(self, error):
        """Muestra el error junto a su línea y conserva el detalle completo en una banda visible.
        No cambia el código, el cursor ni Resultados; con None retira ambos diagnósticos.
        """
        self.cerrar_detalle_error()
        self.linea_error = None
        self.editor.tag_remove('error', '1.0', 'end')
        self.diagnostico.set('')
        self.panel_diagnostico.pack_forget()
        self.diagnostico_inline.place_forget()
        if error is not None:
            nombre = NOMBRES.get(type(error), 'Límite de análisis')
            self.diagnostico.set(f'{nombre}: {error}')
            self.panel_diagnostico.configure(wraplength=max(300, self.root.winfo_width() - 60))
            self.panel_diagnostico.pack(side='bottom', fill='x', before=self.paneles)
            lugar = re.search(r'Línea (\d+), columna (\d+)', str(error))
            if lugar:
                self.linea_error = int(lugar.group(1))
                self.editor.tag_add('error', f'{self.linea_error}.0', f'{self.linea_error}.end+1c')
        self.resaltar_linea_actual()
        self.ubicar_diagnostico()

    def ubicar_diagnostico(self):
        """Coloca el mensaje al final de la línea visible sin insertarlo en el archivo.
        Si falta espacio muestra un aviso compacto; el detalle se consulta al pasar el ratón.
        Recalcula la posición al desplazar, cambiar el tema o redimensionar el editor.
        """
        if not hasattr(self, 'diagnostico_inline'):
            return
        self.diagnostico_inline.place_forget()
        if self.linea_error is None:
            return
        info = self.editor.dlineinfo(f'{self.linea_error}.0')
        if info is None:
            return
        ancho = self.editor.winfo_width()
        if ancho < 100:
            return
        fin = self.editor.bbox(f'{self.linea_error}.end')
        x = fin[0] + 18 if fin else ancho - 105
        x = max(12, min(x, ancho - 105))
        disponible = max(80, ancho - x - 10)
        self.panel_diagnostico.configure(wraplength=max(260, self.root.winfo_width() - 60))
        completo = self.diagnostico.get()
        categoria = completo.split(':', 1)[0]
        costeño = completo.split('Costeñol: ', 1)[-1].replace('\n', ' ')
        texto = f'{categoria}: {costeño}'
        fuente = tkfont.Font(font=self.diagnostico_inline.cget('font'))
        while len(texto) > 1 and fuente.measure(texto + '…') > disponible - 12:
            texto = texto[:-1]
        if texto != f'{categoria}: {costeño}':
            texto += '…'
        oscuro = self.tema.get() == 'Oscuro'
        self.diagnostico_inline.configure(text=texto, background='#45272e' if oscuro else '#ffe1e5',
                                          foreground=COLORES['error'])
        self.diagnostico_inline.place(x=x, y=info[1], width=disponible, height=max(info[3], 19))
        self.diagnostico_inline.lift()

    def abrir_detalle_error(self, evento=None):
        """Abre un globo sin foco con el mensaje español y costeño íntegro, sin recortes."""
        if not self.diagnostico.get():
            return
        self.cerrar_detalle_error()
        ventana = tk.Toplevel(self.root)
        self.detalle_error = ventana
        ventana.overrideredirect(True)
        ancho = max(260, min(620, self.root.winfo_width() - 40))
        tk.Label(ventana, text=self.diagnostico.get(), justify='left', wraplength=ancho - 24,
                 bg=COLORES['panel'], fg=COLORES['error'], padx=12, pady=10,
                 relief='solid', borderwidth=1, font=('Segoe UI', 10)).pack()
        ventana.update_idletasks()
        x = min(self.diagnostico_inline.winfo_rootx(),
                self.root.winfo_screenwidth() - ventana.winfo_reqwidth() - 12)
        y = self.diagnostico_inline.winfo_rooty() + self.diagnostico_inline.winfo_height() + 4
        y = min(y, self.root.winfo_screenheight() - ventana.winfo_reqheight() - 12)
        ventana.geometry(f'+{max(0, x)}+{max(0, y)}')

    def cerrar_detalle_error(self, evento=None):
        """Cierra el globo de diagnóstico al salir del mensaje o actualizar el código."""
        if self.detalle_error is not None:
            self.detalle_error.destroy()
            self.detalle_error = None

    def codigo(self):
        """Devuelve el texto actual del editor sin el salto final que Tkinter añade automáticamente."""
        return self.editor.get('1.0', 'end-1c')

    def cargar(self, codigo, archivo=None):
        """Reemplaza el editor por el código recibido y asocia una ruta opcional.
        Reinicia el historial y la marca de cambios, limpia resultados y enfoca el editor.
        """
        self.revision.detener()
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', codigo)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.archivo = archivo
        self.ultimo_codigo = codigo
        self.resaltar_palabras()
        self.publicar_diagnostico(None)
        self.revision.solicitar(codigo)
        self.titulo()
        self.limpiar()
        self.editor.focus_set()
        self.resaltar_linea_actual()

    def confirmar_cambios(self):
        """Pregunta si deben guardarse los cambios pendientes.
        Devuelve True si se puede continuar; False si se cancela o falla el guardado.
        """
        if not self.editor.edit_modified():
            return True
        respuesta = dialogo(self.root, 'Cambios sin guardar', '¿Guardar los cambios antes de continuar?',
                            [('Guardar', True), ('Descartar', False), ('Cancelar', None)])
        return self.guardar() if respuesta is True else respuesta is False

    def nuevo(self):
        """Crea un documento vacío si la aplicación está libre y se resolvieron los cambios pendientes."""
        if not self.ocupada:
            self.nueva_pestana('')

    def abrir(self):
        """Solicita una ruta y carga texto UTF-8, aceptando .pqek, .cost y otros archivos.
        Consulta cambios pendientes y muestra un diálogo si falla la lectura.
        """
        if self.ocupada:
            return
        nombre = seleccionar_archivo(self.root, self.archivo)
        if nombre:
            try:
                archivo = Path(nombre)
                codigo = archivo.read_text(encoding='utf-8-sig')
            except (OSError, UnicodeError) as error:
                avisar(self.root, 'No se pudo abrir', str(error))
                return
            for identificador, datos in self.documentos.items():
                ruta = self.archivo if identificador == self.activa else datos['archivo']
                if ruta is not None and ruta.resolve() == archivo.resolve():
                    self.pestanas.select(identificador)
                    self.cambiar_documento()
                    return
            self.nueva_pestana(codigo, archivo)

    def guardar(self):
        """Guarda en la ruta actual o delega en Guardar como si aún no existe.
        Devuelve True al guardar y False si está ocupada, se cancela o falla.
        """
        if self.ocupada:
            return False
        if self.archivo is None or self.archivo.suffix.casefold() != '.pqek':
            return self.guardar_como()
        return self.escribir(self.archivo)

    def guardar_como(self):
        """Solicita una ruta proponiendo .pqek y escribe el documento.
        Devuelve False si se cancela o está ocupada; en otro caso, el resultado de escribir.
        """
        if self.ocupada:
            return False
        nombre = seleccionar_archivo(self.root, self.archivo, guardar=True)
        return self.escribir(Path(nombre)) if nombre else False

    def escribir(self, archivo):
        """Escribe el contenido del editor en la ruta recibida con codificación UTF-8.
        Actualiza ruta y estado; devuelve True si guarda o False si hay un error de archivo.
        """
        try:
            archivo = ruta_guardado(archivo)
        except ValueError as error:
            avisar(self.root, 'Extensión no permitida', str(error))
            return False
        for identificador, datos in self.documentos.items():
            if identificador != self.activa and datos['archivo'] is not None and datos['archivo'].resolve() == archivo.resolve():
                avisar(self.root, 'Archivo ya abierto', 'Ese archivo ya está abierto en otra pestaña. Guarda con otro nombre.')
                return False
        try:
            archivo.write_text(self.codigo(), encoding='utf-8')
        except (OSError, UnicodeError) as error:
            avisar(self.root, 'No se pudo guardar', str(error))
            return False
        self.archivo = archivo
        self.editor.edit_modified(False)
        self.titulo()
        self.estado.set('Archivo guardado')
        return True

    def cerrar(self):
        """Revisa cambios de cada documento antes de salir; Cancelar conserva todas las pestañas."""
        if self.ocupada:
            return
        for identificador in list(self.documentos):
            self.pestanas.select(identificador)
            self.cambiar_documento()
            if not self.confirmar_cambios():
                return
        self.revision.detener()
        self.cerrar_detalle_error()
        self.root.destroy()

    def limpiar(self):
        """Vacía el panel de resultados y lo devuelve al estado de solo lectura."""
        self.salida.configure(state='normal')
        self.salida.delete('1.0', 'end')
        self.salida.configure(state='disabled')

    def imprimir(self, texto, etiqueta=''):
        """Añade texto y un salto de línea al panel con una etiqueta visual opcional.
        Desplaza la salida al final y actualiza tareas de dibujo pendientes.
        """
        self.salida.configure(state='normal')
        self.salida.insert('end', texto + '\n', etiqueta)
        self.salida.see('end')
        self.salida.configure(state='disabled')
        self.root.update_idletasks()

    def mostrar_error(self, error):
        """Muestra categoría y descripción del error.
        Si incluye línea y columna, resalta esa línea y coloca allí el cursor.
        """
        nombre = NOMBRES.get(type(error), 'Error')
        self.publicar_diagnostico(error)
        self.imprimir(f'{nombre}: {error}', 'error')
        self.estado.set(nombre)
        lugar = re.search(r'Línea (\d+), columna (\d+)', str(error))
        if lugar:
            linea, columna = map(int, lugar.groups())
            self.editor.tag_add('error', f'{linea}.0', f'{linea}.end+1c')
            self.editor.mark_set('insert', f'{linea}.{columna - 1}')
            self.editor.see('insert')
            self.resaltar_linea_actual()

    def capturar(self, prompt):
        """Solicita un dato mediante un diálogo y registra la entrada en Resultados.
        Devuelve el texto o None al cancelar, para que el intérprete gestione la cancelación.
        """
        self.imprimir(prompt)
        tipo = prompt.split('.', 1)[1].split()[0]
        ayuda = 'Formato: ' + FORMATOS[tipo]
        valor = dialogo(self.root, 'Entrada de datos', f'{prompt}\n\n{ayuda}',
                        [('Aceptar', True), ('Cancelar', None)], entrada=True, tipo_captura=tipo)
        self.imprimir('> ' + valor if valor is not None else '> Captura cancelada')
        return valor

    def procesar(self, ejecutar_programa):
        """Analiza o ejecuta el texto actual según ejecutar_programa.
        Bloquea las acciones durante el proceso, presenta errores y restaura los controles al terminar.
        """
        if self.ocupada:
            return
        self.revision.detener()
        self.publicar_diagnostico(None)
        codigo = self.codigo()
        self.ocupada = True
        self.limpiar()
        self.editor.tag_remove('error', '1.0', 'end')
        self.resaltar_linea_actual()
        self.editor.configure(state='disabled')
        for boton in self.botones:
            boton.configure(state='disabled')
        self.estado.set('Ejecutando…' if ejecutar_programa else 'Analizando…')
        try:
            if ejecutar_programa:
                ejecutar(codigo, entrada=self.capturar, salida=self.imprimir)
                self.imprimir('Ejecución finalizada.', 'ok')
            else:
                analizar_semantica(codigo)
                self.imprimir('Código válido: análisis léxico, sintáctico y semántico correctos.', 'ok')
            self.estado.set('Ejecución finalizada' if ejecutar_programa else 'Código válido')
        except ERRORES as error:
            self.mostrar_error(error)
        except (RecursionError, ValueError, OverflowError) as error:
            self.imprimir(f'Límite de procesamiento: {error}', 'error')
            self.estado.set('No se pudo completar el procesamiento')
        finally:
            self.ocupada = False
            self.editor.configure(state='normal')
            for boton in self.botones:
                boton.configure(state='normal')
            self.editor.focus_set()

    def analizar(self):
        """Activa la validación léxica, sintáctica y semántica sin ejecutar instrucciones."""
        self.procesar(False)

    def ejecutar(self):
        """Activa la validación y ejecución del código actual, usando diálogos para las capturas."""
        self.procesar(True)


def main():
    """Inicia Tkinter con la raíz oculta y una bienvenida animada hasta preparar el editor."""
    configurar_tk_portable()
    identidad_windows()
    root = tk.Tk()
    root.withdraw()
    icono_ventana(root)
    inicio = InicioIndependiente(root, Aplicacion)
    root.mainloop()


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == '--autoprueba':
        from verificar_portable import verificar
        sys.exit(verificar(Aplicacion, sys.argv[2]))
    main()



