# ROADMAP PyQt6 Port de ksnip

Este archivo resume el estado del port desde C++ a PyQt6 usando `ksnip_py/` como implementación actual.

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
- [x] Restauración de geometría de ventana
- [x] Pestañas para múltiples capturas/imágenes
- [x] Manejo de estado `dirty` por pestaña
- [ ] Paridad completa con el flujo de arranque y comportamiento general de `MainWindow.cpp`
- [ ] Single-instance / IPC como en C++
- [ ] Integración completa con argumentos de línea de comandos del binario C++

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
- [ ] Paridad de captura con cursor del mouse
- [ ] Paridad Wayland/X11/portal como en C++
- [ ] Captura vía portal genérico Wayland
- [ ] Escalado específico de screenshots Wayland genéricos
- [ ] Delay implícito con la misma semántica del código C++
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
- [ ] Guardar todo
- [ ] Imprimir
- [ ] Vista previa de impresión
- [ ] Renombrar captura/archivo
- [ ] Borrar imagen/captura con paridad de flujo C++
- [ ] Abrir directorio contenedor
- [ ] Copiar ruta del archivo
- [ ] Copy as Data URI / base64
- [ ] Paste embedded image como en C++

## Anotación y Edición

- [x] Herramienta de selección
- [x] Herramienta lápiz
- [x] Herramienta línea
- [x] Herramienta flecha
- [x] Herramienta rectángulo
- [x] Herramienta elipse
- [x] Herramienta texto
- [x] Herramienta blur
- [x] Herramienta pixelate
- [x] Herramienta crop
- [x] Editor multilinea para `Text` con re-edición por doble clic
- [x] Sub-herramientas iniciales funcionales: `Double Arrow`, `Marker Pen`, `Marker Rectangle`, `Marker Ellipse`, `Text Pointer`, `Text Arrow`, `Number`, `Number Pointer`, `Number Arrow`
- [x] Primera implementación funcional de `Sticker` en PyQt6
- [x] Deshacer
- [x] Rehacer
- [x] Rotar imagen
- [x] Escalar imagen
- [x] Selección múltiple aditiva con `Ctrl`
- [x] Mover selección
- [x] Resize handles para rectángulo, elipse, línea, flecha y texto
- [x] Eliminar item seleccionado
- [x] Duplicar item seleccionado
- [x] Re-editar texto seleccionado
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
- [ ] Modify canvas
- [ ] Cut tool
- [ ] Más efectos y pulido de efectos existentes
- [ ] Stickers
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
- [ ] Estructura jerárquica de `Settings` igual a la del original
- [ ] Ajustes de aplicación avanzados
- [ ] Ajustes completos de image grabber
- [ ] Ajustes completos de annotation
- [ ] Ajustes completos de saver
- [ ] Ajustes completos de actions
- [ ] Ajustes completos de plugins
- [ ] Ajustes completos de tray icon del original

## UI, Iconografía y Fidelidad Visual

- [x] Iconos originales copiados a `ksnip_py/icons/`
- [x] Iconos de `kImageAnnotator` copiados a `ksnip_py/icons/kimageannotator/`
- [x] Icono principal de aplicación disponible dentro de `ksnip_py/`
- [x] Asignar iconos de ksnip a acciones principales visibles
- [ ] Asignar iconos de ksnip a todas las acciones visibles relevantes
- [x] Toolbar principal simplificada y acercada al patrón visual de Ksnip (`New`, `Save`, `Copy`, `Undo`, `Redo`, `Crop`, `Delay`)
- [ ] Toolbar principal igual al original
- [x] Menú principal reestructurado a `File / Edit / View / Tools / Help`
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
- [x] `Fill Mode` adaptado a la semántica real del C++ original para la UI PyQt6: `Border and Fill`, `Border and No Fill`, `No Border and No Fill`
- [x] Toolbar de `Item Settings` sin separador visible cuando la herramienta no expone controles
- [x] `Fill Mode` dinámico por herramienta como en el C++ original: `Text` y `Number` permiten `No Border and No Fill`, mientras `Text Arrow`, `Rectangle` y `Ellipse` sólo muestran los modos aplicables
- [x] Grupos de `Color` y `Fill Mode` en `Item Settings` con icono visible a la izquierda, más cercanos a la disposición original de Ksnip
- [ ] Igualar exactamente los controles visibles de `Item Settings` para cada herramienta según las capturas en `/images/Ksnip-Tools-selected/`
- [ ] Controles de propiedades iguales al original
- [x] Zoom básico con controles inferiores
- [x] Barra inferior de zoom compactada y acercada visualmente al patrón de Ksnip
- [ ] Barra inferior y zoom igual al original
- [ ] Tema visual, espaciado y densidad visual equivalentes a las capturas de referencia

## Calidad y Empaquetado

- [x] `pyproject.toml`
- [x] Entrada ejecutable `ksnip-pyqt6`
- [x] Compilación sintáctica verificada con `py_compile`
- [x] Incluir recursos gráficos del paquete en distribución instalada
- [ ] Smoke tests GUI para flujos principales
- [ ] Tests automatizados equivalentes para la parte Python
- [ ] Documentación de ejecución/instalación actualizada conforme crezca la paridad
