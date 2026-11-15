"""Pruebas de coordinación del splash separado, sin abrir ventanas ni procesos reales."""
import unittest
from unittest.mock import Mock
from inicio import InicioIndependiente


class PruebasInicioIndependiente(unittest.TestCase):
    def setUp(self):
        """Aísla la coordinación mediante raíz, proceso y canal simulados."""
        self.inicio = object.__new__(InicioIndependiente)
        self.inicio.root = Mock()
        self.inicio.proceso = Mock()
        self.inicio.proceso.pid = 123
        self.inicio.conexion = Mock()
        self.inicio.conexion.poll.return_value = False
        self.inicio.cerrado = False
        self.inicio.construir = Mock(return_value=Mock())

    def test_editor_preparado_antes_de_cerrar_splash(self):
        """Mantiene el splash hasta preparar el editor y envía su cierre sin bloquear el bucle."""
        self.inicio.cargar_editor()
        self.inicio.construir.assert_called_once_with(self.inicio.root)
        self.inicio.root.deiconify.assert_called_once()
        self.inicio.conexion.send.assert_called_once_with('terminar')
        self.inicio.proceso.join.assert_not_called()
        self.inicio.root.after.assert_called_once()

    def test_splash_desaparecido_no_impide_abrir(self):
        """Un cierre inesperado del canal no rompe la construcción de la aplicación principal."""
        self.inicio.conexion.poll.side_effect = EOFError()
        self.inicio.cargar_editor()
        self.inicio.root.deiconify.assert_called_once()

    def test_cierre_se_solicita_una_sola_vez(self):
        """Evita enviar instrucciones a un canal ya cerrado al finalizar dos veces."""
        self.inicio.finalizar_vista()
        self.inicio.finalizar_vista()
        self.inicio.conexion.send.assert_called_once_with('terminar')
        self.inicio.conexion.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
