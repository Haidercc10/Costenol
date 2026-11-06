# Costeñol: paso 1

Requiere Python 3.10 o posterior. No necesita paquetes externos.
Abre esta carpeta en VS Code y ejecuta en su terminal:

    python lexer.py ejemplos/ejemplo.pqek

Si Windows no reconoce python, usa py en su lugar.

## Cómo leer el código

1. Token guarda tipo, lexema original, línea y columna desde 1.
2. PALABRAS distingue palabras reservadas de identificadores.
3. SIMBOLOS reconoce operadores y signos; se comprueban primero los de dos caracteres.
4. PATRON reconoce espacios, reales con coma, enteros e identificadores.
5. tokenizar recorre las líneas de izquierda a derecha. Omite espacios y comentarios.
6. Las cadenas se reconocen antes que los operadores: // dentro de una cadena es texto.
7. main lee un archivo UTF-8 y muestra la tabla de tokens.

## Reglas y decisiones

Se distinguen mayúsculas. Los comentarios se abren y cierran con // en la misma línea.
Los reales usan coma decimal. Las cadenas usan comillas dobles rectas.
Los identificadores admiten letras Unicode y guion bajo, seguidos también de dígitos.
Se conservan los lexemas originales; todavía no se convierten a valores Python.

Decisiones provisionales que el enunciado no detalla:
- Comparaciones: ==, !=, >, <, >=, <=.
- Dentro de cadenas, una barra invertida permite escapar el carácter siguiente.
Los literales lógicos y los operadores lógicos quedan pendientes de definición.

## Ejercicios

- Cambia Si por si: debe pasar de SI a IDENTIFICADOR.
- Modifica 3,1416: debe seguir siendo un único NUM_REAL.
- Agrega @ fuera de una cadena: debe indicar línea y columna del error.
- Quita la comilla final de una cadena o el cierre // de un comentario.

Este programa solo reconoce tokens. Puede tokenizar edad = ;, aunque esa instrucción
sea incorrecta. El parser del siguiente paso verificará la estructura; después
validaremos declaraciones y tipos, y añadiremos ejecución básica.

## Paso 2: analizador sintáctico

Ejecuta desde esta carpeta:

    python parser.py ejemplos/ejemplo_sintactico.pqek
    python parser.py ejemplos/ejemplo_sintactico.pqek --arbol
    python -m unittest test_parser.py -v

El primer comando valida; el segundo también muestra el árbol sintáctico (AST)
en JSON; el tercero ejecuta las pruebas automáticas. El lexer sigue disponible
con su comando original. No se modificó ejemplos/ejemplo.pqek para conservar tus ejercicios.

### Cómo funciona el parser

1. analizar(codigo) llama al lexer y entrega sus tokens al Parser.
2. actual consulta el token actual; pos indica cuánto se ha consumido.
3. aceptar consume un token si coincide; exigir informa un error si falta.
4. instruccion selecciona declaración, asignación, mensaje o condicional.
5. bloque reúne instrucciones y se detiene ante Sino, FinSi o fin del archivo,
   según corresponda. Cada condicional procesa su propio bloque anidado.
6. expresion, suma, producto, unaria y primaria construyen las expresiones.
   La multiplicación y división tienen prioridad sobre suma y resta; los
   paréntesis permiten cambiar el orden. Los operadores aritméticos binarios
   son asociativos a la izquierda. La comparación tiene menor prioridad.
7. Cada función devuelve diccionarios que forman el AST. No calcula valores.

### Gramática implementada (EBNF)

    programa     = { instruccion } ;
    instruccion  = declaracion | asignacion | mensaje | condicional ;
    declaracion  = IDENTIFICADOR tipo ";" ;
    tipo         = "Texto" | "Entero" | "Real" | "Logico" ;
    asignacion   = IDENTIFICADOR "=" expresion ";" ;
    mensaje      = "Mensaje" "." "Texto" "(" expresion ")" ";" ;
    condicional  = "Si" "(" expresion ")" { instruccion }
                   [ "Sino" { instruccion } ] "FinSi" ;
    expresion    = suma [ comparador suma ] ;
    comparador   = "==" | "!=" | ">" | "<" | ">=" | "<=" ;
    suma         = producto { ("+" | "-") producto } ;
    producto     = unaria { ("*" | "/") unaria } ;
    unaria       = ("+" | "-") unaria | primaria ;
    primaria     = NUM_ENTERO | NUM_REAL | CADENA | IDENTIFICADOR
                   | captura | "(" expresion ")" ;
    captura      = "Captura" "." tipo "(" ")" ;

Las llaves indican repetición, los corchetes indican una parte opcional y
las comillas representan texto literal del lenguaje. Estas llaves y corchetes
no se escriben en los programas Costeñol.

### Decisiones de esta versión

- Mensaje.Texto recibe una expresión (incluye cadenas y variables). Es una
  ampliación provisional respecto al ejemplo literal del enunciado.
- Se permiten bloques vacíos, Sino opcional y condicionales anidados.
- El salto de línea es espacio de separación, no termina una instrucción.
- Las declaraciones, asignaciones y mensajes terminan con punto y coma;
  Si, Sino y FinSi no llevan punto y coma.
- Solo se permite una comparación por nivel de expresión; no se admiten
  comparaciones encadenadas como a < b < c.
- Los valores literales lógicos y operadores lógicos siguen pendientes.
  Sí se reconoce una declaración Logico y Captura.Logico().
- No se exige un espacio concreto después de Si: el lexer ignora espacios.
- Se detiene en el primer error; no recupera ni enumera errores posteriores.

### Ejercicios de errores sintácticos

Crea un archivo prueba_error.pqek con un solo ejemplo a la vez y ejecuta:

    python parser.py prueba_error.pqek

Prueba `edad = ;` para ver la ausencia de una expresión.
Prueba `edad Entero` para ver la ausencia del punto y coma.
Prueba `Si (edad > 18)` para ver la ausencia de FinSi.
Prueba `Mensaje.Texto("Hola";` para ver la ausencia de un paréntesis.

Los errores pueden apuntar al token siguiente, que es donde se detectó la
omisión, o al final del archivo si no hay más tokens.

### Límites y siguiente etapa

Un resultado sintáctico correcto no garantiza que el programa tenga sentido.
`sinDeclarar = "texto" + 2;` todavía pasa: usa piezas y estructura válidas.
El análisis semántico deberá comprobar declaraciones, tipos y que las condiciones
sean lógicas. Después construiremos la ejecución básica. No se usa eval ni exec.

## Paso 3: análisis semántico

Desde la carpeta costenol:

    python semantico.py ejemplos/ejemplo_semantico.pqek
    python semantico.py ejemplos/ejemplo_semantico.pqek --simbolos
    python semantico.py ejemplos/error_semantico.pqek
    python -m unittest discover -p "test_*.py" -v

El tercer comando falla intencionalmente con ErrorSemantico en línea 3,
columna 1: no se puede asignar Texto a edad de tipo Entero. Los comandos
anteriores de lexer.py y parser.py siguen funcionando por separado.

### Recorrido y tabla de símbolos

analizar_semantica llama al parser, que primero llama al lexer. Después,
AnalizadorSemantico recorre el árbol sin ejecutar código ni pedir entradas.
La tabla registra nombre, tipo, ubicación de declaración e inicialización;
no guarda valores calculados. expresion infiere el tipo de cada expresión;
bloque comprueba las instrucciones. Se informa el primer error y se termina.
El parser ahora conserva línea y columna en los nodos necesarios para ubicar
los errores semánticos. La gramática no cambió.

### Reglas adoptadas para esta versión

Estas decisiones concretan aspectos que el enunciado no define por completo:

- Se declara antes de usar. No se puede repetir un nombre visible.
- La declaración no asigna un valor inicial. Leer una variable sin asignación
  previa es error; se admite declarar una variable y no usarla.
- Cada rama de Si/Sino tiene alcance local para sus declaraciones. Los nombres
  del bloque exterior son visibles dentro. No se permite ocultarlos con otra
  declaración. Las variables locales no existen fuera de la rama y las dos
  ramas pueden declarar, de forma independiente, el mismo nombre.
- Una asignación a una variable exterior se considera segura después de un
  condicional solo si estaba inicializada antes o queda inicializada en ambas
  ramas. Sin Sino, también se contempla que no se ejecute el bloque Si.
  No se calculan condiciones constantes para eliminar caminos posibles.
- Se permite Entero hacia Real. No se permite Real hacia Entero ni otras
  conversiones implícitas, tampoco entre Logico y Entero.
- +, -, * requieren números; + permite además Texto + Texto (concatenación).
  Una operación numérica produce Real si alguno de sus operandos es Real.
- / siempre produce Real, incluso 4 / 2. Los signos unarios exigen números.
- == y != admiten dos tipos iguales o la pareja Entero/Real.
  <, >, <= y >= requieren números. Toda comparación produce Logico.
- Si exige una expresión de tipo Logico.
- Captura.Tipo() tiene el tipo indicado sin leer datos durante esta etapa.
- Mensaje.Texto admite expresiones de los cuatro tipos. La futura ejecución
  deberá convertir el valor a texto para mostrarlo.
- Siguen sin definirse literales ni operadores lógicos adicionales. Puedes
  obtener Logico mediante comparaciones o Captura.Logico().

### Pruebas y límites

test_semantico.py verifica declaraciones, conversiones, operaciones, condiciones,
ubicaciones, alcance local e inicialización en ramas independientes y anidadas.
También verifica que se conserven los errores léxicos y sintácticos.

Los archivos de ejercicios anteriores pueden contener errores que hayas añadido
para practicar; las pruebas nuevas usan su propio ejemplo y casos independientes.

El éxito de esta etapa confirma las reglas estáticas anteriores. No garantiza
que una captura futura sea válida ni detecta división entre cero: esos errores
se atenderán en ejecución. No se ejecutan instrucciones ni se usa eval/exec.

Siguiente paso: intérprete que use el árbol, implemente capturas y mensajes,
calcule expresiones y seleccione las ramas de los condicionales.

## Paso 4: ejecución básica

Desde esta carpeta ejecuta:

    python interprete.py ejemplos/ejemplo_ejecucion.pqek

El programa primero valida TODO el código con lexer, parser y semántica.
Solo si pasa comienza a leer datos y mostrar mensajes. Para el ejemplo escribe
una respuesta por línea: Ana, 20, 12,5 y Verdadero. No incluyas comillas.
Debe mostrar Hola, Ana, Mayor de edad, Asistencia confirmada y total 25,0,
además de las preguntas. Con edad 15, ejecutará la rama Menor de edad.

### Funciones principales

- ejecutar(codigo): construye el árbol, valida y ejecuta. Devuelve las variables
  globales con sus tipos y valores. No genera binarios ni usa eval o exec.
- evaluar: convierte literales y resuelve variables, capturas y operaciones.
- bloque: ejecuta instrucciones en orden y selecciona solo una rama de Si/Sino.
- capturar: lee y valida la entrada de acuerdo al tipo solicitado.
- mostrar: presenta reales con coma y lógicos como Verdadero/Falso.

La ejecución conserva las reglas semánticas: las declaraciones de las ramas son
locales y las asignaciones a variables exteriores se conservan al salir.
Los operandos se evalúan de izquierda a derecha. Cada Mensaje.Texto añade un
salto de línea. Una variable declarada y no usada puede quedar sin valor.

### Formato de capturas

- Texto: admite cualquier texto, incluso vacío; conserva espacios.
- Entero: dígitos con signo opcional, como 12 o -5.
- Real: dígitos con signo opcional y coma decimal opcional: 12 o -3,5.
  No admite punto decimal, notación exponencial, NaN ni infinito en la entrada.
- Logico: Verdadero o Falso, sin distinguir mayúsculas. No admite 1/0 ni sí/no.

Las entradas numéricas y lógicas ignoran espacios en sus extremos.
Una entrada inválida detiene el programa en el primer error, sin reintentar.
EOF o cancelación de captura también producen ErrorEjecucion con ubicación.
Los valores lógicos anteriores son formatos de captura, no nuevos literales
que se puedan escribir sin comillas dentro del código fuente.

### Cadenas y números

En cadenas se interpretan los escapes \n, \t, \r, \" y \\.
Un escape desconocido se informa en ejecución si esa cadena se evalúa.
Los reales usan float de Python (precisión finita, posibles redondeos).
Los resultados no finitos y los desbordamientos controlados generan error.
La salida de un real puede usar notación científica para valores extremos.

### Probar errores de ejecución

Crea prueba_ejecucion.pqek con:

    divisor Entero;
    divisor = Captura.Entero();
    Mensaje.Texto(10 / divisor);

Ejecuta `python interprete.py prueba_ejecucion.pqek` e introduce 0: informará
ErrorEjecucion, línea 3, columna 22, división entre cero. Si introduces letras,
el error corresponde a la captura de la línea 2. Las salidas ya producidas
antes de un error de ejecución se conservan; no se revierte el programa.

### Pruebas automáticas e interfaz futura

    python -m unittest discover -p "test_*.py" -v

Las pruebas nuevas cubren entradas válidas e inválidas, operaciones, escapes,
comparaciones, ramas anidadas, alcance, errores numéricos y validación completa
antes de cualquier lectura o salida. Las pruebas semánticas ya no dependen
del archivo de ejercicios editable.

Para una futura interfaz, ejecutar admite las funciones entrada(prompt) y
salida(texto). Esto permitirá conectar diálogos de captura y un panel de salida
sin cambiar las reglas del lenguaje. La interfaz todavía no está implementada.

## Paso 5: interfaz gráfica de escritorio

Abre una terminal en costenol y ejecuta:

    python interfaz.py

En Windows también puedes usar `py interfaz.py` si ese es tu lanzador habitual.
Requiere Python 3.10+ con Tcl/Tk instalado; no necesita paquetes de pip.
Si aparece un error de tkinter/Tcl/Tk, revisa la instalación de Python y su
componente Tcl/Tk. `python -m tkinter` permite comprobar que abre una ventana.

### Uso

- Nuevo, Abrir, Guardar y Guardar como trabajan con archivos .pqek en UTF-8.
- Al reemplazar o cerrar un documento modificado se pregunta si deseas guardarlo.
- F5 / Analizar valida léxico, sintaxis y semántica sin ejecutar capturas.
- F6 / Ejecutar valida primero y ejecuta el contenido actual del editor,
  aunque todavía no lo hayas guardado.
- Captura abre un diálogo. Cancelar detiene la ejecución y muestra su ubicación.
- El panel Resultados muestra mensajes, datos introducidos y errores.
- Los errores del lenguaje incluyen su categoría, línea y columna; la línea
  se resalta y el cursor se coloca en la columna indicada.
- Corregir el código quita el resaltado; analiza de nuevo para revisar el cambio.
- Ctrl+N crea un documento, Ctrl+O abre y Ctrl+S guarda.
- Tab inserta cuatro espacios. Hay números de línea y barras de desplazamiento.

Prueba abriendo ejemplos/ejemplo_ejecucion.pqek, pulsa F5 y luego F6. Introduce Ana,
20, 12,5 y Verdadero. Para probar un error, escribe `edad Entero; edad="Hola";`
y pulsa F5. Para un error de ejecución usa `Mensaje.Texto(1/0);` y pulsa F6.

### Implementación y límites

interfaz.py reutiliza analizar_semantica y ejecutar. La ventana usa diálogos
para entrada y un panel para salida. Los botones y el editor se bloquean durante
el procesamiento para evitar ejecutar o cambiar el documento simultáneamente.
Se informa el primer error. No hay resaltado de sintaxis, depurador ni botón
Detener. El procesamiento es síncrono y está pensado para programas educativos
cortos; documentos muy grandes pueden mantener la ventana ocupada.

Las pruebas test_interfaz.py crean una ventana oculta y verifican análisis,
errores, resaltado, capturas, cancelación y archivos. Requieren Tcl/Tk funcional;
si no está disponible, aparecen como omitidas (skipped), no como verificadas.
En el entorno de desarrollo no se pudo iniciar Tcl/Tk, por lo que la comprobación
visual de la ventana queda pendiente en la instalación local.


## Actualizaci?n: concatenaci?n y extensi?n .pqek

La extensi?n predeterminada es ahora .pqek. La interfaz abre .pqek, .cost
mediante el filtro de archivos anteriores y otros textos con Todos los archivos.
Guardar como propone .pqek; Guardar conserva la ruta del documento ya abierto.
Se crearon copias .pqek de los programas .cost existentes sin borrar originales.
Los analizadores de consola leen texto y funcionan con ambas extensiones.

    python interprete.py ejemplos/ejemplo_ejecucion.pqek

El operador + admite Texto + Entero, Entero + Texto, Texto + Real y Real + Texto,
adem?s de Texto + Texto. Usa el formato de salida del lenguaje, con coma decimal.
No se agreg? concatenaci?n con Logico. Las operaciones entre n?meros siguen
siendo aritm?ticas; no cambi? la conversi?n de una asignaci?n directa a Texto.

    Mensaje.Texto("El resultado de la operaci?n es: " + res);

La concatenaci?n se puede asignar a una variable Texto y no solo usar en mensajes.
Los operadores + se agrupan por la izquierda: "Total: " + 2 + 3 produce
"Total: 23". Para sumar primero usa "Total: " + (2 + 3), que produce "Total: 5".
La gu?a PDF anterior refleja las reglas previas a esta actualizaci?n.

## Tema oscuro

La interfaz usa una paleta oscura uniforme en editor, resultados, botones,
números de línea, barras, capturas, confirmaciones y selector de archivos.
La configuración se encuentra en tema.py; las funciones nuevas incluyen docstrings.
Los botones Analizar y Ejecutar tienen acento azul; errores en rosa y éxitos en verde.

Abre con `python interfaz.py`. Reinicia una ventana ya abierta para aplicar el cambio.
El selector oscuro inicia en ejemplos o en la carpeta del documento actual.
Muestra carpetas a la izquierda y archivos a la derecha. Puedes cambiar el filtro
superior por *.pqek, *.cost o * y pulsar Aplicar filtro. Al guardar, si no escribes
extensión se añade .pqek; reemplazar un archivo requiere confirmación.
La barra de título solicita el modo oscuro de Windows cuando es compatible.
Las decoraciones externas dependen del sistema operativo.

Validación del cambio: módulos compilados y 27 pruebas de lógica correctas.
Las tres pruebas gráficas requieren Tcl/Tk funcional; su comprobación visual
sigue pendiente en este entorno.

## Selector de tema claro y oscuro

La cabecera incluye un selector Tema con las opciones Oscuro y Claro.
El cambio es inmediato y conserva el código, resultados y cambios sin guardar.
También afecta a las capturas, confirmaciones y selectores de archivos que se
abran después. El tema inicial sigue siendo Oscuro; no se guarda la preferencia
entre sesiones. La barra de título depende del soporte del sistema operativo.
Las paletas se definen en PALETAS dentro de tema.py. cambiar_tema en interfaz.py
actualiza los widgets existentes sin reconstruir el documento.

## Logo de la aplicación

La cabecera y el icono de ventana usan logo/image.png. La función cargar_logo
conserva la proporción y reduce la imagen al mostrarla, sin alterar el original.
La ruta se resuelve desde interfaz.py para funcionar desde cualquier carpeta.
Si no se puede leer el logo, se muestra el nombre Costeñol como alternativa.
La imagen conserva su fondo original tanto en tema claro como oscuro.

## Logos según el tema

La cabecera utiliza Logo costeñol con fondo transparente.png para el tema Claro,
y Logo costeñol blanco sobre fondo transparente.png para el tema Oscuro.
Cambiar de tema actualiza el logo inmediatamente, conservando sus proporciones.
El icono de ventana y los nuevos diálogos usan únicamente el isotipo
Puente, sol y ondas_ isotipo costero.png, sin letras y sin cambiar con el tema.
Los recursos originales se conservan en logo/. cargar_logo carga las variantes;
actualizar_logo selecciona la apropiada. Si falta una variante, se muestra el
nombre Costeñol como alternativa para ese tema.
