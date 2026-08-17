# Ejecución manual de los paquetes en GitHub Actions

## Comportamiento configurado

Los workflows de Linux, Windows y macOS continúan ejecutando sus trabajos de
compilación y pruebas cuando se crea un `push` o un `pull_request`. Sin embargo,
los trabajos que generan paquetes solamente se ejecutan cuando una persona
inicia manualmente el workflow mediante `workflow_dispatch`.

| Workflow | Paquetes manuales |
| --- | --- |
| `linux.yml` | AppImage, RPM y DEB |
| `windows.yml` | ZIP/EXE y MSI |
| `macos.yml` | DMG |

Por tanto, estos comandos ya no generan paquetes automáticamente:

```bash
git add .
git commit
git push
```

El `push` puede seguir iniciando las pruebas automáticas. Esto es intencional:
permite detectar errores sin gastar tiempo en crear y publicar todos los
paquetes.

## Advertencia sobre el estado del port

Los workflows existentes todavía utilizan CMake, las fuentes C++ bajo `src/`
y los scripts históricos de empaquetado. En su estado actual generan paquetes
del ksnip C++ de referencia, no paquetes finales del port `ksnip_py`.

No deben presentarse como paquetes oficiales de ksnip_py hasta completar la
tarea de migración de CI y empaquetado indicada en `ROADMAP.md`.

## Iniciar un workflow desde la página de GitHub

1. Abra el repositorio en GitHub.
2. Entre en la pestaña **Actions**.
3. En la columna izquierda seleccione uno de estos workflows:
   - **linux**;
   - **windows**;
   - **macOS**.
4. Pulse **Run workflow**.
5. Seleccione la rama que desea construir, normalmente `master`.
6. Pulse el botón verde **Run workflow** para confirmar.
7. Abra la nueva ejecución para observar cada trabajo y sus registros.

Una ejecución manual de `linux` construye los tres formatos Linux después de
que finalicen sus pruebas. Una ejecución manual de `windows` construye tanto el
ZIP como el MSI. Actualmente no existe un selector para pedir solamente uno de
los formatos.

## Descargar los artefactos

1. Abra la ejecución terminada desde **Actions**.
2. Desplácese hasta la sección **Artifacts**.
3. Descargue el artefacto deseado.

Los nombres configurados actualmente incluyen:

```text
ksnip.AppImage
ksnip.rpm
ksnip.deb
ksnip-windows.zip
ksnip-windows.msi
ksnip-macos.dmg
```

## Ejecutar manualmente mediante GitHub CLI

Si `gh` está instalado y autenticado:

```bash
gh auth status
```

Inicie el workflow deseado:

```bash
gh workflow run linux.yml --ref master
gh workflow run windows.yml --ref master
gh workflow run macos.yml --ref master
```

Consulte las ejecuciones recientes:

```bash
gh run list --limit 10
```

Para seguir una ejecución concreta:

```bash
gh run watch ID_DE_LA_EJECUCIÓN
```

Para descargar sus artefactos:

```bash
gh run download ID_DE_LA_EJECUCIÓN
```

## Publicación de releases

Los trabajos históricos no se limitan a crear artefactos: también contienen
pasos para eliminar una release previa con el mismo nombre y subir los paquetes
a una release de GitHub. Por ello, no se debe pulsar **Run workflow** como una
simple prueba sin revisar primero:

- la rama o etiqueta seleccionada;
- la versión y el nombre de release calculados por los scripts;
- los artefactos que se publicarán;
- los secretos requeridos para firma en Windows o macOS;
- que realmente se desea publicar el binario C++ heredado.

Para futuras pruebas sin publicación conviene separar en otro cambio la
creación de artefactos y la publicación de releases mediante una opción manual
explícita.

## Resumen para el mantenedor

- `git push`: ejecuta pruebas, pero no crea paquetes.
- **Actions > linux > Run workflow**: crea manualmente AppImage, RPM y DEB.
- **Actions > windows > Run workflow**: crea manualmente ZIP y MSI.
- **Actions > macOS > Run workflow**: crea manualmente DMG.
- Una ejecución manual puede publicar releases; revise sus datos antes de
  iniciarla.
- Los paquetes actuales corresponden todavía al código C++ histórico.
