"""Regresión de salida y concatenación de enteros que superan el límite decimal de Python."""
import sys
import unittest
from pathlib import Path
import subprocess
from interprete import ejecutar, ErrorEjecucion


@unittest.skipUnless(hasattr(sys, 'set_int_max_str_digits'), 'Python no expone el límite decimal')
class PruebasEnterosExtremos(unittest.TestCase):
    def setUp(self):
        """Fija el límite solo durante cada prueba para reproducir el fallo de manera determinista."""
        self.limite_anterior = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(4300)

    def tearDown(self):
        """Restaura la configuración de Python; el intérprete de producción nunca la modifica."""
        sys.set_int_max_str_digits(self.limite_anterior)

    def comprobar_error(self, instruccion, columna):
        """Ejecuta el cuadrado extremo y comprueba categoría, ubicación, identidad y ausencia de salida parcial."""
        salida = []
        codigo = 'num Entero;\nnum=Captura.Entero();\nres Entero;\nres=num*num;\n' + instruccion
        with self.assertRaises(ErrorEjecucion) as captura:
            ejecutar(codigo, entrada=lambda p: '9'*3000, salida=salida.append)
        mensaje = str(captura.exception)
        self.assertIn(f'Línea 5, columna {columna}:', mensaje)
        self.assertIn('entero demasiado grande para convertir a texto', mensaje)
        self.assertIn('Costeñol:', mensaje)
        self.assertEqual(salida, [])
        self.assertEqual(sys.get_int_max_str_digits(), 4300)

    def test_mostrar_resultado_extremo(self):
        """Ubica el fallo en Mensaje.Texto en lugar de propagar ValueError de Python."""
        self.comprobar_error('Mensaje.Texto(res);', 1)

    def test_concatenacion_ambos_ordenes(self):
        """Controla el mismo problema con el número a la izquierda o derecha del texto."""
        self.comprobar_error('Mensaje.Texto("Total: " + res);', 25)
        self.comprobar_error('Mensaje.Texto(res + " total");', 19)

    def test_negativo_y_asignacion_a_texto(self):
        """Controla enteros negativos y concatenaciones asignadas, aunque no haya Mensaje.Texto."""
        self.comprobar_error('Mensaje.Texto(-res);', 1)
        self.comprobar_error('t Texto; t = "Total: " + res;', 24)

    def test_grande_representable_sigue_funcionando(self):
        """No rechaza cálculos ni salidas grandes que sí caben en el límite configurado."""
        salida = []
        entorno = ejecutar('n Entero; n=Captura.Entero(); Mensaje.Texto(n*n);',
                           entrada=lambda p: '9'*2000, salida=salida.append)
        self.assertEqual(len(salida[0]), 4000)
        self.assertEqual(entorno['n']['valor'], int('9'*2000))

    def test_consola_sin_traceback(self):
        """Comprueba que el caso reproducible termine con error controlado y sin traceback en consola."""
        base = Path(__file__).resolve().parent.parent
        prueba = base / 'ejemplos' / 'pruebas_errores' / '10_entero_extremo.pqek'
        resultado = subprocess.run([sys.executable, str(base/'interprete.py'), str(prueba)],
                                  input='9'*3000+'\n', text=True, capture_output=True,
                                  encoding='utf-8', errors='replace', timeout=15,
                                  env={**__import__('os').environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONINTMAXSTRDIGITS': '4300'})
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn('ErrorEjecucion:', resultado.stderr)
        self.assertIn('Costeñol:', resultado.stderr)
        self.assertNotIn('Traceback', resultado.stderr)


if __name__ == '__main__':
    unittest.main()

