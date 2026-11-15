"""Pruebas de documentos simultáneos y selector de tema; requieren Tcl/Tk funcional."""
import tkinter as tk
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
from interfaz import Aplicacion


class PruebasPestanas(unittest.TestCase):
    def setUp(self):
        """Crea una aplicación oculta; omite si Tkinter no puede iniciar en el entorno."""
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.root.withdraw()
        self.app = Aplicacion(self.root)
        self.root.update()

    def tearDown(self):
        """Cancela la revisión pendiente y libera todos los editores y sus callbacks."""
        self.app.revision.detener()
        self.root.destroy()

    def test_texto_historial_y_resultados_independientes(self):
        """Conserva código no guardado, historial y salida al alternar entre documentos."""
        self.app.cargar('x Entero;')
        primero = self.app.activa
        self.app.editor.insert('end', '\nx=1;')
        self.app.editor.edit_separator()
        self.app.imprimir('Salida uno')
        self.app.nueva_pestana('y Texto;')
        segundo = self.app.activa
        self.app.imprimir('Salida dos')
        self.app.pestanas.select(primero)
        self.app.cambiar_documento()
        self.assertIn('x=1;', self.app.codigo())
        self.assertTrue(self.app.editor.edit_modified())
        self.assertIn('Salida uno', self.app.salida.get('1.0', 'end'))
        self.app.editor.edit_undo()
        self.assertEqual(self.app.codigo(), 'x Entero;')
        self.app.pestanas.select(segundo)
        self.app.cambiar_documento()
        self.assertEqual(self.app.codigo(), 'y Texto;')
        self.assertIn('Salida dos', self.app.salida.get('1.0', 'end'))

    def test_cierre_cancelable_y_ultima_pestana(self):
        """No descarta ediciones al cancelar y permite cerrar la última creando un documento vacío."""
        self.app.editor.insert('end', '\n// cambio //')
        with patch('interfaz.dialogo', return_value=None):
            self.app.cerrar_pestana()
        self.assertEqual(len(self.app.documentos), 1)
        with patch('interfaz.dialogo', return_value=False):
            self.app.cerrar_pestana()
        self.assertEqual(len(self.app.documentos), 1)
        self.assertEqual(self.app.codigo(), '')

    def test_abrir_archivo_sin_duplicarlo(self):
        """Abrir una ruta repetida selecciona su pestaña sin perder cambios ni crear duplicados."""
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / 'uno.pqek'
            archivo.write_text('x Entero;', encoding='utf-8')
            with patch('interfaz.seleccionar_archivo', return_value=str(archivo)):
                self.app.abrir()
                self.app.editor.insert('end', '\nx=2;')
                self.app.abrir()
            self.assertEqual(len(self.app.documentos), 2)
            self.assertIn('x=2;', self.app.codigo())

    def test_switch_conserva_documentos(self):
        """El interruptor alterna la paleta y conserva el código de los archivos abiertos."""
        codigo = self.app.codigo()
        self.app.selector_tema.alternar()
        self.assertEqual(self.app.tema.get(), 'Claro')
        self.assertEqual(self.app.codigo(), codigo)
        self.app.selector_tema.alternar()
        self.assertEqual(self.app.tema.get(), 'Oscuro')


if __name__ == '__main__':
    unittest.main()
