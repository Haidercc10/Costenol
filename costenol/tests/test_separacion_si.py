"""Reglas de separación entre Si y su paréntesis de apertura."""
import unittest
from parser import analizar, ErrorSintactico
from semantico import analizar_semantica
from interprete import ejecutar


class PruebasSeparacionSi(unittest.TestCase):
    def test_rechaza_si_pegado_con_ubicacion(self):
        """Señala el paréntesis pegado a Si y sugiere la escritura correcta."""
        with self.assertRaisesRegex(ErrorSintactico, 'Línea 1, columna 3.*un espacio entre Si'):
            analizar('Si(Verdadero) FinSi')

    def test_admite_separacion_y_condicionales_anidados(self):
        """Acepta separadores en blanco y conserva las llamadas sin espacios obligatorios."""
        for separador in (' ', '  ', '\t', '\n'):
            with self.subTest(separador=repr(separador)):
                analizar_semantica(f'Si{separador}(Verdadero) Si (Falso) Sino Mensaje.Texto("Hola"); FinSi FinSi')

    def test_ejecucion_no_produce_efectos_con_si_pegado(self):
        """La validación completa rechaza la sintaxis antes de mostrar mensajes."""
        salida=[]
        with self.assertRaises(ErrorSintactico):
            ejecutar('Mensaje.Texto("Antes"); Si(Verdadero) FinSi', salida=salida.append)
        self.assertEqual(salida, [])
