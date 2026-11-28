# Handoff: trabajo hecho en Windows (2026-11-27) → continuar en Linux

Este documento resume **todo** lo que se cambió en esta máquina Windows y lo que
un agente (DeepSeek Harness) necesita saber para continuar el desarrollo en
Linux sin repetir el diagnóstico. Está escrito para leerse de principio a fin
una vez, y luego consultar secciones sueltas.

| Dato | Valor |
| --- | --- |
| Repositorio | `wachin/ksnip` (fork ksnip C++ → Python/PyQt6) |
| Rama | `master` |
| Último commit | `1afed43c` (fix de menús) |
| Versión del paquete | `ksnip-pyqt6 0.2.2` |
| Submódulo | `libs/pyqt6-linguistic-tools` en `b513634` = **v1.1.0** |
| Otros repos tocados | `wachin/pyqt6-linguistic-tools` (créditos, About, icono, PEP 639) |

## 1. Dejar el repo listo en Linux

```bash
git clone https://github.com/wachin/ksnip.git
cd ksnip

# Obligatorio: el submódulo trae dos motores anidados.
git submodule update --init --recursive

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .               # aplicación y PyQt6
python -m pip install pytest             # el CI usa `python -m pytest tests_py`
# Solo para trabajar en OCR (PaddlePaddle, ~2 GB de ruedas):
# python -m pip install -e ".[ocr]"

python -m ksnip_py --smoke-test          # debe salir con código 0
python -m pytest tests_py -q             # ver la sección 8 sobre fallos esperados
```

Comprobaciones rápidas:

```bash
python -c "import ksnip_py.linguistics as l; print(l.toolkit_supported_platform())"   # False en Linux
python -c "import ksnip_py.spellcheck as s; print(s.shared_spell_checker().backend_name())"
# -> "hunspell" si el paquete hunspell y sus diccionarios están instalados, "none" si no
```

## 2. Qué se hizo, por área

### 2.1 Gestor de modelos OCR (`ksnip_py/download_manager.py`)

El diagnóstico de partida: en Windows el modelo "PaddleOCR Structure
(PP-StructureV3)" decía "Falló la instalación" sin ningún motivo, y la tarjeta
anunciaba 300 MB cuando la descarga real es ~1,8 GB.

Cambios:

- `_run_pip()` ejecuta pip capturando salida con `encoding="utf-8"`,
  `errors="replace"`, guarda el final de la salida y la escribe en el log.
- `_fail()` registra el motivo real; la tarjeta muestra
  `✗ Falló la instalación: <motivo>` y aparece un botón **Mostrar log**
  (`_on_show_log_clicked`) que abre
  `<appdata>/ksnip-pyqt6/logs/model-manager.log`
  (en Windows `%LOCALAPPDATA%\ksnip-pyqt6\logs\model-manager.log`).
- `DownloadWorker` ya no emite el texto del error como si fuera el id del modelo
  (`finished.emit(False, self._model.id)`), y comparte `self._errors` con la
  tarjeta.
- `_structure_kwargs()` usa **los mismos modelos que
  `OcrBackend._recognize_with_pp_structure`** (`PP-DocLayout_plus-L`,
  `PP-OCRv5_mobile_det/rec`, `SLANeXt_wired`, `SLANet_plus`,
  `RT-DETR-L_*_table_cell_det`), para no cachear dos juegos distintos.
- Tamaños corregidos: estructura ~1800 MB, fórmulas ~700 MB.
- La tarjeta de diccionarios Hunspell **se eliminó** del Gestor de modelos
  (ver 2.2).

Documentación: `docs/WINDOWS_OCR_SETUP.md` §9 (tamaños reales, que la barra no
se mueve durante la descarga, que el caché se reutiliza, y dónde está el log).

### 2.2 Corrección ortográfica (`ksnip_py/linguistics.py`, `spellcheck.py`)

Antes: `HunspellSpellChecker` invocaba el **programa** `hunspell`; en Windows no
existe, así que la corrección nunca funcionó allí.

Ahora hay dos backends y el puente decide:

- `ksnip_py/linguistics.py` (nuevo, ~300 líneas): localiza el submódulo
  `libs/pyqt6-linguistic-tools`, lo pone en `sys.path` con su bootstrap,
  crea un `LinguisticService` compartido (`create_service(namespace="ksnip-pyqt6")`),
  resuelve el locale del diccionario y expone `toolkit_available()`,
  `toolkit_error()`, `dictionary_storage_directory()`,
  `resolve_spellcheck_locale()`, `preferred_languages()`, `spelling_summary()`
  e `install_toolkit_translations()`.
- **Regla de plataforma, deliberada**: `TOOLKIT_PLATFORMS = ("win32",)`. El
  toolkit se usa **solo en Windows**; en Linux y macOS se ignora aunque el
  submódulo esté presente, y se usa `hunspell` del sistema. La comprobación
  ocurre **antes de importar** nada del toolkit.
- `ksnip_py/spellcheck.py`: `HunspellSpellChecker` pasó a `SpellChecker`, con
  selección de backend en `refresh()`:
  1. si el toolkit está disponible y hay diccionario con ortografía → `toolkit`;
  2. si no, `hunspell` del sistema;
  3. si no, `none` (silencioso: nunca marca palabras como mal escritas).
  Se conserva toda la interfaz de UI: `SpellResult`, el esquema de colores, el
  subrayado con contraste calculado y el menú contextual con hasta 8
  sugerencias.
- Nuevos helpers de módulo: `shared_spell_checker()` (singleton) y
  `reset_spell_checking()` (reconstruye el servicio y repinta los editores
  abiertos).
- Resolución de locale (`linguistics.resolve_spellcheck_locale`): coincidencia
  exacta (`es_EC`), luego otra variante del mismo idioma (`es_ES`), luego
  cualquier locale **con ortografía**. Un bundle solo-tesauro nunca tapa a uno
  de ortografía. `QLocale.system().name()` es la primera fuente del locale, y
  `locale.getdefaultlocale()` solo se usa como último recurso (está obsoleto).
- UI: `Opciones → Dictionary Download Manager…` (nuevo `dictionaries_action` en
  `main_window.py`) abre el `DictionaryDownloadManagerDialog` del toolkit con el
  catálogo de 57 idiomas. Al cerrar el diálogo se llama a
  `reset_spell_checking()`, así el diccionario recién instalado funciona sin
  reiniciar. La acción se deshabilita fuera de Windows con un tooltip que lo
  explica.
- `app.py` instala las traducciones propias del toolkit en el arranque
  (`install_toolkit_translations(app, configured_language)`).

Documentación: `docs/SPELLCHECK.md` (backends, ubicaciones, selección de idioma,
límites, notas para empaquetadores).

### 2.3 Submódulo `libs/pyqt6-linguistic-tools`

Se añadió como submódulo (con `spylls` y `pythes` anidados) y se subió a
**v1.1.0**. En ese repositorio se hizo:

- `about.py`: fuente única de créditos (nombre, correo, web, licencia, resumen y
  descripción) + `about_text_plain()` / `about_text_html()`.
- Botón **About…** en `DictionaryManagerDialog` (`_about_message_box()` y
  `show_about()`), con icono propio.
- Icono del proyecto: `icons/app.svg` + `icons/app-256.png`;
  `qt/icons.py` (`application_icon()`, `application_pixmap()`) lo carga desde
  los **bytes del paquete** (no por ruta) y arma pixmaps de 16 a 256 px.
  El diálogo hace `setWindowIcon(...)`, que es lo que evita que el About herede
  el icono de ksnip.
- `docs/assets/app.ico` multiescala (16, 24, 32, 48, 64, 128, 256) para
  instaladores; `tools/render-app-icon.py` regenera PNG e ICO desde el SVG.
- `pyproject.toml`: autor y mantenedor, `license = "GPL-3.0-only"`,
  `project.license-files`, `setuptools>=77` (PEP 639, sin avisos), URLs.
- Tests: `tests/test_about.py`, `tests/test_icons.py`, y el botón About en
  `tests/test_dictionary_manager.py`.

### 2.4 Menús: atajos duplicados (`ksnip_py/menu_style.py`)

Síntoma reportado: en tema **sistema** (estilo nativo de Windows) los atajos
salían dos veces, desfasados y solapados, y solo con acciones habilitadas.

Causa: `SolidMenu.paintEvent` repintaba **siempre** el atajo de los ítems
habilitados; el estilo nativo no está envuelto por `SolidDisabledMenuStyle` (que
es quien quita la etiqueta del búfer), así que el estilo nativo ya lo había
dibujado.

Arreglo:

- `enabled_shortcut_color(style)` devuelve color solo si el estilo es
  `SolidDisabledMenuStyle` **y** tiene `enabled_color`; en cualquier otro caso
  `SolidMenu` no repinta nada.
- El estilo registra los ítems cuyo búfer no pudo recolorear
  (`_native_shortcut_rects`, `begin_menu_paint()`, `drew_native_shortcut()`),
  para que la ruta de repliegue tampoco duplique.

Pruebas: `tests_py/test_disabled_menu_style.py` (9 en total; 5 nuevas) verifican
la decisión, que con estilo nativo `SolidMenu` renderiza idéntico a un `QMenu`,
que el estilo envuelto sí pinta el atajo, y que el repliegue no duplica.

### 2.5 Licencia

- `LICENSE.txt` se eliminó; queda solo `LICENSE` (GPL-3.0).
- Referencias actualizadas: `pyproject.toml` (`license-files = ["LICENSE"]`),
  `.github/workflows/build.yml` (`Copy-Item "LICENSE"`) y `README.md`
  (badge y sección License).

### 2.6 Documentación y muestras

- `docs/SPELLCHECK.md` (nuevo).
- `docs/WINDOWS_OCR_SETUP.md` §9 (nuevo).
- `docs/ocr-samples/`: `tabla-ejemplo-ocr.xlsx` (28×8, acentos y símbolos),
  `README.md` con el procedimiento y la precisión medida, la captura de
  LibreOffice, `RESULTADO OCR.md` y las notas del usuario.
- `tools/make_ocr_table_sample.py`: regenera el libro con openpyxl (ojo: openpyxl
  no calcula fórmulas; hay que abrir y guardar una vez en LibreOffice).
- `CHANGELOG.md`: sección **Unreleased** con todo lo anterior.

## 3. Decisiones que no se deben revertir

1. **Toolkit solo en Windows.** No "arreglar" Linux habilitando el toolkit: la
   decisión es explícita y evita un segundo almacén de diccionarios junto al del
   sistema. Si algún día se quiere cambiar, hay que actualizar
   `TOOLKIT_PLATFORMS`, `docs/SPELLCHECK.md` y las pruebas.
2. **La `.deb` no debe incluir `libs/` ni ejecutar pip.** El corte por
   plataforma ocurre antes de importar, así que el paquete funciona sin el
   submódulo usando hunspell.
3. **No volver a poner la tarjeta Hunspell en el Gestor de modelos**; los
   diccionarios se gestionan en el diálogo del toolkit (solo Windows).
4. **No quitar la condición de `SolidMenu`**; sin ella vuelven los atajos
   duplicados en el tema sistema.
5. **`LICENSE` es el único archivo de licencia.**

## 4. Comportamiento esperado por plataforma

| | Windows | Linux |
| --- | --- | --- |
| Backend de ortografía | toolkit (Spylls) + diccionarios descargados | `hunspell` del sistema, siempre |
| `Opciones → Dictionary Download Manager…` | habilitado | **deshabilitado** (tooltip explica) |
| Diccionarios | `%LOCALAPPDATA%\ksnip-pyqt6\dictionaries\{managed,user,personal}` | `/usr/share/hunspell` (paquetes) |
| Temas | `system` usa el estilo nativo | `system` puede usar qt6ct/Kvantum |
| Modelos OCR | `%USERPROFILE%\.paddlex\official_models` | `~/.paddlex/official_models` |

## 5. Pendientes y tareas para Linux

1. **Traducciones** (lo más importante). Hay cadenas nuevas sin traducir:
   - `main_window.py`: `Dictionary Download Manager…`, los dos tooltips de esa
     acción, los mensajes del gestor y el estado `Dictionaries updated`.
   - `download_manager.py`: `Show log`, `Full log`, `Installation log`,
     `Unknown error`, los mensajes de `_fail()` y los de
     `_install_paddle_structure()`.
   - toolkit: `About…`, `Show the project credits and license`,
     `About PyQt6 Linguistic Tools`.
   Procedimiento: `python3 tools/update_pyqt_translations.py` en ksnip y
   `pylupdate6` + `lrelease` según `docs/translations.md` del toolkit. En Windows
   no hay `lrelease`, por eso quedó pendiente.
2. **Empaquetado Debian**: confirmar que `libs/` queda fuera del source package y
   que `dpkg-buildpackage` funciona; probar que sin el submódulo aparece
   `hunspell` como backend.
3. **Créditos visibles en Linux**: el diálogo del toolkit (y con él su About)
   está deshabilitado en Linux, así que los créditos solo se ven en el README y
   el LICENSE. Si se quieren en la app, hace falta otro punto de entrada
   (por ejemplo `Ayuda → Acerca de` con el texto de `about_text_html()`).
4. **macOS**: cae en el fallback `hunspell`, que allí no viene garantizado. Si se
   quiere soportar, es otro caso de `TOOLKIT_PLATFORMS`.
5. **Opcional**: exponer palabras personales/ignoradas del toolkit en el editor,
   menú de tesauro, y hacer traducible el contenido del About.

## 6. Verificación hecha en Windows (evidencia)

- **OCR de tablas**: con la misma captura y los modelos mobile, 52/60 celdas de
  texto equivalentes y 60/60 numéricas; con una imagen de 2.463 px de ancho,
  55/60 y 60/60; ampliando la captura ×2 empeora (48/60); los modelos *server*
  empeoran (44/60, quitan tildes, descolocan filas y tardan ~15 min). Detalle en
  `docs/ocr-samples/README.md`.
- **Ortografía**: `backend=toolkit`, `locale=es_ES`, `hoola → ('hola','hollara')`,
  `canssion → ('cansancio', …)`, y el tesauro (`feliz → bendito, dichoso, …`).
  Se instaló el bundle `dict-es`: 22 variantes `es_*` (es_AR … es_VE, incluida
  es_EC) + `th_es_v2`.
- **Menús**: capturas antes/después con el estilo nativo, y verificación de que
  las pruebas nuevas fallan con el comportamiento anterior.
- **Suites**: `pytest tests_py` → 281 passed y 20 fallos preexistentes de
  plataforma Windows (ver sección 8). Toolkit: 325 passed y 2 fallos
  preexistentes (`test_owned_bundle_removal_refuses_symbolic_links`,
  `test_thesaurus_validator_checks_count_offsets_and_lookup`).
- **Paddle en Python 3.11**: `docs/WINDOWS_OCR_SETUP.md` pide Python 3.12, pero
  en esta máquina `paddlepaddle==3.3.1` + `paddleocr==3.7.0` funcionan con
  **3.11.9**. No es un error de la documentación (3.12 es lo probado), pero no
  hay que "arreglar" un entorno 3.11 que ya funciona.

## 7. Historial de commits

`ksnip` (`master`), del más antiguo al más nuevo:

```text
5fec1987  fix(model-manager): report real failures and fix download sizes
97d48237  feat(spellcheck): use pyqt6-linguistic-tools and add its dictionary manager
04a1c000  docs: add a sample workbook for table OCR
dca50b0f  chore(license): add the GPL-3.0 text at the repository root
771b485d  docs: create the virtual environment with the default Python
56208b27  feat(spellcheck): use the bundled toolkit on Windows only
7a5930c7  chore(deps): update pyqt6-linguistic-tools to 1eb17df
b9b06d5d  chore(license): keep only LICENSE and update its references
06b7ed04  chore(deps): update pyqt6-linguistic-tools to be2aea9
c5a45d11  chore(deps): update pyqt6-linguistic-tools to v1.1.0
1afed43c  fix(menus): stop drawing menu shortcuts twice under the system theme
```

`pyqt6-linguistic-tools` (`main`): `6ca510d` (LICENSE) → `1eb17df` (créditos y
About) → `be2aea9` (icono y PEP 639) → `b513634` (release 1.1.0, tag `v1.1.0`).

## 8. Fallos de tests esperados

`python -m pytest tests_py -q` en Windows da **20 `failed` preexistentes**; con
`python -m unittest discover -s tests_py` son **17 `FAIL` + 3 `ERROR`** (mismo
conjunto, distinto formato). Reparto: `test_color_picker` (10 fallos + 1 error),
`test_capture_cursor` (3), `test_capture_geometry` (2), `test_file_dialogs` (1),
`test_i18n` (1) y `test_ocr_structure` (2 errores). Son de plataforma (QSettings,
geometría, rutas con `\`, traducción de diálogos nativos), **no** regresiones de
este trabajo. En Linux algunos deberían pasar; compara contra esta lista antes de
culpar a un cambio nuevo.

Ojo: `python -m unittest discover -s tests_py` **no** recoge los archivos de
estilo pytest (por ejemplo `test_disabled_menu_style.py`), así que da 269 tests.
El CI usa `pytest`, que sí los recoge.

## 9. Trampas conocidas

- El toolkit se importa por `sys.path` desde `libs/`. En Windows, si falta
  `git submodule update --init --recursive`,
  `linguistics.toolkit_available()` devuelve `False` y la ortografía cae a
  `hunspell`/`none`. En Linux devuelve `False` **a propósito**, aunque el
  submódulo esté completo.
- `QIcon` carga `app-256.png`, no el SVG, para no depender del plugin de
  imágenes SVG de Qt.
- `SpellChecker` cachea resultados por palabra; tras instalar un diccionario hay
  que llamar a `reset_spell_checking()`.
- El locale de ortografía debe ser regional (`es_EC`), no `es`: el bundle
  genérico `es` es solo de tesauro.
- En Windows de esta máquina ksnip está instalado con `pip install -e .` en el
  Python **del sistema** (3.11.9), no en `C:\D\ksnip-Dev\ksnip\.venv`, que está
  vacío. En Linux usa un venv de verdad.

## 10. Mapa de archivos nuevos

```text
AGENT_HANDOFF.md                 este documento (excluido del sdist en MANIFEST.in)
ksnip_py/linguistics.py          puente al toolkit (nuevo)
ksnip_py/spellcheck.py           backend doble (modificado)
ksnip_py/menu_style.py           gate de atajos + repliegue (modificado)
ksnip_py/download_manager.py     errores reales, tamaños, modelos (modificado)
ksnip_py/main_window.py          acción del gestor de diccionarios (modificado)
ksnip_py/app.py                  traducciones del toolkit (modificado)
tests_py/test_linguistics.py     pruebas del puente (nuevo)
docs/SPELLCHECK.md               documentación de ortografía (nuevo)
docs/ocr-samples/                libro de ejemplo + captura + resultados (nuevo)
tools/make_ocr_table_sample.py   generador del libro (nuevo)
libs/pyqt6-linguistic-tools/     submódulo v1.1.0 (nuevo)
```

---

Si algo de este documento no coincide con el código, **manda el código**: las
pruebas y el `CHANGELOG.md` son la referencia; este texto es el contexto de por
qué se hizo así.
