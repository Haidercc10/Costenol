"""Analizador léxico manual de Costeñol. Python 3.10+."""
from dataclasses import dataclass
from pathlib import Path
import re
import sys

@dataclass(frozen=True)
class Token:
    tipo: str
    valor: str
    linea: int
    columna: int

class ErrorLexico(ValueError):
    pass

PALABRAS = {p: p.upper() for p in (
    'Texto', 'Entero', 'Real', 'Logico', 'Captura', 'Mensaje', 'Si', 'Sino', 'FinSi'
)}
SIMBOLOS = {
    '==': 'IGUAL', '!=': 'DIFERENTE', '>=': 'MAYOR_IGUAL', '<=': 'MENOR_IGUAL',
    '=': 'ASIGNACION', '>': 'MAYOR', '<': 'MENOR', '+': 'SUMA', '-': 'RESTA',
    '*': 'MULTIPLICACION', '/': 'DIVISION', '(': 'PAREN_ABRE', ')': 'PAREN_CIERRA',
    '.': 'PUNTO', ';': 'PUNTO_Y_COMA',
}
PATRON = re.compile(r'(?P<ESPACIO>[ \t]+)|(?P<NUM_REAL>[0-9]+,[0-9]+)|(?P<NUM_ENTERO>[0-9]+)|(?P<IDENTIFICADOR>[^\W\d]\w*)')

def tokenizar(codigo: str) -> list[Token]:
    tokens = []
    for linea, texto in enumerate(codigo.splitlines(), 1):
        pos = 0
        while pos < len(texto):
            columna = pos + 1
            def error(mensaje):
                return ErrorLexico(f'Línea {linea}, columna {columna}: {mensaje}')
            if texto.startswith('//', pos):
                fin = texto.find('//', pos + 2)
                if fin == -1:
                    raise error('comentario sin cierre //')
                pos = fin + 2
                continue
            if texto[pos] == '"':
                fin = pos + 1
                while fin < len(texto) and texto[fin] != '"':
                    fin += 2 if texto[fin] == '\\' else 1
                if fin >= len(texto):
                    raise error('cadena sin comillas de cierre')
                tokens.append(Token('CADENA', texto[pos:fin + 1], linea, columna))
                pos = fin + 1
                continue
            match = PATRON.match(texto, pos)
            if match:
                tipo, valor = match.lastgroup, match.group()
                if tipo == 'IDENTIFICADOR':
                    tipo = PALABRAS.get(valor, tipo)
                if tipo != 'ESPACIO':
                    tokens.append(Token(tipo, valor, linea, columna))
                pos = match.end()
                continue
            simbolo = texto[pos:pos + 2]
            if simbolo not in SIMBOLOS:
                simbolo = texto[pos]
            if simbolo not in SIMBOLOS:
                raise error(f'carácter inválido {texto[pos]!r}')
            tokens.append(Token(SIMBOLOS[simbolo], simbolo, linea, columna))
            pos += len(simbolo)
    return tokens

def main():
    if len(sys.argv) != 2:
        sys.exit('Uso: python lexer.py ejemplo.cost')
    try:
        tokens = tokenizar(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError, ErrorLexico) as error:
        sys.exit(str(error))
    print(f'{"LÍNEA":<7} {"COLUMNA":<9} {"TIPO":<20} LEXEMA')
    for token in tokens:
        print(f'{token.linea:<7} {token.columna:<9} {token.tipo:<20} {token.valor}')

if __name__ == '__main__':
    main()
