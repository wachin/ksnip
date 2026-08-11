# ROADMAP PyQt6 Port de ksnip

Este archivo resume el estado del port desde C++ a PyQt6 usando `ksnip_py/` como implementación actual.

## Estado para retomar después del formateo

- [x] Este `ROADMAP.md` quedó preparado como documento de continuidad para retomar el port sin depender de este chat
- [x] El `README` activo del proyecto es `README.md`
- [x] El `README` anterior del repositorio fue preservado como `README_Old.md`
- [x] La implementación activa del port sigue concentrada en `ksnip_py/`
- [x] Ya existe una base funcional real sobre la que se puede seguir afinando sin reiniciar el trabajo
- [x] Ya existe esqueleto inicial de empaquetado Debian en `debian/`, pero todavía no debe considerarse terminado
- [ ] Al retomar después del formateo, leer primero `README.md`, luego este `ROADMAP.md`, y después ejecutar `python3 -m ksnip_py`
- [ ] Al retomar, priorizar primero la paridad visual/funcional fina y dejar el cierre Debian para el tramo final

## Regla de Interfaz

- [x] La interfaz final de `ksnip_py` debe quedar visual y funcionalmente alineada con las capturas de referencia:
- [x] `/images/01-Ksnip-recien-abierto.png`
- [x] `/images/02-ksnip-cuando-a-hecho-su-primer-captura-de-pantalla.png`
- [x] Las ventanas de `Settings` también deben alinearse visual y funcionalmente con estas referencias:
- [x] `/images/GUI/03-Settings_Application.png`
- [x] `/images/GUI/04-Settings_Application_Saver.png`
- [x] `/images/GUI/05-Settings_Application_Tray-Icon.png`
- [x] `/images/GUI/06-Settings_Imge-Grabber.png`
- [x] `/images/GUI/07-Settings_Imge-Grabber_Snipping-Area.png`
- [x] `/images/GUI/08-Settings_Uploader.png`
- [x] `/images/GUI/09-Settings_Uploader_Imur_Uploader.png`
- [x] `/images/GUI/10-Settings_Uploader_FTP_Uploader.png`
- [x] `/images/GUI/11-Settings_Uploader_Script_Uploader.png`
- [x] `/images/GUI/12-Settings_Annotator.png`
- [x] `/images/GUI/13-Settings_Annotator_Stickers.png`
- [x] `/images/GUI/14-Settings_Annotator_Watermark.png`
- [x] `/images/GUI/15-Settings_HotKeys.png`
- [x] `/images/GUI/16-Settings_Actions.png`
- [x] `/images/GUI/17-Settings_Plugins.png`
**Ksnip herramientas y sus controles**
- [x] Los `Item Settings` por herramienta también deben alinearse visual y funcionalmente con estas referencias:
- [x] `/images/Ksnip-Tools-selected/01-herramienta-de-seleccion-seleccionada.png`
  Descripción C++ original: `Tools::Select` no muestra pickers de propiedades. Debe verse únicamente el área de `Item Settings` vacía, sin color, ancho, relleno, fuente, sombra, opacidad ni sticker. Referencia de lógica: `libraries/kImageAnnotator/src/gui/annotator/settings/ItemSettingsWidgetConfigurator.cpp`.
- [x] `/images/Ksnip-Tools-selected/02-Tool_Duplicate(selected).png`
  Descripción C++ original: `Tools::Duplicate` sólo muestra `Opacity`. No muestra color, texto, ancho, relleno, número inicial, obfuscación, sticker, sombra, fuente ni escalado.
- [x] `/images/Ksnip-Tools-selected/03-Tool_Arrow(selected).png`
  Descripción C++ original: `Tools::Arrow` muestra, en el orden base del toolbar, `Color`, `Width`, `Item Shadow`, `Opacity`. No muestra `Text Color`, `Fill Mode`, `Number Seed`, `Obfuscation Factor`, `Sticker`, `Font` ni `Scaling`.
- [x] `/images/Ksnip-Tools-selected/04-Tool_Pen(selected).png`
  Descripción C++ original: `Tools::Pen` muestra `Color`, `Width`, `Item Shadow`, `Opacity`. Es prácticamente el mismo patrón visible que `Arrow`, pero sin `Fill Mode` y sin controles de texto o número.
- [x] `/images/Ksnip-Tools-selected/05-Tool_Marker-Pen(selected).png`
  Descripción C++ original: `Tools::MarkerPen` muestra sólo `Color` y `Width`. El `Width` cambia su rango a `1..100`, y el color se maneja sin canal alpha. No hay sombra ni opacidad.
- [x] `/images/Ksnip-Tools-selected/06-Tool_Text(selected).png`
  Descripción C++ original: `Tools::Text` muestra `Color`, `Width`, `Fill Mode`, `Text Color`, `Font`, `Item Shadow`, `Opacity`. En `Fill Mode` deben existir las opciones `Border and Fill`, `Border and No Fill` y `No Border and No Fill`. El `FontPicker` incluye familia, tamaño, `Bold`, `Italic` y `Underline`.
- [x] `/images/Ksnip-Tools-selected/07-Tool_Number(selected).png`
  Descripción C++ original: `Tools::Number` muestra `Color`, `Width`, `Fill Mode`, `Text Color`, `Font`, `Number Seed`, `Item Shadow`, `Opacity`. Igual que `Text`, debe permitir `No Border and No Fill` en `Fill Mode`.
- [x] `/images/Ksnip-Tools-selected/08-Tool_Blur(selected).png`
  Descripción C++ original: `Tools::Blur` y `Tools::Pixelate` muestran sólo `Obfuscation Factor`. No usan color, ancho, relleno, sombra, fuente ni opacidad.
- [x] `/images/Ksnip-Tools-selected/09-Tool_Rectangle(selected).png`
  Descripción C++ original: `Tools::Rect` y `Tools::Ellipse` muestran `Color`, `Width`, `Fill Mode`, `Item Shadow`, `Opacity`. No muestran `Text Color`, `Font`, `Number Seed`, `Sticker`, `Scaling` ni `Obfuscation Factor`.
- [x] `/images/Ksnip-Tools-selected/10-Tool_Sticker(selected).png`
  Descripción C++ original: `Tools::Sticker` muestra `Sticker`, `Item Shadow`, `Scaling`, `Opacity`. No usa color, ancho, relleno, texto ni obfuscación. El `StickerPicker` es un botón con menú en cuadrícula de stickers SVG.
- [x] Orden base real de los controles en el C++ original dentro de `AnnotationItemSettings`: `Color`, `Width`, `Fill Mode`, `Text Color`, `Font`, `Number Seed`, `Obfuscation Factor`, `Sticker`, `Item Shadow`, `Scaling`, `Opacity`.
- [x] Fuentes C++ de referencia para mantener esta paridad:
  `libraries/kImageAnnotator/src/gui/annotator/settings/AnnotationItemSettings.cpp`
  `libraries/kImageAnnotator/src/gui/annotator/settings/ItemSettingsWidgetConfigurator.cpp`
  `libraries/kImageAnnotator/src/widgets/settingsPicker/FillModePicker.cpp`
  `libraries/kImageAnnotator/src/widgets/settingsPicker/FontPicker.cpp`
  `libraries/kImageAnnotator/src/widgets/settingsPicker/BoolPicker.cpp`
  `libraries/kImageAnnotator/src/widgets/settingsPicker/StickerPicker.cpp`
- [x] La meta no es reinterpretar ksnip: la UI PyQt6 debe conservar la estructura del programa original.
- [x] Deben usarse los iconos de ksnip en la interfaz gráfica de `ksnip_py`.
- [ ] Igualar por completo la disposición visual del toolbar, menús, panel lateral izquierdo, barra de estado y controles inferiores del ksnip original.
- [ ] Igualar por completo la navegación, categorías, controles y densidad visual de `Settings` respecto a las capturas de referencia.

## Núcleo de Aplicación

- [x] Estructura base de aplicación PyQt6 en `ksnip_py/`
- [x] Ventana principal funcional
- [x] Persistencia básica con `QSettings`
- [x] Infraestructura inicial Qt Linguist para el port PyQt6, carga automática de `.qm`, override `--language` y diagnóstico del portal en español
- [x] Selector persistente de idioma en `Settings > Application`, poblado dinámicamente desde los 41 catálogos instalados
- [x] Sincronizador reproducible que reutiliza traducciones coincidentes de `ksnip` y `kImageAnnotator` y compila los catálogos PyQt6
- [x] Reutilización del catálogo Qt Linguist del ksnip C++ y migración inicial de menús/acciones principales a `tr()`
- [x] Traducción inicial de modos de captura, herramientas de anotación y submenús principales del port
- [x] Traducción de las acciones restantes de archivo, imagen, elementos, OCR, watermark, docks y zoom
- [x] Traducción de tooltips de `Item Settings` y mensajes de estado de edición, archivo, portapapeles, watermark, uploader y OCR
- [x] Traducción de textos restantes del lienzo: estado vacío, ayuda multilinea, inserción y edición contextual de texto
- [x] Traducción de vista previa de impresión, diálogos/progreso OCR y estado sin sugerencias del corrector ortográfico
- [x] Traducción inicial de `Settings > Application` e `Image Grabber`, incluidos controles de portal, captura y apariencia
- [x] Traducción de `Settings > Saver`, incluida calidad, plantilla de ruta, autoguardado y sobrescritura
- [x] Traducción de `Settings > Tray Icon`, menú real de bandeja, acciones predeterminadas y notificaciones
- [x] Traducción de `Settings > HotKeys`, nombres de acciones y botones para limpiar atajos
- [x] Traducción de `Settings > Uploader`, `Script Uploader` y `OCR`, manteniendo estables los identificadores de backend
- [x] Traducción de `Settings > Image Grabber > Snipping Area`, comportamiento y apariencia
- [x] Traducción de `Settings > Annotator`, herramientas predeterminadas, estilos y placeholders de paridad avanzada
- [x] Traducción de `Settings > Annotator > Watermark`, estados dinámicos y diálogos de selección/error
- [x] Traducción de las páginas placeholder `Settings > Actions` y `Plugins`, conservando su estado pendiente/deshabilitado
- [x] Traducción de `Settings > Annotator > Scheme colors`, cabeceras, explicación dinámica y selector de color
- [x] Cierre inicial de traducción de Settings: título, búsqueda, botones y placeholders de Imgur, FTP y Stickers
- [ ] Migrar todos los textos de la interfaz PyQt6 a `tr()` y completar los catálogos de los idiomas soportados
- [x] Restauración de geometría de ventana
- [x] Pestañas para múltiples capturas/imágenes
- [x] Manejo de estado `dirty` por pestaña
- [ ] Paridad completa con el flujo de arranque y comportamiento general de `MainWindow.cpp`
- [x] Título dinámico de ventana alineado con `ApplicationTitleProvider`: ruta, prefijo de cambios y estado `Unsaved`
- [x] Single-instance / IPC local mediante `QLocalServer`: reenvío de argumentos para mostrar, abrir, capturar, guardar y subir
- [ ] Integración completa con argumentos de línea de comandos del binario C++
- [x] Integración CLI inicial para abrir imágenes, seleccionar los seis modos de captura, delay temporal, ayuda y versión
- [x] Apertura CLI de imágenes desde `stdin` usando `-`, incluida transferencia de bytes a la instancia activa por IPC
- [x] CLI `--save` y `--saveto` para capturar y guardar directamente sin abrir el editor
- [x] CLI `--cursor` para incluir el puntero en capturas solicitadas por línea de comandos
- [x] CLI `--upload` para capturar y ejecutar el uploader por script sin abrir el editor; combinable con `--save`
- [x] CLI `--portal` conectado al backend genérico de `xdg-desktop-portal`
- [x] Captura Portal accesible desde toolbar, menú Archivo, bandeja, acción predeterminada y atajo configurable

## Captura de Pantalla

- [x] Captura de área rectangular
- [x] Captura de último rectángulo
- [x] Captura de pantalla completa
- [x] Captura de pantalla actual
- [x] Captura de ventana activa
- [x] Captura de ventana bajo el cursor
- [x] Preferencias de captura para delay
- [x] Control visible de delay de captura en la barra principal
- [x] Ocultar ventana principal durante la captura
- [x] Restaurar/mostrar ventana principal después de la captura
- [x] Copia automática al portapapeles para nuevas capturas
- [x] Captura opcional del cursor real mediante XFixes en X11, insertado como `Image Item` editable; fallback seguro cuando no está disponible
- [ ] Paridad Wayland/X11/portal como en C++
- [x] Captura vía portal genérico Wayland mediante QtDBus, con cancelación, timeout y carga del URI devuelto
- [x] Preferencia funcional `Force Generic Wayland`: redirige capturas GUI al portal y distingue fullscreen no interactivo
- [x] Detección automática de sesión Wayland mediante plataforma Qt y `XDG_SESSION_TYPE`, con redirección al portal
- [x] Diagnóstico de entorno para fallos del portal, con recomendación del backend Debian según `XDG_CURRENT_DESKTOP`
- [ ] Escalado específico de screenshots Wayland genéricos
- [x] Delay implícito con la misma semántica del código C++: máximo con delay explícito sólo cuando la ventana estaba visible
- [ ] Hotkeys globales nativos para capturas

## Archivo e Imagen

- [x] Abrir imagen desde disco
- [x] Pegar imagen desde portapapeles
- [x] Guardar imagen
- [x] Guardar imagen como
- [x] Copiar imagen al portapapeles
- [x] Menú de imágenes recientes
- [x] Reabrir imágenes recientes
- [x] Recordar último directorio usado
- [x] Guardar todo
- [x] Imprimir mediante el diálogo nativo de Qt, ajustando la imagen a la página sin deformarla
- [x] Vista previa de impresión con el mismo render escalado y centrado
- [x] Renombrar captura/archivo con `F2`, soporte para pestañas sin guardar y archivos existentes, preservando estado dirty
- [x] Borrar imagen/captura con confirmación, eliminación del archivo y cierre de su pestaña, separado de `Delete Item`
- [x] Abrir directorio contenedor
- [x] Copiar ruta del archivo
- [x] Copy as Data URI / base64
- [x] Paste Embedded image como `Image Item` centrado, con `Ctrl+Shift+V`, undo y edición mediante selección
- [x] Formato de proyecto editable `.ksnip` basado en ZIP (`project.json` + `background.png`) con anotaciones, imágenes incrustadas, efecto, zoom y contador restaurables
- [x] Copia raster automática junto a cada proyecto `.ksnip`, PNG por defecto y formato PNG/JPEG/WebP/BMP configurable desde `Settings > Saver`
- [x] Formato principal de guardado configurable entre PNG (predeterminado) y proyecto `.ksnip`, aplicado a `Save As` y `Save All`
- [x] Numeración aislada por lienzo: las capturas nuevas empiezan siempre en 1 y los proyectos `.ksnip` restauran su propia secuencia
- [x] Previsualización fiel durante el arrastre de `Number Pointer` y `Number Arrow`, mostrando círculo, número y puntero/flecha en lugar de un rectángulo genérico
- [x] Círculo de `Number Pointer` centrado exactamente en el clic inicial para evitar el desplazamiento visual hacia una esquina
- [x] Exportación SVG para Inkscape con fondo PNG incrustado y anotaciones vectoriales editables; overlays raster se conservan como imágenes PNG embebidas

## Anotación y Edición

- [x] Herramienta de selección
- [x] Herramienta lápiz
- [x] Pen y Marker Pen convertidos en trazos no destructivos: puntos serializables, selección, movimiento, undo y soporte real de Opacity/Item Shadow para Pen
- [x] Ancho persistente por herramienta con valores iniciales del C++ (`Marker Pen` 30, flechas 6, número 5 y texto 2); Marker Pen usa el ancho final sin multiplicarlo
- [x] `Item Shadow` y `Opacity` persistentes por herramienta, con valores iniciales de sombra alineados con `Config::defaultShadowEnabled`
- [x] Color persistente por herramienta con valores iniciales de `Config::defaultToolColor`: marcadores amarillos, línea azul, rectángulo gris, texto negro y resto rojo
- [x] Color de texto persistente e independiente para `Text`, punteros, flechas y herramientas `Number`, usando blanco como valor inicial de `Config::defaultToolTextColor`
- [x] Fuente y estilos persistentes por herramienta como `Config::defaultToolFont`: fuente del sistema en negrita, tamaño 15 para `Text`, 20 para `Number`, con cursiva y subrayado independientes
- [x] `Number`, `Number Pointer` y `Number Arrow` aplican al elemento nuevo la negrita, cursiva y subrayado configurados, sin reintroducir estilos hardcodeados al construirlo; los constructores especializados de `Number Arrow` y `Text Arrow` ya no quedan ocultos tras la rama genérica de líneas
- [x] `Text Arrow` y `Number Arrow` conservan siempre el asta y la punta con `No Border and No Fill`; el modo de relleno sólo controla el recuadro o círculo, como en el pintado C++
- [x] Hit-testing completo para `Text Arrow` y `Number Arrow`: se pueden seleccionar desde el asta, el recuadro de texto o el círculo numerado, incluso sin borde ni relleno
- [x] Geometría unificada de `Text Arrow`: pintura, selección, sombra y bounds comparten una etiqueta medida con la fuente real, multilínea y colocada correctamente al apuntar hacia izquierda o derecha
- [x] Corregido el mapeo ratón→imagen cuando Qt centra capturas menores que el canvas mínimo: flechas, formas y demás herramientas comienzan exactamente bajo el clic, incluyendo zoom y margen de Drop Shadow
- [x] `Text Pointer` y `Text Arrow` se pueden reeditar desde doble clic, menú contextual y acción `Edit text`, conservando undo y evitando cambios vacíos o cancelados
- [x] `Text Pointer` usa el color principal de la herramienta para borde, relleno y puntero, en vez del blanco semitransparente hardcodeado; el color del texto continúa siendo independiente
- [x] El círculo de `Number` se recalcula con `QFontMetrics` al cambiar familia, tamaño, negrita, cursiva o subrayado, conservando su centro y siendo reversible con undo como `NumberRectHelper` del C++
- [x] `Number Pointer` y `Number Arrow` comparten el diámetro calculado por métricas tipográficas en pintura, hit-testing y bounds; la punta permanece fija al crecer el número
- [x] `Number Pointer` reemplaza los cuatro handles del rectángulo inexistente por controles independientes para centro de burbuja y punta; el hit-testing deja de seleccionar zonas vacías entre ambos
- [x] `Text Pointer` usa una burbuja medida con la fuente y handles independientes para burbuja y punta; el triángulo se conecta al lado correcto según la dirección y no selecciona zonas vacías
- [x] La creación de `Number` y los cambios de valor recalculan inmediatamente el círculo mediante métricas, conservan el centro y restauran texto y geometría con undo como `BaseAnnotationNumber::setNumber`
- [x] Duplicar o pegar `Number`, `Number Pointer` y `Number Arrow` asigna valores nuevos y consecutivos mediante el contador local, igual que el registro de clones en `NumberManager` con `UpdateOnlyNewNumbers`
- [x] Activada la opción `Number Tool Seed change updates all Number Items` en `Settings > Annotator`, con persistencia y modos equivalentes a `UpdateOnlyNewNumbers`/`UpdateAllNumbers`, incluida renumeración tras borrar
- [x] En modo `UpdateAllNumbers`, crear, duplicar o pegar cualquier variante numérica normaliza toda la secuencia desde la semilla; undo restaura también los valores previos de los elementos existentes
- [x] Activada y persistida la opción `Switch to Select Tool after drawing Item`; el canvas solicita el cambio al terminar una anotación y `MainWindow` sincroniza herramienta y acciones
- [x] Activada `Select Item after drawing`, dependiente visualmente de `Switch to Select Tool`; permite cambiar a Selección sin mantener el item seleccionado, salvo `Duplicate`, que requiere selección tras crearse
- [x] Activada `Remember annotation tool selection and load on startup`: restaura la última herramienta sólo al habilitarla y usa `Pen` como valor inicial del C++ en caso contrario o ante configuración inválida
- [x] Activada `Show Controls Widget`: añade un toolbar inferior opcional con `Undo`, `Redo`, `Crop`, `Scale`, `Rotate`, `Modify Canvas` y `Cut`, oculto por defecto como el dock `AnnotationControlsWidget` del C++
- [x] `Fill Mode` persistente por herramienta con valores iniciales de `Config::defaultToolFillMode` y descarte seguro de modos incompatibles guardados por versiones anteriores
- [x] Marker Pen, Marker Rectangle y Marker Ellipse renderizados con composición `Multiply`, igual que los elementos marcador del C++
- [x] Marker Rectangle y Marker Ellipse alineados con `NoBorderAndFill`: relleno completo, sin borde, sombra, ancho ni opacidad configurables
- [x] Herramienta línea
- [x] Herramienta flecha
- [x] Herramienta rectángulo
- [x] Herramienta elipse
- [x] Herramienta texto
- [x] Herramienta blur
- [x] Herramienta pixelate
- [x] Herramienta crop que desplaza las anotaciones respecto al origen recortado, con undo/redo como `CropCommand`
- [x] Vista dedicada de cut con orientación explícita, posición, ancho de franja, previsualización y Aplicar/Cancelar
- [x] Editor multilinea para `Text` con re-edición por doble clic
- [x] `Text` ahora define su caja arrastrando un rectángulo antes de insertar el contenido, más cercano al flujo original de Ksnip
- [x] `Text` entra en edición inline sobre la captura al soltar el rectángulo, sin diálogo aparte
- [x] El editor inline de `Text` aparece ya con el color de fondo y el color de fuente elegidos en la herramienta
- [x] `Text` permite re-edición tanto por doble clic como desde el menú contextual `Edit text`
- [x] `Text` evita crear un nuevo recuadro accidental cuando se confirma el anterior con un clic fuera del editor
- [x] `Undo` y `Ctrl+Z` ya pueden eliminar un recuadro de texto recién creado mientras está en edición inline
- [x] Los recuadros de `Text` ya no quedan pegados al cursor después de moverlos con la herramienta `Select`
- [x] La caja inline de `Text` crece automáticamente hacia la derecha al escribir y hacia abajo al crear nuevas líneas
- [x] `Text` dispone de handles especializados visibles para redimensionar desde esquinas y lados
- [x] Los handles de `Text` aceptan mejor el clic centrado sobre el círculo
- [x] Soporte base de corrección ortográfica en editores de texto usando `hunspell` del sistema, con detección de `es_MX` y `en_US`, subrayado de errores y sugerencias en menú contextual
- [x] Las sugerencias ortográficas del menú contextual ya reemplazan correctamente la palabra seleccionada
- [x] El menú contextual de corrección ortográfica ya no dispara recuadros espurios al devolver el foco al editor
- [x] Nueva sección `Settings > Scheme colors` con esquema editable de 12 colores base para definir el color de subrayado de palabras mal escritas según el color de fondo de `Text`
- [x] Sub-herramientas iniciales funcionales: `Double Arrow`, `Marker Pen`, `Marker Rectangle`, `Marker Ellipse`, `Text Pointer`, `Text Arrow`, `Number`, `Number Pointer`, `Number Arrow`
- [x] Primera implementación funcional de `Sticker` en PyQt6
- [x] Deshacer
- [x] Rehacer
- [x] Diálogo de rotación alineado con kImageAnnotator: 180°, 90° horario/antihorario, ángulo arbitrario y volteo horizontal/vertical
- [x] Diálogo de escalado alineado con kImageAnnotator: píxeles y porcentajes sincronizados, relación de aspecto opcional y límites 1–400 %
- [x] Selección múltiple aditiva con `Ctrl`
- [x] Mover selección
- [x] Resize handles para rectángulo, elipse, línea, flecha y texto
- [x] Eliminar item seleccionado
- [x] Duplicar item seleccionado
- [x] Herramienta `Duplicate` independiente: captura una región compuesta como elemento movible, con undo y sólo `Opacity` en Item Settings
- [x] Re-editar texto seleccionado
- [x] Re-editar `Text` desde doble clic o menú contextual `Edit text`
- [x] Traer selección al frente
- [x] Enviar selección al fondo
- [x] Editar color de trazo en items seleccionados
- [x] Editar grosor de trazo en items seleccionados
- [x] Editar color de relleno en items seleccionados
- [x] Editar opacidad en items seleccionados
- [x] Editar modo de relleno en items seleccionados
- [x] Editar fuente y tamaño de texto en items seleccionados
- [x] Editar bold/italic de texto seleccionado
- [x] Copiar items seleccionados
- [x] Pegar items seleccionados
- [x] Soporte básico de overlay image item
- [ ] Paridad completa con `kImageAnnotator`
- [x] Modify Canvas alineado con `ModifyCanvasWidget`: vista previa, color, modo restringido, origen X/Y, tamaño W/H, recorte libre y undo
- [x] Cut tool
- [x] Selector de efectos no destructivo y mutuamente excluyente: `No Effect`, `Drop Shadow`, `Grayscale`, `Invert Color` y `Border`
- [x] `Drop Shadow` alineado con kImageAnnotator: negro, blur `30` y offset `(0, 2)`, incluyendo su margen en exportación y edición
- [x] Efectos de imagen base alineados con `ImageEffectPicker` e `ImageEffectFactory` del submódulo original
- [x] Stickers
- [ ] Controles laterales y layout igual al original
- [ ] Comportamiento visual fino del editor igual al C++

## Watermark, Upload y OCR

- [x] Almacenamiento de imagen watermark
- [x] Actualización de imagen watermark
- [x] Inserción de watermark en la captura
- [x] Rotación opcional de watermark
- [x] Script uploader configurable
- [x] Persistencia de ajustes del uploader
- [x] Copia opcional de salida del uploader al portapapeles
- [x] OCR experimental
- [x] Backend opcional PaddleOCR
- [x] Backend OCR por script
- [x] Diálogo para mostrar el resultado OCR
- [ ] Paridad con el sistema de plugins de C++
- [ ] Integración OCR equivalente a ventanas/modeless workflow del original
- [ ] Soporte de Imgur nativo
- [ ] Soporte FTP nativo

## Tray, Ventanas y UX

- [x] Workflow de system tray
- [x] Mostrar/ocultar desde tray
- [x] Minimizar al tray
- [x] Cerrar al tray
- [x] Inicio minimizado al tray
- [x] Notificaciones del tray
- [x] Ventanas pin "always on top"
- [x] Acción por defecto del tray configurable como en C++
- [ ] Menú/acciones del tray con paridad completa
- [ ] Ventanas modeless adicionales con paridad

## Configuración y Ajustes

- [x] Diálogo de settings en PyQt6
- [x] Referencias visuales de `Settings` añadidas al roadmap
- [x] Navegación lateral base para `Settings`
- [x] Página `Application` reestructurada con layout más cercano a la referencia
- [x] Página `Tray Icon` reestructurada con layout más cercano a la referencia
- [x] Página `Image Grabber` reestructurada con layout base cercano a la referencia
- [x] Página `Snipping Area` reestructurada con layout base cercano a la referencia
- [x] Página `Annotator` reestructurada con layout base cercano a la referencia
- [x] Página `Uploader` reestructurada con layout base cercano a la referencia
- [x] Página `HotKeys` reestructurada con layout base cercano a la referencia
- [x] Página `Actions` reestructurada con layout base cercano a la referencia
- [x] Página `Plugins` reestructurada con layout base cercano a la referencia
- [x] Confirmación antes de subir imagen conectada a la lógica real
- [x] Activación/desactivación de atajos conectada a la lógica real
- [x] Toggles compartidos de captura conectados entre `Application` e `Image Grabber`
- [x] Acción por defecto del `Tray Icon` conectada a la lógica real
- [x] Persistencia de valores por defecto del editor
- [x] Persistencia de hotkeys de aplicación
- [x] Ajustes de tray
- [x] Ajustes de uploader
- [x] Ajustes de OCR
- [x] Ajustes de watermark
- [x] Ajustes de captura básicos
- [ ] Paridad completa con todas las pestañas/categorías del `SettingsDialog.cpp`
- [x] Estructura jerárquica de `Settings` alineada con el árbol del original, conservando `Scheme colors` como subpágina de `Annotator`
- [x] Ajustes experimentales de OCR integrados en su propia página, evitando que el grupo quedara suelto fuera del layout
- [ ] Ajustes de aplicación avanzados
- [x] `Remember Main Window position` y `Auto hide Tabs` habilitados, persistidos y conectados al comportamiento real
- [x] `Capture screenshot at startup` habilitado y conectado al último modo de captura usado
- [x] `Auto hide Docks` funcional al arrancar y acción `Tab` para mostrar/ocultar barras como en el C++
- [x] `Auto resize to content` y `Resize delay` conectados al abrir, pegar o capturar, limitando la ventana al escritorio disponible
- [ ] Ajustes completos de image grabber
- [ ] Ajustes completos de annotation
- [ ] Ajustes completos de saver
- [x] Página `Saver` reemplaza el placeholder con el layout base original y conecta confirmación al descartar y recuerdo del directorio de guardado
- [x] `Saver > Save Quality` funcional con modo predeterminado o factor `0..100`, persistido y aplicado al guardado real
- [x] Autoguardado de nuevas capturas con plantilla configurable, comodines de fecha/hora, contador `#` y política de sobrescritura
- [ ] Ajustes completos de actions
- [ ] Ajustes completos de plugins
- [ ] Ajustes completos de tray icon del original

## UI, Iconografía y Fidelidad Visual

- [x] Iconos originales copiados a `ksnip_py/icons/`
- [x] Iconos de `kImageAnnotator` copiados a `ksnip_py/icons/kimageannotator/`
- [x] Stickers originales copiados a `ksnip_py/stickers/`, incluidos en el paquete y desacoplados del submódulo en tiempo de ejecución
- [x] Colección SVG original para tutoriales: atención, información, consejo, pregunta, siguiente paso, clic, teclado y terminal
- [x] Selector de stickers con pestañas Original/Papirus/GNOME/Numix/SuperTux/Usuario, exclusión de enlaces simbólicos y favoritos persistentes
- [x] Restauración persistente de la última pestaña utilizada en el selector de stickers
- [x] Papirus/GNOME/Numix vendorizados sin enlaces simbólicos, con atribución, licencias completas, package-data y cobertura DEP-5
- [x] Visto bueno y X originales para Papirus/GNOME/Numix, adaptados visualmente a cada paleta y declarados GPL-3 en DEP-5
- [x] Papirus/GNOME/Numix completados con las 24 expresiones y utilidades de Original que faltaban, mediante 72 SVG propios y reproducibles
- [x] Pestaña SuperTux con 26 stickers SVG originales y reproducibles: expresiones, marcas y utilidades para tutoriales
- [x] Pestaña Usuario con importación multiformato, conversión PNG, límite de 512 px, nombres únicos y acceso a su carpeta de configuración
- [x] Inserción de stickers mediante clic en el lienzo, compatible con SVG/PNG externos y con undo
- [x] Tamaño inicial de stickers normalizado a 50 px, fuentes de alta resolución para ampliación y sombra tintada sin duplicar la imagen
- [x] Interpolación suave de alta calidad para stickers e imágenes al reducir, ampliar, previsualizar y exportar
- [x] Migración única de la escala antigua de stickers a 100% tras normalizar el tamaño base
- [x] Icono principal de aplicación disponible dentro de `ksnip_py/`
- [x] Asignar iconos de ksnip a acciones principales visibles
- [x] Asignar iconos locales o del tema de escritorio, con fallback empaquetado, a todas las acciones visibles relevantes
- [x] Toolbar principal simplificada y acercada al patrón visual de Ksnip (`New`, `Save`, `Copy`, `Undo`, `Redo`, `Crop`, `Cut`, `Delay`)
- [x] Botón desplegable `New` muestra icono y texto como en la barra principal original
- [ ] Toolbar principal igual al original
- [x] Menú principal reestructurado según el C++ a `File / Edit / View / Options / Help`, sin duplicar `Settings`
- [ ] Menú principal igual al original
- [x] Panel de herramientas lateral izquierdo base en PyQt6
- [x] Panel lateral con iconos del editor original
- [x] Grupos de sub-herramientas en barra lateral para `Arrow`, `Marker`, `Text`, `Number`, `Blur/Pixelate` y `Rectangle/Ellipse`
- [x] Caja de herramientas lateral reajustada sin marco extra, con primera columna alineada y columna de flechas angosta como en Ksnip
- [ ] Panel de herramientas lateral izquierdo igual al original
- [x] Barra de propiedades base con iconografía del editor original
- [x] Barra de propiedades compactada con swatches visibles y controles más cercanos al layout de Ksnip
- [x] `Item Settings` dinámicos en barra superior según herramienta seleccionada
- [x] Segunda pasada de `Item Settings`: visibilidad por herramienta afinada para `Selection`, `Duplicate/Image`, `Arrow`, `Pen`, `Marker Pen`, `Text`, `Number`, `Blur/Pixelate` y `Rectangle`
- [x] Barra de `Item Settings` reordenada para seguir la secuencia base del C++ original: `Color`, `Width`, `Fill Mode`, `Text Color`, `Font`, `Number Seed`, `Obfuscation Factor`, `Sticker`, `Item Shadow`, `Scaling`, `Opacity`
- [x] Primera conexión funcional en Python para controles de `Item Settings`: `Text Color`, `Underline`, `Item Shadow`, `Scaling`, `Number Seed` y `Sticker`
- [x] `Item Shadow` aplicado al crear líneas, flechas, rectángulos y elipses, excluyendo marcadores, y editable con undo
- [x] `Fill Mode` adaptado a la semántica real del C++ original para la UI PyQt6: `Border and Fill`, `Border and No Fill`, `No Border and No Fill`
- [x] Toolbar de `Item Settings` sin separador visible cuando la herramienta no expone controles
- [x] `Item Settings` colocado en una segunda fila real; para `Selection` sin elemento conserva sólo el asa y el área vacía, como en la referencia
- [x] `Fill Mode` dinámico por herramienta como en el C++ original: `Text` y `Number` permiten `No Border and No Fill`, mientras `Text Arrow`, `Rectangle` y `Ellipse` sólo muestran los modos aplicables
- [x] Grupos de `Color` y `Fill Mode` en `Item Settings` con icono visible a la izquierda, más cercanos a la disposición original de Ksnip
- [x] Grupo de `Font` con icono inicial en `Item Settings`, más cercano al patrón visual de `Text` y `Number` en Ksnip
- [x] Selector de color de marcadores (`Marker Pen`, `Marker Rectangle`, `Marker Ellipse`) sin canal alpha, como en el configurador C++ original
- [x] Selector emergente inspirado directamente en `kColorPicker`: cuadrícula de colores rápidos, muestras alpha sobre tablero ajedrezado, color personalizado y sincronización entre barras
- [x] Toolbar de `Item Settings` con separadores reales entre grupos visibles y espaciado interno más compacto
- [x] Ajuste fino de densidad visual en controles superiores: `Font`, `Scaling` y `Opacity` con anchura más cercana a las capturas de Ksnip
- [ ] Igualar exactamente los controles visibles de `Item Settings` para cada herramienta según las capturas en `/images/Ksnip-Tools-selected/`
- [ ] Controles de propiedades iguales al original
- [x] Zoom básico con controles inferiores
- [x] Barra inferior de zoom compactada y acercada visualmente al patrón de Ksnip
- [x] Controles inferiores de zoom reubicados a la izquierda y simplificados al patrón visible del Ksnip original
- [x] `ZoomPicker` alineado con kImageAnnotator: rango 10–800%, pasos de 10%, botones de ajustar/restablecer y atajos `Ctrl++`, `Ctrl+-`, `Ctrl+0` y `Ctrl+F`
- [x] Accesos compactos a `Modify Canvas` e `Image Effect` restaurados en el extremo derecho de la barra inferior
- [ ] Barra inferior y zoom igual al original
- [ ] Tema visual, espaciado y densidad visual equivalentes a las capturas de referencia

## Calidad y Empaquetado

- [x] `pyproject.toml`
- [x] Esqueleto inicial de empaquetado Debian en `debian/`
- [x] Dependencias de sistema para corrección ortográfica declaradas en `debian/control`: `hunspell`, `hunspell-en-us`
- [x] `README.md` actualizado para reflejar el flujo actual de `Text`, el uso de `hunspell` y la ejecución sobre paquetes del sistema
- [ ] Empaquetado Debian completo y pulido según políticas Debian
- [ ] Publicación potencial en Debian / `packages.debian.org` sólo después de terminar primero el refinado funcional y visual del programa
- [x] Entrada ejecutable `ksnip-pyqt6`
- [x] Compilación sintáctica verificada con `py_compile`
- [x] Incluir recursos gráficos del paquete en distribución instalada
- [ ] Smoke tests GUI para flujos principales
- [ ] Tests automatizados equivalentes para la parte Python
- [x] Primera suite automatizada Python para paridad de Crop, Cut y efectos de imagen
- [ ] Documentación de ejecución/instalación actualizada conforme crezca la paridad

## Próximo bloque recomendado

- [ ] Afinar todavía más la paridad visual del toolbar principal, barra de propiedades y barra inferior frente a Ksnip original
- [ ] Igualar con más precisión los `Item Settings` visibles por herramienta según `/images/Ksnip-Tools-selected/`
- [ ] Seguir puliendo `Text` hasta acercarlo lo más posible al comportamiento visual y de edición del C++ original
- [ ] Completar más categorías y semántica fina de `Settings`
- [ ] Dejar el empaquetado Debian listo sólo cuando la UI y el comportamiento ya estén estabilizados
