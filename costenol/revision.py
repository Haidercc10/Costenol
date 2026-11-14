"""Revisión estática diferida y editor que notifica cada cambio de contenido."""
import tkinter as tk
from lexer import ErrorLexico
from parser import ErrorSintactico
from semantico import analizar_semantica, ErrorSemantico


class RevisionAutomatica:
    def __init__(self, programar, cancelar, publicar, analizar=analizar_semantica, espera=700):
        """Recibe funciones de temporización y publicación; nunca ejecuta el código revisado."""
        self.programar = programar
        self.cancelar = cancelar
        self.publicar = publicar
        self.analizar = analizar
        self.espera = espera
        self.pendiente = None
        self.version = 0

    def detener(self):
        """Cancela la revisión pendiente e invalida callbacks de documentos anteriores."""
        self.version += 1
        if self.pendiente is not None:
            self.cancelar(self.pendiente)
            self.pendiente = None

    def solicitar(self, codigo):
        """Reinicia la espera tras cada edición; solo publica el diagnóstico del código más reciente."""
        self.detener()
        version = self.version

        def revisar():
            """Valida sin efectos y publica el primer error o None si el texto es válido."""
            if version != self.version:
                return
            self.pendiente = Non e 
            error = None
            try:
                self.analizar(codigo)
            except (ErrorLexico, ErrorSintactico, ErrorSemantico, RecursionError, ValueError, OverflowError) as causa:
                error = causa
            if version == self.version:
                self.publicar(error)

        self.pendiente = self.programar(self.espera, revisar)


class EditorObservable(tk.Text):
    def __init__(self, master, **opciones):
        """Intercepta ediciones para notificar escritura, pegado, borrado y deshacer/rehacer."""
        super().__init__(master, **opciones)
        self.comando_original = self._w + '_original'
        self.tk.call('rename', self._w, self.comando_original)
        self.comando_proxy = self._w + '_proxy'
        self.tk.createcommand(self.comando_proxy, self.procesar_seguro)
        # Los bindings de Tk consultan sel.first dentro de un catch de Tcl.
        # Un callback Python no debe lanzar antes de que ese catch pueda actuar.
        self.tk.call('proc', self._w, 'args',
                     'set respuesta [' + self.comando_proxy + ' {*}$args]; '
                     'if {[lindex $respuesta 0]} {'
                     'return -code error [lindex $respuesta 1]}; '
                     'return [lindex $respuesta 1]')

    def procesar_seguro(self, *argumentos):
        """Transporta resultados y errores de Tk como datos hasta el wrapper de Tcl.
        Así Tcl puede capturar consultas de selección vacía durante copiar/pegar
        sin que Python imprima una excepción. No oculta otros errores de Tk:
        el wrapper los devuelve con -code error al llamador original.
        """
        try:
            return (0, self.procesar_comando(*argumentos))
        except tk.TclError as error:
            return (1, str(error))

    def procesar_comando(self, *argumentos):
        """Delega en Text y emite un evento solo ante operaciones que pueden modificar el texto.
        No reinicia la marca de cambios sin guardar ni interviene en la selección del usuario.
        """
        resultado = self.tk.call(self.comando_original, *argumentos)
        edicion = argumentos[0] in {'insert', 'delete', 'replace'}
        historial = argumentos[0] == 'edit' and len(argumentos) > 1 and argumentos[1] in {'undo', 'redo'}
        if edicion or historial:
            self.event_generate('<<ContenidoCambiado>>', when='tail')
        return resultado

    def destroy(self):
        """Libera el comando proxy al destruir el editor y sus recursos de Tkinter."""
        super().destroy()
        self.tk.call('rename', self._w, '')
        self.tk.deletecommand(self.comando_proxy)
