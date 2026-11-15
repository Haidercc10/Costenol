"""Validación de rutas de guardado de programas Costeñol."""
from pathlib import Path


def ruta_guardado(archivo):
    """Devuelve una ruta .pqek; añade la extensión ausente y rechaza otras extensiones.
    No escribe ni reemplaza archivos. Las extensiones se comparan sin distinguir mayúsculas.
    """
    ruta = Path(archivo)
    if not ruta.name or ruta.name.endswith(('.', ' ')):
        raise ValueError('Escribe un nombre de archivo válido terminado en .pqek.')
    if not ruta.suffix:
        ruta = ruta.with_suffix('.pqek')
    if ruta.suffix.casefold() != '.pqek':
        raise ValueError('Eche, los programas de Costeñol se guardan con extensión .pqek. Cambia la extensión para continuar.')
    return ruta
