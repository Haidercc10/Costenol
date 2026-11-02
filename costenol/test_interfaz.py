"""Pruebas de integración de Tkinter; requieren un escritorio disponible."""
import tempfile
import tkinter as tk
from pathlib import Path
import unittest
from unittest.mock import patch
from interfaz import Aplicacion


class PruebasInterfaz(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk no disponible: {error}')
        self.root.withdraw()
        self.app = Aplicacion(self.root)
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def cargar(self, codigo):
        self.app.cargar(codigo)
        self.root.update()

    def salida(self):
        return self.app.salida.get('1.0', 'end')

    def test_analisis_y_errores(self):
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
        self.cargar('x Entero; x=Captura.Entero(); Mensaje.Texto(x*2);')
        with patch('interfaz.simpledialog.askstring', return_value='7'):
            self.app.ejecutar()
        self.assertIn('14\n', self.salida())
        self.assertIn('Ejecución finalizada.', self.salida())
        with patch('interfaz.simpledialog.askstring', return_value=None):
            self.app.ejecutar()
        self.assertIn('captura cancelada', self.salida())
        self.assertNotIn('Ejecución finalizada.', self.salida())

    def test_archivos_y_cambios(self):
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / 'programa.cost'
            self.cargar('Mensaje.Texto("Hola");')
            self.assertTrue(self.app.escribir(archivo))
            self.app.editor.insert('end', '\n// cambio //')
            self.root.update()
            self.assertTrue(self.app.editor.edit_modified())
            with patch('interfaz.messagebox.askyesnocancel', return_value=None):
                self.assertFalse(self.app.confirmar_cambios())
            with patch('interfaz.messagebox.askyesnocancel', return_value=True):
                self.assertTrue(self.app.confirmar_cambios())
            self.assertIn('// cambio //', archivo.read_text(encoding='utf-8'))
            with patch('interfaz.filedialog.askopenfilename', return_value=str(archivo)):
                self.app.abrir()
            self.assertEqual(self.app.codigo(), archivo.read_text(encoding='utf-8'))
            self.assertFalse(self.app.editor.edit_modified())
            self.assertIn('programa.cost', self.root.title())


if __name__ == '__main__':
    unittest.main()

