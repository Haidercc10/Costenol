"""Parser descendente recursivo para Costeñol. No ejecuta el programa."""
import argparse
import json
from pathlib import Path
from lexer import Token, ErrorLexico, tokenizar


def ubicacion(token):
    return {"linea": token.linea, "columna": token.columna}


class ErrorSintactico(ValueError):
    pass


TIPOS = {'TEXTO', 'ENTERO', 'REAL', 'LOGICO'}
COMPARACIONES = {'IGUAL', 'DIFERENTE', 'MAYOR', 'MENOR', 'MAYOR_IGUAL', 'MENOR_IGUAL'}


class Parser:
    def __init__(self, tokens: list[Token], fin_linea=1, fin_columna=1):
        self.tokens = list(tokens) + [Token('EOF', '', fin_linea, fin_columna)]
        self.pos = 0

    @property
    def actual(self):
        return self.tokens[self.pos]

    def error(self, esperado):
        t = self.actual
        encontrado = 'fin del archivo' if t.tipo == 'EOF' else repr(t.valor)
        return ErrorSintactico(
            f'Línea {t.linea}, columna {t.columna}: se esperaba {esperado}; '
            f'se encontró {encontrado}.'
        )

    def aceptar(self, *tipos):
        if self.actual.tipo in tipos:
            token = self.actual
            self.pos += 1
            return token
        return None

    def exigir(self, tipo, descripcion):
        token = self.aceptar(tipo)
        if token is None:
            raise self.error(descripcion)
        return token

    def analizar(self):
        instrucciones = self.bloque(set())
        self.exigir('EOF', 'fin del archivo')
        return {'nodo': 'Programa', 'instrucciones': instrucciones}

    def bloque(self, cierres):
        instrucciones = []
        while self.actual.tipo not in cierres | {'EOF'}:
            instrucciones.append(self.instruccion())
        return instrucciones

    def instruccion(self):
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
        izquierda = self.suma()
        if self.actual.tipo in COMPARACIONES:
            operador = self.actual
            self.pos += 1
            izquierda = self.binaria(operador, izquierda, self.suma())
        return izquierda

    @staticmethod
    def binaria(operador, izquierda, derecha):
        return {'nodo': 'Binaria', 'operador': operador.valor, **ubicacion(operador),
                'izquierda': izquierda, 'derecha': derecha}

    def suma(self):
        izquierda = self.producto()
        while self.actual.tipo in {'SUMA', 'RESTA'}:
            operador = self.actual
            self.pos += 1
            izquierda = self.binaria(operador, izquierda, self.producto())
        return izquierda

    def producto(self):
        izquierda = self.unaria()
        while self.actual.tipo in {'MULTIPLICACION', 'DIVISION'}:
            operador = self.actual
            self.pos += 1
            izquierda = self.binaria(operador, izquierda, self.unaria())
        return izquierda

    def unaria(self):
        operador = self.aceptar('SUMA', 'RESTA')
        if operador:
            return {'nodo': 'Unaria', 'operador': operador.valor, **ubicacion(operador), 'valor': self.unaria()}
        return self.primaria()

    def primaria(self):
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
    normalizado = codigo.replace('\r\n', '\n').replace('\r', '\n')
    linea = normalizado.count('\n') + 1
    columna = len(normalizado.rsplit('\n', 1)[-1]) + 1
    return Parser(tokenizar(codigo), linea, columna).analizar()


def main():
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
