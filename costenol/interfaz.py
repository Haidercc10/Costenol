"""Editor de escritorio para Costeñol. Ejecutar: python interfaz.py"""
from pathlib import Path
import re
import tkinter as tk
from tkinter import ttk
from tema import aplicar_tema, COLORES, dialogo, avisar, seleccionar_archivo
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
        self.ocupada = False
        root.title('Costeñol — Editor')
        root.geometry('1050x760')
        root.minsize(920, 560)
        root.protocol('WM_DELETE_WINDOW', self.cerrar)
        aplicar_tema(root)
        cabecera = ttk.Frame(root, padding=(16, 12))
        cabecera.pack(fill='x')
        self.cargar_logo(cabecera)
        ttk.Label(cabecera, text='Editor y ejecución de programas', padding=(20, 0)).pack(side='left')
        selector_tema = ttk.Frame(cabecera)
        selector_tema.pack(side='right')
        ttk.Label(selector_tema, text='Tema', padding=(0, 0, 8, 0)).pack(side='left')
        self.tema = tk.StringVar(value='Oscuro')
        self.selector_tema = ttk.Combobox(selector_tema, textvariable=self.tema,
                                         values=('Oscuro', 'Claro'), state='readonly', width=9)
        self.selector_tema.pack(side='left')
        self.selector_tema.bind('<<ComboboxSelected>>', self.cambiar_tema)
        barra = ttk.Frame(root, padding=(16, 0, 16, 10))
        barra.pack(fill='x')
        self.botones = []
        for texto, funcion in [('Nuevo', self.nuevo), ('Abrir…', self.abrir),
                               ('Guardar', self.guardar), ('Guardar como…', self.guardar_como),
                               ('Analizar · F5', self.analizar), ('Ejecutar · F6', self.ejecutar)]:
            boton = ttk.Button(barra, text=texto, command=funcion,
                               style='Accion.TButton' if funcion in (self.analizar, self.ejecutar) else 'TButton')
            boton.pack(side='left', padx=(0, 6))
            self.botones.append(boton)
        paneles = ttk.Panedwindow(root, orient='vertical')
        paneles.pack(fill='both', expand=True, padx=16)
        zona = ttk.Frame(paneles)
        paneles.add(zona, weight=3)
        ttk.Label(zona, text='CÓDIGO · Costeñol', padding=(0, 4)).pack(anchor='w')
        marco = ttk.Frame(zona)
        marco.pack(fill='both', expand=True)
        self.numeros = tk.Canvas(marco, width=52, bg=COLORES['panel'], highlightthickness=0)
        self.numeros.pack(side='left', fill='y')
        self.editor = tk.Text(marco, wrap='none', undo=True, font=('Consolas', 12),
                              bg=COLORES['panel'], fg=COLORES['texto'], insertbackground=COLORES['acento'],
                              relief='flat', highlightthickness=1, highlightbackground=COLORES['borde'], highlightcolor=COLORES['acento'],
                              selectbackground=COLORES['seleccion'], selectforeground=COLORES['texto'], padx=10, pady=8, tabstyle='wordprocessor')
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
        self.editor.configure(xscrollcommand=horizontal.set)
        self.editor.tag_configure('error', background='#542c39', foreground='#ffe4e7')
        self.editor.bind('<<Modified>>', self.modificado)
        self.editor.bind('<Configure>', lambda e: self.dibujar_numeros())
        self.editor.bind('<Tab>', self.tabular)
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
        ttk.Label(root, textvariable=self.estado, padding=(16, 8)).pack(fill='x')
        for tecla, funcion in [('<Control-n>', self.nuevo), ('<Control-o>', self.abrir),
                               ('<Control-s>', self.guardar), ('<F5>', self.analizar), ('<F6>', self.ejecutar)]:
            root.bind(tecla, lambda e, f=funcion: self.atajo(f))
        self.cargar(EJEMPLO)

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
                imagen = tk.PhotoImage(master=self.root, file=str(carpeta / nombre))
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
            isotipo = tk.PhotoImage(master=self.root,
                                   file=str(carpeta / 'Puente, sol y ondas_ isotipo costero.png'))
            factor = max(1, (max(isotipo.width(), isotipo.height()) + 127) // 128)
            self.logo_icono = isotipo.subsample(factor, factor)
            # True propaga el símbolo sin letras a los nuevos diálogos de la aplicación.
            self.root.iconphoto(True, self.logo_icono)
        except (tk.TclError, OSError):
            self.logo_icono = None

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
        self.actualizar_logo(self.tema.get())
        c = COLORES
        self.numeros.configure(bg=c['panel'])
        self.editor.configure(bg=c['panel'], fg=c['texto'], insertbackground=c['acento'],
                              selectbackground=c['seleccion'], selectforeground=c['texto'],
                              highlightbackground=c['borde'], highlightcolor=c['acento'])
        self.salida.configure(bg=c['panel'], fg=c['texto'],
                              selectbackground=c['seleccion'], selectforeground=c['texto'])
        oscuro = self.tema.get() == 'Oscuro'
        self.editor.tag_configure('error', background='#542c39' if oscuro else '#ffe1e5',
                                  foreground='#ffe4e7' if oscuro else '#8c1326')
        self.salida.tag_configure('error', foreground=c['error'])
        self.salida.tag_configure('ok', foreground=c['ok'])
        self.dibujar_numeros()

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

    def titulo(self):
        """Actualiza el título con el nombre del archivo y un asterisco si hay cambios sin guardar."""
        marca = '*' if self.editor.edit_modified() else ''
        self.root.title(f'{marca}{self.archivo.name if self.archivo else "Sin título"} — Costeñol')

    def modificado(self, evento=None):
        """Atiende cambios del editor: actualiza título, números y estado, y retira el error anterior.
        El parámetro evento lo entrega Tkinter y es opcional para llamadas directas.
        """
        self.titulo()
        self.editor.tag_remove('error', '1.0', 'end')
        self.dibujar_numeros()
        if self.editor.edit_modified():
            self.estado.set('Código modificado · Analiza nuevamente con F5')

    def codigo(self):
        """Devuelve el texto actual del editor sin el salto final que Tkinter añade automáticamente."""
        return self.editor.get('1.0', 'end-1c')

    def cargar(self, codigo, archivo=None):
        """Reemplaza el editor por el código recibido y asocia una ruta opcional.
        Reinicia el historial y la marca de cambios, limpia resultados y enfoca el editor.
        """
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', codigo)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.archivo = archivo
        self.titulo()
        self.limpiar()
        self.editor.focus_set()

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
        if not self.ocupada and self.confirmar_cambios():
            self.cargar('')

    def abrir(self):
        """Solicita una ruta y carga texto UTF-8, aceptando .pqek, .cost y otros archivos.
        Consulta cambios pendientes y muestra un diálogo si falla la lectura.
        """
        if self.ocupada or not self.confirmar_cambios():
            return
        nombre = seleccionar_archivo(self.root, self.archivo)
        if nombre:
            try:
                archivo = Path(nombre)
                codigo = archivo.read_text(encoding='utf-8-sig')
            except (OSError, UnicodeError) as error:
                avisar(self.root, 'No se pudo abrir', str(error))
                return
            self.cargar(codigo, archivo)

    def guardar(self):
        """Guarda en la ruta actual o delega en Guardar como si aún no existe.
        Devuelve True al guardar y False si está ocupada, se cancela o falla.
        """
        if self.ocupada:
            return False
        if self.archivo is None:
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
        """Cierra la ventana si está libre y el usuario resolvió los cambios pendientes."""
        if not self.ocupada and self.confirmar_cambios():
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
        self.imprimir(f'{nombre}: {error}', 'error')
        self.estado.set(nombre)
        lugar = re.search(r'Línea (\d+), columna (\d+)', str(error))
        if lugar:
            linea, columna = map(int, lugar.groups())
            self.editor.tag_add('error', f'{linea}.0', f'{linea}.end+1c')
            self.editor.mark_set('insert', f'{linea}.{columna - 1}')
            self.editor.see('insert')

    def capturar(self, prompt):
        """Solicita un dato mediante un diálogo y registra la entrada en Resultados.
        Devuelve el texto o None al cancelar, para que el intérprete gestione la cancelación.
        """
        self.imprimir(prompt)
        ayuda = 'Real: usa coma decimal. Logico: Verdadero o Falso.'
        valor = dialogo(self.root, 'Entrada de datos', f'{prompt}\n\n{ayuda}',
                        [('Aceptar', True), ('Cancelar', None)], entrada=True)
        self.imprimir('> ' + valor if valor is not None else '> Captura cancelada')
        return valor

    def procesar(self, ejecutar_programa):
        """Analiza o ejecuta el texto actual según ejecutar_programa.
        Bloquea las acciones durante el proceso, presenta errores y restaura los controles al terminar.
        """
        if self.ocupada:
            return
        codigo = self.codigo()
        self.ocupada = True
        self.limpiar()
        self.editor.tag_remove('error', '1.0', 'end')
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
    """Crea la ventana raíz, construye la aplicación e inicia el bucle de eventos de Tkinter."""
    root = tk.Tk()
    Aplicacion(root)
    root.mainloop()


if __name__ == '__main__':
    main()

