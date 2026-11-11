"""Validación estática de declaraciones, tipos e inicialización de Costeñol."""
from mensajes import personalizar
import argparse
import json
from pathlib import Path
from lexer import ErrorLexico, PALABRAS
from parser import analizar, ErrorSintactico


class ErrorSemantico(ValueError):
    pass


NUMERICOS = {'Entero', 'Real'}
RESERVADAS = {palabra.casefold() for palabra in PALABRAS}


class AnalizadorSemantico:
    def error(self, nodo, mensaje):
        """Lanza ErrorSemantico con la ubicación del nodo y la causa recibida."""
        raise ErrorSemantico(f'Línea {nodo["linea"]}, columna {nodo["columna"]}: {personalizar(mensaje)}')

    def buscar(self, nodo, simbolos):
        """Busca el nombre del nodo en la tabla visible y devuelve su registro.
        Lanza ErrorSemantico si no fue declarado antes de usarse.
        """
        nombre = nodo['nombre']
        if nombre not in simbolos:
            self.error(nodo, f"variable '{nombre}' no declarada antes de su uso")
        return simbolos[nombre]

    def expresion(self, nodo, simbolos):
        """Infiere y devuelve el tipo Costeñol de una expresión sin calcular su valor.
        Valida inicialización, operandos y concatenación de texto con números.
        """
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
            if operador == '+' and (
                    (izquierda == 'Texto' and derecha in NUMERICOS | {'Texto'})
                    or (derecha == 'Texto' and izquierda in NUMERICOS)):
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
        """Recorre instrucciones y actualiza la tabla de símbolos recibida.
        Comprueba declaraciones, asignaciones y condiciones; combina inicialización de ambas ramas.
        """
        for nodo in instrucciones:
            clase = nodo['nodo']
            if clase == 'Declaracion':
                nombre = nodo['nombre']
                if nombre.casefold() in RESERVADAS:
                    self.error(nodo, f"el nombre '{nombre}' coincide con una palabra reservada")
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
        """Recibe el nodo Programa, valida sus instrucciones y devuelve la tabla global.
        Cada llamada comienza con una tabla nueva y no ejecuta capturas ni mensajes.
        """
        simbolos = {}
        self.bloque(arbol['instrucciones'], simbolos)
        return simbolos


def analizar_semantica(codigo: str):
    """Recibe código fuente; ejecuta lexer, parser y validación semántica.
    Devuelve la tabla global o propaga el primer error de cualquiera de esas etapas.
    """
    return AnalizadorSemantico().analizar(analizar(codigo))


def main():
    """Valida el archivo recibido por consola y, con --simbolos, muestra la tabla global.
    Informa los errores por categoría sin ejecutar el programa.
    """
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
