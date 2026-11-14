"""Pruebas de revisión diferida sin requerir una ventana de Tkinter."""
import unittest
from revision import RevisionAutomatica
from lexer import ErrorLexico
from parser import ErrorSintactico
from semantico import ErrorSemantico


class PruebasRevision(unittest.TestCase):
    def setUp(self):
        """Construye un reloj simulado y registra diagnósticos sin ejecutar el programa."""
        self.tareas = {}
        self.historial = []
        self.resultados = []
        self.revision = RevisionAutomatica(self.programar, self.cancelar, self.resultados.append)

    def programar(self, demora, callback):
        """Registra una tarea y su demora para dispararla de forma determinista en la prueba."""
        identificador = len(self.historial)
        self.historial.append((demora, callback))
        self.tareas[identificador] = callback
        return identificador

    def cancelar(self, identificador):
        """Retira la tarea del reloj simulado."""
        self.tareas.pop(identificador, None)

    def disparar(self):
        """Ejecuta la revisión vigente sin esperar tiempo real."""
        identificador = self.revision.pendiente
        self.tareas.pop(identificador)()

    def test_espera_y_solo_ultimo_codigo(self):
        """Comprueba que nuevas teclas reinician la espera y descartan callbacks anteriores."""
        self.revision.solicitar('x = @;')
        anterior = self.historial[-1][1]
        self.revision.solicitar('x Entero; x=1;')
        anterior()
        self.assertEqual(self.resultados, [])
        self.assertEqual(len(self.tareas), 1)
        self.assertEqual(self.historial[-1][0], 700)
        self.disparar()
        self.assertEqual(self.resultados, [None])

    def test_diagnostico_por_etapa_y_correccion(self):
        """Publica el primer error por etapa y None al corregir o vaciar el documento."""
        for codigo, categoria in [('x=@;', ErrorLexico), ('x=;', ErrorSintactico),
                                  ('x=1;', ErrorSemantico)]:
            self.revision.solicitar(codigo)
            self.disparar()
            self.assertIsInstance(self.resultados[-1], categoria)
        for codigo in ['x Entero; x=1;', '']:
            self.revision.solicitar(codigo)
            self.disparar()
            self.assertIsNone(self.resultados[-1])

    def test_no_ejecuta_capturas_o_division(self):
        """Valida código con capturas y división por cero sin pedir datos ni calcular resultados."""
        self.revision.solicitar('x Entero; x=Captura.Entero(); Mensaje.Texto(1/0);')
        self.disparar()
        self.assertEqual(self.resultados, [None])

    def test_cancelacion_al_cerrar_o_ejecutar(self):
        """Evita publicar un diagnóstico pendiente tras detener la revisión."""
        self.revision.solicitar('x=;')
        callback = self.historial[-1][1]
        self.revision.detener()
        callback()
        self.assertEqual(self.tareas, {})
        self.assertEqual(self.resultados, [])

    def test_limite_de_recursion(self):
        """Convierte un límite de análisis en diagnóstico en vez de romper el callback de la ventana."""
        def limite(codigo):
            """Simula una entrada que supera la profundidad de análisis."""
            raise RecursionError('Expresión demasiado profunda')
        self.revision.analizar = limite
        self.revision.solicitar('codigo')
        self.disparar()
        self.assertIsInstance(self.resultados[-1], RecursionError)


if __name__ == '__main__':
    unittest.main()
