# Resultados observados

Entorno: Python 3.12.14; ejecución programática, sin interfaz.

## 01_simbolo_desconocido.pqek / principal

Resultado: ErrorLexico
Capturas solicitadas: 0

Línea 3, columna 11: carácter inválido '@'
Costeñol: Eche, ese símbolo no va por aquí. Cámbialo por uno que el lenguaje reconozca.

## 02_cadena_sin_cierre.pqek / principal

Resultado: ErrorLexico
Capturas solicitadas: 0

Línea 3, columna 10: cadena sin comillas de cierre
Costeñol: Ajá, bro, falta cerrar el texto con comillas dobles.

## 03_falta_punto_y_coma.pqek / principal

Resultado: ErrorSintactico
Capturas solicitadas: 0

Línea 3, columna 1: se esperaba ';' después de la declaración; se encontró 'edad'.
Costeñol: Ajá, a esa instrucción le falta su punto y coma. Ponle ; para dejarla lista.

## 04_condicional_sin_cierre.pqek / principal

Resultado: ErrorSintactico
Capturas solicitadas: 0

Línea 6, columna 1: se esperaba FinSi para cerrar el condicional; se encontró fin del archivo.
Costeñol: Eche, ese Si quedó abierto. Ciérralo con FinSi, compae.

## 05_nombre_reservado.pqek / principal

Resultado: ErrorSemantico
Capturas solicitadas: 0

Línea 2, columna 1: el nombre 'eNtErO' coincide con una palabra reservada
Costeñol: Eche, ese nombre ya está apartado. Ponle otro nombre a la variable.

## 06_valor_solo_en_una_rama.pqek / principal

Resultado: ErrorSemantico
Capturas solicitadas: 0

Línea 8, columna 15: variable 'res' sin valor asignado en todos los caminos
Costeñol: Suave, vale, esa variable todavía puede estar sin valor. Asígnale uno en todos los caminos antes de leerla.

## 07_concatenacion_asignada_a_entero.pqek / principal

Resultado: ErrorSemantico
Capturas solicitadas: 0

Línea 3, columna 1: no se puede asignar Texto a 'res' de tipo Entero
Costeñol: Eche, esa mezcla no cuadra. Revisa que el valor corresponda al tipo de la variable.

## 08_divisor_cero_en_ejecucion.pqek / divisor cero

Resultado: ErrorEjecucion
Capturas solicitadas: 1

Línea 4, columna 18: división entre cero
Costeñol: Eche, entre cero no se puede dividir. Cambia el divisor y prueba otra vez.

## 09_capturas_incompatibles.pqek / Texto numérico

Resultado: ErrorEjecucion
Capturas solicitadas: 1

Línea 6, columna 18: entrada inválida para Texto: '123'; se esperaba solo letras y espacios, con al menos una letra
Costeñol: Ajá, ese dato no cuadra con la caja. Sigue el formato indicado y prueba de nuevo.

## 09_capturas_incompatibles.pqek / Entero con letras

Resultado: ErrorEjecucion
Capturas solicitadas: 2

Línea 7, columna 16: entrada inválida para Entero: 'veinte'; se esperaba un entero con signo opcional, por ejemplo -12
Costeñol: Ajá, ese dato no cuadra con la caja. Sigue el formato indicado y prueba de nuevo.

## 09_capturas_incompatibles.pqek / Real con punto

Resultado: ErrorEjecucion
Capturas solicitadas: 3

Línea 8, columna 18: entrada inválida para Real: '3.5'; se esperaba un número con coma decimal opcional, por ejemplo 3,5
Costeñol: Ajá, ese dato no cuadra con la caja. Sigue el formato indicado y prueba de nuevo.

## 09_capturas_incompatibles.pqek / Logico numérico

Resultado: ErrorEjecucion
Capturas solicitadas: 4

Línea 9, columna 18: entrada inválida para Logico: '1'; se esperaba Verdadero o Falso
Costeñol: Ajá, ese dato no cuadra con la caja. Sigue el formato indicado y prueba de nuevo.

## 09_capturas_incompatibles.pqek / Control válido

Resultado: ACEPTADO
Capturas solicitadas: 4

Datos aceptados

## 10_entero_extremo.pqek / 3000 dígitos

Resultado: BRECHA: ValueError
Capturas solicitadas: 1

Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit
