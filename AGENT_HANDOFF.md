# Handoff: trabajo hecho en Windows (2026-11-27/28) → continuar en Linux

> **Actualizado:** 2026-11-28. Desde la primera versión de este documento se
> añadieron el botón **Open folder** del Gestor de modelos, la sección de OCR en
> Windows del README, el arreglo de los atajos duplicados en el tema sistema, el
> arreglo del tinte que aplanaba los iconos de menú, el arreglo de la
> herramienta de texto en Windows, los iconos `open`,
> `includeCursor`, `pyqt6_linguistic_tools` y los `wayland` rediseñados, y el
> arreglo del tamaño maximizado al restaurar desde la bandeja en Windows.
> Secciones nuevas o reescritas: 2.4 (final), 2.6, 2.7, **2.8 (nueva)**, **2.9
> (nueva)**, 3 (reglas 6-10), 5 (tareas 7-8), 6, 7, 9 y 10.

Este documento resume **todo** lo que se cambió en esta máquina Windows y lo que
un agente (DeepSeek Harness) necesita saber para continuar el desarrollo en
Linux sin repetir el diagnóstico. Está escrito para leerse de principio a fin
una vez, y luego consultar secciones sueltas.

| Dato | Valor |
| --- | --- |
| Repositorio | `wachin/ksnip` (fork ksnip C++ → Python/PyQt6) |
| Rama | `master` |
| Último commit de código | `02dfb6f0` (herramienta de texto) |
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
- Cada tarjeta instalada muestra un botón **Open folder** junto a *Reinstall*
  (`ModelCard.folder_btn`) que abre la carpeta en el gestor de archivos:
  los tres modelos OCR abren el caché de Paddle
  (`~/.paddlex/official_models`, o `~/.paddleocr` si solo existe el legado) y la
  tarjeta del script externo abre la carpeta del script configurado. La ruta se
  resuelve al pulsar (`ModelInfo.folder`), porque aparece tras instalar.
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

Pruebas: `tests_py/test_disabled_menu_style.py` (10 en total, 6 nuevas) verifican
la decisión, que con estilo nativo `SolidMenu` renderiza idéntico a un `QMenu`,
que el estilo envuelto sí pinta el atajo, que el repliegue no duplica, y que un
icono de color no se aplana dentro de un menú teñido.

**Segundo arreglo (iconos en menús).** El estilo envuelto tiñe los ítems
habilitados de un solo color, y eso incluía el **icono**: todo icono de menú se
veía como una silueta. Con los monocolor no se notaba; con la carpeta ámbar, el
logo, el cursor o el icono del toolkit se veía una mancha negra. Ahora el estilo
deja que el estilo base dibuje los ítems habilitados **que llevan icono** (el
icono conserva su color) y registra ese rectángulo para que `SolidMenu` no
repinte un segundo atajo. Los ítems sin icono mantienen el tinte del texto y el
atajo repintado.

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
- `README.md` (commit `4b7f86d9`): sección **OCR on Windows (works from source)**
  con los pasos del Model Manager, backends, caché y tabla de versiones
  verificadas; corrección ortográfica con el Dictionary Download Manager; tabla
  del Model Manager con los tamaños reales y sin la fila de Hunspell; Python 3.11
  o 3.12 (no 3.13); nota de que el build empaquetado no trae OCR ni ortografía;
  layout del proyecto, tabla de documentación y aviso de los fallos de test
  conocidos en Windows.
- `docs/WINDOWS_OCR_SETUP.md`: acepta 3.11 o 3.12, comandos de venv corregidos,
  espacio en disco ~5 GB y aviso que redirige al Model Manager si se trabaja
  desde fuentes.
- `CHANGELOG.md`: sección **Unreleased** con todo lo anterior.

### 2.7 Iconos de acción (`ksnip_py/icons/`, `menu_style.py`)

Contexto: los iconos son SVG por tema en `icons/light` (glifos `#4d4d4d`) e
`icons/dark` (glifos `#e6e6e6`), cargados con `_load_icon(nombre)`, que además
registra el nombre para recargarlos al cambiar de tema.

- **Abrir** usaba el icono estándar de Qt (`SP_DialogOpenButton`) teñido de un
  color, así que en el tema claro salía como una mancha negra. Ahora hay
  `open.svg` en ambos temas (página con esquina doblada, sol y montaña) y la
  acción usa `_themed_icon("document-open", "open")`.
- **Incluir el ratón en el cursor** no tenía icono: se añadió `includeCursor.svg`
  (marco de captura con el puntero dentro) en ambos temas.
- **Dictionary Download Manager…** usa `pyqt6_linguistic_tools.svg`, basado en el
  icono del toolkit y redibujado con el estilo del juego (burbuja monocroma con
  el subrayado rojo), en versión clara y oscura.
- **`_icon_tint_colors()`** devuelve `None` como color habilitado: los iconos
  habilitados conservan sus colores y solo el estado deshabilitado se tiñe. Antes
  el tema claro convertía en silueta los iconos de sistema (Imprimir, Vista
  previa, Salir).
- `icons/*/wayland.svg`: el usuario los redibujó fusionando disco y W en **un
  solo path** por tema. No hay que volver a tocarlos.
- `tools/render_icon_sheets.py` dibuja una hoja por tema con todos los SVG al
  tamaño de la barra, para revisar iconos nuevos o editados.
- `tests_py/test_app_icons.py` comprueba que ambos temas tienen **el mismo juego
  de nombres**, que cada SVG dibuja algo y que los iconos habilitados no se
  tiñen; `test_disabled_menu_style.py` añade la prueba de píxeles del icono de
  color dentro de un menú.

### 2.8 Ventana, bandeja y geometría (`ksnip_py/main_window.py`)

Síntoma en Windows: tras minimizar o cerrar a la bandeja, al restaurar desde el
icono la ventana volvía **maximizada pero en un recuadro pequeño**, y la opción
**Recordar tamaño y posición de la ventana de captura** no se guardaba. En Linux
no se reproducía.

Tres causas y sus arreglos:

- `show_from_tray()` llamaba `showNormal()` siempre, y en Windows ocultar la
  ventana pierde el estado maximizado, así que volvía al tamaño normal. Ahora
  `hide_to_tray()` guarda `_tray_restore_state` (maximizado/pantalla completa) y
  `show_from_tray()` reaplica `showMaximized()` / `showFullScreen()` /
  `showNormal()` según ese estado.
- `changeEvent()` ocultaba a la bandeja **durante** el minimizado nativo; Windows
  volvía a mapear la ventana. Ahora el ocultado se difiere un turno del bucle de
  eventos (`_hide_to_tray_when_settled`) y solo actúa si sigue minimizada.
- Cerrar o minimizar a la bandeja sale por `closeEvent()` sin llegar a
  `_save_ui_settings()`, así que `window/capture_geometry` nunca se escribía.
  `hide_to_tray()` llama ahora a `_persist_capture_geometry()` antes de `hide()`.

Pruebas (`tests_py/test_capture_geometry.py`, 10 en total): usan un `QSettings`
INI temporal inyectado en la ventana (sin él, Qt da `AccessError` y descarta las
escrituras, que es por lo que estas pruebas fallaban en Windows), cubren la
restauración del maximizado, la ventana normal, el envío a la bandeja al
minimizar y el guardado de la geometría al ocultar.

### 2.9 Herramienta de texto (`ksnip_py/canvas.py`)

Síntoma en Windows: la herramienta **Texto (T)** "no hacía nada". Al arrastrar
sobre la imagen aparecía el editor un instante y desaparecía sin dejar texto.

Causa: `InlineTextEditor.focusOutEvent()` aceptaba la edición ante cualquier
pérdida de foco. En Windows, justo después del clic que crea el editor, la ventana
se reactiva y el foco vuelve al **botón de la barra**, así que llegaba un
`focusOut` con `ActiveWindowFocusReason`; aceptar un texto nuevo y vacío lo
elimina (`_finish_inline_text_edit`, rama `is_new` + texto vacío → `del`).

Arreglo: si el motivo es `ActiveWindowFocusReason` y el editor está vacío, se
ignora la pérdida de foco y se vuelve a pedir el foco en el siguiente turno
(`QTimer.singleShot(0, self.setFocus)`). Los demás motivos no cambian: clic en
otro widget (`MouseFocusReason`) cierra y acepta, y un popup (menú de ortografía)
no cierra.

Uso verificado: arrastrar crea el texto; doble clic con la herramienta de
selección sobre un texto lo abre con todo seleccionado; `Ctrl+Enter` acepta y
`Esc` cancela; el texto aparece en la imagen compuesta.

Pruebas: `tests_py/test_text_editor.py` (6) cubren los cuatro motivos de foco y
la creación por arrastre y por clic; la del editor vacío **falla** con el código
anterior.

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
6. **No reintroducir el tinte del ítem completo en menús.** Si se tiñen ítems con
   icono, los iconos de color (carpeta, logo, cursor, toolkit) vuelven a verse
   como siluetas negras. El estilo debe dejar esos ítems al estilo base.
7. **Los dos temas deben tener el mismo juego de iconos**, con el mismo nombre de
   archivo; `tests_py/test_app_icons.py` lo verifica. Un icono nuevo va en
   `light/` **y** `dark/`.
8. **No tocar `icons/*/wayland.svg`**: el diseño actual (un solo path por tema)
   es deliberado del autor.
9. **Restaurar desde la bandeja respeta el estado guardado.** No volver a llamar
   `showNormal()` sin condición en `show_from_tray()`: en Windows pierde el
   maximizado. El estado se captura en `hide_to_tray()`.
10. **Todo lo que abre a la bandeja debe persistir antes de `hide()`.** Cerrar y
    minimizar a la bandeja no pasan por `closeEvent()`, así que
    `_save_ui_settings()` no se ejecuta; `hide_to_tray()` guarda la geometría.
11. **No quitar la excepción de `ActiveWindowFocusReason`** en
    `InlineTextEditor.focusOutEvent()`: sin ella el editor de texto se cierra solo
    en Windows y la herramienta parece rota.

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
     `Unknown error`, `Open folder`, su tooltip, `Open model folder` /
     `The folder does not exist yet: %1`, los mensajes de `_fail()` y los de
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
6. **Empaquetar el toolkit en el build de Windows (Nuitka)**: hoy
   `packaging/scripts/build-windows-portable.ps1` no incluye `libs/`, así que el
   `.exe` instalado no tiene corrección ortográfica ni gestor de diccionarios
   (solo el checkout de fuentes). Añadir `libs/pyqt6-linguistic-tools` con
   `--include-data-dir` (y comprobar que `linguistics.repository_root()` lo
   encuentra en el standalone) cerraría ese hueco. Está anotado como *known gap*
   en el README.
7. **Iconos pendientes**: `Usar puntero de flecha` (en el mismo submenú de
   captura) sigue sin icono; encajaría `captureCursor`. Además quedan iconos con
   varios elementos sin fusionar (ver la auditoría de la sesión:
   `copy`, `crop`, `delete`, `redo`, `undo`, `lastRect`, `fullScreen`, `saveAs`,
   `model_manager`, `currentScreen`, `drawRect`, `open`, `panels`,
   `uploadCloud`, `windowUnderCursor`, `activeWindow`, `clock`). Fusionar los que
   son solo rellenos es trivial; los que tienen trazos requieren
   *Trazo a trazado* primero.
8. **Colores de iconos inconsistentes en el tema claro**: `model_manager` usa
   `#000000` y `panels`/`settings`/`uploadCloud` usan `#2f2f2f`, mientras el
   resto usa `#4d4d4d`. Unificarlos es cosmético y de bajo riesgo.

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
- **Iconos**: capturas de `Archivo`, `Archivo → Nueva captura` y `Opciones` en
  ambos temas; el icono del toolkit y el del cursor conservan su color dentro del
  menú, y los atajos siguen apareciendo una sola vez. Se comprobó que la prueba
  del icono de color **falla** con el código anterior.
- **Ventana y bandeja**: flujo real en Windows (ventana maximizada 1366×705 →
  minimizar a la bandeja → restaurar) comprobado antes y después del arreglo:
  antes la ventana no se ocultaba y volvía a 716×467; ahora se oculta y vuelve
  maximizada a 1366×705, y la geometría queda en `window/capture_geometry`.
  También se verificó que las pruebas nuevas **fallan** con el código anterior.
- **Texto**: en Windows, arrastrar con la herramienta Texto abre el editor y
  guarda el texto; el doble clic sobre un texto lo edita con todo seleccionado;
  `Ctrl+Enter` acepta y `Esc` cancela; el texto aparece en la imagen compuesta
  (3.513 píxeles oscuros en la zona).
- **Suites**: `pytest tests_py` → **304 passed** y 18 fallos preexistentes de
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
45f7dc9f  docs: add a handoff note for continuing development on Linux
898f345a  feat(model-manager): let each installed model card open its model folder
4b7f86d9  docs: document Windows OCR and spell checking in the README
326e9d2a  fix(icons): give Open its own icon and stop flattening enabled icons
5f14cd4b  feat(icons): add the cursor and dictionary icons, keep menu icons coloured
79d63ae6  chore(icons): finalise the Wayland and linguistic toolkit icons
b3e9305f  fix(window): restore a maximized window from the tray and persist geometry
02dfb6f0  fix(canvas): keep the inline text editor open on Windows
```

Los commits posteriores a `45f7dc9f` (el handoff original) no están descritos en
detalle allí: leer esta actualización y `CHANGELOG.md`.

`pyqt6-linguistic-tools` (`main`): `6ca510d` (LICENSE) → `1eb17df` (créditos y
About) → `be2aea9` (icono y PEP 639) → `b513634` (release 1.1.0, tag `v1.1.0`).

## 8. Fallos de tests esperados

`python -m pytest tests_py -q` en Windows da **18 `failed` preexistentes**; con
`python -m unittest discover -s tests_py` son **15 `FAIL` + 3 `ERROR`** (mismo
conjunto, distinto formato). Reparto: `test_color_picker` (10 fallos + 1 error),
`test_capture_cursor` (3), `test_file_dialogs` (1), `test_i18n` (1) y
`test_ocr_structure` (2 errores). Son de plataforma (QSettings, geometría,
rutas con `\`, traducción de diálogos nativos), **no** regresiones de este
trabajo. En Linux algunos deberían pasar; compara contra esta lista antes de
culpar a un cambio nuevo.

`test_capture_geometry` **sí pasa** desde `b3e9305f`: sus dos fallos venían de
crear `QSettings` sin nombre de organización, que Qt deja en `AccessError` y
descarta en silencio. Las pruebas usan ahora un INI temporal.

Ojo: `python -m unittest discover -s tests_py` **no** recoge los archivos de
estilo pytest (por ejemplo `test_disabled_menu_style.py` o
`test_app_icons.py`), así que da 269 tests. El CI usa `pytest`, que sí los
recoge.

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
- **Iconos en menús**: el tinte del ítem habilitado aplana cualquier icono; por
  eso el estilo deja esos ítems al estilo base. Si un icono "desaparece" o se ve
  como una mancha en un menú, revisa primero `SolidDisabledMenuStyle`, no el SVG.
- **`_load_icon(nombre)`** busca `icons/<nombre>.svg|png`, luego
  `icons/light|dark/…` según el tema y al final `kimageannotator/…`. Si un icono
  nuevo no aparece, comprueba que existe **en los dos** directorios de tema.
- **Los SVG con gradiente** deben usar un `id` único en su archivo; Qt resuelve
  `url(#id)` por documento y un id repetido entre iconos puede dar relleno negro.
- Los iconos de sistema (`_standard_icon`, `_system_icon`) conservan su color
  desde `1afed43c`/`326e9d2a`: solo se tiñe el estado deshabilitado.
- **`QSettings` sin nombre de organización** devuelve `Status.AccessError` y
  **descarta todas las escrituras**; `setValue()` seguido de `value()` da
  `None`. El código real funciona porque `app.py` fija organización y aplicación
  antes de crear la ventana; en pruebas hay que inyectar un `QSettings` con
  archivo propio (INI temporal).
- **Bandeja y estado maximizado**: ocultar la ventana pierde el maximizado en
  Windows. Cualquier restauración desde la bandeja debe reaplicar el estado
  guardado en `_tray_restore_state`, no `showNormal()`.
- **Ocultar durante el minimizado nativo** deja la ventana mapeada otra vez; el
  ocultado tiene que ir diferido un turno (`_hide_to_tray_when_settled`).
- **Foco del editor de texto en Windows**: al mostrarlo, la ventana se reactiva y
  el foco vuelve al botón de la barra. Un `focusOut` acepta la edición, y aceptar
  un texto nuevo vacío lo borra; por eso el editor ignora ese motivo mientras
  está vacío.

## 10. Mapa de archivos nuevos

```text
AGENT_HANDOFF.md                 este documento (excluido del sdist en MANIFEST.in)
ksnip_py/linguistics.py          puente al toolkit (nuevo)
ksnip_py/spellcheck.py           backend doble (modificado)
ksnip_py/menu_style.py           gate de atajos, iconos y repliegue (modificado)
ksnip_py/download_manager.py     errores reales, tamaños, modelos, Open folder (modificado)
ksnip_py/main_window.py          acciones e iconos nuevos (modificado)
ksnip_py/app.py                  traducciones del toolkit (modificado)
ksnip_py/icons/light/open.svg    icono Abrir (nuevo)
ksnip_py/icons/dark/open.svg     icono Abrir (nuevo)
ksnip_py/icons/light/includeCursor.svg    icono Incluir el ratón (nuevo)
ksnip_py/icons/dark/includeCursor.svg     icono Incluir el ratón (nuevo)
ksnip_py/icons/light/pyqt6_linguistic_tools.svg   icono del gestor de diccionarios (nuevo)
ksnip_py/icons/dark/pyqt6_linguistic_tools.svg    ídem (nuevo)
ksnip_py/icons/light/wayland.svg  rediseñado por el autor (un solo path)
ksnip_py/icons/dark/wayland.svg   rediseñado por el autor (un solo path)
tests_py/test_linguistics.py     pruebas del puente (nuevo)
tests_py/test_app_icons.py       pruebas de iconos (nuevo)
tests_py/test_model_manager_folders.py  pruebas del botón Open folder (nuevo)
tests_py/test_capture_geometry.py  geometría, bandeja y maximizado (reescrito)
tests_py/test_text_editor.py     foco del editor y creación de texto (nuevo)
ksnip_py/canvas.py               guarda de foco del editor (modificado)
tools/make_ocr_table_sample.py   generador del libro (nuevo)
tools/render_icon_sheets.py      hojas de contactos de iconos (nuevo)
docs/SPELLCHECK.md               documentación de ortografía (nuevo)
docs/ocr-samples/                libro de ejemplo + captura + resultados (nuevo)
libs/pyqt6-linguistic-tools/     submódulo v1.1.0 (nuevo)
```

---

Si algo de este documento no coincide con el código, **manda el código**: las
pruebas y el `CHANGELOG.md` son la referencia; este texto es el contexto de por
qué se hizo así.