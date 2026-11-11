# Diez programas para probar errores de Costeñol

Ejecutar desde la carpeta costenol. Son pruebas adversas: que un programa sea
rechazado con el error esperado significa que la comprobación funcionó.
Cada archivo prioriza un fallo porque el motor se detiene en el primero.

| Archivo | Etapa esperada | Qué pone a prueba |
|---|---|---|
| 01_simbolo_desconocido.pqek | Léxica | Símbolo @ fuera de una cadena. |
| 02_cadena_sin_cierre.pqek | Léxica | Texto sin comillas de cierre. |
| 03_falta_punto_y_coma.pqek | Sintáctica | Declaración sin punto y coma. |
| 04_condicional_sin_cierre.pqek | Sintáctica | Cierra el Si interior, pero no el exterior. |
| 05_nombre_reservado.pqek | Semántica | Nombre eNtErO con mayúsculas mezcladas. |
| 06_valor_solo_en_una_rama.pqek | Semántica | Lectura de res que no tiene valor en todos los caminos. |
| 07_concatenacion_asignada_a_entero.pqek | Semántica | Una concatenación válida produce Texto y no puede guardarse en Entero. |
| 08_divisor_cero_en_ejecucion.pqek | Ejecución | El divisor es una expresión que termina siendo cero. |
| 09_capturas_incompatibles.pqek | Capturas / ejecución | Validación de los cuatro tipos de entrada. |
| 10_entero_extremo.pqek | Ejecución / límite | Resultado entero demasiado largo para convertir a texto. |

## Cómo ejecutarlos

En la interfaz: Abrir, entrar a ejemplos/pruebas_errores, elegir un archivo y
pulsar Analizar o Ejecutar. Los casos 01 a 07 deben fallar al analizar.
El caso 06 no debe solicitar la edad: la semántica valida antes de ejecutar.
Los casos 08 a 10 requieren Ejecutar para llegar al fallo de ejecución.

En consola, por ejemplo:

    python interprete.py ejemplos/pruebas_errores/01_simbolo_desconocido.pqek
    python interprete.py ejemplos/pruebas_errores/08_divisor_cero_en_ejecucion.pqek

Para el caso 08 introduce 7; también cualquier otro entero deja el divisor en cero.

## Entradas para el caso 09

Repite con estas combinaciones. La ejecución por consola se detiene al primer
valor inválido; en la interfaz la caja debe bloquearlo o permitir corregirlo.

| Objetivo | Respuestas en orden |
|---|---|
| Texto numérico | 123 |
| Entero con letras | Ana, veinte |
| Real con punto | Ana, 20, 3.5 |
| Logico numérico | Ana, 20, 3,5, 1 |
| Control correcto | Ana, 20, 3,5, Verdadero |

La última combinación debe ser aceptada y mostrar Datos aceptados.
No confundir la coma decimal dentro de una respuesta con la separación entre
respuestas: cada dato se introduce en una captura diferente.

## Brecha encontrada en el caso 10

Copia como respuesta la línea de entrada_extrema.txt: contiene 3000 nueves.
La captura del entero es válida. Al elevarlo al cuadrado se genera un entero
de 6000 dígitos aproximadamente. Python 3.11 de este entorno impone un límite
predeterminado de 4300 dígitos en su conversión decimal a texto. Al mostrar res,
se lanza ValueError en lugar de ErrorEjecucion con ubicación y mensaje costeño.

Resultado observado mediante la API del intérprete: ValueError sin convertir.
La consola no captura esa excepción genérica y puede presentar un traceback.
La interfaz tiene una captura general de ValueError y puede mostrar Límite de
procesamiento, pero ese camino no ofrece ubicación ni personalización costeña.
La ventana no se verificó porque Tcl/Tk no inicia en el entorno de desarrollo.
El resultado depende de la versión y configuración de Python.

Este caso se conserva como reproducción de una brecha pendiente; no se cambió
el motor para ocultarla o corregirla en esta entrega de ejemplos. Una solución
posterior debe controlar el tamaño o traducir el fallo de conversión a un error
propio, con ubicación de la instrucción de salida.

## Alcance de esta revisión

Se probaron los 10 archivos con entradas simuladas, incluyendo cuatro capturas
inválidas y un control válido en el caso 09: 14 ejecuciones en total.
Los detalles y los mensajes reales están en RESULTADOS.md. Los primeros nueve
archivos respondieron según las reglas; el décimo reprodujo la brecha indicada.
Estos casos aportan cobertura adicional, pero no garantizan ausencia de otros
fallos ni sustituyen las pruebas gráficas pendientes.
