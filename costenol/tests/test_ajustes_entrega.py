"""Regresión de concatenación lógica, extensiones y cancelación voluntaria."""
import unittest
from unittest.mock import patch
from pathlib import Path
from archivos import ruta_apertura
from interprete import ejecutar, EjecucionCancelada
from recursos import tema_barra_windows


class PruebasAjustesEntrega(unittest.TestCase):
    def test_texto_real_y_logico_ambos_ordenes(self):
        """Concatena reales y lógicos en español, conservando coma decimal y orden de operandos."""
        salida=[]
        ejecutar('b Logico; b=1==1; Mensaje.Texto("Precio: " + 3,5); '
                 'Mensaje.Texto("Activo: " + b); Mensaje.Texto(b + " activo"); '
                 'Mensaje.Texto(3,5 + " pesos"); Mensaje.Texto("No: " + (1==2));', salida=salida.append)
        self.assertEqual(salida,['Precio: 3,5','Activo: Verdadero','Verdadero activo','3,5 pesos','No: Falso'])

    def test_apertura_solo_pqek(self):
        """Rechaza archivos ajenos aunque se escriba la ruta manualmente en el selector."""
        self.assertEqual(ruta_apertura('ejemplo.PQEK'),Path('ejemplo.PQEK'))
        for nombre in ['ejemplo.txt','ejemplo.cost','ejemplo.py','ejemplo','ejemplo.pqek.exe']:
            with self.subTest(nombre=nombre),self.assertRaises(ValueError):
                ruta_apertura(nombre)

    def test_cancelacion_detiene_sin_mensajes_posteriores(self):
        """Cancelar cualquier captura produce una interrupción voluntaria y no ejecuta el resto."""
        for tipo in ['Texto','Entero','Real','Logico']:
            salida=[]
            with self.subTest(tipo=tipo),self.assertRaises(EjecucionCancelada):
                ejecutar(f'x {tipo}; x=Captura.{tipo}(); Mensaje.Texto("No debe salir");',
                         entrada=lambda p:None,salida=salida.append)
            self.assertEqual(salida,[])

    def test_tono_barra_del_sistema(self):
        """Lee SystemUsesLightTheme, sin confundirlo con el tema elegido dentro de Costeñol."""
        import winreg
        for valor, esperado in [(0,'Oscuro'),(1,'Claro')]:
            with patch('winreg.OpenKey'), patch('winreg.QueryValueEx',return_value=(valor,winreg.REG_DWORD)) as consulta:
                self.assertEqual(tema_barra_windows(),esperado)
                self.assertEqual(consulta.call_args.args[1],'SystemUsesLightTheme')


if __name__ == '__main__':
    unittest.main()

