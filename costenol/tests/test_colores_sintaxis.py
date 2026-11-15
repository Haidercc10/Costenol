"""Pruebas del coloreado de cadenas, funciones, signos y paréntesis."""
import unittest
from resaltado import rangos_sintaxis, PALETAS_SINTAXIS


class PruebasColoresSintaxis(unittest.TestCase):
    def segmentos(self, codigo):
        """Devuelve categoría y lexema de cada rango para comprobar el escáner sin Tkinter."""
        lineas = codigo.split('\n')
        resultado = []
        for categoria, inicio, fin in rangos_sintaxis(codigo):
            linea, columna = map(int, inicio.split('.'))
            columna_fin = int(fin.split('.')[1])
            resultado.append((categoria, lineas[linea-1][columna:columna_fin]))
        return resultado

    def test_tipos_y_llamadas(self):
        """Distingue una declaración azul de una llamada amarilla, sin convertir Si en función."""
        segmentos = self.segmentos('n Entero; n = Captura.Entero(); Mensaje.Texto("Hola"); Si (n>0) FinSi')
        self.assertIn(('reservada', 'Entero'), segmentos)
        self.assertIn(('funcion', 'Entero'), segmentos)
        self.assertIn(('funcion', 'Texto'), segmentos)
        self.assertIn(('reservada', 'Si'), segmentos)
        self.assertNotIn(('funcion', 'Si'), segmentos)
        self.assertIn(('cadena', '"Hola"'), segmentos)

    def test_cadenas_comentarios_y_escapes(self):
        """Todo el contenido entre comillas o dentro de comentarios conserva una sola categoría."""
        for codigo in ['"Entero() + (Si)"', r'"Texto \" Entero()"', '"Texto sin cerrar']:
            self.assertEqual(len(self.segmentos(codigo)), 1)
            self.assertEqual(self.segmentos(codigo)[0][0], 'cadena')
        self.assertEqual(self.segmentos('// Entero() + "Si" //'), [('comentario', '// Entero() + "Si" //')])

    def test_parentesis_emparejados_y_signos(self):
        """Colorea cada pareja según la profundidad y reconoce comparaciones de dos caracteres."""
        segmentos = self.segmentos('((2 + 3) * 4) >= 1;')
        parentesis = [(c,t) for c,t in segmentos if c.startswith('parentesis')]
        self.assertEqual(parentesis, [('parentesis_0','('),('parentesis_1','('),
                                     ('parentesis_1',')'),('parentesis_0',')')])
        self.assertIn(('operador', '>='), segmentos)
        self.assertIn(('numero', '4'), segmentos)
        self.assertIn(('simbolo', ';'), segmentos)

    def test_temas_y_codigo_incompleto(self):
        """Ambos temas ofrecen las mismas categorías y el escáner tolera cierres ausentes."""
        self.assertEqual(set(PALETAS_SINTAXIS['Claro']), set(PALETAS_SINTAXIS['Oscuro']))
        self.assertNotEqual(PALETAS_SINTAXIS['Claro']['funcion'], PALETAS_SINTAXIS['Oscuro']['funcion'])
        for codigo in ['Si (', ') + "', 'Captura.Entero(', '// pendiente', 'x=3,']:
            self.segmentos(codigo)


if __name__ == '__main__':
    unittest.main()
