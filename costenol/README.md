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
Los literales lógicos son Verdadero y Falso. Los operadores lógicos compuestos siguen pendientes.

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
    primaria     = NUM_ENTERO | NUM_REAL | CADENA | VERDADERO | FALSO | IDENTIFICADOR
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
- Se admiten los literales Verdadero y Falso; los operadores lógicos compuestos siguen pendientes.
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
- Puedes obtener Logico mediante Verdadero, Falso, comparaciones o Captura.Logico().
  No se han definido operadores lógicos compuestos.

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
En captura se admite Verdadero/Falso sin distinguir mayúsculas. En el código
fuente los literales se escriben exactamente Verdadero y Falso, sin comillas.

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

## Validación estricta de nombres y capturas

No se permite declarar variables cuyo nombre coincida con una palabra reservada,
sin distinguir mayúsculas: entero Entero;, texto Texto; y ENTERO Entero; fallan.
Los nombres entero1 y textoUsuario sí están permitidos. La escritura de comandos
sigue distinguiendo mayúsculas: se escribe Captura.Texto(), no captura.Texto().
Las formas exactas de una reservada ya se rechazan por sintaxis; sus variantes
que parecen identificadores se rechazan en semántica con ubicación.

capturas.py centraliza los formatos para consola e interfaz:
- Texto: solo letras Unicode y espacios, con al menos una letra; no acepta números,
  signos, símbolos ni una entrada vacía. Esto reemplaza la regla anterior que
  permitía cualquier texto o vacío en Captura.Texto(). Las cadenas literales del
  código y la concatenación conservan sus reglas: "Total: " + res sigue siendo válido.
- Entero: dígitos y un signo opcional al principio.
- Real: dígitos, signo opcional y coma decimal opcional.
- Logico: selección Verdadero o Falso; en consola no distingue mayúsculas.

La interfaz bloquea caracteres incompatibles y pegados mediante validación de
edición. Permite borrar y escribir estados parciales como - o 3,, pero no
aceptarlos como dato terminado. Al pulsar Aceptar o Enter se valida el formato
completo; si falla muestra la causa dentro del diálogo y permite corregir.
Cancelar conserva la posibilidad de detener la ejecución. En consola, una
entrada inválida produce ErrorEjecucion con ubicación, como antes.

convertir_captura valida y convierte; permite_edicion valida estados parciales.
Las funciones nuevas están documentadas. Los PDF previos reflejan las reglas
anteriores de captura de Texto y no se han regenerado en esta actualización.

## Sombreado de línea y selección

La línea del cursor tiene un sombreado suave. Si contiene un error, su resaltado
se intensifica al posicionar el cursor en ella. La selección de texto tiene
prioridad sobre ambos fondos y permanece visible al cambiar de foco.
Se actualiza con teclado, clic y arrastre, tanto en tema claro como oscuro.
configurar_resaltado define colores y prioridades; resaltar_linea_actual mueve
las etiquetas sin modificar el código ni la selección del usuario.

## Diagnósticos con identidad costeña

mensajes.py añade una orientación costeña a los errores léxicos, sintácticos,
semánticos, de ejecución y a las capturas inválidas. Conserva la descripción
técnica y la ubicación; la interfaz y la consola reutilizan el mismo mensaje.
Usa expresiones como Eche, Hey, Ajá, bro, compae, vale, Bájale dos y Deja el viaje,
con una indicación concreta para corregir el problema y sin insultos personales.
La selección depende de la causa, sin aleatoriedad. Los errores propagados no
repiten la frase. Las excepciones y reglas de validación siguen siendo las mismas.
Las funciones nuevas están documentadas.

Desde costenol, ejecuta las pruebas organizadas en tests con:

    python -m unittest discover -s tests -p "test_*.py" -v

## Diagnóstico automático mientras escribes

La interfaz analiza el contenido 700 ms después de la última edición. Detecta
escritura, pegado, borrado, deshacer y rehacer, incluso con cambios sin guardar.
Muestra el primer error léxico, sintáctico o semántico con ubicación y mensaje
costeño debajo del editor. Marca la línea sin desplazar ni mover el cursor,
y conserva la selección. Cuando el código es válido o vacío, no muestra nada
en esa zona; tampoco agrega mensajes de éxito automáticos a Resultados.

No ejecuta capturas, cálculos ni instrucciones: los errores de ejecución siguen
requiriendo F6. Las instrucciones aún incompletas pueden dar errores temporales.
F5 y F6 conservan su comportamiento manual y sus mensajes en Resultados.
La revisión automática no borra esos resultados. Se cancelan tareas pendientes
al abrir otro documento, cerrar o iniciar un análisis/ejecución manual.

revision.py contiene RevisionAutomatica (temporización y validación estática)
y EditorObservable (notificación de cambios sin alterar la marca de guardado).
Las funciones nuevas incluyen docstrings. El procesamiento sigue siendo síncrono
y está pensado para ejercicios cortos; no es un analizador incremental por tokens.

## Diagnósticos al lado de la línea con error

La revisión automática y F5/F6 muestran el error junto al final de la línea,
sin insertar texto en el programa. El aviso conserva categoría y orientación
costeña. Si falta espacio, se abrevia visualmente; al pasar el ratón o hacer clic
aparece el detalle completo con línea, columna y explicación en español.
La banda de diagnóstico completa se reserva fuera de los paneles redimensionables
para que no dependa de desplegar Resultados. El mensaje se recoloca al desplazar
o redimensionar el editor y se adapta a Claro/Oscuro. Al corregir se ocultan
el aviso, el globo y la banda. Las funciones nuevas incluyen documentación.

## Bienvenida animada

Al iniciar con python interfaz.py se oculta inmediatamente la ventana raíz.
inicio.py muestra una pantalla oscura con el logo blanco, un movimiento suave
y una barra de actividad animada, sin porcentajes ficticios. Precarga los logos
por turnos y los comparte con el editor; cuando está construido y dibujado se
revela la ventana principal y se retira la bienvenida. El tiempo mínimo de
presentación es 800 ms; no se añade una pausa fija de varios segundos.

Escape cierra la bienvenida y la aplicación. Los recursos que falten no impiden
abrir el editor, que conserva su texto alternativo. Los callbacks de animación
se cancelan al cerrar. Las funciones nuevas están documentadas. La construcción
de widgets sigue en el hilo de Tkinter y puede pausar brevemente la animación;
la bienvenida evita mostrar la ventana principal mientras se prepara.

Las pruebas de ciclo de vida verifican transición, cancelación y limpieza ante
fallos sin escritorio; la apariencia y fluidez requieren revisión local de Tkinter.

## Fluidez de la bienvenida

El arranque actual utiliza InicioIndependiente: la bienvenida tiene su propio
proceso y bucle de Tkinter. La carga del editor ya no bloquea la animación.
La barra se actualiza aproximadamente cada 16 ms y calcula su posición según
el tiempo transcurrido. No se promete una tasa fija, que depende del equipo.
El proceso principal prepara la ventana oculta y avisa al splash cuando está
lista. La bienvenida solo carga su logo visible; no comparte objetos Tk entre
procesos. Si la bienvenida falla, el editor intenta abrir de todas formas.
La apariencia y la fluidez deben comprobarse localmente; las pruebas sin ventana
cubren coordinación, cierre y recuperación del canal. No se añade tiempo mínimo
artificial en este modo independiente.

## Menús, pestañas y switch de tema

La cabecera conserva el logo grande de Costeñol. Encima hay una barra de menús
Archivo, Editar, Selección, Ver, Ejecutar y Ayuda. Solo se ofrecen acciones
implementadas; no hay terminal integrado ni extensiones de VS Code.
El interruptor de tema alterna Claro/Oscuro con clic, Espacio o Enter. Su indicador
se anima y adapta la paleta de los archivos abiertos y de los nuevos diálogos.

Nuevo y Abrir crean pestañas sin descartar los documentos existentes. Abrir una
ruta ya abierta selecciona su pestaña. Cada documento conserva editor, cursor,
selección, historial de deshacer, cambios pendientes y resultados. El análisis
automático y F5/F6 se aplican únicamente al documento activo. No ejecuta varios
programas simultáneamente; durante una ejecución no se permite cambiar de archivo.

Ctrl+Tab cambia de pestaña. Ctrl+W, el icono de cierre, el botón central o el botón
Cerrar pestaña cierran el documento activo preguntando por cambios sin guardar.
Al cerrar el último se crea un documento vacío. Salir revisa todos los documentos;
Cancelar interrumpe el cierre sin descartar las pestañas. Guardar conserva la ruta;
Guardar como no permite sobrescribir otra pestaña abierta con la misma ruta.
La sesión de pestañas y el tema no se persisten entre aperturas de la aplicación.
Las funciones nuevas incluyen docstrings. Las pruebas de GUI cubren documentos,
historial, cancelación, rutas duplicadas y switch; requieren Tkinter funcional.

## Palabras reservadas y guardado exclusivo .pqek

Las palabras reservadas con escritura válida (Texto, Entero, Real, Logico,
Captura, Mensaje, Si, Sino, FinSi) se ven azules y en negrita. Se actualizan al
escribir, pegar, cargar y cambiar de tema. No se colorean dentro de cadenas ni
comentarios y no se altera el contenido ni la marca de cambios sin guardar.
resaltado.py reconoce los rangos de forma tolerante a instrucciones incompletas.

Solo se permite guardar programas con extensión .pqek, incluida .PQEK. Si no se
escribe extensión, se añade .pqek; si se escribe .txt, .py, .cost u otra extensión,
se muestra un aviso y se permite corregir. La validación se aplica tanto al
selector como al método de escritura. Abrir otros textos sigue permitido, pero
Guardar solicita una ruta .pqek para no sobrescribir el archivo de otro formato.
archivos.py centraliza esta regla. Las funciones nuevas están documentadas.

## Corrección de enteros extremos al mostrar o concatenar

Interprete.texto_seguro controla ValueError y OverflowError durante la conversión
a texto. Cuando un entero calculado supera el límite decimal de Python, se lanza
ErrorEjecucion con ubicación y mensaje costeño, sin traceback en la consola.
Mensaje.Texto conserva ahora su ubicación en el AST; las concatenaciones señalan
el operador +. No se modifica ni se desactiva el límite global de Python.
Las pruebas cubren salida, concatenación en ambos órdenes, negativos, asignación
Texto, números representables y ejecución real del caso 10 desde consola.
RESULTADOS.md de pruebas_errores fue actualizado con la ejecución de los casos.

## Resaltado completo del código

El editor distingue reservadas (azul y negrita), llamadas Texto(), Entero(),
Real() y Logico() (amarillo/dorado y negrita), cadenas con sus comillas (salmón),
comentarios (verde), números (verde suave), operadores (violeta), signos de
puntuación (neutro) y paréntesis por profundidad (dorado, violeta, azul).
Si (...) mantiene color de reservada, no de función. Las declaraciones como
n Entero; siguen azules; Captura.Entero() destaca Entero en amarillo.

Las tonalidades del tema claro son más oscuras para conservar contraste sobre
blanco. El resaltado se actualiza con la edición y el cambio de tema. No modifica
las reglas ni los archivos; las selecciones y errores conservan prioridad visual.
PALETAS_SINTAXIS centraliza los colores; rangos_sintaxis reconoce categorías
sin colorear como código el interior de cadenas o comentarios.

## Entrega portable Windows x64

Se añadió empaquetado/Costenol.spec y construir.ps1 para reconstruir un portable
con PyInstaller. El exe incluye el isotipo como icono. recursos.py prepara la
identidad de la barra de tareas y localiza ejemplos editables junto al ejecutable.
El arranque llama a multiprocessing.freeze_support() para la bienvenida separada.
verificar_portable.py permite comprobar el paquete con --autoprueba informe.json.
La distribución debe copiarse completa, incluyendo _internal y ejemplos.
La prueba en un segundo equipo real es el paso final de validación de portabilidad.

## Ajustes de entrega: 16 de noviembre de 2026

- Texto + Real ya funcionaba; ahora Texto + Logico y Logico + Texto también
  producen Texto, mostrando Verdadero/Falso. La suma numérica sigue rechazando Logico.
- El icono sin letras consulta SystemUsesLightTheme de Windows: barra clara,
  isotipo oscuro; barra oscura, isotipo claro. Se revisa cada cuatro segundos.
  Es independiente del switch del editor. Los accesos directos anclados pueden
  conservar el icono del archivo según el comportamiento de Windows.
- Abrir admite solo .pqek (también .PQEK), con validación de ruta además del filtro.
  Ya no se abren .cost, .txt ni otros formatos desde la interfaz.
- El switch queda alineado hacia el borde superior de la cabecera y se retiró
  el subtítulo Editor y ejecución de programas, conservando el logo grande.
- El ejemplo inicial empieza con // Saludo inicial //.
- Cancelar una captura es voluntario: detiene el programa y muestra un aviso,
  sin diagnóstico rojo ni resaltado de error. Los datos inválidos siguen validándose.
  EjecucionCancelada distingue esa interrupción; no ejecuta instrucciones posteriores.


## Literales de tipo Logico

Verdadero y Falso son literales nativos del código fuente, sin comillas. El lexer
produce VERDADERO/FALSO; el parser crea nodos Literal; la semántica les asigna
Logico y el intérprete los convierte a bool de Python. No se mezclan con Entero.
Se pueden asignar, comparar, usar como condición y concatenar con Texto.
El resaltado los reconoce automáticamente como palabras reservadas, en azul
sin negrita. No pueden usarse como nombres de variables en ninguna combinación
de mayúsculas. Los literales en expresiones sí distinguen mayúsculas.

    logic Logico;
    logic = Verdadero;
    Mensaje.Texto("Estado: " + logic);
    Si (Falso)
        Mensaje.Texto("No se ejecuta");
    Sino
        Mensaje.Texto("Se ejecuta");
    FinSi

Captura.Logico sigue admitiendo Verdadero/Falso sin distinguir mayúsculas al
introducir un dato. La guía PDF anterior no incluye esta ampliación.
