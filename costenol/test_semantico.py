import unittest
from semantico import analizar_semantica, ErrorSemantico
from lexer import ErrorLexico
from parser import ErrorSintactico


class PruebasSemanticas(unittest.TestCase):
    def test_ejemplos(self):
        # Caso independiente de los archivos que el estudiante edita al practicar.
        analizar_semantica('edad Entero; edad=20; nombre Texto; nombre="Ana"; '
                          'b Logico; b=edad>=18; resultado Texto; '
                          'Si (b) resultado="mayor"; Sino resultado="menor"; FinSi '
                          'Mensaje.Texto(nombre); Mensaje.Texto(resultado);')

    def test_capturas_y_tabla(self):
        for tipo in ['Texto', 'Entero', 'Real', 'Logico']:
            with self.subTest(tipo=tipo):
                tabla = analizar_semantica(f'x {tipo}; x = Captura.{tipo}(); Mensaje.Texto(x);')
                self.assertEqual(tabla['x']['tipo'], tipo)
                self.assertTrue(tabla['x']['inicializada'])
        self.assertFalse(analizar_semantica('x Entero;')['x']['inicializada'])
        self.assertEqual(analizar_semantica(''), {})

    def test_declaraciones(self):
        for codigo in ['x = 1;', 'Mensaje.Texto(x);', 'x Entero; x Real;',
                       'x Entero; x = y + 1;', 'x = 1; x Entero;']:
            with self.subTest(codigo=codigo), self.assertRaises(ErrorSemantico):
                analizar_semantica(codigo)

    def test_asignaciones(self):
        analizar_semantica('x Real; x = 2; x = 3,5;')
        for codigo in ['x Entero; x = 2,5;', 'x Entero; x = 4 / 2;',
                       'x Texto; x = 2;', 'x Logico; x = 1;',
                       'x Entero; x = Captura.Real();']:
            with self.subTest(codigo=codigo), self.assertRaises(ErrorSemantico):
                analizar_semantica(codigo)

    def test_operaciones(self):
        analizar_semantica('x Real; x = -(2 + 3,5) * 4 / 2; t Texto; t = "a" + "b";')
        for expresion in ['"a" - 1', '"a" + 1', '-"a"', '(1 == 1) + 2']:
            with self.subTest(expresion=expresion), self.assertRaises(ErrorSemantico):
                analizar_semantica(f'x Real; x = {expresion};')

    def test_condiciones_y_comparaciones(self):
        for op in ['==', '!=', '<', '>', '<=', '>=']:
            analizar_semantica(f'Si (1 {op} 2,0) FinSi')
        analizar_semantica('b Logico; b = 1 == 1; Si (b) FinSi Si ("a" != "b") FinSi')
        for condicion in ['1', '"hola"', '1 == "a"', '"a" < "b"', '(1 == 1) == 1']:
            with self.subTest(condicion=condicion), self.assertRaises(ErrorSemantico):
                analizar_semantica(f'Si ({condicion}) FinSi')

    def test_inicializacion(self):
        for codigo in ['x Entero; Mensaje.Texto(x);', 'x Entero; x = x + 1;',
                       'b Logico; Si (b) FinSi']:
            with self.subTest(codigo=codigo), self.assertRaises(ErrorSemantico):
                analizar_semantica(codigo)
        analizar_semantica('x Entero; x = 1; x = x + 1;')

    def test_flujo_de_ramas(self):
        inicio = 'x Entero; Si (1 == 1) '
        analizar_semantica(inicio + 'x = 1; Sino x = 2; FinSi Mensaje.Texto(x);')
        analizar_semantica('x Entero; x = 0; Si (1 == 1) x = 1; FinSi Mensaje.Texto(x);')
        for bloque in ['x = 1; FinSi', 'x = 1; Sino Mensaje.Texto(x); FinSi',
                       'Si (1 == 1) x = 1; FinSi Sino x = 2; FinSi']:
            with self.subTest(bloque=bloque), self.assertRaises(ErrorSemantico):
                analizar_semantica(inicio + bloque + ' Mensaje.Texto(x);')
        analizar_semantica(inicio + 'Si (1 == 1) x = 1; Sino x = 2; FinSi Sino x = 3; FinSi Mensaje.Texto(x);')

    def test_alcance(self):
        tabla = analizar_semantica('Si (1 == 1) x Entero; x = 1; Sino x Texto; x = "a"; FinSi')
        self.assertNotIn('x', tabla)
        for codigo in ['Si (1 == 1) x Entero; FinSi x = 1;',
                       'x Entero; Si (1 == 1) x Entero; FinSi']:
            with self.subTest(codigo=codigo), self.assertRaises(ErrorSemantico):
                analizar_semantica(codigo)

    def test_ubicaciones_y_etapas(self):
        casos = [('x Entero;\nx = "a";', 'Línea 2, columna 1'),
                 ('x Entero;\nx = y;', 'Línea 2, columna 5'),
                 ('x Entero;\nx = "a" - 1;', 'Línea 2, columna 9'),
                 ('Si (1) FinSi', 'Línea 1, columna 5')]
        for codigo, mensaje in casos:
            with self.subTest(codigo=codigo), self.assertRaisesRegex(ErrorSemantico, mensaje):
                analizar_semantica(codigo)
        with self.assertRaises(ErrorLexico):
            analizar_semantica('x = @;')
        with self.assertRaises(ErrorSintactico):
            analizar_semantica('x = ;')


if __name__ == '__main__':
    unittest.main()
