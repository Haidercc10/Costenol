"""Regresión del transporte de errores Tcl en el editor observable, sin escritorio."""
import tkinter as tk
import unittest
from unittest.mock import Mock
from revision import EditorObservable


class PruebasProxyEditor(unittest.TestCase):
    def setUp(self):
        """Construye el proxy sin abrir Tk para aislar la frontera entre Python y Tcl."""
        self.editor = object.__new__(EditorObservable)
        self.editor.tk = Mock()
        self.editor.comando_original = '.editor_original'
        self.editor.event_generate = Mock()

    def test_seleccion_inexistente_se_devuelve_a_tcl(self):
        """Devuelve el error como datos para que los catch de Tk lo manejen sin traceback Python."""
        mensaje = 'text doesn\'t contain any characters tagged with "sel"'
        self.editor.tk.call.side_effect = tk.TclError(mensaje)
        self.assertEqual(self.editor.procesar_seguro('index', 'sel.first'), (1, mensaje))
        self.editor.event_generate.assert_not_called()

    def test_edicion_valida_notifica(self):
        """Una inserción válida conserva el resultado y sigue avisando al análisis automático."""
        self.editor.tk.call.return_value = ''
        self.assertEqual(self.editor.procesar_seguro('insert', 'insert', 'Hola'), (0, ''))
        self.editor.event_generate.assert_called_once_with('<<ContenidoCambiado>>', when='tail')

    def test_otros_errores_no_se_ocultan(self):
        """Un índice inválido sigue viajando como error Tcl y no se transforma en operación exitosa."""
        self.editor.tk.call.side_effect = tk.TclError('bad text index "noexiste"')
        estado, mensaje = self.editor.procesar_seguro('get', 'noexiste')
        self.assertEqual(estado, 1)
        self.assertIn('bad text index', mensaje)
        self.editor.event_generate.assert_not_called()

    def test_consulta_no_notifica(self):
        """Leer o consultar selección existente no programa una revisión de código."""
        self.editor.tk.call.return_value = '1.0'
        self.assertEqual(self.editor.procesar_seguro('index', 'sel.first'), (0, '1.0'))
        self.editor.event_generate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
