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
