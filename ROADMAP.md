# ROADMAP PyQt6 Port de ksnip

Este archivo resume el estado del port desde C++ a PyQt6 usando `ksnip_py/` como implementación actual.

## Regla de Interfaz

- [x] La interfaz final de `ksnip_py` debe quedar visual y funcionalmente alineada con las capturas de referencia:
- [x] `/images/01-Ksnip-recien-abierto.png`
- [x] `/images/02-ksnip-cuando-a-hecho-su-primer-captura-de-pantalla.png`
- [x] La meta no es reinterpretar ksnip: la UI PyQt6 debe conservar la estructura del programa original.
- [x] Deben usarse los iconos de ksnip en la interfaz gráfica de `ksnip_py`.
- [ ] Igualar por completo la disposición visual del toolbar, menús, panel lateral izquierdo, barra de estado y controles inferiores del ksnip original.

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
- [x] Captura de pantalla completa
- [x] Captura de pantalla actual
- [x] Captura de ventana activa
- [x] Captura de ventana bajo el cursor
- [x] Preferencias de captura para delay
- [x] Ocultar ventana principal durante la captura
- [x] Restaurar/mostrar ventana principal después de la captura
- [x] Copia automática al portapapeles para nuevas capturas
- [ ] Paridad de captura con cursor del mouse
- [ ] Paridad Wayland/X11/portal como en C++
- [ ] Captura de último rectángulo
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
- [ ] Acción por defecto del tray configurable como en C++
- [ ] Menú/acciones del tray con paridad completa
- [ ] Ventanas modeless adicionales con paridad

## Configuración y Ajustes

- [x] Diálogo de settings en PyQt6
- [x] Persistencia de valores por defecto del editor
- [x] Persistencia de hotkeys de aplicación
- [x] Ajustes de tray
- [x] Ajustes de uploader
- [x] Ajustes de OCR
- [x] Ajustes de watermark
- [x] Ajustes de captura básicos
- [ ] Paridad completa con todas las pestañas/categorías del `SettingsDialog.cpp`
- [ ] Ajustes de aplicación avanzados
- [ ] Ajustes completos de image grabber
- [ ] Ajustes completos de annotation
- [ ] Ajustes completos de saver
- [ ] Ajustes completos de actions
- [ ] Ajustes completos de plugins
- [ ] Ajustes completos de tray icon del original

## UI, Iconografía y Fidelidad Visual

- [x] Iconos originales copiados a `ksnip_py/icons/`
- [x] Icono principal de aplicación disponible dentro de `ksnip_py/`
- [x] Asignar iconos de ksnip a acciones principales visibles
- [ ] Asignar iconos de ksnip a todas las acciones visibles relevantes
- [ ] Toolbar principal igual al original
- [ ] Menú principal igual al original
- [x] Panel de herramientas lateral izquierdo base en PyQt6
- [ ] Panel de herramientas lateral izquierdo igual al original
- [ ] Controles de propiedades iguales al original
- [x] Zoom básico con controles inferiores
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
