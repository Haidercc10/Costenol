# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
base = Path(SPECPATH).parent

a = Analysis([str(base/'interfaz.py')], pathex=[str(base)],
             datas=[(str(base/'logo'), 'logo')], binaries=[], hiddenimports=[],
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Costenol', console=False,
          icon=str(base/'logo'/'costenol.ico'), strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Costenol')
