"""Build the sample spreadsheet used to test ksnip-pyqt6 table OCR.

The workbook deliberately mixes letters, numbers, accents, currency signs and
typographic symbols so a screenshot of it exercises the PP-StructureV3 table
pipeline.  Output: docs/ocr-samples/tabla-ejemplo-ocr.xlsx
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "ocr-samples" / "tabla-ejemplo-ocr.xlsx"

TITLE = "Inventario de ejemplo — prueba de OCR de tablas"
SUBTITLE = "ksnip-pyqt6 · documento de prueba · 27/11/2026 · uso libre"

HEADERS = [
    "Código",
    "Producto",
    "Cantidad",
    "Precio unit.",
    "Dto.",
    "Importe",
    "Estado",
    "Notas / referencia",
]

# Código, Producto, Cantidad, Precio, Descuento, Estado, Notas
ROWS: list[tuple[str, str, int, float, float, str, str]] = [
    ("KS-0042/A", "Cámara réflex «EOS 90D»", 4, 1299.90, 0.05, "En stock", "pedido#A-77 & urgente"),
    ("KS-0043/B", "Objetivo 50 mm f/1.8", 7, 189.00, 0.00, "En stock", "Factura N.º 2026/0114"),
    ("KS-0044-C", "Memoria USB-C 128 GB", 25, 24.95, 0.10, "En stock", "Lote 25 % + 4 unidades"),
    ("KS-0045/D", "Monitor LED 27\" 4K", 3, 459.50, 0.07, "Pendiente", "soporte@ejemplo.com"),
    ("KS-0046/E", "Teclado español (ñ) inalámbrico", 12, 39.99, 0.00, "En stock", "@almacén-B"),
    ("KS-0047/F", "Ratón óptico — 1600 dpi", 18, 15.75, 0.15, "En stock", "Ref. «X-1180» (v2)"),
    ("KS-0048/G", "Cable HDMI 2.1 (2 m)", 40, 8.90, 0.00, "En stock", "http://intranet.local/stock?id=42&v=2"),
    ("KS-0049/H", "Adaptador USB-A → USB-C", 33, 6.45, 0.05, "Agotado", "#42 [prioridad]"),
    ("KS-0050/I", "Disco SSD NVMe 1 TB", 6, 109.00, 0.03, "Pendiente", "±0,5 % tolerancia"),
    ("KS-0051/J", "Tarjeta microSD 256 GB", 21, 32.80, 0.10, "En stock", "✓ revisado 2026-11-27"),
    ("KS-0052/K", "Hub USB 7 puertos", 9, 27.60, 0.00, "En stock", "Tel. +593 (04) 123-4567"),
    ("KS-0053/L", "Webcam Full HD 1080p", 5, 54.20, 0.08, "En stock", "€ 12,50 & € 8,75"),
    ("KS-0054/M", "Micrófono condensador Ø 25 mm", 2, 219.00, 0.00, "Pendiente", "Descuento 5 % → 7 %"),
    ("KS-0055/N", "Auriculares over-ear", 11, 89.90, 0.12, "En stock", "Caja 30×20×15 cm"),
    ("KS-0056/O", "Soporte para portátil 13,3\"", 16, 34.50, 0.00, "En stock", "Ubicación: pasillo 3 / estante B"),
    ("KS-0057/P", "Regleta 6 tomas + interruptor", 8, 19.99, 0.05, "En stock", "Potencia máx. 2.500 W"),
    ("KS-0058/Q", "Etiquetas adhesivas (pack 100 uds.)", 30, 4.85, 0.20, "En stock", "≈ 100 uds. / caja"),
    ("KS-0059/R", "Tóner láser negro", 4, 74.30, 0.00, "Agotado", "Compat. HP 26A #cf226a"),
    ("KS-0060/S", "Papel A4 80 g/m²", 50, 5.40, 0.15, "En stock", "Resma 500 hojas ± 5"),
    ("KS-0061/T", "Grapadora metálica", 14, 12.25, 0.00, "En stock", "Incluye 1.000 grapas"),
    ("KS-0062/U", "Funda neopreno 13,3\"", 22, 17.80, 0.06, "En stock", "Color azul/negro (2 en 1)"),
    ("KS-0063/V", "Limpiador de pantalla 250 ml", 19, 7.35, 0.00, "En stock", "No tóxico · uso diario"),
    ("KS-0064/W", "Pilas AA (4 uds.)", 60, 3.95, 0.25, "En stock", "Alcalinas 1,5 V ±0,1 V"),
    ("KS-0065/X", "Bombilla LED 9 W ≈ 806 lm", 27, 6.20, 0.10, "En stock", "Casquillo E27 · 2700 K"),
    ("KS-0066/Y", "Termómetro -20 °C a +50 °C", 10, 11.40, 0.00, "Pendiente", "Precisión ±0,5 °C"),
    ("KS-0067/Z", "Cinta métrica 5 m × 19 mm", 13, 9.15, 0.05, "En stock", "Carcasa ABS #amarillo"),
    ("KS-0068/AA", "Caja organizadora 30×20×15 cm", 24, 8.70, 0.08, "En stock", "Apilable «stack» & cierre"),
    ("KS-0069/AB", "Rotulador permanente (negro/azul)", 45, 2.35, 0.30, "En stock", "Punta 1,5 mm · xileno libre"),
]

TITLE_FILL = PatternFill("solid", fgColor="D9E2F3")
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
TOTAL_FILL = PatternFill("solid", fgColor="DDEBF7")
THIN = Side(style="thin", color="8EA9C1")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

WIDTHS = {"A": 14, "B": 40, "C": 10, "D": 14, "E": 9, "F": 15, "G": 12, "H": 46}


def build() -> Workbook:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Inventario"

    last_column = get_column_letter(len(HEADERS))

    sheet.merge_cells(f"A1:{last_column}1")
    title = sheet["A1"]
    title.value = TITLE
    title.font = Font(name="Arial", size=14, bold=True, color="1F4E79")
    title.fill = TITLE_FILL
    title.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    sheet.row_dimensions[1].height = 30

    sheet.merge_cells(f"A2:{last_column}2")
    subtitle = sheet["A2"]
    subtitle.value = SUBTITLE
    subtitle.font = Font(name="Arial", size=9, italic=True, color="44546A")
    subtitle.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    sheet.row_dimensions[2].height = 18

    for index, header in enumerate(HEADERS, start=1):
        cell = sheet.cell(row=3, column=index, value=header)
        cell.font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    sheet.row_dimensions[3].height = 32

    first_data_row = 4
    for offset, row in enumerate(ROWS):
        excel_row = first_data_row + offset
        code, product, quantity, price, discount, state, notes = row

        values = [
            code,
            product,
            quantity,
            price,
            discount,
            f"=C{excel_row}*D{excel_row}*(1-E{excel_row})",
            state,
            notes,
        ]
        for column, value in enumerate(values, start=1):
            cell = sheet.cell(row=excel_row, column=column, value=value)
            cell.font = Font(name="Arial", size=11)
            cell.border = BORDER
            if column in (1, 7, 8):
                cell.alignment = Alignment(
                    horizontal="left",
                    vertical="center",
                    wrap_text=column == 8,
                    indent=1 if column in (1, 7) else 0,
                )
            elif column == 2:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")

        sheet.cell(row=excel_row, column=3).number_format = "#,##0"
        sheet.cell(row=excel_row, column=4).number_format = '"$" #,##0.00'
        sheet.cell(row=excel_row, column=5).number_format = "0 %"
        sheet.cell(row=excel_row, column=6).number_format = '"$" #,##0.00'
        sheet.row_dimensions[excel_row].height = 22

    last_data_row = first_data_row + len(ROWS) - 1
    totals_row = last_data_row + 1

    summary_rows = [
        ("TOTALES", f"=SUM(C{first_data_row}:C{last_data_row})", f"=SUM(F{first_data_row}:F{last_data_row})"),
        ("IVA 15 %", None, f"=ROUND(F{totals_row}*0.15,2)"),
        ("TOTAL CON IVA", None, f"=F{totals_row}+F{totals_row + 1}"),
    ]

    for offset, (label, quantity_formula, importe_formula) in enumerate(summary_rows):
        excel_row = totals_row + offset
        sheet.merge_cells(f"A{excel_row}:B{excel_row}")
        label_cell = sheet.cell(row=excel_row, column=1, value=label)
        label_cell.font = Font(name="Arial", size=11, bold=True)
        label_cell.fill = TOTAL_FILL
        label_cell.alignment = Alignment(horizontal="right", vertical="center", indent=1)

        for column in range(1, len(HEADERS) + 1):
            cell = sheet.cell(row=excel_row, column=column)
            cell.border = BORDER
            cell.fill = TOTAL_FILL
            cell.font = Font(name="Arial", size=11, bold=True)

        if quantity_formula is not None:
            quantity_cell = sheet.cell(row=excel_row, column=3, value=quantity_formula)
            quantity_cell.number_format = "#,##0"
            quantity_cell.alignment = Alignment(horizontal="right", vertical="center")

        importe_cell = sheet.cell(row=excel_row, column=6, value=importe_formula)
        importe_cell.number_format = '"$" #,##0.00'
        importe_cell.alignment = Alignment(horizontal="right", vertical="center")

        sheet.row_dimensions[excel_row].height = 22

    for column, width in WIDTHS.items():
        sheet.column_dimensions[column].width = width

    sheet.freeze_panes = "A4"
    sheet.sheet_view.zoomScale = 100

    return workbook


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    workbook = build()
    workbook.save(OUTPUT)
    print(f"written: {OUTPUT}")
    print(f"rows: {len(ROWS)} data rows, columns: {len(HEADERS)}")


if __name__ == "__main__":
    main()
