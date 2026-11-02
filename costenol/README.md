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
