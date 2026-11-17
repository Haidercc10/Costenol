"""Pruebas integrales de los literales Verdadero y Falso."""
import unittest
from lexer import tokenizar
from parser import analizar
from semantico import analizar_semantica, ErrorSemantico
from interprete import ejecutar
from resaltado import rangos_sintaxis


class PruebasLiteralesLogicos(unittest.TestCase):
    def test_tokens_ast_tipo_y_valor(self):
        """Comprueba cada etapa desde la palabra reservada hasta el valor booleano real."""
        self.assertEqual([t.tipo for t in tokenizar('Verdadero Falso')], ['VERDADERO','FALSO'])
        for texto, tipo, esperado in [('Verdadero','VERDADERO',True),('Falso','FALSO',False)]:
            codigo=f'b Logico; b={texto};'
            nodo=analizar(codigo)['instrucciones'][1]['valor']
            self.assertEqual(nodo['tipo'],tipo)
            self.assertEqual(analizar_semantica(codigo)['b']['tipo'],'Logico')
            self.assertIs(ejecutar(codigo)['b']['valor'],esperado)

    def test_condiciones_comparaciones_y_concatenacion(self):
        """Usa literales directamente en condiciones, comparación y concatenación de textos."""
        salida=[]
        ejecutar('Si (Verdadero) Mensaje.Texto("Si"); Sino Mensaje.Texto("No"); FinSi '
                 'Si (Falso) Mensaje.Texto("No"); Sino Mensaje.Texto("Sino"); FinSi '
                 'Mensaje.Texto("Activo: " + Verdadero); Mensaje.Texto(Falso + " inactivo"); '
                 'Mensaje.Texto(Verdadero != Falso);',salida=salida.append)
        self.assertEqual(salida,['Si','Sino','Activo: Verdadero','Falso inactivo','Verdadero'])

    def test_no_se_convierten_a_numeros(self):
        """Rechaza asignaciones y operaciones que intenten tratar Logico como Entero o Real."""
        for codigo in ['x Entero; x=Verdadero;', 'x Real; x=Falso;',
                       'Mensaje.Texto(Verdadero+1);','Mensaje.Texto(-Falso);',
                       'Mensaje.Texto(Verdadero==1);']:
            with self.subTest(codigo=codigo),self.assertRaises(ErrorSemantico):
                analizar_semantica(codigo)

    def test_escritura_y_resaltado(self):
        """Distingue mayúsculas y no colorea las palabras dentro de una cadena como literales."""
        for palabra in ['verdadero','VERDADERO','falso','FALSO']:
            with self.subTest(palabra=palabra),self.assertRaises(ErrorSemantico):
                analizar_semantica(f'b Logico; b={palabra};')
        segmentos=rangos_sintaxis('Verdadero Falso "Verdadero"')
        self.assertEqual([s[0] for s in segmentos],['reservada','reservada','cadena'])

    def test_saludo_original_del_usuario(self):
        """Ejecuta el saludo con asignación directa de Verdadero y una captura de texto válida."""
        salida=[]
        ejecutar('nombre Texto; logic Logico; logic=Verdadero; '
                 'Mensaje.Texto("¿Como te llamas? " + logic); '
                 'nombre=Captura.Texto(); Mensaje.Texto("Hola, " + nombre);',
                 entrada=lambda p:'Ana',salida=salida.append)
        self.assertEqual(salida,['¿Como te llamas? Verdadero','Hola, Ana'])


if __name__ == '__main__':
    unittest.main()
