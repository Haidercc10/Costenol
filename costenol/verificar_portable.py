"""Comprobación reproducible del paquete portable sin interacción manual."""
import json
from pathlib import Path
import tkinter as tk
from interprete import ejecutar
from recursos import carpeta_ejemplos, identidad_windows, icono_ventana, configurar_tk_portable


def verificar(aplicacion, destino):
    """Construye una ventana real oculta y comprueba recursos, editor e intérprete.
    Escribe un informe JSON y devuelve un código de salida; no reemplaza la prueba en otro equipo.
    """
    root = None
    informe = {'resultado': 'ERROR', 'comprobaciones': {}}
    try:
        configurar_tk_portable()
        identidad_windows()
        root = tk.Tk()
        root.withdraw()
        icono_ventana(root)
        app = aplicacion(root)
        root.update_idletasks()
        checks = informe['comprobaciones']
        checks['tkinter'] = True
        checks['logos_claro_oscuro'] = set(app.logos_cabecera) == {'Claro', 'Oscuro'}
        checks['icono_isotipo'] = app.logo_icono is not None
        checks['icono_exe_disponible'] = (Path(__file__).parent/'logo'/'costenol.ico').is_file()
        checks['ejemplos_editables'] = (carpeta_ejemplos()/'ejemplo_ejecucion.pqek').is_file()
        for tema in ['Claro', 'Oscuro']:
            app.tema.set(tema)
            app.cambiar_tema()
        checks['cambio_tema'] = True
        primera = app.activa
        app.nueva_pestana('n Entero; n=1;')
        app.pestanas.select(primera)
        app.cambiar_documento()
        checks['pestanas'] = len(app.documentos) == 2
        salida = []
        datos = iter(['7','5'])
        ejecutar('a Entero; b Entero; a=Captura.Entero(); b=Captura.Entero(); '
                 'Si (a+b>=10) Mensaje.Texto("Total: " + (a+b)); Sino Mensaje.Texto("Menor"); FinSi',
                 entrada=lambda p: next(datos), salida=salida.append)
        checks['captura_operacion_condicion_concatenacion'] = salida == ['Total: 12']
        app.revision.detener()
        informe['resultado'] = 'OK' if all(checks.values()) else 'ERROR'
    except Exception as error:
        informe['error'] = f'{type(error).__name__}: {error}'
        # Datos del arranque para diagnosticar fallos en otro equipo, sin recoger información personal.
        import os
        informe['rutas_tk'] = {clave: os.environ.get(clave, '') for clave in ('TCL_LIBRARY', 'TK_LIBRARY')}
        try:
            import ctypes
            biblioteca = ctypes.CDLL('tcl86t.dll')
            biblioteca.Tcl_CreateInterp.restype = ctypes.c_void_p
            biblioteca.Tcl_Eval.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            biblioteca.Tcl_GetStringResult.argtypes = [ctypes.c_void_p]
            biblioteca.Tcl_GetStringResult.restype = ctypes.c_char_p
            biblioteca.Tcl_DeleteInterp.argtypes = [ctypes.c_void_p]
            interprete = biblioteca.Tcl_CreateInterp()
            pruebas = ['pwd', 'info patchlevel',
                       'set tcl_library {' + os.environ.get('TCL_LIBRARY', '') + '}; source [file join $tcl_library init.tcl]']
            informe['diagnostico_tcl'] = []
            for prueba in pruebas:
                estado = biblioteca.Tcl_Eval(interprete, prueba.encode('utf-8'))
                informe['diagnostico_tcl'].append({'estado': estado,
                    'detalle': biblioteca.Tcl_GetStringResult(interprete).decode('utf-8', errors='replace')})
            biblioteca.Tcl_DeleteInterp(interprete)
        except Exception:
            pass
    finally:
        if root is not None:
            root.destroy()
        Path(destino).write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if informe['resultado'] == 'OK' else 1
