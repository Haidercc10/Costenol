"""Regresión del diagnóstico semántico de reservadas como nombres de declaración."""
import unittest
from lexer import PALABRAS
from semantico import analizar_semantica, ErrorSemantico


class PruebasNombresReservados(unittest.TestCase):
    def test_mismo_error_en_todos_los_casos(self):
        """La escritura exacta y sus variantes reciben el mismo tipo y explicación costeña."""
        for palabra in PALABRAS:
            for nombre in {palabra, palabra.lower(), palabra.upper(), palabra.swapcase()}:
                with self.subTest(nombre=nombre), self.assertRaises(ErrorSemantico) as captura:
                    analizar_semantica(f'{nombre} Texto;')
                mensaje = str(captura.exception)
                self.assertIn('Línea 1, columna 1:', mensaje)
                self.assertIn('palabra reservada', mensaje)
                self.assertIn('ese nombre ya está apartado', mensaje)

    def test_tipos_del_ejemplo(self):
        """Verifica explícitamente las declaraciones indicadas por el usuario."""
        for codigo in ['Texto Texto;', 'texto Texto;', 'Entero Entero;', 'entero Entero;']:
            with self.subTest(codigo=codigo), self.assertRaises(ErrorSemantico):
                analizar_semantica(codigo)
        analizar_semantica('nombre Texto; edad Entero; Si (1 == 1) Mensaje.Texto("Hola"); FinSi')


if __name__ == '__main__':
    unittest.main()
