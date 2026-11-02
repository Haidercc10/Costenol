import unittest
from pathlib import Path
from interprete import ejecutar, ErrorEjecucion
from lexer import ErrorLexico
from parser import ErrorSintactico
from semantico import ErrorSemantico


class PruebasEjecucion(unittest.TestCase):
    def correr(self, codigo, entradas=()):
        datos = iter(entradas)
        salida = []
        entorno = ejecutar(codigo, entrada=lambda prompt: next(datos), salida=salida.append)
        return salida, entorno

    def test_operaciones_y_conversion(self):
        salida, entorno = self.correr('x Real; x = 2; Mensaje.Texto(x); Mensaje.Texto(2+3*4); Mensaje.Texto((2+3)*4); Mensaje.Texto(8-3-1); Mensaje.Texto(-4/2);')
        self.assertEqual(salida, ['2,0', '14', '20', '4', '-2,0'])
        self.assertIsInstance(entorno['x']['valor'], float)

    def test_capturas(self):
        salida, _ = self.correr('t Texto; n Entero; r Real; b Logico; t=Captura.Texto(); n=Captura.Entero(); r=Captura.Real(); b=Captura.Logico(); Mensaje.Texto(t); Mensaje.Texto(n); Mensaje.Texto(r); Mensaje.Texto(b);', [' Ana ', '-2', '3,5', 'vErDaDeRo'])
        self.assertEqual(salida, [' Ana ', '-2', '3,5', 'Verdadero'])
        salida, _ = self.correr('b Logico; b=Captura.Logico(); Mensaje.Texto(b);', ['Falso'])
        self.assertEqual(salida, ['Falso'])

    def test_entradas_invalidas(self):
        for tipo, valor in [('Entero', '2,5'), ('Entero', 'hola'), ('Real', '3.5'),
                            ('Real', 'nan'), ('Real', 'inf'), ('Logico', '1'), ('Logico', 'si')]:
            with self.subTest(tipo=tipo, valor=valor), self.assertRaisesRegex(ErrorEjecucion, 'entrada inválida'):
                self.correr(f'x {tipo}; x=Captura.{tipo}();', [valor])
        with self.assertRaisesRegex(ErrorEjecucion, 'no hay datos'):
            self.correr('x Entero; x=Captura.Entero();')
        with self.assertRaisesRegex(ErrorEjecucion, 'cancelada'):
            self.correr('x Texto; x=Captura.Texto();', [None])

    def test_ramas_y_alcance(self):
        codigo = 'x Entero; x=0; Si (Captura.Entero()>0) local Entero; local=3; x=local; Si (x==3) x=x+1; FinSi Sino x=9; FinSi Mensaje.Texto(x);'
        for entrada, esperado in [('1', '4'), ('-1', '9')]:
            salida, entorno = self.correr(codigo, [entrada])
            self.assertEqual(salida, [esperado])
            self.assertNotIn('local', entorno)
        salida, _ = self.correr('Si (1==2) Mensaje.Texto(1/0); Mensaje.Texto(Captura.Entero()); FinSi Mensaje.Texto("ok");')
        self.assertEqual(salida, ['ok'])

    def test_comparaciones(self):
        for op in ['==', '!=', '>', '<', '>=', '<=']:
            with self.subTest(op=op):
                salida, _ = self.correr(f'Mensaje.Texto(2 {op} 3);')
                esperado = op in {'!=', '<', '<='}
                self.assertEqual(salida, ['Verdadero' if esperado else 'Falso'])

    def test_cadenas_y_escapes(self):
        salida, _ = self.correr(r'Mensaje.Texto("A" + "ñ\n\t\"\\");')
        self.assertEqual(salida, ['Añ\n\t"\\'])
        with self.assertRaisesRegex(ErrorEjecucion, 'escape no admitido'):
            self.correr(r'Mensaje.Texto("\q");')

    def test_errores_numericos(self):
        with self.assertRaisesRegex(ErrorEjecucion, 'Línea 2, columna 14: división entre cero'):
            self.correr('x Real;\nx = 3; x = 1 / (x-3);')
        with self.assertRaisesRegex(ErrorEjecucion, 'fuera del rango'):
            self.correr('x Real; x=Captura.Real();', ['9'*400])
        with self.assertRaisesRegex(ErrorEjecucion, 'fuera del rango'):
            self.correr('x Real; x=Captura.Real(); Mensaje.Texto(x*x);', ['9'*200])

    def test_valida_antes_de_efectos(self):
        for codigo, error in [('Mensaje.Texto("hola"); x=1;', ErrorSemantico),
                              ('Mensaje.Texto("hola"); x=;', ErrorSintactico),
                              ('Mensaje.Texto("hola"); @', ErrorLexico),
                              ('x Entero; x=Captura.Entero(); Si (1==2) y=1; FinSi', ErrorSemantico)]:
            with self.subTest(codigo=codigo):
                def no_llamar(*args):
                    self.fail('No debe capturar ni mostrar antes de validar todo el programa')
                with self.assertRaises(error):
                    ejecutar(codigo, no_llamar, no_llamar)

    def test_ejemplo_completo_y_reutilizacion(self):
        codigo = Path(__file__).with_name('ejemplo_ejecucion.cost').read_text(encoding='utf-8-sig')
        salida, entorno = self.correr(codigo, ['Ana', '20', '12,5', 'Verdadero'])
        self.assertIn('Mayor de edad', salida)
        self.assertIn('Asistencia confirmada', salida)
        self.assertEqual(salida[-1], '25,0')
        self.assertEqual(entorno['total']['valor'], 25.0)
        salida, _ = self.correr(codigo, ['Luis', '15', '2', 'Falso'])
        self.assertIn('Menor de edad', salida)


if __name__ == '__main__':
    unittest.main()

