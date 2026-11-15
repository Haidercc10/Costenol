"""Pruebas de resaltado tolerante y extensión de guardado, sin requerir interfaz gráfica."""
from pathlib import Path
import unittest
from resaltado import rangos_reservadas
from archivos import ruta_guardado


class PruebasResaltadoYArchivos(unittest.TestCase):
    def test_reservadas_exactas_y_posiciones(self):
        """Colorea solo palabras completas con la escritura válida del lenguaje."""
        self.assertEqual(rangos_reservadas('edad Entero;\nSi (edad > 0) FinSi'),
                         [('1.5', '1.11'), ('2.0', '2.2'), ('2.14', '2.19')])
        self.assertEqual(rangos_reservadas('entero ENTERO Siendo CapturaExtra'), [])
        self.assertEqual(rangos_reservadas('Captura.Texto();'), [('1.0', '1.7'), ('1.8', '1.13')])

    def test_no_colorea_cadenas_y_comentarios(self):
        """Evita falsos resaltados incluso si una cadena o comentario está incompleto."""
        self.assertEqual(rangos_reservadas('"Si Entero" // Captura FinSi //'), [])
        self.assertEqual(rangos_reservadas('"Texto Si sin cierre'), [])
        self.assertEqual(rangos_reservadas('// Si Entero sin cierre'), [])
        self.assertEqual(rangos_reservadas('// Si // Texto'), [('1.9', '1.14')])
        self.assertEqual(rangos_reservadas(r'"Texto \" Si" Entero'), [('1.14', '1.20')])

    def test_guardado_pqek(self):
        """Añade la extensión ausente y acepta su forma en mayúsculas."""
        self.assertEqual(ruta_guardado('programa'), Path('programa.pqek'))
        self.assertEqual(ruta_guardado('programa.PQEK'), Path('programa.PQEK'))
        self.assertEqual(ruta_guardado('carpeta/programa.pqek'), Path('carpeta/programa.pqek'))

    def test_rechaza_extensiones_ajenas(self):
        """Rechaza extensiones incorrectas y nombres ambiguos antes de escribir contenido."""
        for nombre in ['programa.txt', 'programa.py', 'programa.cost', 'programa.pqek.exe', 'programa.', 'programa ']:
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                ruta_guardado(nombre)


if __name__ == '__main__':
    unittest.main()
