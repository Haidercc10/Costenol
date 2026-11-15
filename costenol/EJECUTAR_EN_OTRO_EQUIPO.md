# Código fuente de Costeñol: ejecución en otro equipo

Requisitos: Windows con Python 3.10 o posterior y el componente Tcl/Tk.
La ejecución normal no requiere instalar paquetes de pip ni disponer de VS Code.

1. Extrae toda la carpeta costenol.
2. Abre una terminal en esa carpeta.
3. Comprueba Tkinter con `python -m tkinter`.
4. Inicia con `python interfaz.py` (o `py interfaz.py`).

Los logos deben permanecer en logo y los programas en ejemplos.
También puedes probar por consola:

    python interprete.py ejemplos/ejemplo_ejecucion.pqek

Pruebas automatizadas:

    python -m unittest discover -s tests -p "test_*.py" -v

Si no aparece la ventana de tkinter, repara o instala el componente Tcl/Tk de
Python. La interfaz necesita un escritorio gráfico. No requiere red para operar.

El paquete portable Costenol_Windows_x64.zip evita instalar Python en el equipo
receptor. Para reconstruir ese ejecutable consulta empaquetado/README.md.

La documentación PDF de docs corresponde a versiones anteriores del proyecto;
README.md y las docstrings describen también las actualizaciones posteriores.
