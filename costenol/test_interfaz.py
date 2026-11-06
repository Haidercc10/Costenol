"""Pruebas de integración de Tkinter; requieren un escritorio disponible."""
import tempfile
import tkinter as tk
from pathlib import Path
import unittest
from unittest.mock import patch
from interfaz import Aplicacion


class PruebasInterfaz(unittest.TestCase):
    def setUp(self):
        """Crea una ventana oculta y una aplicación nueva para cada prueba; omite si Tcl/Tk no inicia."""
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk no disponible: {error}')
        self.root.withdraw()
        self.app = Aplicacion(self.root)
        self.root.update()

    def tearDown(self):
        """Destruye la ventana de la prueba para liberar los recursos gráficos."""
        self.root.destroy()

    def cargar(self, codigo):
        """Carga código en el editor y procesa eventos pendientes antes de realizar las comprobaciones."""
        self.app.cargar(codigo)
        self.root.update()

    def salida(self):
        """Devuelve el contenido del panel de resultados para comprobarlo en la prueba."""
        return self.app.salida.get('1.0', 'end')

    def test_analisis_y_errores(self):
        """Comprueba análisis correcto, categorías de error, resaltado y restauración del editor."""
        self.cargar('edad Entero; edad=20;')
        self.app.analizar()
        self.assertIn('Código válido', self.salida())
        for codigo, categoria in [('x = @;', 'Error léxico'), ('x = ;', 'Error sintáctico'),
                                  ('x Entero;\nx="hola";', 'Error semántico'),
                                  ('Mensaje.Texto(1/0);', 'Error de ejecución')]:
            with self.subTest(categoria=categoria):
                self.cargar(codigo)
                self.app.ejecutar()
                self.root.update()
                self.assertIn(categoria, self.salida())
                self.assertTrue(self.app.editor.tag_ranges('error'))
                self.assertFalse(self.app.ocupada)
                self.assertEqual(str(self.app.editor['state']), 'normal')

    def test_captura_cancelacion_y_buffer(self):
        """Comprueba capturas simuladas, ejecución del editor y cancelación sin mensaje de éxito."""
        self.cargar('x Entero; x=Captura.Entero(); Mensaje.Texto(x*2);')
        with patch('interfaz.dialogo', return_value='7'):
            self.app.ejecutar()
        self.assertIn('14\n', self.salida())
        self.assertIn('Ejecución finalizada.', self.salida())
        with patch('interfaz.dialogo', return_value=None):
            self.app.ejecutar()
        self.assertIn('captura cancelada', self.salida())
        self.assertNotIn('Ejecución finalizada.', self.salida())

    def test_cambio_tema_conserva_documento(self):
        """Comprueba que alternar temas conserva código, salida y cambios pendientes."""
        self.cargar('Mensaje.Texto("Hola");')
        self.app.editor.insert('end', '\n// pendiente //')
        self.app.imprimir('Resultado conservado')
        codigo = self.app.codigo()
        salida = self.salida()
        for nombre, fondo in [('Claro', '#ffffff'), ('Oscuro', '#161b22')]:
            self.app.tema.set(nombre)
            self.app.cambiar_tema()
            self.assertIs(self.app.logo_cabecera, self.app.logos_cabecera[nombre])
            self.assertEqual(self.app.editor.cget('background'), fondo)
            self.assertEqual(self.app.salida.cget('background'), fondo)
            self.assertEqual(self.app.codigo(), codigo)
            self.assertEqual(self.salida(), salida)
            self.assertTrue(self.app.editor.edit_modified())

    def test_archivos_y_cambios(self):
        """Verifica guardado, apertura, cambios pendientes y cancelación usando archivos temporales."""
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / 'programa.cost'
            self.cargar('Mensaje.Texto("Hola");')
            self.assertTrue(self.app.escribir(archivo))
            self.app.editor.insert('end', '\n// cambio //')
            self.root.update()
            self.assertTrue(self.app.editor.edit_modified())
            with patch('interfaz.dialogo', return_value=None):
                self.assertFalse(self.app.confirmar_cambios())
            with patch('interfaz.dialogo', return_value=True):
                self.assertTrue(self.app.confirmar_cambios())
            self.assertIn('// cambio //', archivo.read_text(encoding='utf-8'))
            with patch('interfaz.seleccionar_archivo', return_value=str(archivo)):
                self.app.abrir()
            self.assertEqual(self.app.codigo(), archivo.read_text(encoding='utf-8'))
            self.assertFalse(self.app.editor.edit_modified())
            self.assertIn('programa.cost', self.root.title())


if __name__ == '__main__':
    unittest.main()

