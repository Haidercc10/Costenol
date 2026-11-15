"""Pruebas del ciclo de vida de la bienvenida, sin requerir un escritorio."""
import unittest
from unittest.mock import Mock, patch
from inicio import PantallaInicio


class PruebasInicio(unittest.TestCase):
    def setUp(self):
        """Prepara una pantalla simulada para comprobar tareas, cierre y transición al editor."""
        self.inicio = object.__new__(PantallaInicio)
        self.inicio.root = Mock()
        self.inicio.ventana = Mock()
        self.inicio.cerrada = False
        self.inicio.lista = False
        self.inicio.tareas = set()
        self.inicio.aplicacion = Mock()

    def test_callback_cancelado_no_ejecuta(self):
        """Impide que una tarea ya cancelada actúe sobre una ventana destruida."""
        self.inicio.root.after.return_value = 'tarea1'
        accion = Mock()
        self.inicio.programar(20, accion)
        callback = self.inicio.root.after.call_args.args[1]
        self.inicio.limpiar()
        callback()
        accion.assert_not_called()
        self.inicio.root.after_cancel.assert_called_once_with('tarea1')

    def test_no_abre_editor_antes_de_estar_listo(self):
        """Mantiene oculta la raíz hasta completar la construcción del editor."""
        self.inicio.terminar()
        self.inicio.root.deiconify.assert_not_called()
        self.inicio.lista = True
        self.inicio.terminar()
        self.inicio.root.deiconify.assert_called_once()
        self.inicio.aplicacion.editor.focus_set.assert_called_once()
        self.assertTrue(self.inicio.cerrada)

    def test_cierre_idempotente(self):
        """Destruye el splash una sola vez aunque se solicite cerrar más de una vez."""
        self.inicio.limpiar()
        self.inicio.limpiar()
        self.inicio.ventana.destroy.assert_called_once()

    def test_fallo_construccion_libera_ventanas(self):
        """Limpia ventanas y tareas si la creación del editor falla y conserva la excepción."""
        self.inicio.construir = Mock(side_effect=RuntimeError('fallo simulado'))
        with self.assertRaises(RuntimeError):
            self.inicio.construir_editor()
        self.inicio.root.destroy.assert_called_once()
        self.assertTrue(self.inicio.cerrada)


if __name__ == '__main__':
    unittest.main()
