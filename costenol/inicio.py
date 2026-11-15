"""Pantalla de bienvenida animada y precarga de los recursos visuales de Costeñol."""
import math
from pathlib import Path
import time
import tkinter as tk
from recursos import identidad_windows, icono_ventana, ruta_tk, configurar_tk_portable


class PantallaInicio:
    def __init__(self, root, construir):
        """Muestra el splash oscuro mientras precarga logos y construye la ventana oculta.
        construir debe recibir la raíz y devolver la aplicación principal.
        """
        self.root = root
        self.construir = construir
        self.cerrada = False
        self.lista = False
        self.tareas = set()
        self.inicio = time.monotonic()
        root.withdraw()
        root.configure(bg='#0d1117')
        root._imagenes_precargadas = {}
        self.ventana = tk.Toplevel(root, bg='#0d1117')
        self.ventana.withdraw()
        self.ventana.overrideredirect(True)
        ancho, alto = 540, 300
        x = max(0, (root.winfo_screenwidth() - ancho) // 2)
        y = max(0, (root.winfo_screenheight() - alto) // 2)
        self.ventana.geometry(f'{ancho}x{alto}+{x}+{y}')
        self.canvas = tk.Canvas(self.ventana, width=ancho, height=alto,
                                bg='#0d1117', highlightthickness=1, highlightbackground='#263549')
        self.canvas.pack(fill='both', expand=True)
        self.logo = self.canvas.create_text(270, 105, text='Costeñol', fill='#e6edf3',
                                             font=('Segoe UI', 30, 'bold'))
        self.canvas.create_text(270, 190, text='Tu código, con sabor a la costa.',
                                fill='#9daabc', font=('Segoe UI', 11))
        self.canvas.create_rectangle(90, 226, 450, 230, fill='#202b3b', outline='')
        self.barra = self.canvas.create_rectangle(90, 226, 180, 230, fill='#00c9c2', outline='')
        self.estado = self.canvas.create_text(270, 255, text='Preparando Costeñol…',
                                              fill='#9daabc', font=('Segoe UI', 10))
        self.ventana.protocol('WM_DELETE_WINDOW', self.cancelar)
        self.ventana.bind('<Escape>', lambda evento: self.cancelar())
        self.recursos = iter([
            'Logo costeñol blanco sobre fondo transparente.png',
            'Logo costeñol con fondo transparente.png',
            'Puente, sol y ondas_ isotipo costero.png',
        ])
        self.ventana.deiconify()
        self.programar(20, self.animar)
        self.programar(40, self.precargar)

    def programar(self, demora, funcion):
        """Registra un callback de inicio y evita ejecutarlo después de cerrar el splash."""
        def ejecutar():
            """Retira la tarea completada y ejecuta su acción si la pantalla sigue activa."""
            self.tareas.discard(identificador)
            if not self.cerrada:
                funcion()
        identificador = self.root.after(demora, ejecutar)
        self.tareas.add(identificador)

    def animar(self):
        """Anima suavemente el logo y una barra indeterminada, sin inventar porcentajes."""
        tiempo = time.monotonic() - self.inicio
        self.canvas.coords(self.logo, 270, 105 + 3 * math.sin(tiempo * 3))
        avance = (1 + math.sin(tiempo * 3.6 - math.pi / 2)) / 2
        x = 90 + 270 * avance
        self.canvas.coords(self.barra, x, 226, x + 90, 230)
        self.programar(16, self.animar)

    def precargar(self):
        """Carga un recurso por turno del bucle gráfico y lo comparte con la ventana principal."""
        nombre = next(self.recursos, None)
        if nombre is None:
            self.canvas.itemconfigure(self.estado, text='Preparando el editor…')
            self.programar(30, self.construir_editor)
            return
        try:
            imagen = tk.PhotoImage(master=self.root, file=ruta_tk(Path(__file__).parent / 'logo' / nombre))
            self.root._imagenes_precargadas[nombre] = imagen
            if 'blanco' in nombre:
                factor = max(1, (imagen.width() + 359) // 360, (imagen.height() + 119) // 120)
                self.logo_visible = imagen.subsample(factor, factor)
                self.canvas.delete(self.logo)
                self.logo = self.canvas.create_image(270, 105, image=self.logo_visible)
        except (tk.TclError, OSError):
            # La falta de una imagen no impide abrir el editor.
            pass
        self.programar(35, self.precargar)

    def construir_editor(self):
        """Construye el editor todavía oculto y lo revela cuando su diseño está listo."""
        try:
            self.aplicacion = self.construir(self.root)
            self.root.update_idletasks()
        except Exception:
            self.cancelar()
            raise
        self.lista = True
        # Una bienvenida breve, sin añadir una espera artificial de varios segundos.
        espera = max(0, 800 - int((time.monotonic() - self.inicio) * 1000))
        self.programar(espera, self.terminar)

    def limpiar(self):
        """Cancela las tareas de animación pendientes y destruye la pantalla una sola vez."""
        if self.cerrada:
            return
        self.cerrada = True
        for tarea in list(self.tareas):
            self.root.after_cancel(tarea)
        self.tareas.clear()
        self.ventana.destroy()

    def terminar(self):
        """Muestra el editor completamente preparado y retira la bienvenida sin perder el foco."""
        if not self.lista:
            return
        self.root.deiconify()
        self.root.update_idletasks()
        self.limpiar()
        self.root.lift()
        self.aplicacion.editor.focus_set()

    def cancelar(self):
        """Permite salir con Escape y libera tanto el splash como la aplicación pendiente."""
        self.limpiar()
        self.root.destroy()

class VistaIndependiente(PantallaInicio):
    """Vista de bienvenida cuyo bucle de animación vive separado de la carga del editor."""
    def __init__(self, root, conexion):
        """Recibe un canal con el proceso principal y carga solo el logo visible del splash."""
        self.conexion = conexion
        super().__init__(root, None)
        self.recursos = iter(['Logo costeñol blanco sobre fondo transparente.png'])

    def construir_editor(self):
        """Anuncia que el splash está visible; la construcción ocurre en el proceso principal."""
        try:
            self.conexion.send('visible')
        except (BrokenPipeError, EOFError, OSError):
            self.terminar()
            return
        self.escuchar()

    def escuchar(self):
        """Consulta el canal sin bloquear la animación y cierra al terminar la carga real."""
        try:
            if self.conexion.poll():
                self.conexion.recv()
                self.terminar()
                return
        except (BrokenPipeError, EOFError, OSError):
            self.terminar()
            return
        self.programar(16, self.escuchar)

    def terminar(self):
        """Retira únicamente la bienvenida; el editor pertenece a otro proceso."""
        self.limpiar()
        self.root.destroy()

    def cancelar(self):
        """Comunica Escape al editor y cierra la vista sin dejar su proceso abierto."""
        try:
            self.conexion.send('cancelar')
        except (BrokenPipeError, EOFError, OSError):
            pass
        self.terminar()


def ejecutar_vista(conexion):
    """Punto de entrada del proceso de bienvenida; crea y usa su propio intérprete de Tk."""
    try:
        configurar_tk_portable()
        identidad_windows()
        root = tk.Tk()
        root.withdraw()
        icono_ventana(root)
        VistaIndependiente(root, conexion)
        root.mainloop()
    except Exception:
        try:
            conexion.send('fallo')
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        conexion.close()


class InicioIndependiente:
    def __init__(self, root, construir):
        """Inicia el splash en un proceso spawn y mantiene oculto el editor hasta estar listo.
        Cada proceso utiliza su propio Tk; no se accede a widgets desde hilos externos.
        """
        import multiprocessing
        self.root = root
        self.construir = construir
        self.cerrado = False
        self.aplicacion = None
        self.inicio = time.monotonic()
        self.proceso = None
        self.conexion = None
        root.withdraw()
        root.configure(bg='#0d1117')
        contexto = multiprocessing.get_context('spawn')
        padre, hijo = contexto.Pipe()
        try:
            self.proceso = contexto.Process(target=ejecutar_vista, args=(hijo,), daemon=True)
            self.proceso.start()
            hijo.close()
            self.conexion = padre
            root.after(20, self.esperar_vista)
        except (OSError, RuntimeError):
            padre.close()
            hijo.close()
            self.cargar_editor()

    def esperar_vista(self):
        """Espera la confirmación de dibujo sin bloquear Tk; si el splash falla abre el editor."""
        if self.cerrado:
            return
        try:
            if self.conexion.poll():
                mensaje = self.conexion.recv()
                if mensaje == 'cancelar':
                    self.cancelar()
                else:
                    self.cargar_editor()
                return
        except (EOFError, OSError):
            self.cargar_editor()
            return
        if not self.proceso.is_alive() or time.monotonic() - self.inicio > 5:
            self.cargar_editor()
        else:
            self.root.after(20, self.esperar_vista)

    def cargar_editor(self):
        """Construye la ventana principal; la bienvenida continúa animándose en paralelo."""
        try:
            self.aplicacion = self.construir(self.root)
            self.root.update_idletasks()
            # Respetar una cancelación recibida mientras se construían los widgets.
            if self.cancelacion_pendiente():
                self.cancelar()
                return
            self.root.deiconify()
            self.root.update_idletasks()
            self.finalizar_vista()
            self.root.lift()
            self.aplicacion.editor.focus_set()
        except Exception:
            self.finalizar_vista()
            if self.root.winfo_exists():
                self.root.destroy()
            raise

    def cancelacion_pendiente(self):
        """Detecta Escape sin convertir la desaparición del splash en un fallo del editor."""
        try:
            return self.conexion is not None and self.conexion.poll() and self.conexion.recv() == 'cancelar'
        except (EOFError, OSError):
            return False

    def finalizar_vista(self):
        """Solicita cerrar el proceso de bienvenida y programa su recogida sin esperar en Tk."""
        if self.cerrado:
            return
        self.cerrado = True
        if self.conexion is not None:
            try:
                self.conexion.send('terminar')
            except (BrokenPipeError, EOFError, OSError):
                pass
            self.conexion.close()
        if self.proceso is not None and self.proceso.pid is not None:
            self.limite_recogida = time.monotonic() + 2
            self.root.after(100, self.recoger_proceso)

    def recoger_proceso(self):
        """Libera el proceso cerrado; evita dejar una bienvenida bloqueada de forma indefinida."""
        if self.proceso.is_alive():
            if time.monotonic() >= self.limite_recogida:
                self.proceso.terminate()
            self.proceso.join(timeout=0)
            self.root.after(100, self.recoger_proceso)
        else:
            self.proceso.join(timeout=0)
            self.proceso.close()

    def cancelar(self):
        """Cancela también el inicio principal cuando se pulsa Escape en la bienvenida."""
        self.finalizar_vista()
        if self.proceso is not None and self.proceso.pid is not None:
            self.proceso.join(timeout=0.1)
            if self.proceso.is_alive():
                self.proceso.terminate()
        self.root.destroy()
