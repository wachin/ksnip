# Muestras para el OCR de tablas

Material de ejemplo para comprobar qué bien reconoce ksnip-pyqt6 una tabla real
y para documentar el resultado. No forma parte del paquete ni de las pruebas
automáticas: son datos de demostración.

## `tabla-ejemplo-ocr.xlsx`

Libro de una hoja (`Inventario`) con 28 filas de datos y 8 columnas:

| Columna | Contenido |
| --- | --- |
| Código | Identificadores con letras, números y separadores: `KS-0042/A`, `KS-0069/AB` |
| Producto | Nombres en español con tildes, `ñ`, comillas angulares, `Ø`, `≈`, `×`, `→`, `·` |
| Cantidad | Enteros, incluido el total de la columna |
| Precio unit. | Importes con dos decimales y formato de moneda |
| Dto. | Porcentajes (`5 %`, `30 %`) |
| Importe | Fórmula `=C*D*(1-E)` por fila, con su resultado calculado |
| Estado | Texto corto: `En stock`, `Agotado`, `Pendiente` |
| Notas / referencia | Lo más difícil de reconocer: `#`, `&`, `@`, `%`, `±`, `°C`, `€`, `✓`, correos, URLs con `?` y `&`, teléfonos y rangos |

Las tres últimas filas son totales con IVA, así que la tabla también ejercita
los números grandes con separador de miles y dos decimales.

La idea es que la captura no sea un caso fácil: mayúsculas y minúsculas,
puntuación tipográfica, símbolos junto a cifras y celdas de texto largo.

## Cómo usarla

1. Abre el archivo con **LibreOffice Calc** (doble clic).
2. Deja el zoom al **100 %** y la ventana maximizada; no hace falta ampliar,
   pero conviene que las columnas no queden cortadas (`Producto` y `Notas` se
   ajustan solas si arrastras el borde).
3. Haz la captura de la tabla:
   - con ksnip: **Archivo → Nueva captura** y arrastra la región, o
   - pulsa `Impr Pant` y pega la imagen en ksnip.
4. Con la captura abierta en ksnip, ejecuta
   **Opciones → OCR Text Recognition (tables + Markdown)**.
   Es la acción del pipeline PP-StructureV3, la que conserva la tabla como
   tabla. La acción **OCR Text Recognition** a secas devuelve solo líneas de
   texto y pierde la estructura.
5. Revisa el resultado en Markdown: cada fila debe quedar como una fila de la
   tabla y el total debe coincidir con `$ 17.587,10`.

## Qué esperar de la precisión

Medición sobre este archivo (15 filas × 8 columnas) con los modelos que instala
el Gestor de modelos, PP-OCRv5 *mobile*. Una sola pasada por caso, así que
tómalo como orden de magnitud, no como nota exacta:

| Entrada | Celdas de texto equivalentes | Celdas numéricas correctas |
| --- | --- | --- |
| Captura de 1.099 px de ancho (zoom normal) | 52/60 (47 idénticas) | 60/60 |
| Imagen de 2.463 px de ancho | 55/60 (49 idénticas) | 60/60 |
| Captura de 1.099 px ampliada ×2 con interpolación | 48/60 (44 idénticas) | 56/60 |

Lo que sale de ahí:

- **Los números no son el problema.** Importes, cantidades y porcentajes
  aciertan incluso en la captura pequeña; es lo que importa en una tabla.
- **Lo que falla son las tildes y los símbolos tipográficos.** Con la captura
  pequeña perdía tildes (`Cámara` → `Camara`, `portátil` → `portatil`,
  `pasillo` → `pasilo`, `español` → `españiol`) y confundía `f/1.8` con
  `1/1.8`. Con la imagen de 2.463 px todos esos casos salieron bien.
- **Ampliar una captura pequeña empeora el resultado**, no lo mejora: la
  interpolación no añade información y además descoloca la detección de
  columnas. Captura más grande de origen, no más grande después.
- **Los símbolos fuera del alfabeto del modelo se pierden casi siempre**, con
  cualquier resolución: `Ø` → `O`, `✓` → `√` o desaparece, `«»` → `《》`,
  `×` → `x`, `&` → `＆`. No es un fallo de ksnip: el modelo no tiene esos
  glifos en su vocabulario.

Para una tabla de trabajo real: sube el zoom de Calc al 150–200 % antes de
capturar y no hace falta tocar nada más.

## Consejos

- Captura la tabla completa, incluidas las cabeceras, y deja un pequeño margen
  alrededor. El detector de diseño necesita ver los bordes.
- Evita escalar la captura después: el OCR trabaja mejor con el tamaño nativo
  de la pantalla.
- Si trabajas con varias pantallas y distinta escala, revisa que la captura no
  salga borrosa; una tabla nítida a 100 % da mejores resultados que una ampliada.
- Un fondo de celda oscuro con texto claro (o al revés) puede bajar la precisión.
  El formato de este archivo usa encabezado oscuro con texto blanco a propósito,
  como caso realista.

## Regenerar o ampliar el archivo

El archivo se genera con `tools/make_ocr_table_sample.py` (requiere `openpyxl`):

```bash
python tools/make_ocr_table_sample.py
```

Edita la lista `ROWS` del script para añadir más filas o símbolos. Después de
regenerarlo, ábrelo una vez en LibreOffice Calc y guarda para que las fórmulas
tengan su valor calculado; openpyxl no evalúa fórmulas.
