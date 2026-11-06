"""Intérprete de Costeñol: valida el programa completo antes de ejecutarlo."""
import argparse
import math
import operator
import re
from pathlib import Path
from lexer import ErrorLexico
from parser import analizar, ErrorSintactico
from semantico import AnalizadorSemantico, ErrorSemantico


class ErrorEjecucion(ValueError):
    pass


OPERACIONES = {'+': operator.add, '-': operator.sub, '*': operator.mul,
               '/': operator.truediv, '==': operator.eq, '!=': operator.ne,
               '>': operator.gt, '<': operator.lt, '>=': operator.ge, '<=': operator.le}


def mostrar(valor):
    """Convierte un valor a su representación de salida en Costeñol.
    Usa coma para reales y Verdadero/Falso para lógicos; devuelve una cadena.
    """
    if isinstance(valor, bool):
        return 'Verdadero' if valor else 'Falso'
    if isinstance(valor, float):
        return str(valor).replace('.', ',')
    return str(valor)


class Interprete:
    def __init__(self, entrada=input, salida=print):
        # Funciones inyectables para pruebas y para una futura interfaz.
        """Recibe funciones de entrada y salida; por defecto usa input y print.
        Permite conectar el mismo intérprete a la consola, las pruebas o la interfaz.
        """
        self.entrada = entrada
        self.salida = salida

    def error(self, nodo, mensaje):
        """Lanza ErrorEjecucion con línea, columna y descripción de la causa."""
        raise ErrorEjecucion(f'Línea {nodo["linea"]}, columna {nodo["columna"]}: {mensaje}')

    def numero_finito(self, nodo, valor):
        """Devuelve el valor si es válido; rechaza reales infinitos o NaN con ErrorEjecucion."""
        if isinstance(valor, float) and not math.isfinite(valor):
            self.error(nodo, 'resultado numérico fuera del rango permitido')
        return valor

    def cadena(self, nodo):
        """Decodifica el lexema de una cadena y devuelve su texto sin comillas.
        Interpreta los escapes admitidos y rechaza escapes desconocidos.
        """
        texto = nodo['lexema'][1:-1]
        escapes = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\'}
        resultado = []
        pos = 0
        while pos < len(texto):
            if texto[pos] == '\\':
                pos += 1
                if texto[pos] not in escapes:
                    self.error(nodo, f'escape no admitido: \\{texto[pos]}')
                resultado.append(escapes[texto[pos]])
            else:
                resultado.append(texto[pos])
            pos += 1
        return ''.join(resultado)

    def capturar(self, nodo):
        """Solicita un dato del tipo del nodo y devuelve su valor convertido.
        Valida formato y rango; una entrada inválida, agotada o cancelada detiene la ejecución.
        """
        tipo = nodo['tipo']
        try:
            texto = self.entrada(f'Captura.{tipo} > ')
        except (EOFError, StopIteration):
            self.error(nodo, f'no hay datos disponibles para Captura.{tipo}()')
        except KeyboardInterrupt:
            self.error(nodo, 'captura cancelada')
        if texto is None:
            self.error(nodo, 'captura cancelada')
        if tipo == 'Texto':
            return texto
        limpio = texto.strip()
        try:
            if tipo == 'Entero' and re.fullmatch(r'[+-]?[0-9]+', limpio):
                return int(limpio)
            if tipo == 'Real' and re.fullmatch(r'[+-]?[0-9]+(?:,[0-9]+)?', limpio):
                return self.numero_finito(nodo, float(limpio.replace(',', '.')))
            if tipo == 'Logico' and limpio.lower() in {'verdadero', 'falso'}:
                return limpio.lower() == 'verdadero'
        except (ValueError, OverflowError) as error:
            if isinstance(error, ErrorEjecucion):
                raise
            self.error(nodo, f'entrada fuera de rango para {tipo}')
        formato = {'Entero': 'un entero, por ejemplo -12',
                   'Real': 'un real con coma decimal, por ejemplo 3,5',
                   'Logico': 'Verdadero o Falso'}[tipo]
        self.error(nodo, f'entrada inválida para {tipo}: {texto!r}; se esperaba {formato}')

    def evaluar(self, nodo, entorno):
        """Evalúa recursivamente una expresión del AST usando el entorno recibido.
        Devuelve su valor, concatena texto con números y controla errores numéricos.
        """
        clase = nodo['nodo']
        if clase == 'Literal':
            if nodo['tipo'] == 'CADENA':
                return self.cadena(nodo)
            try:
                valor = (int(nodo['lexema']) if nodo['tipo'] == 'NUM_ENTERO'
                         else float(nodo['lexema'].replace(',', '.')))
            except (ValueError, OverflowError):
                self.error(nodo, 'literal numérico fuera del rango permitido')
            return self.numero_finito(nodo, valor)
        if clase == 'Variable':
            return entorno[nodo['nombre']]['valor']
        if clase == 'Captura':
            return self.capturar(nodo)
        if clase == 'Unaria':
            valor = self.evaluar(nodo['valor'], entorno)
            return -valor if nodo['operador'] == '-' else +valor
        if clase == 'Binaria':
            # Evaluación de izquierda a derecha, incluso si hay capturas.
            izquierda = self.evaluar(nodo['izquierda'], entorno)
            derecha = self.evaluar(nodo['derecha'], entorno)
            if nodo['operador'] == '+' and (isinstance(izquierda, str) or isinstance(derecha, str)):
                return mostrar(izquierda) + mostrar(derecha)
            try:
                valor = OPERACIONES[nodo['operador']](izquierda, derecha)
            except ZeroDivisionError:
                self.error(nodo, 'división entre cero')
            except OverflowError:
                self.error(nodo, 'operación numérica fuera del rango permitido')
            return self.numero_finito(nodo, valor)
        raise ValueError(f'Expresión desconocida: {clase}')

    def bloque(self, instrucciones, entorno):
        """Ejecuta instrucciones en orden y modifica los valores del entorno.
        Selecciona una sola rama de cada Si y conserva locales sus declaraciones nuevas.
        """
        for nodo in instrucciones:
            clase = nodo['nodo']
            if clase == 'Declaracion':
                entorno[nodo['nombre']] = {'tipo': nodo['tipo'], 'valor': None}
            elif clase == 'Asignacion':
                destino = entorno[nodo['nombre']]
                valor = self.evaluar(nodo['valor'], entorno)
                if destino['tipo'] == 'Real':
                    try:
                        valor = self.numero_finito(nodo, float(valor))
                    except OverflowError:
                        self.error(nodo, 'conversión a Real fuera del rango permitido')
                destino['valor'] = valor
            elif clase == 'Mensaje':
                self.salida(mostrar(self.evaluar(nodo['valor'], entorno)))
            elif clase == 'Condicional':
                rama = nodo['entonces'] if self.evaluar(nodo['condicion'], entorno) else nodo['sino'] or []
                # Se comparten las celdas externas; los nombres nuevos quedan locales.
                self.bloque(rama, dict(entorno))
            else:
                raise ValueError(f'Instrucción desconocida: {clase}')

    def ejecutar(self, codigo):
        """Valida todo el código con lexer, parser y semántica antes de producir efectos.
        Ejecuta el AST con un entorno nuevo y devuelve las variables globales y sus valores.
        """
        arbol = analizar(codigo)
        AnalizadorSemantico().analizar(arbol)
        entorno = {}
        self.bloque(arbol['instrucciones'], entorno)
        return entorno


def ejecutar(codigo, entrada=input, salida=print):
    """Recibe código y funciones opcionales de entrada/salida; crea un intérprete y devuelve el entorno final.
    Propaga los errores de validación o ejecución para que consola o interfaz los presenten.
    """
    return Interprete(entrada, salida).ejecutar(codigo)


def main():
    """Lee el archivo indicado por consola y lo ejecuta con entrada y salida de terminal.
    Presenta el primer error conocido con su categoría y termina con código distinto de cero.
    """
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('archivo', type=Path)
    args = cli.parse_args()
    try:
        ejecutar(args.archivo.read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError, ErrorLexico, ErrorSintactico, ErrorSemantico, ErrorEjecucion) as error:
        cli.exit(1, f'{type(error).__name__}: {error}\n')


if __name__ == '__main__':
    main()
