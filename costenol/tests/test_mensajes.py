"""Pruebas de identidad costeña y conservación de los datos del diagnóstico."""
import unittest
from mensajes import personalizar
from interprete import ejecutar, ErrorEjecucion
from semantico import analizar_semantica, ErrorSemantico
from parser import analizar, ErrorSintactico
from lexer import tokenizar, ErrorLexico
from capturas import convertir_captura


class PruebasMensajes(unittest.TestCase):
    def test_identidad_por_etapa(self):
        """Comprueba tono contextual y ubicación en las cuatro categorías de error."""
        casos = [(lambda: tokenizar('x=@;'), ErrorLexico, 'Eche'),
                 (lambda: analizar('x Entero'), ErrorSintactico, 'punto y coma'),
                 (lambda: analizar_semantica('x=1;'), ErrorSemantico, 'bro'),
                 (lambda: ejecutar('Mensaje.Texto(1/0);'), ErrorEjecucion, 'divisor')]
        for accion, categoria, frase in casos:
            with self.subTest(categoria=categoria):
                with self.assertRaises(categoria) as captura:
                    accion()
                self.assertIn('Línea 1, columna', str(captura.exception))
                self.assertIn('Costeñol:', str(captura.exception))
                self.assertIn(frase, str(captura.exception))

    def test_no_duplica_y_es_determinista(self):
        """Garantiza que propagar un error de captura no repite la personalización."""
        mensaje = personalizar('entrada inválida para Entero')
        self.assertEqual(personalizar(mensaje), mensaje)
        self.assertEqual(personalizar('entrada inválida para Entero'), mensaje)
        with self.assertRaises(ErrorEjecucion) as captura:
            ejecutar('n Entero; n=Captura.Entero();', entrada=lambda prompt: 'hola')
        self.assertEqual(str(captura.exception).count('Costeñol:'), 1)
        with self.assertRaises(ValueError) as captura:
            convertir_captura('Texto', '123')
        self.assertIn('Costeñol:', str(captura.exception))


if __name__ == '__main__':
    unittest.main()
