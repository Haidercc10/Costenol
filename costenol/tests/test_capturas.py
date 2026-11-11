"""Pruebas de formatos de entrada, edición parcial y nombres reservados."""
import unittest
from capturas import convertir_captura, permite_edicion
from lexer import PALABRAS
from parser import ErrorSintactico
from semantico import analizar_semantica, ErrorSemantico
from interprete import ejecutar, ErrorEjecucion


class PruebasCapturas(unittest.TestCase):
    def test_texto_solo_letras(self):
        """Admite letras acentuadas y espacios; rechaza dígitos, símbolos y texto vacío."""
        self.assertEqual(convertir_captura('Texto', ' María José '), ' María José ')
        for dato in ['123', 'Ana1', '-3,5', '', '   ', 'Ana@']:
            with self.subTest(dato=dato), self.assertRaises(ValueError):
                convertir_captura('Texto', dato)
        for dato in ['123', 'Ana2', '']:
            with self.subTest(dato=dato), self.assertRaises(ErrorEjecucion):
                ejecutar('t Texto; t=Captura.Texto();', entrada=lambda prompt: dato)

    def test_edicion_y_pegado(self):
        """Comprueba formatos parciales sin permitir pegar letras en números o dígitos en texto."""
        casos = {
            'Texto': (['', 'Ana', 'Ángel Ñ'], ['Ana1', '123', 'hola!']),
            'Entero': (['', '-', '+', '-12'], ['a', '12a', '3,5', '2.0', '--']),
            'Real': (['', '-', '3,', '-3,5'], ['hola', '3.5', '1,2,3', '4a']),
            'Logico': (['', 'Verdadero', 'falso'], ['si', '1', '2,5'])}
        for tipo, (validos, invalidos) in casos.items():
            for dato in validos:
                with self.subTest(tipo=tipo, dato=dato):
                    self.assertTrue(permite_edicion(tipo, dato))
            for dato in invalidos:
                with self.subTest(tipo=tipo, dato=dato):
                    self.assertFalse(permite_edicion(tipo, dato))

    def test_aceptacion_final(self):
        """Rechaza estados parciales al aceptar y convierte entradas completas por tipo."""
        for tipo, datos in {'Entero': ['', '-', '+'], 'Real': ['', '-', ',', '3,'],
                            'Logico': ['', '1', 'si']}.items():
            for dato in datos:
                with self.subTest(tipo=tipo, dato=dato), self.assertRaises(ValueError):
                    convertir_captura(tipo, dato)
        self.assertEqual(convertir_captura('Entero', '-12'), -12)
        self.assertEqual(convertir_captura('Real', '3,5'), 3.5)
        self.assertIs(convertir_captura('Logico', 'FALSO'), False)

    def test_reservadas_en_todas_las_variantes(self):
        """Impide usar cualquier reservada como nombre, sin distinguir mayúsculas."""
        for palabra in PALABRAS:
            for variante in {palabra, palabra.lower(), palabra.upper(), palabra.swapcase()}:
                with self.subTest(variante=variante), self.assertRaises((ErrorSintactico, ErrorSemantico)):
                    analizar_semantica(f'{variante} Entero;')
        for codigo in ['entero Entero;', 'texto Texto;', 'ENTERO Entero;',
                       'Si (1==1) mEnSaJe Texto; FinSi']:
            with self.subTest(codigo=codigo), self.assertRaises((ErrorSintactico, ErrorSemantico)):
                analizar_semantica(codigo)
        analizar_semantica('entero1 Entero; textoUsuario Texto;')

    def test_ubicacion_semantica(self):
        """Ubica el nombre reservado en su declaración sin alterar otras reglas del lenguaje."""
        with self.assertRaisesRegex(ErrorSemantico, 'Línea 2, columna 1:.*reservada'):
            analizar_semantica('edad Entero;\nentero Entero;')


if __name__ == '__main__':
    unittest.main()
