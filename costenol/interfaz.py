"""Editor de escritorio para Costeñol. Ejecutar: python interfaz.py"""
from pathlib import Path
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
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
        self.root = root
        self.archivo = None
        self.ocupada = False
        root.title('Costeñol — Editor')
        root.geometry('1050x760')
        root.minsize(720, 500)
        root.protocol('WM_DELETE_WINDOW', self.cerrar)
        estilo = ttk.Style(root)
        estilo.configure('Titulo.TLabel', font=('Segoe UI', 18, 'bold'))
        cabecera = ttk.Frame(root, padding=(16, 12))
        cabecera.pack(fill='x')
        ttk.Label(cabecera, text='Costeñol', style='Titulo.TLabel').pack(side='left')
        ttk.Label(cabecera, text='Editor y ejecución de programas', padding=(20, 0)).pack(side='left')
        barra = ttk.Frame(root, padding=(16, 0, 16, 10))
        barra.pack(fill='x')
        self.botones = []
        for texto, funcion in [('Nuevo', self.nuevo), ('Abrir…', self.abrir),
                               ('Guardar', self.guardar), ('Guardar como…', self.guardar_como),
                               ('Analizar · F5', self.analizar), ('Ejecutar · F6', self.ejecutar)]:
            boton = ttk.Button(barra, text=texto, command=funcion)
            boton.pack(side='left', padx=(0, 6))
            self.botones.append(boton)
        paneles = ttk.Panedwindow(root, orient='vertical')
        paneles.pack(fill='both', expand=True, padx=16)
        zona = ttk.Frame(paneles)
        paneles.add(zona, weight=3)
        ttk.Label(zona, text='CÓDIGO · Costeñol', padding=(0, 4)).pack(anchor='w')
        marco = ttk.Frame(zona)
        marco.pack(fill='both', expand=True)
        self.numeros = tk.Canvas(marco, width=52, bg='#e9edf3', highlightthickness=0)
        self.numeros.pack(side='left', fill='y')
        self.editor = tk.Text(marco, wrap='none', undo=True, font=('Consolas', 12),
                              bg='#162032', fg='#edf2f7', insertbackground='white',
                              selectbackground='#365581', padx=10, pady=8, tabstyle='wordprocessor')
        vertical = ttk.Scrollbar(marco, orient='vertical', command=self.editor.yview)
        vertical.pack(side='right', fill='y')
        self.editor.pack(fill='both', expand=True)
        def desplazar(inicio, fin):
            vertical.set(inicio, fin)
            self.dibujar_numeros()
        self.editor.configure(yscrollcommand=desplazar)
        horizontal = ttk.Scrollbar(zona, orient='horizontal', command=self.editor.xview)
        horizontal.pack(fill='x')
        self.editor.configure(xscrollcommand=horizontal.set)
        self.editor.tag_configure('error', background='#803840', foreground='white')
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
                              font=('Consolas', 11), bg='#f3f5f8', relief='flat', padx=10, pady=8)
        scroll_salida = ttk.Scrollbar(salida, command=self.salida.yview)
        scroll_salida.pack(side='right', fill='y')
        self.salida.configure(yscrollcommand=scroll_salida.set)
        self.salida.pack(fill='both', expand=True)
        self.salida.tag_configure('error', foreground='#a4202c')
        self.salida.tag_configure('ok', foreground='#176638')
        self.estado = tk.StringVar(value='Listo · F5 analiza · F6 ejecuta')
        ttk.Label(root, textvariable=self.estado, padding=(16, 8)).pack(fill='x')
        for tecla, funcion in [('<Control-n>', self.nuevo), ('<Control-o>', self.abrir),
                               ('<Control-s>', self.guardar), ('<F5>', self.analizar), ('<F6>', self.ejecutar)]:
            root.bind(tecla, lambda e, f=funcion: self.atajo(f))
        self.cargar(EJEMPLO)

    def atajo(self, funcion):
        if not self.ocupada:
            funcion()
        return 'break'

    def tabular(self, evento):
        self.editor.insert('insert', '    ')
        return 'break'

    def dibujar_numeros(self):
        self.numeros.delete('all')
        indice = self.editor.index('@0,0')
        while True:
            info = self.editor.dlineinfo(indice)
            if info is None:
                break
            numero = indice.split('.')[0]
            self.numeros.create_text(42, info[1], text=numero, anchor='ne',
                                     font=('Consolas', 12), fill='#526174')
            indice = self.editor.index(f'{indice}+1line')

    def titulo(self):
        marca = '*' if self.editor.edit_modified() else ''
        self.root.title(f'{marca}{self.archivo.name if self.archivo else "Sin título"} — Costeñol')

    def modificado(self, evento=None):
        self.titulo()
        self.editor.tag_remove('error', '1.0', 'end')
        self.dibujar_numeros()
        if self.editor.edit_modified():
            self.estado.set('Código modificado · Analiza nuevamente con F5')

    def codigo(self):
        return self.editor.get('1.0', 'end-1c')

    def cargar(self, codigo, archivo=None):
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', codigo)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.archivo = archivo
        self.titulo()
        self.limpiar()
        self.editor.focus_set()

    def confirmar_cambios(self):
        if not self.editor.edit_modified():
            return True
        respuesta = messagebox.askyesnocancel('Cambios sin guardar', '¿Guardar los cambios antes de continuar?', parent=self.root)
        return self.guardar() if respuesta is True else respuesta is False

    def nuevo(self):
        if not self.ocupada and self.confirmar_cambios():
            self.cargar('')

    def abrir(self):
        if self.ocupada or not self.confirmar_cambios():
            return
        nombre = filedialog.askopenfilename(parent=self.root, filetypes=[('Costeñol', '*.cost'), ('Todos', '*.*')])
        if nombre:
            try:
                archivo = Path(nombre)
                codigo = archivo.read_text(encoding='utf-8-sig')
            except (OSError, UnicodeError) as error:
                messagebox.showerror('No se pudo abrir', str(error), parent=self.root)
                return
            self.cargar(codigo, archivo)

    def guardar(self):
        if self.ocupada:
            return False
        if self.archivo is None:
            return self.guardar_como()
        return self.escribir(self.archivo)

    def guardar_como(self):
        if self.ocupada:
            return False
        nombre = filedialog.asksaveasfilename(parent=self.root, defaultextension='.cost',
                    initialfile=self.archivo.name if self.archivo else 'programa.cost',
                    filetypes=[('Costeñol', '*.cost'), ('Todos', '*.*')])
        return self.escribir(Path(nombre)) if nombre else False

    def escribir(self, archivo):
        try:
            archivo.write_text(self.codigo(), encoding='utf-8')
        except (OSError, UnicodeError) as error:
            messagebox.showerror('No se pudo guardar', str(error), parent=self.root)
            return False
        self.archivo = archivo
        self.editor.edit_modified(False)
        self.titulo()
        self.estado.set('Archivo guardado')
        return True

    def cerrar(self):
        if not self.ocupada and self.confirmar_cambios():
            self.root.destroy()

    def limpiar(self):
        self.salida.configure(state='normal')
        self.salida.delete('1.0', 'end')
        self.salida.configure(state='disabled')

    def imprimir(self, texto, etiqueta=''):
        self.salida.configure(state='normal')
        self.salida.insert('end', texto + '\n', etiqueta)
        self.salida.see('end')
        self.salida.configure(state='disabled')
        self.root.update_idletasks()

    def mostrar_error(self, error):
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
        self.imprimir(prompt)
        ayuda = 'Real: usa coma decimal. Logico: Verdadero o Falso.'
        valor = simpledialog.askstring('Entrada de datos', f'{prompt}\n\n{ayuda}', parent=self.root)
        self.imprimir('> ' + valor if valor is not None else '> Captura cancelada')
        return valor

    def procesar(self, ejecutar_programa):
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
        self.procesar(False)

    def ejecutar(self):
        self.procesar(True)


def main():
    root = tk.Tk()
    Aplicacion(root)
    root.mainloop()


if __name__ == '__main__':
    main()
