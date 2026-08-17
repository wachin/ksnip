# GitHub Actions de ksnip_py

## Qué comprueban los workflows

Los tres workflows fueron migrados del proyecto C++ original al port PyQt6.
Aunque los comandos se ejecutan desde la raíz del repositorio —porque allí se
encuentran `pyproject.toml` y `tests_py/`— todos ellos instalan y comprueban el
paquete Python `ksnip_py/`.

| Workflow | Sistema | Trabajo automático |
| --- | --- | --- |
| `linux.yml` | Ubuntu Linux | Compilación de bytecode, pruebas de `tests_py/` y comprobación del comando |
| `windows.yml` | Windows | Las mismas comprobaciones sobre Windows |
| `macos.yml` | macOS | Las mismas comprobaciones sobre macOS |

Los trabajos automáticos se ejecutan con Python 3.13, PyQt6 instalado desde las
dependencias declaradas en `pyproject.toml` y Qt en modo `offscreen`, para que
las pruebas gráficas no necesiten un monitor físico.

Ya no se llaman CMake, GoogleTest, Qt 5, `src/`, `kColorPicker`,
`kImageAnnotator` ni los scripts históricos que empaquetaban el ksnip C++.

## Qué ocurre al hacer push

Estos comandos ejecutan las pruebas en Linux, Windows y macOS, pero no crean
artefactos de distribución:

```bash
git add .
git commit
git push
```

Esto permite detectar regresiones del port sin crear paquetes en cada commit.

## Crear manualmente distribuciones Python

1. Abra el repositorio en GitHub.
2. Entre en **Actions**.
3. Elija **Linux - ksnip_py**, **Windows - ksnip_py** o
   **macOS - ksnip_py**.
4. Pulse **Run workflow**.
5. Seleccione la rama, normalmente `master`, y confirme.
6. Espere a que terminen las pruebas y el trabajo `package-python`.
7. Abra la ejecución y descargue su artefacto desde **Artifacts**.

Linux crea el `wheel` y la distribución fuente (`sdist`). Windows y macOS
vuelven a construir el `wheel` en su plataforma para comprobar que el paquete
se puede generar correctamente allí. Como el proyecto contiene Python puro,
el wheel resultante es independiente de la plataforma; PyQt6 instala después
los componentes Qt apropiados para cada sistema.

Los artefactos se llaman:

```text
ksnip-pyqt6-python-distributions
ksnip-pyqt6-wheel-windows
ksnip-pyqt6-wheel-macos
```

Estos artefactos no se publican automáticamente en una release.

## Ejecutarlos con GitHub CLI

Después de autenticar `gh`, se puede iniciar cada comprobación manual:

```bash
gh auth status
gh workflow run linux.yml --ref master
gh workflow run windows.yml --ref master
gh workflow run macos.yml --ref master
```

Para consultar, seguir y descargar una ejecución:

```bash
gh run list --limit 10
gh run watch ID_DE_LA_EJECUCIÓN
gh run download ID_DE_LA_EJECUCIÓN
```

## Alcance actual del empaquetado

Los artefactos actuales son distribuciones Python válidas de `ksnip_py`, no
instaladores autónomos. La creación de DEB, AppImage, RPM, EXE/MSI o DMG para
el port requiere recetas específicas adicionales y debe implementarse y
probarse por separado. Los antiguos scripts C++ se conservan temporalmente
como referencia, pero ninguno de estos tres workflows los ejecuta.
