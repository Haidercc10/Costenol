"""Resaltado visual tolerante a código incompleto; no cambia las reglas del lenguaje."""
import re
from lexer import PALABRAS

IDENTIFICADOR = re.compile(r'[^\W\d]\w*')
NUMERO = re.compile(r'[0-9]+(?:,[0-9]+)?')
PALETAS_SINTAXIS = {
    'Oscuro': {
        'reservada': '#79b8ff', 'funcion': '#e5d38a', 'cadena': '#e6a080',
        'comentario': '#8fb77a', 'numero': '#b5cea8', 'operador': '#d5a1e8',
        'parentesis_0': '#ffd866', 'parentesis_1': '#dba5f5', 'parentesis_2': '#75cfff',
        'simbolo': '#b8c4d2',
    },
    'Claro': {
        'reservada': '#1555b6', 'funcion': '#805600', 'cadena': '#a33c24',
        'comentario': '#3c722e', 'numero': '#236346', 'operador': '#8143a1',
        'parentesis_0': '#866100', 'parentesis_1': '#823b9f', 'parentesis_2': '#006d99',
        'simbolo': '#526174',
    },
}


def rangos_sintaxis(codigo):
    """Devuelve segmentos (categoría, inicio, fin) con índices de Text, sin solapamientos.
    Reconoce cadenas escapadas, comentarios cerrados o pendientes, números,
    reservadas, llamadas de tipo, operadores y paréntesis por profundidad.
    Tolera errores para mantener el coloreado durante la escritura.
    """
    rangos = []
    profundidad = 0
    for linea, texto in enumerate(codigo.split('\n'), 1):
        pos = 0
        while pos < len(texto):
            inicio = pos
            categoria = None
            if texto.startswith('//', pos):
                cierre = texto.find('//', pos + 2)
                pos = cierre + 2 if cierre >= 0 else len(texto)
                categoria = 'comentario'
            elif texto[pos] == '"':
                pos += 1
                while pos < len(texto):
                    if texto[pos] == '\\':
                        pos = min(pos + 2, len(texto))
                    elif texto[pos] == '"':
                        pos += 1
                        break
                    else:
                        pos += 1
                categoria = 'cadena'
            elif texto[pos] in '()':
                if texto[pos] == ')':
                    profundidad = max(0, profundidad - 1)
                categoria = f'parentesis_{profundidad % 3}'
                if texto[pos] == '(':
                    profundidad += 1
                pos += 1
            else:
                numero = NUMERO.match(texto, pos)
                nombre = IDENTIFICADOR.match(texto, pos)
                if numero:
                    pos = numero.end()
                    categoria = 'numero'
                elif nombre:
                    pos = nombre.end()
                    palabra = nombre.group()
                    if palabra in PALABRAS:
                        # Si (...) sigue siendo una condición, no una llamada de función.
                        siguiente = texto[pos:].lstrip()
                        categoria = ('funcion' if palabra in {'Texto', 'Entero', 'Real', 'Logico'}
                                     and siguiente.startswith('(') else 'reservada')
                elif texto[pos] in '+-*/=<>!':
                    pos += 2 if texto[pos:pos+2] in {'==', '!=', '>=', '<='} else 1
                    categoria = 'operador'
                elif texto[pos] in '.;':
                    pos += 1
                    categoria = 'simbolo'
                else:
                    pos += 1
            if categoria is not None:
                rangos.append((categoria, f'{linea}.{inicio}', f'{linea}.{pos}'))
    return rangos


def rangos_reservadas(codigo):
    """Devuelve los rangos de reservadas exactas, incluidas las que se usan como llamadas.
    Mantiene la consulta anterior disponible; la interfaz usa rangos_sintaxis para distinguir colores.
    """
    return [(inicio, fin) for categoria, inicio, fin in rangos_sintaxis(codigo)
            if categoria in {'reservada', 'funcion'}]
