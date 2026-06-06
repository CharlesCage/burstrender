# -*- mode: python ; coding: utf-8 -*-
# Two executables (CLI console app + windowed GUI) sharing one one-dir bundle.
# Build:  pyinstaller build/burstrender.spec --distpath dist --workpath build/pyinstaller-work
# Vendored binaries must exist at build/vendor/bin (run build/fetch_binaries.py first).

from pathlib import Path

repo = Path(SPECPATH).parent

cli_a = Analysis(
    [str(repo / "burstrender.py")],
    pathex=[str(repo)],
    datas=[(str(repo / "config.yaml"), ".")],
    hiddenimports=[],
    noarchive=False,
)
gui_a = Analysis(
    [str(repo / "burstrender_gui.py")],
    pathex=[str(repo)],
    datas=[],
    hiddenimports=[],
    noarchive=False,
)

MERGE((cli_a, "burstrender", "burstrender"), (gui_a, "burstrender-gui", "burstrender-gui"))

cli_pyz = PYZ(cli_a.pure)
gui_pyz = PYZ(gui_a.pure)

cli_exe = EXE(
    cli_pyz,
    cli_a.scripts,
    [],
    exclude_binaries=True,
    name="burstrender",
    console=True,
)
gui_exe = EXE(
    gui_pyz,
    gui_a.scripts,
    [],
    exclude_binaries=True,
    name="burstrender-gui",
    console=False,
)

coll = COLLECT(
    cli_exe, cli_a.binaries, cli_a.datas,
    gui_exe, gui_a.binaries, gui_a.datas,
    Tree(str(repo / "build" / "vendor" / "bin"), prefix="bin"),
    name="burstrender",
)
