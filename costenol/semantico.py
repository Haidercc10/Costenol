"""Validación estática de declaraciones, tipos e inicialización de Costeñol."""
import argparse
import json
from pathlib import Path
from lexer import ErrorLexico
from parser import analizar, ErrorSintactico


class ErrorSemantico(ValueError):
    pass


NUMERICOS = {'Entero', 'Real'}


class AnalizadorSemantico:
    def error(self, nodo, mensaje):
        raise ErrorSemantico(f'Línea {nodo["linea"]}, columna {nodo["columna"]}: {mensaje}')

    def buscar(self, nodo, simbolos):
        nombre = nodo['nombre']
        if nombre not in simbolos:
            self.error(nodo, f"variable '{nombre}' no declarada antes de su uso")
        return simbolos[nombre]

    def expresion(self, nodo, simbolos):
        clase = nodo['nodo']
        if clase == 'Literal':
            return {'NUM_ENTERO': 'Entero', 'NUM_REAL': 'Real', 'CADENA': 'Texto'}[nodo['tipo']]
        if clase == 'Captura':
            return nodo['tipo']
        if clase == 'Variable':
            simbolo = self.buscar(nodo, simbolos)
            if not simbolo['inicializada']:
                self.error(nodo, f"variable '{nodo['nombre']}' sin valor asignado en todos los caminos")
            return simbolo['tipo']
        if clase == 'Unaria':
            tipo = self.expresion(nodo['valor'], simbolos)
            if tipo not in NUMERICOS:
                self.error(nodo, f"el signo '{nodo['operador']}' requiere un número, recibió {tipo}")
            return tipo
        if clase == 'Binaria':
            izquierda = self.expresion(nodo['izquierda'], simbolos)
            derecha = self.expresion(nodo['derecha'], simbolos)
            operador = nodo['operador']
            numericos = izquierda in NUMERICOS and derecha in NUMERICOS
            if operador == '+' and izquierda == derecha == 'Texto':
                return 'Texto'
            if operador in {'+', '-', '*', '/'}:
                if not numericos:
                    self.error(nodo, f"operación '{operador}' incompatible entre {izquierda} y {derecha}")
                return 'Real' if operador == '/' or 'Real' in {izquierda, derecha} else 'Entero'
            if operador in {'==', '!='}:
                if not (numericos or izquierda == derecha):
                    self.error(nodo, f"comparación '{operador}' incompatible entre {izquierda} y {derecha}")
                return 'Logico'
            if operador in {'>', '<', '>=', '<='}:
                if not numericos:
                    self.error(nodo, f"comparación '{operador}' requiere números, recibió {izquierda} y {derecha}")
                return 'Logico'
        raise ValueError(f'Nodo de expresión no admitido: {clase}')

    def bloque(self, instrucciones, simbolos):
        # Los nombres visibles al entrar no se pueden redeclarar ni sombrear.
        for nodo in instrucciones:
            clase = nodo['nodo']
            if clase == 'Declaracion':
                nombre = nodo['nombre']
                if nombre in simbolos:
                    self.error(nodo, f"variable '{nombre}' ya declarada")
                simbolos[nombre] = {'tipo': nodo['tipo'], 'inicializada': False,
                                    'linea': nodo['linea'], 'columna': nodo['columna']}
            elif clase == 'Asignacion':
                destino = self.buscar(nodo, simbolos)
                tipo = self.expresion(nodo['valor'], simbolos)
                if tipo != destino['tipo'] and not (tipo == 'Entero' and destino['tipo'] == 'Real'):
                    self.error(nodo, f"no se puede asignar {tipo} a '{nodo['nombre']}' de tipo {destino['tipo']}")
                destino['inicializada'] = True
            elif clase == 'Mensaje':
                # Se permiten los cuatro tipos; la ejecución futura los convertirá a texto.
                self.expresion(nodo['valor'], simbolos)
            elif clase == 'Condicional':
                tipo = self.expresion(nodo['condicion'], simbolos)
                if tipo != 'Logico':
                    self.error(nodo['condicion'], f'la condición de Si debe ser Logico, recibió {tipo}')
                entonces = {nombre: dict(datos) for nombre, datos in simbolos.items()}
                sino = {nombre: dict(datos) for nombre, datos in simbolos.items()}
                self.bloque(nodo['entonces'], entonces)
                self.bloque(nodo['sino'] or [], sino)
                for nombre in simbolos:
                    simbolos[nombre]['inicializada'] = (
                        entonces[nombre]['inicializada'] and sino[nombre]['inicializada'])
            else:
                raise ValueError(f'Instrucción no admitida: {clase}')

    def analizar(self, arbol):
        simbolos = {}
        self.bloque(arbol['instrucciones'], simbolos)
        return simbolos


def analizar_semantica(codigo: str):
    """Ejecuta lexer, parser y semántica; devuelve símbolos globales, sin ejecutar código."""
    return AnalizadorSemantico().analizar(analizar(codigo))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('archivo', type=Path)
    cli.add_argument('--simbolos', action='store_true', help='Mostrar tabla de símbolos globales')
    args = cli.parse_args()
    try:
        simbolos = analizar_semantica(args.archivo.read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError, ErrorLexico, ErrorSintactico, ErrorSemantico) as error:
        cli.exit(1, f'{type(error).__name__}: {error}\n')
    print('Análisis semántico correcto. El programa no se ha ejecutado.')
    if args.simbolos:
        print(json.dumps(simbolos, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
