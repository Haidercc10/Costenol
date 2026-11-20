"""Controles visuales reutilizables de la interfaz de Costeñol."""
import tkinter as tk
from tema import COLORES


class InterruptorTema(tk.Canvas):
    def __init__(self, parent, variable, command, compacto=False):
        """Crea un switch accesible con ratón, Espacio y Enter para alternar Claro/Oscuro."""
        self.compacto = compacto
        super().__init__(parent, width=42 if compacto else 118, height=28 if compacto else 34, highlightthickness=0 if compacto else 1,
                         takefocus=True, cursor='hand2', relief='flat')
        self.variable = variable
        self.command = command
        self.posicion = 1.0 if variable.get() == 'Oscuro' else 0.0
        self.animacion = None
        self.bind('<Button-1>', self.alternar)
        self.bind('<space>', self.alternar)
        self.bind('<Return>', self.alternar)
        self.bind('<FocusIn>', self.dibujar)
        self.bind('<FocusOut>', self.dibujar)
        self.dibujar()

    def alternar(self, evento=None):
        """Alterna el tema y sincroniza el indicador inmediatamente, sin animaciones pendientes."""
        if self.animacion is not None:
            self.after_cancel(self.animacion)
            self.animacion = None
        self.variable.set('Claro' if self.variable.get() == 'Oscuro' else 'Oscuro')
        self.posicion = 1.0 if self.variable.get() == 'Oscuro' else 0.0
        self.command()
        self.dibujar()
        return 'break'

    def animar(self, destino):
        """Interpola el indicador hacia su nueva posición; cancela la tarea al llegar."""
        self.animacion = None
        diferencia = destino - self.posicion
        self.posicion = destino if abs(diferencia) < 0.025 else self.posicion + diferencia * 0.35
        self.dibujar()
        if self.posicion != destino:
            self.animacion = self.after(12, self.animar, destino)

    def dibujar(self, evento=None):
        """Redibuja la pista, el indicador y el nombre del tema con la paleta actual."""
        c = COLORES
        self.configure(bg=c['fondo'], highlightbackground=c['borde'], highlightcolor=c['acento'])
        self.delete('all')
        color = '#315880' if self.variable.get() == 'Oscuro' else '#7796b5'
        if self.compacto:
            self.configure(bg=c['panel'])
            self.create_line(12, 14, 30, 14, fill=color, width=18, capstyle='round')
            x = 12 + 18 * self.posicion
            self.create_oval(x-6, 8, x+6, 20, fill='#f4f7fc', outline='')
            return
        self.create_line(17, 17, 43, 17, fill=color, width=24, capstyle='round')
        x = 17 + 26 * self.posicion
        self.create_oval(x-9, 8, x+9, 26, fill='#f4f7fc', outline='')
        self.create_text(66, 17, text=self.variable.get(), anchor='w',
                         fill=c['texto'], font=('Segoe UI', 10))

    def destroy(self):
        """Cancela la animación pendiente antes de liberar el control."""
        if self.animacion is not None:
            self.after_cancel(self.animacion)
        super().destroy()

class Tooltip:
    def __init__(self, widget, texto):
        """Asocia una ayuda breve al pasar el ratón o enfocar un control con el teclado."""
        self.widget = widget
        self.texto = texto
        self.ventana = None
        self.tarea = None
        widget.bind('<Enter>', self.programar, add='+')
        widget.bind('<FocusIn>', self.programar, add='+')
        for evento in ('<Leave>', '<FocusOut>', '<ButtonPress>', '<Destroy>'):
            widget.bind(evento, self.ocultar, add='+')

    def programar(self, evento=None):
        """Programa la ayuda con una breve espera para no interrumpir el movimiento del puntero."""
        self.ocultar()
        self.tarea = self.widget.after(350, self.mostrar)

    def mostrar(self):
        """Abre un globo sin foco junto al control, ajustado a los límites de pantalla."""
        self.tarea = None
        if not self.widget.winfo_exists():
            return
        texto = self.texto() if callable(self.texto) else self.texto
        self.ventana = tk.Toplevel(self.widget)
        self.ventana.overrideredirect(True)
        tk.Label(self.ventana, text=texto, bg=COLORES['elevado'], fg=COLORES['texto'],
                 font=('Segoe UI', 10), padx=10, pady=6, relief='solid', borderwidth=1).pack()
        self.ventana.update_idletasks()
        x = min(self.widget.winfo_rootx() + self.widget.winfo_width() + 6,
                self.widget.winfo_screenwidth() - self.ventana.winfo_reqwidth() - 8)
        y = min(self.widget.winfo_rooty(),
                self.widget.winfo_screenheight() - self.ventana.winfo_reqheight() - 8)
        self.ventana.geometry(f'+{max(0,x)}+{max(0,y)}')

    def ocultar(self, evento=None):
        """Cancela la ayuda pendiente y destruye el globo al salir o activar el control."""
        if self.tarea is not None:
            self.widget.after_cancel(self.tarea)
            self.tarea = None
        if self.ventana is not None:
            self.ventana.destroy()
            self.ventana = None


class IconoAccion(tk.Canvas):
    def __init__(self, parent, icono, command, ayuda, ancho=46, alto=46):
        """Crea un botón vectorial sin texto visible, accesible por clic, Enter y Espacio."""
        super().__init__(parent, width=ancho, height=alto, highlightthickness=0,
                         takefocus=True, cursor='hand2', borderwidth=0)
        self.icono = icono
        self.command = command
        self.ancho, self.alto = ancho, alto
        self.encima = False
        self.tooltip = Tooltip(self, ayuda)
        self.bind('<Enter>', self.entrar, add='+')
        self.bind('<Leave>', self.salir, add='+')
        self.bind('<FocusIn>', self.entrar, add='+')
        self.bind('<FocusOut>', self.salir, add='+')
        for evento in ('<ButtonRelease-1>', '<Return>', '<space>'):
            self.bind(evento, self.activar)
        self.dibujar()

    def entrar(self, evento=None):
        """Marca el control al pasar el puntero o enfocarlo, sin ejecutar ninguna acción."""
        self.encima = True
        self.dibujar()

    def salir(self, evento=None):
        """Retira el estado visual de interacción al perder el puntero o el foco."""
        self.encima = False
        self.dibujar()

    def activar(self, evento=None):
        """Ejecuta una acción habilitada y cierra su tooltip; bloquea controles deshabilitados."""
        self.tooltip.ocultar()
        if self.cget('state') != 'disabled':
            self.command()
        return 'break'

    def dibujar(self):
        """Dibuja iconos con trazos consistentes, sin depender de fuentes o imágenes externas."""
        c = COLORES
        super().configure(bg=c['elevado'] if self.encima else c['panel'])
        self.delete('all')
        color = c['acento'] if self.encima else c['suave']
        if self.cget('state') == 'disabled':
            color = '#68768a'
        x, y = self.ancho/2, self.alto/2
        if self.encima:
            self.create_rectangle(0, 8, 2, self.alto-8, fill=c['acento'], outline='')
        if self.icono == 'ejecutar':
            self.create_polygon(x-7,y-10,x+10,y,x-7,y+10, fill='', outline=color, width=1.7)
        elif self.icono == 'analizar':
            self.create_line(x-8,y-11,x+4,y-11,x+9,y-6,x+9,y+10,x-8,y+10,x-8,y-11,fill=color,width=1.5)
            self.create_line(x-4,y,x,y+4,x+6,y-4,fill=color,width=1.8)
        elif self.icono == 'cerrar':
            self.create_rectangle(x-10,y-10,x+4,y+4,outline=color,width=1.3)
            self.create_rectangle(x-4,y-4,x+10,y+10,fill=c['elevado'] if self.encima else c['panel'],outline=color,width=1.3)
            self.create_line(x,y,x+6,y+6,fill=color,width=1.5)
            self.create_line(x+6,y,x,y+6,fill=color,width=1.5)
        elif self.icono == 'limpiar':
            self.create_line(x+9,y-11,x-2,y+1,fill=color,width=1.8)
            self.create_polygon(x-5,y-1,x+3,y+6,x-3,y+12,x-12,y+5,fill='',outline=color,width=1.5)
            self.create_line(x-8,y+3,x-1,y+9,fill=color,width=1.2)
        elif self.icono == 'abrir':
            self.create_line(x-11,y+8,x-11,y-8,x-3,y-8,x,y-4,x+10,y-4,fill=color,width=1.5)
            self.create_polygon(x-10,y-2,x+12,y-2,x+8,y+10,x-12,y+10,fill='',outline=color,width=1.5)

    def configure(self, cnf=None, **opciones):
        """Refresca el icono al cambiar el estado normal/deshabilitado desde la ejecución."""
        resultado = super().configure(cnf, **opciones)
        if hasattr(self, 'icono') and ('state' in opciones or isinstance(cnf, dict) and 'state' in cnf):
            self.dibujar()
        return resultado
