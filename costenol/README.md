# Costeñol: paso 1

Requiere Python 3.10 o posterior. No necesita paquetes externos.
Abre esta carpeta en VS Code y ejecuta en su terminal:

    python lexer.py ejemplo.cost

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

    python parser.py ejemplo_sintactico.cost
    python parser.py ejemplo_sintactico.cost --arbol
    python -m unittest test_parser.py -v

El primer comando valida; el segundo también muestra el árbol sintáctico (AST)
en JSON; el tercero ejecuta las pruebas automáticas. El lexer sigue disponible
con su comando original. No se modificó ejemplo.cost para conservar tus ejercicios.

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

Crea un archivo prueba_error.cost con un solo ejemplo a la vez y ejecuta:

    python parser.py prueba_error.cost

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

    python semantico.py ejemplo_semantico.cost
    python semantico.py ejemplo_semantico.cost --simbolos
    python semantico.py error_semantico.cost
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

    python interprete.py ejemplo_ejecucion.cost

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

Crea prueba_ejecucion.cost con:

    divisor Entero;
    divisor = Captura.Entero();
    Mensaje.Texto(10 / divisor);

Ejecuta `python interprete.py prueba_ejecucion.cost` e introduce 0: informará
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
