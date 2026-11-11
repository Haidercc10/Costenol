"""Parser descendente recursivo para Costeñol. No ejecuta el programa."""
from mensajes import personalizar
import argparse
import json
from pathlib import Path
from lexer import Token, ErrorLexico, tokenizar


def ubicacion(token):
    """Recibe un Token y devuelve su línea y columna para incorporarlas al AST."""
    return {"linea": token.linea, "columna": token.columna}


class ErrorSintactico(ValueError):
    pass


TIPOS = {'TEXTO', 'ENTERO', 'REAL', 'LOGICO'}
COMPARACIONES = {'IGUAL', 'DIFERENTE', 'MAYOR', 'MENOR', 'MAYOR_IGUAL', 'MENOR_IGUAL'}


class Parser:
    def __init__(self, tokens: list[Token], fin_linea=1, fin_columna=1):
        """Recibe tokens y la ubicación final del texto; añade EOF e inicia el cursor pos en cero."""
        self.tokens = list(tokens) + [Token('EOF', '', fin_linea, fin_columna)]
        self.pos = 0

    @property
    def actual(self):
        """Devuelve el token situado en pos sin consumirlo; es una propiedad de consulta."""
        return self.tokens[self.pos]

    def error(self, esperado):
        """Construye un ErrorSintactico con lo esperado, el token encontrado y su ubicación."""
        t = self.actual
        encontrado = 'fin del archivo' if t.tipo == 'EOF' else repr(t.valor)
        return ErrorSintactico(personalizar(
            f'Línea {t.linea}, columna {t.columna}: se esperaba {esperado}; '
            f'se encontró {encontrado}.'
        ))

    def aceptar(self, *tipos):
        """Consume y devuelve el token actual si coincide con alguno de los tipos recibidos.
        Si no coincide, devuelve None sin mover el cursor.
        """
        if self.actual.tipo in tipos:
            token = self.actual
            self.pos += 1
            return token
        return None

    def exigir(self, tipo, descripcion):
        """Consume el tipo requerido y devuelve su token.
        Si falta, lanza ErrorSintactico usando la descripción recibida.
        """
        token = self.aceptar(tipo)
        if token is None:
            raise self.error(descripcion)
        return token

    def analizar(self):
        """Reconoce todas las instrucciones hasta EOF y devuelve el nodo Programa del AST."""
        instrucciones = self.bloque(set())
        self.exigir('EOF', 'fin del archivo')
        return {'nodo': 'Programa', 'instrucciones': instrucciones}

    def bloque(self, cierres):
        """Recibe los tipos que cierran un bloque y devuelve su lista de instrucciones.
        Se detiene también ante EOF; no consume el cierre.
        """
        instrucciones = []
        while self.actual.tipo not in cierres | {'EOF'}:
            instrucciones.append(self.instruccion())
        return instrucciones

    def instruccion(self):
        """Reconoce una declaración, asignación, mensaje o condicional y devuelve su nodo.
        Consume los tokens correspondientes y exige los delimitadores de cada instrucción.
        """
        if self.actual.tipo == 'IDENTIFICADOR':
            nombre = self.exigir('IDENTIFICADOR', 'un identificador')
            if self.actual.tipo in TIPOS:
                tipo = self.actual
                self.pos += 1
                self.exigir('PUNTO_Y_COMA', "';' después de la declaración")
                return {'nodo': 'Declaracion', 'nombre': nombre.valor, 'tipo': tipo.valor, **ubicacion(nombre)}
            self.exigir('ASIGNACION', "un tipo de dato o '=' después del identificador")
            valor = self.expresion()
            self.exigir('PUNTO_Y_COMA', "';' después de la asignación")
            return {'nodo': 'Asignacion', 'nombre': nombre.valor, 'valor': valor, **ubicacion(nombre)}
        if self.aceptar('MENSAJE'):
            self.exigir('PUNTO', "'.' después de Mensaje")
            self.exigir('TEXTO', 'Texto después de Mensaje.')
            self.exigir('PAREN_ABRE', "'('")
            valor = self.expresion()
            self.exigir('PAREN_CIERRA', "')' después del mensaje")
            self.exigir('PUNTO_Y_COMA', "';' después del mensaje")
            return {'nodo': 'Mensaje', 'valor': valor}
        if self.aceptar('SI'):
            self.exigir('PAREN_ABRE', "'(' después de Si")
            condicion = self.expresion()
            self.exigir('PAREN_CIERRA', "')' después de la condición")
            entonces = self.bloque({'SINO', 'FINSI'})
            sino = self.bloque({'FINSI'}) if self.aceptar('SINO') else None
            self.exigir('FINSI', 'FinSi para cerrar el condicional')
            return {'nodo': 'Condicional', 'condicion': condicion, 'entonces': entonces, 'sino': sino}
        raise self.error('una declaración, asignación, Mensaje.Texto(...) o Si (...)')

    def expresion(self):
        """Construye una expresión con una comparación opcional entre expresiones aritméticas."""
        izquierda = self.suma()
        if self.actual.tipo in COMPARACIONES:
            operador = self.actual
            self.pos += 1
            izquierda = self.binaria(operador, izquierda, self.suma())
        return izquierda

    @staticmethod
    def binaria(operador, izquierda, derecha):
        """Recibe operador y operandos; devuelve un nodo Binaria con ubicación y ambos subárboles."""
        return {'nodo': 'Binaria', 'operador': operador.valor, **ubicacion(operador),
                'izquierda': izquierda, 'derecha': derecha}

    def suma(self):
        """Construye sumas y restas por la izquierda, dejando mayor prioridad a producto."""
        izquierda = self.producto()
        while self.actual.tipo in {'SUMA', 'RESTA'}:
            operador = self.actual
            self.pos += 1
            izquierda = self.binaria(operador, izquierda, self.producto())
        return izquierda

    def producto(self):
        """Construye multiplicaciones y divisiones por la izquierda a partir de expresiones unarias."""
        izquierda = self.unaria()
        while self.actual.tipo in {'MULTIPLICACION', 'DIVISION'}:
            operador = self.actual
            self.pos += 1
            izquierda = self.binaria(operador, izquierda, self.unaria())
        return izquierda

    def unaria(self):
        """Reconoce signos + y - recursivos; sin signo, delega en primaria."""
        operador = self.aceptar('SUMA', 'RESTA')
        if operador:
            return {'nodo': 'Unaria', 'operador': operador.valor, **ubicacion(operador), 'valor': self.unaria()}
        return self.primaria()

    def primaria(self):
        """Reconoce un literal, variable, captura o expresión entre paréntesis.
        Devuelve su nodo o lanza ErrorSintactico si no puede comenzar una expresión.
        """
        literal = self.aceptar('NUM_ENTERO', 'NUM_REAL', 'CADENA')
        if literal:
            return {'nodo': 'Literal', 'tipo': literal.tipo, 'lexema': literal.valor, **ubicacion(literal)}
        nombre = self.aceptar('IDENTIFICADOR')
        if nombre:
            return {'nodo': 'Variable', 'nombre': nombre.valor, **ubicacion(nombre)}
        if self.aceptar('CAPTURA'):
            self.exigir('PUNTO', "'.' después de Captura")
            if self.actual.tipo not in TIPOS:
                raise self.error('Texto, Entero, Real o Logico después de Captura.')
            tipo = self.actual
            self.pos += 1
            self.exigir('PAREN_ABRE', "'(' después del tipo de captura")
            self.exigir('PAREN_CIERRA', "')': Captura no recibe argumentos")
            return {'nodo': 'Captura', 'tipo': tipo.valor, **ubicacion(tipo)}
        if self.aceptar('PAREN_ABRE'):
            valor = self.expresion()
            self.exigir('PAREN_CIERRA', "')' para cerrar la expresión")
            return valor
        raise self.error('un número, cadena, variable, Captura.Tipo() o expresión entre paréntesis')


def analizar(codigo: str):
    # EOF apunta al final real del texto, incluso si termina en comentarios o espacios.
    """Reconoce todas las instrucciones hasta EOF y devuelve el nodo Programa del AST."""
    normalizado = codigo.replace('\r\n', '\n').replace('\r', '\n')
    linea = normalizado.count('\n') + 1
    columna = len(normalizado.rsplit('\n', 1)[-1]) + 1
    return Parser(tokenizar(codigo), linea, columna).analizar()


def main():
    """Analiza el archivo indicado por consola y comunica si su estructura es válida.
    Con --arbol muestra el AST en JSON; no ejecuta ni valida tipos.
    """
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('archivo', type=Path)
    cli.add_argument('--arbol', action='store_true', help='Mostrar el árbol sintáctico en JSON')
    args = cli.parse_args()
    try:
        arbol = analizar(args.archivo.read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError, ErrorLexico, ErrorSintactico) as error:
        cli.exit(1, f'{type(error).__name__}: {error}\n')
    print('Análisis sintáctico correcto. El programa no se ha ejecutado.')
    if args.arbol:
        print(json.dumps(arbol, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
