"""Identidad costeña de los diagnósticos, conservando su explicación técnica."""


def personalizar(mensaje):
    """Añade una orientación costeña al diagnóstico sin borrar tipos, nombres ni causas.
    Usa reglas deterministas y evita repetir la frase cuando otra etapa propaga el error.
    """
    marca = '\nCosteñol: '
    if marca in mensaje:
        return mensaje
    reglas = [
        ('carácter inválido', 'Eche, ese símbolo no va por aquí. Cámbialo por uno que el lenguaje reconozca.'),
        ('comentario sin cierre', 'Hey, ese comentario quedó abierto. Ponle su cierre // y seguimos.'),
        ('cadena sin comillas', 'Ajá, bro, falta cerrar el texto con comillas dobles.'),
        ('palabra reservada', 'Eche, ese nombre ya está apartado. Ponle otro nombre a la variable.'),
        ('no declarada', 'Ajá, ¿y esa variable de dónde salió? Declárala primero, bro.'),
        ('ya declarada', 'Hey, esa variable ya tiene su puesto. Usa la que existe o elige otro nombre.'),
        ('sin valor asignado', 'Suave, vale, esa variable todavía puede estar sin valor. Asígnale uno en todos los caminos antes de leerla.'),
        ('no se puede asignar', 'Eche, esa mezcla no cuadra. Revisa que el valor corresponda al tipo de la variable.'),
        ('incompatible entre', 'Deja el viaje, bro: esos tipos no combinan con ese operador. Revisa los dos lados.'),
        ('condición de Si', 'Ajá, esa condición debe dar Verdadero o Falso. Usa una comparación o una variable Logico.'),
        ('requiere números', 'Hey, por aquí van números. Revisa los valores que estás comparando.'),
        ('requiere un número', 'Bájale dos, ese signo necesita un número. Revisa la expresión.'),
        ('división entre cero', 'Eche, entre cero no se puede dividir. Cambia el divisor y prueba otra vez.'),
        ('captura cancelada', 'Listo, vale, cancelaste la captura. Cuando quieras, vuelve a ejecutar.'),
        ('no hay datos', 'Hey, faltó el dato de la captura. Ingresa un valor para poder seguir.'),
        ('entrada inválida', 'Ajá, ese dato no cuadra con la caja. Sigue el formato indicado y prueba de nuevo.'),
        ('fuera de rango', 'Bájale dos, bro, ese número supera el rango permitido. Prueba con uno más pequeño.'),
        ('fuera del rango', 'Bájale dos, bro, ese número supera el rango permitido. Prueba con uno más pequeño.'),
        ('escape no admitido', 'Hey, esa secuencia con barra invertida no va. Usa un escape permitido o escribe doble barra.'),
    ]
    for fragmento, orientacion in reglas:
        if fragmento in mensaje:
            return mensaje + marca + orientacion
    if 'se esperaba' in mensaje:
        if "';'" in mensaje:
            frase = 'Ajá, a esa instrucción le falta su punto y coma. Ponle ; para dejarla lista.'
        elif 'FinSi' in mensaje and 'cerrar el condicional' in mensaje:
            frase = 'Eche, ese Si quedó abierto. Ciérralo con FinSi, compae.'
        elif "')'" in mensaje:
            frase = 'Hey, ese paréntesis quedó sin pareja. Agrega el cierre donde corresponde.'
        else:
            frase = 'Ajá, bro, revisa el orden de la instrucción y el elemento que hace falta.'
        return mensaje + marca + frase
    return mensaje + marca + 'Hey, revisa ese detalle y prueba de nuevo, vale.'
