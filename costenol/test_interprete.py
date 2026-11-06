import unittest
from pathlib import Path
from interprete import ejecutar, ErrorEjecucion
from lexer import ErrorLexico
from parser import ErrorSintactico
from semantico import ErrorSemantico


class PruebasEjecucion(unittest.TestCase):
    def correr(self, codigo, entradas=()):
        """Ejecuta código con entradas simuladas y acumula mensajes; devuelve salida y entorno final."""
        datos = iter(entradas)
        salida = []
        entorno = ejecutar(codigo, entrada=lambda prompt: next(datos), salida=salida.append)
        return salida, entorno

    def test_operaciones_y_conversion(self):
        """Comprueba resultados aritméticos, prioridad y conversión de Entero a Real."""
        salida, entorno = self.correr('x Real; x = 2; Mensaje.Texto(x); Mensaje.Texto(2+3*4); Mensaje.Texto((2+3)*4); Mensaje.Texto(8-3-1); Mensaje.Texto(-4/2);')
        self.assertEqual(salida, ['2,0', '14', '20', '4', '-2,0'])
        self.assertIsInstance(entorno['x']['valor'], float)

    def test_concatenacion_numeros_y_texto(self):
        """Comprueba concatenación en ambos órdenes, coma decimal, agrupación y capturas."""
        codigo = ('res Entero; res=5+3; t Texto; t="Resultado: " + res; '
                  'Mensaje.Texto(t); Mensaje.Texto(2 + " entradas"); '
                  'Mensaje.Texto("Precio: " + 3,5); Mensaje.Texto(-2 + " grados"); '
                  'Mensaje.Texto("Suma: " + (2+3)); Mensaje.Texto("Cadena: " + 2 + 3); '
                  'Mensaje.Texto(2+3);')
        salida, entorno = self.correr(codigo)
        self.assertEqual(salida, ['Resultado: 8', '2 entradas', 'Precio: 3,5',
                                 '-2 grados', 'Suma: 5', 'Cadena: 23', '5'])
        self.assertEqual(entorno['t']['tipo'], 'Texto')
        salida, _ = self.correr('Mensaje.Texto("Dato: " + Captura.Entero());', ['9'])
        self.assertEqual(salida, ['Dato: 9'])

    def test_capturas(self):
        """Comprueba lectura y presentación de Texto, Entero, Real y Logico."""
        salida, _ = self.correr('t Texto; n Entero; r Real; b Logico; t=Captura.Texto(); n=Captura.Entero(); r=Captura.Real(); b=Captura.Logico(); Mensaje.Texto(t); Mensaje.Texto(n); Mensaje.Texto(r); Mensaje.Texto(b);', [' Ana ', '-2', '3,5', 'vErDaDeRo'])
        self.assertEqual(salida, [' Ana ', '-2', '3,5', 'Verdadero'])
        salida, _ = self.correr('b Logico; b=Captura.Logico(); Mensaje.Texto(b);', ['Falso'])
        self.assertEqual(salida, ['Falso'])

    def test_entradas_invalidas(self):
        """Verifica rechazo de formatos de captura incorrectos, entrada agotada y cancelación."""
        for tipo, valor in [('Entero', '2,5'), ('Entero', 'hola'), ('Real', '3.5'),
                            ('Real', 'nan'), ('Real', 'inf'), ('Logico', '1'), ('Logico', 'si')]:
            with self.subTest(tipo=tipo, valor=valor), self.assertRaisesRegex(ErrorEjecucion, 'entrada inválida'):
                self.correr(f'x {tipo}; x=Captura.{tipo}();', [valor])
        with self.assertRaisesRegex(ErrorEjecucion, 'no hay datos'):
            self.correr('x Entero; x=Captura.Entero();')
        with self.assertRaisesRegex(ErrorEjecucion, 'cancelada'):
            self.correr('x Texto; x=Captura.Texto();', [None])

    def test_ramas_y_alcance(self):
        """Comprueba que solo se ejecuta la rama elegida y que las variables locales no escapan."""
        codigo = 'x Entero; x=0; Si (Captura.Entero()>0) local Entero; local=3; x=local; Si (x==3) x=x+1; FinSi Sino x=9; FinSi Mensaje.Texto(x);'
        for entrada, esperado in [('1', '4'), ('-1', '9')]:
            salida, entorno = self.correr(codigo, [entrada])
            self.assertEqual(salida, [esperado])
            self.assertNotIn('local', entorno)
        salida, _ = self.correr('Si (1==2) Mensaje.Texto(1/0); Mensaje.Texto(Captura.Entero()); FinSi Mensaje.Texto("ok");')
        self.assertEqual(salida, ['ok'])

    def test_comparaciones(self):
        """Comprueba los valores lógicos calculados por los seis comparadores."""
        for op in ['==', '!=', '>', '<', '>=', '<=']:
            with self.subTest(op=op):
                salida, _ = self.correr(f'Mensaje.Texto(2 {op} 3);')
                esperado = op in {'!=', '<', '<='}
                self.assertEqual(salida, ['Verdadero' if esperado else 'Falso'])

    def test_cadenas_y_escapes(self):
        """Verifica concatenación de cadenas, escapes válidos y rechazo de escapes desconocidos."""
        salida, _ = self.correr(r'Mensaje.Texto("A" + "ñ\n\t\"\\");')
        self.assertEqual(salida, ['Añ\n\t"\\'])
        with self.assertRaisesRegex(ErrorEjecucion, 'escape no admitido'):
            self.correr(r'Mensaje.Texto("\q");')

    def test_errores_numericos(self):
        """Comprueba división entre cero, su ubicación y resultados numéricos fuera de rango."""
        with self.assertRaisesRegex(ErrorEjecucion, 'Línea 2, columna 14: división entre cero'):
            self.correr('x Real;\nx = 3; x = 1 / (x-3);')
        with self.assertRaisesRegex(ErrorEjecucion, 'fuera del rango'):
            self.correr('x Real; x=Captura.Real();', ['9'*400])
        with self.assertRaisesRegex(ErrorEjecucion, 'fuera del rango'):
            self.correr('x Real; x=Captura.Real(); Mensaje.Texto(x*x);', ['9'*200])

    def test_valida_antes_de_efectos(self):
        """Verifica que un error estático impide cualquier captura o salida del programa."""
        for codigo, error in [('Mensaje.Texto("hola"); x=1;', ErrorSemantico),
                              ('Mensaje.Texto("hola"); x=;', ErrorSintactico),
                              ('Mensaje.Texto("hola"); @', ErrorLexico),
                              ('x Entero; x=Captura.Entero(); Si (1==2) y=1; FinSi', ErrorSemantico)]:
            with self.subTest(codigo=codigo):
                def no_llamar(*args):
                    """Hace fallar la prueba si se intenta producir un efecto antes de completar la validación."""
                    self.fail('No debe capturar ni mostrar antes de validar todo el programa')
                with self.assertRaises(error):
                    ejecutar(codigo, no_llamar, no_llamar)

    def test_ejemplo_completo_y_reutilizacion(self):
        """Ejecuta el ejemplo .pqek con distintas entradas y comprueba resultados y ramas."""
        codigo = (Path(__file__).parent / 'ejemplos' / 'ejemplo_ejecucion.pqek').read_text(encoding='utf-8-sig')
        salida, entorno = self.correr(codigo, ['Ana', '20', '12,5', 'Verdadero'])
        self.assertIn('Mayor de edad', salida)
        self.assertIn('Asistencia confirmada', salida)
        self.assertEqual(salida[-1], '25,0')
        self.assertEqual(entorno['total']['valor'], 25.0)
        salida, _ = self.correr(codigo, ['Luis', '15', '2', 'Falso'])
        self.assertIn('Menor de edad', salida)


if __name__ == '__main__':
    unittest.main()


