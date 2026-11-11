"""Reglas compartidas de captura para consola y diálogos de Costeñol."""
from mensajes import personalizar
import math
import re

FORMATOS = {
    'Texto': 'solo letras y espacios, con al menos una letra',
    'Entero': 'un entero con signo opcional, por ejemplo -12',
    'Real': 'un número con coma decimal opcional, por ejemplo 3,5',
    'Logico': 'Verdadero o Falso',
}


def convertir_captura(tipo, texto):
    """Valida la entrada completa y devuelve su valor Python según el tipo.
    Texto admite letras Unicode y espacios; números y lógicos usan sus formatos propios.
    Lanza ValueError si el formato es incorrecto o el número está fuera de rango.
    """
    if tipo not in FORMATOS:
        raise ValueError(f'Tipo de captura desconocido: {tipo}')
    limpio = texto.strip()
    if tipo == 'Texto':
        if any(c.isalpha() for c in texto) and all(c.isalpha() or c.isspace() for c in texto):
            return texto
    elif tipo == 'Entero':
        if re.fullmatch(r'[+-]?[0-9]+', limpio):
            try:
                return int(limpio)
            except ValueError:
                raise ValueError(personalizar('entrada fuera de rango para Entero')) from None
    elif tipo == 'Real':
        if re.fullmatch(r'[+-]?[0-9]+(?:,[0-9]+)?', limpio):
            valor = float(limpio.replace(',', '.'))
            if not math.isfinite(valor):
                raise ValueError(personalizar('entrada fuera del rango permitido para Real'))
            return valor
    elif tipo == 'Logico':
        if limpio.casefold() in {'verdadero', 'falso'}:
            return limpio.casefold() == 'verdadero'
    raise ValueError(personalizar(f'entrada inválida para {tipo}: {texto!r}; se esperaba {FORMATOS[tipo]}'))


def permite_edicion(tipo, texto):
    """Acepta estados parciales al escribir o pegar sin permitir caracteres de otro tipo.
    Permite borrar, dejar un signo o una coma decimal pendiente; la aceptación final
    se comprueba por separado con convertir_captura.
    """
    if tipo == 'Texto':
        return all(c.isalpha() or c.isspace() for c in texto)
    if tipo == 'Entero':
        return re.fullmatch(r'[+-]?[0-9]*', texto) is not None
    if tipo == 'Real':
        return re.fullmatch(r'[+-]?[0-9]*(?:,[0-9]*)?', texto) is not None
    if tipo == 'Logico':
        return texto.casefold() in {'', 'verdadero', 'falso'}
    return False
