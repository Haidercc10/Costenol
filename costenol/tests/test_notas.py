"""Regresión del programa de tres notas con capturas Real y Entero."""
import unittest
from unittest.mock import patch
import test_interfaz
from interprete import ejecutar
from semantico import analizar_semantica, ErrorSemantico

CODIGO = '''n1 Real;
n2 Real;
n3 Real;

Mensaje.Texto("Digite nota 1");
n1 = Captura.Real();
Mensaje.Texto("Digita nota 2");
n2 = Captura.Entero();
Mensaje.Texto("Digita nota 3");
n3 = Captura.Entero();
'''


class PruebasNotas(unittest.TestCase):
    def test_tipo_de_captura_coincide_con_destino(self):
        """Exige capturas del mismo tipo que su destino, incluidos los paréntesis."""
        for destino in ('Real', 'Entero', 'Texto', 'Logico'):
            for captura in ('Real', 'Entero', 'Texto', 'Logico'):
                with self.subTest(destino=destino, captura=captura):
                    codigo = f'n {destino}; n = (Captura.{captura}());'
                    if destino == captura:
                        analizar_semantica(codigo)
                    else:
                        with self.assertRaisesRegex(ErrorSemantico, f'usa Captura.{destino}'):
                            analizar_semantica(codigo)

    def test_rechazo_antes_de_producir_efectos(self):
        """Una captura incompatible se rechaza antes de mostrar mensajes o pedir datos."""
        entrada = unittest.mock.Mock()
        salida = unittest.mock.Mock()
        with self.assertRaisesRegex(ErrorSemantico, 'Captura.Real'):
            ejecutar(CODIGO, entrada=entrada, salida=salida)
        entrada.assert_not_called()
        salida.assert_not_called()

    def test_valores_enteros_y_notas_corregidas(self):
        """Mantiene la promoción de valores y ejecuta las tres capturas Real correctas."""
        analizar_semantica('n Real; n = 4; m Entero; m = 2; n = m;')
        entradas = iter(['3,5', '4', '5'])
        entorno = ejecutar(CODIGO.replace('Captura.Entero()', 'Captura.Real()'),
                           entrada=lambda prompt: next(entradas), salida=lambda texto: None)
        self.assertEqual([entorno[n]['valor'] for n in ('n1', 'n2', 'n3')], [3.5, 4.0, 5.0])


class PruebasNotasInterfaz(unittest.TestCase):
    setUp = test_interfaz.PruebasInterfaz.setUp
    tearDown = test_interfaz.PruebasInterfaz.tearDown

    def test_analizar_y_ejecutar_notas_sin_diagnosticos(self):
        """Valida el caso en la interfaz y conserva vacíos los avisos de error al terminar."""
        self.app.cargar(CODIGO)
        self.root.update()
        self.app.analizar()
        self.assertIn('Captura.Real()', self.app.diagnostico.get())
        with patch('interfaz.dialogo') as captura_invalida:
            self.app.ejecutar()
        captura_invalida.assert_not_called()
        self.app.cargar(CODIGO.replace('Captura.Entero()', 'Captura.Real()'))
        self.root.update()
        self.app.analizar()
        self.assertEqual(self.app.diagnostico.get(), '')
        with patch('interfaz.dialogo', side_effect=['3,5', '4', '5']) as capturas:
            self.app.ejecutar()
        self.assertEqual(capturas.call_count, 3)
        self.assertEqual([c.kwargs['tipo_captura'] for c in capturas.call_args_list], ['Real', 'Real', 'Real'])
        self.assertIn('Ejecución finalizada.', self.app.salida.get('1.0', 'end'))
        self.assertEqual(self.app.diagnostico.get(), '')
        self.assertFalse(self.app.editor.tag_ranges('error'))
        self.assertFalse(self.app.ocupada)
