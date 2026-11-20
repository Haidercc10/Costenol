"""Pruebas de acciones de la barra lateral y limpieza del documento activo."""
from unittest.mock import patch
import unittest
import test_pestanas


class PruebasBarraLateral(unittest.TestCase):
    setUp = test_pestanas.PruebasPestanas.setUp
    tearDown = test_pestanas.PruebasPestanas.tearDown

    def test_limpieza_se_puede_deshacer_y_respeta_otro_documento(self):
        """Limpiar solo afecta al archivo activo y conserva el historial del código."""
        self.app.cargar('uno Entero;')
        primero = self.app.activa
        self.app.nueva_pestana('dos Texto;')
        self.app.imprimir('Resultado anterior')
        with patch('interfaz.dialogo', return_value=True):
            self.app.limpiar_todo()
        self.assertEqual(self.app.codigo(), '')
        self.assertEqual(self.app.salida.get('1.0', 'end-1c'), '')
        self.app.editor.edit_undo()
        self.assertEqual(self.app.codigo(), 'dos Texto;')
        self.app.pestanas.select(primero)
        self.app.cambiar_documento()
        self.assertEqual(self.app.codigo(), 'uno Entero;')

    def test_cancelar_limpieza_conserva_codigo_y_resultados(self):
        """Cancelar la confirmación mantiene el contenido del documento intacto."""
        codigo = self.app.codigo()
        self.app.imprimir('Salida conservada')
        with patch('interfaz.dialogo', return_value=None):
            self.app.limpiar_todo()
        self.assertEqual(self.app.codigo(), codigo)
        self.assertIn('Salida conservada', self.app.salida.get('1.0', 'end'))

    def test_limite_quince_pestanas_sin_perder_documentos(self):
        """Rechaza el documento 16 y permite crear otro al liberar una pestaña."""
        for _ in range(14):
            self.app.nueva_pestana('')
        activa = self.app.activa
        with patch('interfaz.avisar') as aviso:
            self.app.nueva_pestana('rechazado Texto;')
        self.assertEqual(len(self.app.documentos), 15)
        self.assertEqual(self.app.activa, activa)
        aviso.assert_called_once()
        self.assertIn('recursos', aviso.call_args.args[2])
        self.app.cerrar_pestana()
        self.app.nueva_pestana('permitido Texto;')
        self.assertEqual(len(self.app.documentos), 15)
        self.assertEqual(self.app.codigo(), 'permitido Texto;')

    def test_alternar_pestanas_reutiliza_resaltado(self):
        """Volver a un documento intacto no vuelve a recorrer sus tokens; editar sí lo hace."""
        import interfaz
        self.app.cargar('uno Entero;')
        primero = self.app.activa
        self.app.nueva_pestana('dos Texto;')
        with patch('interfaz.rangos_sintaxis', wraps=interfaz.rangos_sintaxis) as recorrer:
            self.app.pestanas.select(primero)
            self.app.cambiar_documento()
            self.app.resaltar_palabras()
            recorrer.assert_not_called()
            self.app.editor.insert('end', '\nuno = 2;')
            self.app.modificado()
            recorrer.assert_called_once()
