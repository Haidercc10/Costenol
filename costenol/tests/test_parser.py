import unittest
from lexer import ErrorLexico
from parser import analizar, ErrorSintactico


class PruebasParser(unittest.TestCase):
    def test_instrucciones_y_tipos(self):
        """Comprueba declaraciones, capturas y mensajes de los cuatro tipos, y programas vacíos."""
        for tipo in ['Texto', 'Entero', 'Real', 'Logico']:
            with self.subTest(tipo=tipo):
                arbol = analizar(f'x {tipo}; x = Captura.{tipo}(); Mensaje.Texto(x);')
                self.assertEqual(len(arbol['instrucciones']), 3)
        self.assertEqual(analizar('// comentario //')['instrucciones'], [])

    def test_precedencia_y_asociatividad(self):
        """Comprueba en el AST prioridad aritmética, paréntesis, signos y agrupación por la izquierda."""
        valor = analizar('x = 2 + 3 * 4;')['instrucciones'][0]['valor']
        self.assertEqual(valor['operador'], '+')
        self.assertEqual(valor['derecha']['operador'], '*')
        valor = analizar('x = (2 + 3) * 4;')['instrucciones'][0]['valor']
        self.assertEqual(valor['izquierda']['operador'], '+')
        valor = analizar('x = 8 - 3 - 1;')['instrucciones'][0]['valor']
        self.assertEqual(valor['izquierda']['operador'], '-')
        valor = analizar('x = -3,5;')['instrucciones'][0]['valor']
        self.assertEqual(valor['nodo'], 'Unaria')

    def test_anidamiento_y_comparaciones(self):
        """Comprueba comparadores, condicionales anidados y la separación de sus ramas."""
        for op in ['==', '!=', '>', '<', '>=', '<=']:
            with self.subTest(op=op):
                arbol = analizar(f'Si (x {op} 1) Si (y) Sino FinSi Sino FinSi')
                nodo = arbol['instrucciones'][0]
                self.assertEqual(nodo['condicion']['operador'], op)
                self.assertEqual(nodo['entonces'][0]['nodo'], 'Condicional')
                self.assertEqual(nodo['sino'], [])

    def test_errores_sintacticos(self):
        """Verifica que instrucciones mal construidas produzcan ErrorSintactico."""
        casos = ['edad Entero', 'edad = ;', 'x = 2 + ;', 'x = (2 + 3;',
                 'Si (x > 1) x = 1;', 'Sino', 'FinSi',
                 'Si () FinSi', 'Si (x) Sino Sino FinSi',
                 'Captura.Entero();', 'x = Captura.Entero(1);',
                 'Mensaje.Texto();', 'Mensaje.Entero(1);',
                 'x = 1 < 2 < 3;', 'si (x) FinSi', 'x = 1; 2;']
        for codigo in casos:
            with self.subTest(codigo=codigo), self.assertRaises(ErrorSintactico):
                analizar(codigo)

    def test_ubicacion_y_error_lexico(self):
        """Verifica ubicaciones de errores sintácticos y propagación de errores léxicos."""
        with self.assertRaisesRegex(ErrorSintactico, 'Línea 2, columna 5'):
            analizar('x Entero;\nx = ;')
        with self.assertRaisesRegex(ErrorSintactico, 'Línea 2, columna 1'):
            analizar('x Entero\n')
        with self.assertRaises(ErrorLexico):
            analizar('x = @;')

    def test_no_adelanta_validacion_semantica(self):
        """Comprueba que el parser acepta estructuras sin adelantar la revisión de tipos y nombres."""
        analizar('sinDeclarar = "texto" + 2;')


if __name__ == '__main__':
    unittest.main()
