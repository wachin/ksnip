<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="sq">
  <context>
    <name>AboutDialog</name>
    <message>
      <location filename="../about_dialog.py" line="29" />
      <source>About ksnip PyQt6</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="81" />
      <source>Original project</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="84" />
      <source>PyQt6 port</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="85" />
      <source>Email</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="86" />
      <source>Website</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="87" />
      <source>License</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="95" />
      <source>Version</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="96" />
      <source>A screenshot and annotation tool, ported from the original C++/Qt ksnip to Python with PyQt6.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="97" />
      <source>Capture, annotate and share screenshots with rectangles, arrows, text, numbering, blur, watermark, OCR, pin windows and upload.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="98" />
      <source>Technologies</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../about_dialog.py" line="98" />
      <source>Python 3, PyQt6 (Qt 6 Widgets), PaddleOCR (optional OCR backend)</source>
      <translation type="unfinished" /></message>
    <message>
      <source>Copyright</source>
      <translation type="vanished">Copyright</translation>
    </message>
  </context>
  <context>
    <name>AnnotationCanvas</name>
    <message>
      <location filename="../canvas.py" line="1642" />
      <source>Take a screenshot or open an image.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../canvas.py" line="2171" />
      <location filename="../canvas.py" line="2138" />
      <source>Edit text</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../canvas.py" line="3149" />
      <location filename="../canvas.py" line="3125" />
      <location filename="../canvas.py" line="2955" />
      <source>Insert text</source>
      <translation type="unfinished" /></message>
  </context>
  <context>
    <name>ColorPaletteMenu</name>
    <message>
      <location filename="../color_picker.py" line="91" />
      <source>Custom color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../color_picker.py" line="108" />
      <source>Select color</source>
      <translation type="unfinished" /></message>
  </context>
  <context>
    <name>CutDialog</name>
    <message>
      <location filename="../canvas.py" line="96" />
      <source>Cut</source>
      <translation>Prije</translation></message>
    <message>
      <location filename="../canvas.py" line="102" />
      <source>Vertical</source>
      <translation>Vertika</translation></message>
    <message>
      <location filename="../canvas.py" line="103" />
      <source>Horizontal</source>
      <translation>Horizontal</translation></message>
    <message>
      <location filename="../canvas.py" line="112" />
      <source>Orientation:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../canvas.py" line="113" />
      <source>Position:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../canvas.py" line="114" />
      <source>Slice width:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../canvas.py" line="117" />
      <source>Apply</source>
      <translation>Aplikoje</translation></message>
  </context>
  <context>
    <name>DownloadManagerDialog</name>
    <message>
      <location filename="../download_manager.py" line="302" />
      <location filename="../download_manager.py" line="282" />
      <source>Model &amp; Component Manager</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="327" />
      <source>Download additional components for OCR and other features. Models are stored in your user directory and are not bundled with the application.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="394" />
      <source>PaddleOCR Line Models (PP-OCRv5)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="395" />
      <source>Lightweight OCR models for text line recognition. Supports English, Spanish, and 80+ languages.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="452" />
      <location filename="../download_manager.py" line="430" />
      <location filename="../download_manager.py" line="416" />
      <location filename="../download_manager.py" line="402" />
      <source>OCR</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="408" />
      <source>PaddleOCR Structure (PP-StructureV3)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="409" />
      <source>Document layout analysis and table recognition. Converts tables to Markdown/HTML.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="422" />
      <source>PaddleOCR Formula Recognition</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="423" />
      <source>Mathematical formula recognition (LaTeX output). Optional extra for structure pipeline.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="436" />
      <source>External OCR Script</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="437" />
      <source>Use any custom OCR engine via a script/executable. The script receives the image path as its only argument and must print the recognized text to stdout. 

Example script (save as ~/ocr.sh):
#!/bin/bash
tesseract "$1" stdout -l spa+eng

Make it executable: chmod +x ~/ocr.sh
Then configure the path in Settings → OCR → External OCR script.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="458" />
      <source>Spellcheck Dictionaries (Hunspell)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="459" />
      <source>Additional language dictionaries for spell checking in text annotations.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="466" />
      <source>Spellcheck</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="512" />
      <source>Downloading &amp; installing packages (pip)...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="530" />
      <source>Downloading: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="538" />
      <source>Initializing model cache...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="591" />
      <location filename="../download_manager.py" line="550" />
      <source>Installation complete!</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="562" />
      <source>Installing PaddleX with OCR extra...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="578" />
      <source>Initializing layout model...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="609" />
      <source>Configure script path in Settings → OCR</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="618" />
      <source>Install hunspell packages with apt/dnf</source>
      <translation type="unfinished" /></message>
    <message>
      <source>Use a custom script/executable for OCR. Configure the script path in Settings → OCR.</source>
      <translation type="vanished">Usa un script o ejecutable personalizado para OCR. Configura la ruta del script en Configuración → OCR.</translation>
    </message>
  </context>
  <context>
    <name>MainWindow</name>
    <message>
      <location filename="../main_window.py" line="3655" />
      <location filename="../main_window.py" line="150" />
      <source>Ready</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="242" />
      <source>New</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="4510" />
      <location filename="../main_window.py" line="1385" />
      <location filename="../main_window.py" line="243" />
      <source>New Screenshot</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="493" />
      <source>Updated selected sticker</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="661" />
      <source>Rect Area</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="664" />
      <source>Last Rect Area</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="667" />
      <source>Full Screen</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="670" />
      <source>Current Screen</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="673" />
      <source>Active Window</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="676" />
      <source>Window Under Cursor</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="679" />
      <source>Portal</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="683" />
      <source>Open</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="751" />
      <location filename="../main_window.py" line="688" />
      <source>Save</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="753" />
      <location filename="../main_window.py" line="693" />
      <source>Save As...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="755" />
      <location filename="../main_window.py" line="697" />
      <source>Save All</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="700" />
      <source>Export as SVG...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="703" />
      <source>Print</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2981" />
      <location filename="../main_window.py" line="707" />
      <source>Print Preview</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="761" />
      <location filename="../main_window.py" line="710" />
      <source>Copy</source>
      <translation>Kopjoje</translation></message>
    <message>
      <location filename="../main_window.py" line="714" />
      <source>Copy as data URI</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="763" />
      <location filename="../main_window.py" line="717" />
      <source>Copy Path</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3011" />
      <location filename="../main_window.py" line="757" />
      <location filename="../main_window.py" line="720" />
      <source>Rename</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="724" />
      <source>Delete Image...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="759" />
      <location filename="../main_window.py" line="727" />
      <source>Open Directory</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="730" />
      <source>Copy Item</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="734" />
      <source>Close Tab</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="740" />
      <source>Close</source>
      <translation>Mbyll</translation></message>
    <message>
      <location filename="../main_window.py" line="743" />
      <source>Close Other</source>
      <translation>Mbyll të tjerat</translation></message>
    <message>
      <location filename="../main_window.py" line="745" />
      <source>Close All</source>
      <translation>Mbyll të gjitha</translation></message>
    <message>
      <location filename="../main_window.py" line="747" />
      <source>Close All to the Left</source>
      <translation>Mbyll të gjitha majtas</translation></message>
    <message>
      <location filename="../main_window.py" line="749" />
      <source>Close All to the Right</source>
      <translation>Mbyll të gjitha djathtas</translation></message>
    <message>
      <location filename="../main_window.py" line="765" />
      <source>Delete</source>
      <translation>Fshi</translation></message>
    <message>
      <location filename="../main_window.py" line="768" />
      <source>Pen</source>
      <translation>Penë</translation></message>
    <message>
      <location filename="../main_window.py" line="773" />
      <source>Marker Pen</source>
      <translation>Penë Shenjë</translation></message>
    <message>
      <location filename="../main_window.py" line="775" />
      <source>Line</source>
      <translation>Vijë</translation></message>
    <message>
      <location filename="../main_window.py" line="780" />
      <source>Arrow</source>
      <translation>Shigjetë</translation></message>
    <message>
      <location filename="../main_window.py" line="785" />
      <source>Double Arrow</source>
      <translation>Shigjetë Dyshe</translation></message>
    <message>
      <location filename="../main_window.py" line="787" />
      <source>Rectangle</source>
      <translation>Drejtkëndësh</translation></message>
    <message>
      <location filename="../main_window.py" line="792" />
      <source>Ellipse</source>
      <translation>Elips</translation></message>
    <message>
      <location filename="../main_window.py" line="797" />
      <source>Text</source>
      <translation>Tekst</translation></message>
    <message>
      <location filename="../main_window.py" line="802" />
      <source>Text Pointer</source>
      <translation>Tregues Teksti</translation></message>
    <message>
      <location filename="../main_window.py" line="803" />
      <source>Text Arrow</source>
      <translation>Shigjetë Teksti</translation></message>
    <message>
      <location filename="../main_window.py" line="805" />
      <source>Blur</source>
      <translation>Turbullim</translation></message>
    <message>
      <location filename="../main_window.py" line="810" />
      <source>Pixelate</source>
      <translation>Pikselizoje</translation></message>
    <message>
      <location filename="../main_window.py" line="815" />
      <source>Crop</source>
      <translation>Qethe</translation></message>
    <message>
      <location filename="../main_window.py" line="820" />
      <source>Cut</source>
      <translation>Prije</translation></message>
    <message>
      <location filename="../main_window.py" line="823" />
      <source>Select</source>
      <translation>Përzgjidhe</translation></message>
    <message>
      <location filename="../main_window.py" line="828" />
      <source>Duplicate</source>
      <translation>Përsëdytje</translation></message>
    <message>
      <location filename="../main_window.py" line="831" />
      <source>Marker Rectangle</source>
      <translation>Drejtkëndësh Shenjë</translation></message>
    <message>
      <location filename="../main_window.py" line="832" />
      <source>Marker Ellipse</source>
      <translation>Elips Shenjë</translation></message>
    <message>
      <location filename="../main_window.py" line="1118" />
      <location filename="../main_window.py" line="833" />
      <source>Number</source>
      <translation>Numër</translation></message>
    <message>
      <location filename="../main_window.py" line="834" />
      <source>Number Pointer</source>
      <translation>Tregues Numri</translation></message>
    <message>
      <location filename="../main_window.py" line="835" />
      <source>Number Arrow</source>
      <translation>Shigjetë Numrash</translation></message>
    <message>
      <location filename="../main_window.py" line="1134" />
      <location filename="../main_window.py" line="836" />
      <source>Sticker</source>
      <translation>Ngjitës</translation></message>
    <message>
      <location filename="../main_window.py" line="866" />
      <source>Color</source>
      <translation>Ngjyrë</translation></message>
    <message>
      <location filename="../main_window.py" line="869" />
      <source>Undo</source>
      <translation>Zhbëje</translation></message>
    <message>
      <location filename="../main_window.py" line="874" />
      <source>Redo</source>
      <translation>Ribëje</translation></message>
    <message>
      <location filename="../main_window.py" line="879" />
      <source>Paste</source>
      <translation>Ngjite</translation></message>
    <message>
      <location filename="../main_window.py" line="884" />
      <source>Paste Embedded</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="888" />
      <source>Paste Item</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="892" />
      <source>Delete Item</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="896" />
      <source>Duplicate Item</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="900" />
      <source>Edit Text...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="903" />
      <source>Bring To Front</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="906" />
      <source>Send To Back</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="909" />
      <source>Rotate</source>
      <translation>Rrotulloje</translation></message>
    <message>
      <location filename="../main_window.py" line="1153" />
      <location filename="../main_window.py" line="912" />
      <source>Scale</source>
      <translation>Ripërmasojeni</translation></message>
    <message>
      <location filename="../main_window.py" line="3307" />
      <location filename="../main_window.py" line="917" />
      <source>No Effect</source>
      <translation>Pa Efekte</translation></message>
    <message>
      <location filename="../main_window.py" line="3308" />
      <location filename="../main_window.py" line="918" />
      <source>Drop Shadow</source>
      <translation>Drop Shadow</translation></message>
    <message>
      <location filename="../main_window.py" line="3309" />
      <location filename="../main_window.py" line="919" />
      <source>Grayscale</source>
      <translation>Shkallë të grisë</translation></message>
    <message>
      <location filename="../main_window.py" line="3310" />
      <location filename="../main_window.py" line="920" />
      <source>Invert Color</source>
      <translation>Përmbyse Ngjyrën</translation></message>
    <message>
      <location filename="../main_window.py" line="3311" />
      <location filename="../main_window.py" line="921" />
      <source>Border</source>
      <translation>Anë</translation></message>
    <message>
      <location filename="../main_window.py" line="924" />
      <source>Modify Canvas...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3188" />
      <location filename="../main_window.py" line="927" />
      <source>Hide Docks</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="931" />
      <source>Pin</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="935" />
      <source>Add Watermark</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3483" />
      <location filename="../main_window.py" line="940" />
      <source>Upload</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="944" />
      <source>OCR Text Recognition</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="947" />
      <source>OCR Text Recognition (tables + Markdown)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="951" />
      <source>Update Watermark Image...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="954" />
      <source>Rotate Watermark</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="959" />
      <source>Settings</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="962" />
      <source>Model Manager…</source>
      <translation>Menaxheri i modeleve…</translation></message>
    <message>
      <location filename="../main_window.py" line="963" />
      <source>Download and manage OCR models and other components</source>
      <translation>Shkarkoni dhe menaxhoni modelet OCR dhe komponentet e tjera</translation></message>
    <message>
      <location filename="../main_window.py" line="966" />
      <source>About</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="969" />
      <source>Clear Recent Images</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="972" />
      <source>Quit</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="975" />
      <source>Zoom Out</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="978" />
      <source>Reset Zoom</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="981" />
      <source>Zoom In</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="984" />
      <source>Fit Image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1006" />
      <source>Capture delay</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1214" />
      <location filename="../main_window.py" line="1034" />
      <location filename="../main_window.py" line="1027" />
      <source>Stroke color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1043" />
      <source>Stroke width: changes the thickness of the line or arrow shaft.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1045" />
      <source>Stroke width</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1053" />
      <source>Arrowhead size: changes the size of the triangular arrow tip.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1056" />
      <source>Arrowhead size</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1068" />
      <location filename="../main_window.py" line="1064" />
      <source>Fill mode</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1080" />
      <location filename="../main_window.py" line="1073" />
      <source>Text color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1087" />
      <source>Font family used by the text or number.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1095" />
      <source>Font size of the text or number.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1098" />
      <source>Font</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1103" />
      <source>Bold</source>
      <translation>Të trasha</translation></message>
    <message>
      <location filename="../main_window.py" line="1104" />
      <source>Italic</source>
      <translation>Të pjerrëta</translation></message>
    <message>
      <location filename="../main_window.py" line="1105" />
      <source>Underline</source>
      <translation>Të nënvijëzuara</translation></message>
    <message>
      <location filename="../main_window.py" line="1116" />
      <source>Number value used by the next numbered annotation.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1125" />
      <source>Effect strength: controls the intensity of blur or pixelation.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1127" />
      <source>Effect strength</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1131" />
      <source>Select Sticker</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1142" />
      <location filename="../main_window.py" line="1140" />
      <source>Item shadow</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1151" />
      <source>Sticker scale as a percentage of its original insertion size.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1161" />
      <source>Opacity: 0% is transparent and 100% is fully visible.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1163" />
      <source>Opacity</source>
      <translation>Patejdukshmëri</translation></message>
    <message>
      <location filename="../main_window.py" line="1279" />
      <source>Zoom Out (%1)</source>
      <translation>Zvogëloje (%1)</translation></message>
    <message>
      <location filename="../main_window.py" line="1296" />
      <source>Zoom In (%1)</source>
      <translation>Zmadhoje (%1)</translation></message>
    <message>
      <location filename="../main_window.py" line="1449" />
      <location filename="../main_window.py" line="1318" />
      <source>Zoom</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3322" />
      <location filename="../main_window.py" line="1340" />
      <source>Image Effect: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1355" />
      <source>Controls</source>
      <translation>Kontrolle</translation></message>
    <message>
      <location filename="../main_window.py" line="1383" />
      <source>&amp;File</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1395" />
      <source>Recent Images</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1410" />
      <source>&amp;Edit</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1425" />
      <source>Effects</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1436" />
      <source>Annotation Items</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1445" />
      <source>&amp;View</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1455" />
      <source>&amp;Options</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1463" />
      <source>Watermark</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1467" />
      <source>Annotation Tools</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1493" />
      <source>&amp;Help</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1526" />
      <source>Show Editor</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1738" />
      <source>ksnip PyQt6 is still running in the system tray.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1766" />
      <source>OCR is still running; ksnip cannot close until it finishes.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="1796" />
      <source>ksnip PyQt6 was minimized to the system tray.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2132" />
      <source>Select color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2141" />
      <source>Updated selected item color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2160" />
      <source>Updated selected item fill</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2170" />
      <source>Select text color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2180" />
      <source>Updated selected text color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2196" />
      <source>Updated selected item width to %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2209" />
      <source>Updated selected arrowhead size to %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2219" />
      <source>Updated selected text font</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2233" />
      <source>Updated selected text size to %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2243" />
      <source>Updated selected item opacity to %1%</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2261" />
      <source>Updated selected item fill mode</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2272" />
      <source>Updated selected text bold style</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2284" />
      <source>Updated selected text italic style</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2295" />
      <source>Updated selected text underline style</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2306" />
      <source>Updated selected item shadow</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2318" />
      <source>Updated selected item scale to %1%</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2327" />
      <source>Updated selected number to %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2685" />
      <location filename="../main_window.py" line="2538" />
      <source>Portal capture canceled.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2616" />
      <source>Loaded %1 capture and copied it to clipboard</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2705" />
      <source>Loaded %1 capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2771" />
      <source>Open image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2773" />
      <source>Ksnip Projects (*.ksnip);;Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)</source>
      <translation>Projektet Ksnip (*.ksnip);;Imazhet (*.png *.jpg *.jpeg *.bmp *.gif *.webp)</translation></message>
    <message>
      <location filename="../main_window.py" line="2783" />
      <source>Ksnip Projects (*.ksnip)</source>
      <translation>Projektet Ksnip (*.ksnip)</translation></message>
    <message>
      <location filename="../main_window.py" line="3438" />
      <location filename="../main_window.py" line="2784" />
      <source>Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2861" />
      <location filename="../main_window.py" line="2805" />
      <source>Save image as</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2863" />
      <location filename="../main_window.py" line="2807" />
      <source>Ksnip Project (*.ksnip);;PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;WebP (*.webp)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2822" />
      <source>Ksnip Project (*.ksnip)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2823" />
      <source>PNG (*.png)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2830" />
      <source>Export as SVG</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2838" />
      <source>Unable to export SVG: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2840" />
      <source>Exported SVG to %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2888" />
      <source>Saved %1 image(s), failed %2</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2893" />
      <source>Save All stopped early; these could not be saved:
%1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2897" />
      <source>Saved %1 image(s)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2918" />
      <source>Unable to save Ksnip project: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2933" />
      <source>The Ksnip project was saved, but its companion image could not be saved to %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2942" />
      <source>Saved %1 and companion image %2</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2955" />
      <source>Saved %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2963" />
      <source>Copied image to clipboard</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="2972" />
      <source>Sent image to printer</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3011" />
      <source>New name:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3045" />
      <source>Renamed to %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3061" />
      <source>Delete Image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3062" />
      <source>The item '%1' will be deleted.
Do you want to continue?</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3071" />
      <source>Unable to delete %1: %2</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3077" />
      <source>Deleted %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3100" />
      <source>Copied image as a base64 encoded Data URI</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3107" />
      <source>Copied path %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3117" />
      <source>Opened directory %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3124" />
      <source>Copied selected item(s)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3137" />
      <source>Loaded image from clipboard</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3157" />
      <source>Pasted embedded image from clipboard</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3171" />
      <source>Canvas modified: %1 × %2 px at (%3, %4)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3188" />
      <source>Show Docks</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3197" />
      <source>Pasted item from clipboard</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3224" />
      <source>Deleted selected item</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3233" />
      <source>Duplicated selected item</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3242" />
      <source>Updated text item</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3251" />
      <source>Brought selected item to front</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3260" />
      <source>Sent selected item to back</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3272" />
      <source>Rotated image by %1 degrees</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3275" />
      <source>Horizontal</source>
      <translation>Horizontal</translation></message>
    <message>
      <location filename="../main_window.py" line="3275" />
      <source>Vertical</source>
      <translation>Vertika</translation></message>
    <message>
      <location filename="../main_window.py" line="3276" />
      <source>Flipped image: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3296" />
      <source>Scaled image to %1 × %2 px</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3315" />
      <source>Image effect: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3334" />
      <source>Image slice removed</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3349" />
      <source>Pinned current image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3359" />
      <source>Language changed. Restart ksnip to apply it.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3361" />
      <source>Settings updated</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3365" />
      <source>Model Manager opened</source>
      <translation>Menaxheri i modeleve hapur</translation></message>
    <message>
      <location filename="../main_window.py" line="3431" />
      <source>Added watermark</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3436" />
      <source>Select watermark image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3446" />
      <source>Updated watermark image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3455" />
      <source>Upload Image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3456" />
      <source>Upload the current image?</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3487" />
      <location filename="../main_window.py" line="3482" />
      <source>Uploading image...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3565" />
      <location filename="../main_window.py" line="3482" />
      <source>Cancel</source>
      <translation>Anuloje</translation></message>
    <message>
      <location filename="../main_window.py" line="3524" />
      <source>Upload canceled</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3527" />
      <source>Upload failed</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3532" />
      <source>Upload finished successfully</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3534" />
      <source>Upload Successful</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3567" />
      <source>OCR</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3571" />
      <source>Running OCR...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3577" />
      <source>Running OCR layout and table recognition…
First run loads several models and may take 1–3 minutes on CPU.</source>
      <translation>Duke ekzekutuar njohjen e organizimit dhe tabelave OCR…
Ekzekutimi i parë ngarkon disa modele dhe mund të zgjasë 1-3 minuta në CPU.</translation></message>
    <message>
      <location filename="../main_window.py" line="3581" />
      <source>Running OCR text recognition...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3623" />
      <source>OCR canceled</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3627" />
      <source>OCR failed</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3637" />
      <source>OCR finished</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3962" />
      <location filename="../main_window.py" line="3935" />
      <source>Opened %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3945" />
      <source>Unable to open Ksnip project: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3953" />
      <source>Unable to restore Ksnip project: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3968" />
      <source>Unable to open image data.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="3976" />
      <source>Opened image from standard input</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="4624" />
      <location filename="../main_window.py" line="4605" />
      <source>Unsaved changes</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="4606" />
      <source>Close this tab and discard unsaved changes?</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../main_window.py" line="4625" />
      <source>Close ksnip PyQt6 and discard unsaved changes in open tabs?</source>
      <translation type="unfinished" /></message>
    <message>
      <source>Running OCR layout and table recognition...</source>
      <translation type="vanished">Ejecutando reconocimiento de diseño y tablas OCR...</translation>
    </message>
    <message>
      <source>Fit</source>
      <translation type="vanished">Ajustar</translation>
    </message>
    <message>
      <source>Border...</source>
      <translation type="vanished">Borde...</translation>
    </message>
    <message>
      <source>Applied effect: %1</source>
      <translation type="vanished">Efecto aplicado: %1</translation>
    </message>
    <message>
      <source>Border width:</source>
      <translation type="vanished">Grosor del borde:</translation>
    </message>
    <message>
      <source>Border color</source>
      <translation type="vanished">Color del borde</translation>
    </message>
    <message>
      <source>Border effect applied</source>
      <translation type="vanished">Efecto de borde aplicado</translation>
    </message>
  </context>
  <context>
    <name>ModelCard</name>
    <message>
      <location filename="../download_manager.py" line="145" />
      <source>Download size: ~%1 MB</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="147" />
      <source>No download required</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="173" />
      <source>Checking status...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="229" />
      <location filename="../download_manager.py" line="181" />
      <source>Install</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="201" />
      <source>Remove</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="270" />
      <location filename="../download_manager.py" line="224" />
      <source>Reinstall</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="226" />
      <source>✓ Installed</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="231" />
      <source>Not installed</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="243" />
      <source>Starting download...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="255" />
      <source>Remove Model</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="256" />
      <source>To remove %1, you can clear its cached directory or uninstall its package via pip.

Directory: %2</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="268" />
      <source>✓ Installed successfully</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../download_manager.py" line="273" />
      <source>✗ Installation failed</source>
      <translation type="unfinished" /></message>
    <message>
      <source>Download size: ~%1 MB</source>
      <translation type="vanished" />
    </message>
  </context>
  <context>
    <name>ModifyCanvasDialog</name>
    <message>
      <location filename="../canvas.py" line="320" />
      <source>Modify Canvas</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../canvas.py" line="325" />
      <source>Restricted</source>
      <translation>E kufizuar</translation></message>
    <message>
      <location filename="../canvas.py" line="326" />
      <source>When enabled, the canvas must include the background image.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../canvas.py" line="338" />
      <source>Color:</source>
      <translation>Ngjyrë:</translation></message>
    <message>
      <location filename="../canvas.py" line="339" />
      <source>X:</source>
      <translation>X:</translation></message>
    <message>
      <location filename="../canvas.py" line="340" />
      <source>Y:</source>
      <translation>Y:</translation></message>
    <message>
      <location filename="../canvas.py" line="341" />
      <source>W:</source>
      <translation>Gj:</translation></message>
    <message>
      <location filename="../canvas.py" line="342" />
      <source>H:</source>
      <translation>L:</translation></message>
    <message>
      <location filename="../canvas.py" line="344" />
      <source>Apply</source>
      <translation>Aplikoje</translation></message>
    <message>
      <location filename="../canvas.py" line="388" />
      <source>Canvas Background Color</source>
      <translation>Ngjyrë Sfondi Kanavace</translation></message>
  </context>
  <context>
    <name>OcrResultDialog</name>
    <message>
      <location filename="../ocr_result_dialog.py" line="10" />
      <source>OCR Text Recognition</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../ocr_result_dialog.py" line="19" />
      <source>Copy to Clipboard</source>
      <translation type="unfinished" /></message>
  </context>
  <context>
    <name>PortalDiagnostics</name>
    <message>
      <location filename="../capture.py" line="73" />
      <source>The screenshot portal did not return an image.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="75" />
      <source>Portal capture is unavailable: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="76" />
      <source>Detected desktop: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="77" />
      <source>Session type: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="78" />
      <source>Install the portal frontend and the recommended backend:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="80" />
      <source>With Fluxbox, Openbox, IceWM, or another manually assembled session, xdg-desktop-portal-gtk is the usual fallback. The session must export XDG_CURRENT_DESKTOP and may require a matching portals.conf file.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="183" />
      <source>the D-Bus session bus is not available.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="192" />
      <source>the xdg-desktop-portal service is not available.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="197" />
      <source>the Screenshot portal interface is unavailable.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="202" />
      <source>the portal returned an invalid request path.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="214" />
      <source>ksnip could not subscribe to the portal response.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="229" />
      <source>the portal response timed out.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="234" />
      <source>capture was canceled.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="236" />
      <source>portal error code %1.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="242" />
      <source>an empty path</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../capture.py" line="243" />
      <source>the returned image could not be loaded from %1.</source>
      <translation type="unfinished" /></message>
  </context>
  <context>
    <name>QAbstractFileIconProvider</name>
    <message>
      <source>Folder</source>
      <translation type="vanished">Carpeta</translation>
    </message>
    <message>
      <source>Drive</source>
      <translation type="vanished">Unidad</translation>
    </message>
  </context>
  <context>
    <name>QFileDialog</name>
    <message>
      <source>Look in:</source>
      <translation type="vanished">Ver en:</translation>
    </message>
    <message>
      <source>&amp;Look in:</source>
      <translation type="vanished">&amp;Ver en:</translation>
    </message>
    <message>
      <source>Files of type:</source>
      <translation type="vanished">Ficheros de tipo:</translation>
    </message>
    <message>
      <source>Files of &amp;type:</source>
      <translation type="vanished">Ficheros de &amp;tipo:</translation>
    </message>
  </context>
  <context>
    <name>RotateDialog</name>
    <message>
      <location filename="../canvas.py" line="175" />
      <source>Rotate Image</source>
      <translation>Rrotulloje Figurën</translation></message>
    <message>
      <location filename="../canvas.py" line="178" />
      <source>180°</source>
      <translation>180°</translation></message>
    <message>
      <location filename="../canvas.py" line="179" />
      <source>90° Clockwise</source>
      <translation>90° Në kah orar</translation></message>
    <message>
      <location filename="../canvas.py" line="180" />
      <source>90° Counter Clockwise</source>
      <translation>90° Në kah antiorar</translation></message>
    <message>
      <location filename="../canvas.py" line="181" />
      <source>Arbitrary</source>
      <translation>Arbitrar</translation></message>
    <message>
      <location filename="../canvas.py" line="189" />
      <source>Rotate</source>
      <translation>Rrotulloje</translation></message>
    <message>
      <location filename="../canvas.py" line="197" />
      <source>Horizontal</source>
      <translation>Horizontal</translation></message>
    <message>
      <location filename="../canvas.py" line="198" />
      <source>Vertical</source>
      <translation>Vertika</translation></message>
    <message>
      <location filename="../canvas.py" line="199" />
      <source>Flip</source>
      <translation>Ktheje më anë tjetër</translation></message>
  </context>
  <context>
    <name>ScaleDialog</name>
    <message>
      <location filename="../canvas.py" line="237" />
      <source>Scale Image</source>
      <translation>Përshkallëzoje Figurën</translation></message>
    <message>
      <location filename="../canvas.py" line="239" />
      <source>Keep Aspect Ratio</source>
      <translation>Ruaji Përpjesëtimet</translation></message>
    <message>
      <location filename="../canvas.py" line="246" />
      <source>Pixel</source>
      <translation>Piksel</translation></message>
    <message>
      <location filename="../canvas.py" line="252" />
      <location filename="../canvas.py" line="248" />
      <source>Width:</source>
      <translation>Gjerësi:</translation></message>
    <message>
      <location filename="../canvas.py" line="253" />
      <location filename="../canvas.py" line="249" />
      <source>Height:</source>
      <translation>Lartësi:</translation></message>
    <message>
      <location filename="../canvas.py" line="250" />
      <source>Percent</source>
      <translation>Përqindje</translation></message>
  </context>
  <context>
    <name>SettingsDialog</name>
    <message>
      <location filename="../settings_dialog.py" line="1079" />
      <location filename="../settings_dialog.py" line="115" />
      <source>Settings</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="123" />
      <source>Search Settings...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="143" />
      <source>Editor Defaults</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="147" />
      <source>Select</source>
      <translation>Përzgjidhe</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="148" />
      <source>Pen</source>
      <translation>Penë</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="149" />
      <source>Marker Pen</source>
      <translation>Penë Shenjë</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="150" />
      <source>Line</source>
      <translation>Vijë</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="151" />
      <source>Arrow</source>
      <translation>Shigjetë</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="152" />
      <source>Double Arrow</source>
      <translation>Shigjetë Dyshe</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="153" />
      <source>Rectangle</source>
      <translation>Drejtkëndësh</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="154" />
      <source>Ellipse</source>
      <translation>Elips</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="155" />
      <source>Marker Rectangle</source>
      <translation>Drejtkëndësh Shenjë</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="156" />
      <source>Marker Ellipse</source>
      <translation>Elips Shenjë</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="157" />
      <source>Text</source>
      <translation>Tekst</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="158" />
      <source>Text Pointer</source>
      <translation>Tregues Teksti</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="159" />
      <source>Text Arrow</source>
      <translation>Shigjetë Teksti</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="160" />
      <source>Number</source>
      <translation>Numër</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="161" />
      <source>Number Pointer</source>
      <translation>Tregues Numri</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="162" />
      <source>Number Arrow</source>
      <translation>Shigjetë Numrash</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="163" />
      <source>Blur</source>
      <translation>Turbullim</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="164" />
      <source>Pixelate</source>
      <translation>Pikselizoje</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="165" />
      <source>Sticker</source>
      <translation>Ngjitës</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="166" />
      <source>Crop</source>
      <translation>Qethe</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="167" />
      <source>Default Tool</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="171" />
      <source>Stroke Width</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="174" />
      <source>Font Family</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="178" />
      <source>Font Size</source>
      <translation>Madhësi Shkronjash</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="181" />
      <source>Border and Fill</source>
      <translation>Anë dhe Mbushje</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="182" />
      <source>Border and No Fill</source>
      <translation>Anë dhe Pa Mbushje</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="183" />
      <source>No Border and No Fill</source>
      <translation>Pa Anë dhe Pa Mbushje</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="184" />
      <source>Shape Fill Mode</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="188" />
      <source>Opacity %</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="191" />
      <source>Bold</source>
      <translation>Të trasha</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="192" />
      <source>Italic</source>
      <translation>Të pjerrëta</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="197" />
      <source>Text Style</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="199" />
      <source>Watermark</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="202" />
      <source>Rotate Watermark 45°</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="207" />
      <source>Update Image...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="213" />
      <source>Stored Image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="215" />
      <source>Application</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="218" />
      <source>Automatically copy new captures to clipboard</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="221" />
      <source>Remember Main Window position on move and load on startup</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="224" />
      <source>Remember capture window size and position</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="226" />
      <source>After you move or resize the window while an image is open, reuse that size and position for the next capture instead of maximizing.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="230" />
      <source>Capture screenshot at startup with default mode</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="233" />
      <source>Use Tabs</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="238" />
      <source>Auto hide Tabs</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="241" />
      <source>Run ksnip as single instance</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="244" />
      <source>Auto hide Docks</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="248" />
      <source>When the first image is loaded:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="250" />
      <source>Maximize the window</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="251" />
      <source>Fit the window intelligently to the image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="253" />
      <source>Maximize keeps the editor maximized for later images. Smart fit preserves enough room for the tool controls.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="258" />
      <source>Enable Debugging</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="262" />
      <source>Appearance and Paths</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="269" />
      <source>Resize delay</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="272" />
      <source>System default</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="607" />
      <location filename="../settings_dialog.py" line="273" />
      <source>English</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="622" />
      <location filename="../settings_dialog.py" line="276" />
      <source>Language</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="281" />
      <source>Application Style</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="808" />
      <location filename="../settings_dialog.py" line="286" />
      <source>Browse</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="292" />
      <source>Temp Directory</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="509" />
      <location filename="../settings_dialog.py" line="294" />
      <source>Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="300" />
      <source>Capture Delay</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="302" />
      <source>Hide Main Window During Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="303" />
      <source>Show Main Window After Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="307" />
      <source>Saver</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="309" />
      <source>Automatically save new captures to default location</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="310" />
      <source>Prompt to save before discarding unsaved changes</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="311" />
      <source>Remember last Save Directory</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="315" />
      <source>Capture save location</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="318" />
      <source>Directory of the last opened file</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="327" />
      <location filename="../settings_dialog.py" line="321" />
      <source>PNG image (*.png)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="322" />
      <source>Ksnip project (*.ksnip)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="324" />
      <source>Default save format:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="328" />
      <source>JPEG image (*.jpg)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="329" />
      <source>WebP image (*.webp)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="330" />
      <source>BMP image (*.bmp)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="332" />
      <source>Image saved alongside Ksnip projects:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="338" />
      <source>Open file dialogs in:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="343" />
      <source>Ksnip Projects (*.ksnip)</source>
      <translation>Projektet Ksnip (*.ksnip)</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="1073" />
      <location filename="../settings_dialog.py" line="345" />
      <source>Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="348" />
      <source>Default file type selected in the File &gt; Open dialog.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="351" />
      <source>Default file type in Open dialog:</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="358" />
      <source>Save Quality</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="798" />
      <location filename="../settings_dialog.py" line="360" />
      <source>Default</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="362" />
      <source>Factor</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="1111" />
      <location filename="../settings_dialog.py" line="374" />
      <source>Capture save location and filename</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="377" />
      <source>Supports $Y, $M, $D, $h, $m, $s, $T and consecutive # characters as a counter.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="614" />
      <location filename="../settings_dialog.py" line="582" />
      <location filename="../settings_dialog.py" line="378" />
      <source>Browse...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="383" />
      <source>Overwrite file with same name</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="387" />
      <source>Image Grabber</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="389" />
      <source>Capture mouse cursor on screenshot</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="390" />
      <source>Show Main Window after capturing screenshot</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="392" />
      <source>Hide Main Window during screenshot</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="394" />
      <source>Force Generic Wayland (xdg-desktop-portal) Screenshot</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="395" />
      <source>Scale Generic Wayland (xdg-desktop-portal) Screenshots</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="396" />
      <source>Use the desktop screenshot portal for every capture mode, including on X11.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="398" />
      <source>Apply the primary screen scale factor to portal screenshots without resampling their pixels.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="406" />
      <source>Delays</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="413" />
      <source>Implicit capture delay</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="415" />
      <source>Snipping Area</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="417" />
      <source>Freeze Image while snipping</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="419" />
      <source>Show magnifying glass on snipping area</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="421" />
      <source>Show Snipping Area rulers</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="423" />
      <source>Show Snipping Area position and size info</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="425" />
      <source>Allow resizing rect area selection by default</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="427" />
      <source>Show Snipping Area info text</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="439" />
      <source>Appearance</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="453" />
      <source>Snipping Area adorner color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="454" />
      <source>Snipping Area cursor color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="455" />
      <source>Snipping Area cursor thickness</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="456" />
      <source>Snipping Area Transparency</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="458" />
      <source>Annotator</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="460" />
      <source>Remember annotation tool selection and load on startup</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="461" />
      <source>Switch to Select Tool after drawing Item</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="462" />
      <source>Select Item after drawing</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="463" />
      <source>Grab selected item when clicking it (Illustrator-style)</source>
      <translation>Kap elementin e zgjedhur kur klikon mbi të (stili Illustrator)</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="465" />
      <source>Number Tool Seed change updates all Number Items</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="466" />
      <source>Show Controls Widget</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="467" />
      <source>Smooth Painter Paths</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="480" />
      <source>Canvas</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="488" />
      <source>Smooth Factor</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="489" />
      <source>Canvas Color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="490" />
      <source>Tray Icon</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="493" />
      <source>Use Tray Icon</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="494" />
      <source>Minimize To Tray</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="495" />
      <source>Close To Tray</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="496" />
      <source>Start Minimized To Tray</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="497" />
      <source>Display Tray Notifications</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="505" />
      <source>Default Action</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="508" />
      <source>Show Editor</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="510" />
      <source>Action</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="513" />
      <source>Rect Area</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="514" />
      <source>Last Rect Area</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="515" />
      <source>Full Screen</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="516" />
      <source>Current Screen</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="517" />
      <source>Active Window</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="518" />
      <source>Window Under Cursor</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="519" />
      <source>Portal</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="520" />
      <source>Capture Mode</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="522" />
      <source>Application Shortcuts</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="524" />
      <source>Enable Application Shortcuts</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="527" />
      <source>These shortcuts work while ksnip is active. For system-wide shortcuts, configure your desktop to run the ksnip command-line capture actions.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="537" />
      <source>Rect Area Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="538" />
      <source>Last Rect Area Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="539" />
      <source>Full Screen Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="540" />
      <source>Current Screen Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="541" />
      <source>Active Window Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="542" />
      <source>Window Under Cursor Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="543" />
      <source>Portal Capture</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="544" />
      <source>Open Image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="545" />
      <source>Save</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="546" />
      <source>Paste Image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="547" />
      <source>Pin Image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="548" />
      <source>Add Watermark</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="549" />
      <source>Upload Image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="550" />
      <source>OCR Text Recognition</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="554" />
      <source>Clear</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="564" />
      <source>Uploader</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="566" />
      <source>Ask for confirmation before uploading</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="605" />
      <location filename="../settings_dialog.py" line="588" />
      <location filename="../settings_dialog.py" line="571" />
      <source>Script</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="576" />
      <source>Uploader Type</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="578" />
      <source>Script Uploader</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="590" />
      <source>Copy script output to clipboard</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="594" />
      <source>Filter</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="596" />
      <source>Treat stderr as failure</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="598" />
      <source>OCR</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="600" />
      <source>Enable OCR actions</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="602" />
      <source>PaddleOCR (plain text)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="603" />
      <source>PaddleOCR (Markdown tables)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="604" />
      <source>PaddleOCR (HTML tables)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="608" />
      <source>Spanish</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="609" />
      <source>Spanish + English (script backend recommended)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="610" />
      <source>Recognize mathematical formulas (LaTeX)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="611" />
      <source>Copy OCR result to clipboard automatically</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="621" />
      <source>Backend</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="625" />
      <source>Script Path</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="629" />
      <source>Color scheme for misspelled words</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="631" />
      <source>%1 base scheme colors used by the Text tool fill color on the left and the underline color for misspelled words on the right.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="817" />
      <location filename="../settings_dialog.py" line="637" />
      <source>Name</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="637" />
      <source>Text fill color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="637" />
      <source>Underline color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="687" />
      <source>Imgur Uploader</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="689" />
      <source>Native Imgur uploader parity is still pending.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="700" />
      <source>FTP Uploader</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="702" />
      <source>Native FTP uploader parity is still pending.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="720" />
      <source>Stickers</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="722" />
      <source>Sticker management and picker parity are still pending.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="753" />
      <source>OK</source>
      <translation>OK</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="754" />
      <source>Cancel</source>
      <translation>Anuloje</translation></message>
    <message>
      <location filename="../settings_dialog.py" line="775" />
      <source>Actions</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="779" />
      <source>Add</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="785" />
      <source>Add new actions by pressing the 'Add' tab button.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="793" />
      <source>Plugins</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="796" />
      <source>Search Path</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="817" />
      <source>Version</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="827" />
      <source>Detect</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="866" />
      <source>Select color</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="1061" />
      <source>No watermark image configured</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="1063" />
      <source>%1x%2 image configured</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="1071" />
      <source>Select watermark image</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="1078" />
      <source>Unable to load watermark image: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="1103" />
      <source>Select upload script</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../settings_dialog.py" line="1119" />
      <source>Select OCR script</source>
      <translation type="unfinished" /></message>
    <message>
      <source>PaddleOCR (tables + Markdown)</source>
      <translation type="vanished">PaddleOCR (tablas + Markdown)</translation>
    </message>
    <message>
      <source>Auto resize to content</source>
      <translation type="vanished">Ajustar automáticamente al contenido</translation>
    </message>
    <message>
      <source>Global HotKeys</source>
      <translation type="vanished">Atajos globales</translation>
    </message>
    <message>
      <source>Enable Global HotKeys</source>
      <translation type="vanished">Activar atajos globales</translation>
    </message>
    <message>
      <source>Cut</source>
      <translation type="vanished">Cortar</translation>
    </message>
    <message>
      <source>Application Settings</source>
      <translation type="vanished">Configuración de la aplicación</translation>
    </message>
    <message>
      <source>Image Grabber Settings</source>
      <translation type="vanished">Configuración del capturador de imágenes</translation>
    </message>
    <message>
      <source>Saver Settings</source>
      <translation type="vanished">Configuración de guardado</translation>
    </message>
    <message>
      <source>Tray Icon Settings</source>
      <translation type="vanished">Configuración del icono de bandeja</translation>
    </message>
    <message>
      <source>HotKeys</source>
      <translation type="vanished">Atajos</translation>
    </message>
    <message>
      <source>Uploader Settings</source>
      <translation type="vanished">Configuración del subidor</translation>
    </message>
    <message>
      <source>Script Uploader Settings</source>
      <translation type="vanished">Configuración del subidor mediante script</translation>
    </message>
    <message>
      <source>OCR Settings</source>
      <translation type="vanished">Configuración de OCR</translation>
    </message>
    <message>
      <source>Snipping Area Settings</source>
      <translation type="vanished">Configuración del área de recorte</translation>
    </message>
    <message>
      <source>Annotator Settings</source>
      <translation type="vanished">Configuración del anotador</translation>
    </message>
    <message>
      <source>Watermark Settings</source>
      <translation type="vanished">Configuración de marca de agua</translation>
    </message>
    <message>
      <source>Action Settings</source>
      <translation type="vanished">Configuración de acciones</translation>
    </message>
    <message>
      <source>Plugin Settings</source>
      <translation type="vanished">Configuración de plugins</translation>
    </message>
    <message>
      <source>Scheme colors</source>
      <translation type="vanished">Colores de esquema</translation>
    </message>
    <message>
      <source>Imgur Uploader Settings</source>
      <translation type="vanished">Configuración del subidor de Imgur</translation>
    </message>
    <message>
      <source>FTP Uploader Settings</source>
      <translation type="vanished">Configuración del subidor FTP</translation>
    </message>
    <message>
      <source>Sticker Settings</source>
      <translation type="vanished">Configuración de adhesivos</translation>
    </message>
  </context>
  <context>
    <name>SpellCheckTextEdit</name>
    <message>
      <location filename="../spellcheck.py" line="301" />
      <source>No suggestions</source>
      <translation type="unfinished" /></message>
  </context>
  <context>
    <name>StickerPickerDialog</name>
    <message>
      <location filename="../sticker_picker.py" line="114" />
      <source>Select Sticker</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="117" />
      <source>Pinned Stickers</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="161" />
      <source>Use the star button to pin frequently used stickers.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="171" />
      <source>User</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="193" />
      <source>Add Images...</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="196" />
      <source>Open Here with File Manager</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="205" />
      <source>Add your own images to use them as stickers.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="207" />
      <source>Sticker theme is not installed: %1</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="228" />
      <source>Add Sticker Images</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="230" />
      <source>Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.svg *.xpm);;All Files (*)</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="238" />
      <source>Unable to Add Images</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="239" />
      <source>Some files could not be imported as stickers.</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="270" />
      <location filename="../sticker_picker.py" line="255" />
      <source>Unpin Sticker</source>
      <translation type="unfinished" /></message>
    <message>
      <location filename="../sticker_picker.py" line="270" />
      <source>Pin Sticker</source>
      <translation type="unfinished" /></message>
  </context>
  <context>
    <name>TextInputDialog</name>
    <message>
      <location filename="../canvas.py" line="24" />
      <source>Shift+Enter adds a new line. Ctrl+Enter accepts.</source>
      <translation type="unfinished" /></message>
  </context>
</TS>
