"""Controles visuales reutilizables de la interfaz de Costeñol."""
import tkinter as tk
from tema import COLORES


class InterruptorTema(tk.Canvas):
    def __init__(self, parent, variable, command):
        """Crea un switch accesible con ratón, Espacio y Enter para alternar Claro/Oscuro."""
        super().__init__(parent, width=118, height=34, highlightthickness=1,
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
        """Alterna el tema y anima el desplazamiento del indicador sin detener Tkinter."""
        self.variable.set('Claro' if self.variable.get() == 'Oscuro' else 'Oscuro')
        self.command()
        if self.animacion is not None:
            self.after_cancel(self.animacion)
        destino = 1.0 if self.variable.get() == 'Oscuro' else 0.0
        self.animar(destino)
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
