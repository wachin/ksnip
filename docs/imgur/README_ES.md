# Port futuro del uploader de Imgur

El uploader nativo de Imgur de ksnip_py queda aplazado deliberadamente para
priorizar otros arreglos. Este documento reúne lo necesario para retomarlo sin
tener que repetir la investigación.

## Requisito de la API oficial

Imgur exige que cada aplicación cliente se registre y reciba sus propias
credenciales. Incluso una subida anónima necesita enviar un `Client ID` en la
cabecera de autorización:

```text
Authorization: Client-ID SU_CLIENT_ID
```

La documentación oficial vigente está en:

- <https://apidocs.imgur.com/>
- <https://api.imgur.com/oauth2/addclient>

No se debe reutilizar ni copiar al port Python el `Client ID` incrustado en el
código C++ antiguo. ksnip_py es otra aplicación y debe utilizar un registro
propio, especialmente si se pretende distribuirla mediante Debian.

## Cómo registrar ksnip_py

Cuando se decida continuar:

1. Iniciar sesión en Imgur.
2. Abrir <https://api.imgur.com/oauth2/addclient>.
3. Registrar una aplicación para ksnip_py.
4. Indicar un nombre reconocible, por ejemplo `ksnip_py`.
5. Para comenzar solamente con subidas anónimas, elegir el tipo de autorización
   sin devolución OAuth que ofrezca Imgur en ese momento.
6. Proporcionar el correo y los datos solicitados por Imgur.
7. Guardar el `Client ID` entregado.
8. No publicar, confirmar en Git ni incluir en capturas el `Client Secret`.

Los nombres de las opciones del formulario pueden cambiar. Antes de registrar
la aplicación se debe volver a comprobar la documentación oficial.

## Primera fase recomendada: subida anónima

La primera implementación debería incluir:

- campo configurable para el `Client ID`;
- URL base predeterminada `https://api.imgur.com`;
- subida PNG mediante la API v3;
- título y descripción configurables;
- opción para devolver el enlace directo a la imagen o la página de Imgur;
- copia opcional del enlace al portapapeles;
- apertura opcional en el navegador;
- ejecución asíncrona mediante `QNetworkAccessManager` de Qt6;
- indicador de progreso y cancelación de la petición;
- análisis seguro de la respuesta JSON;
- mensajes para errores HTTP, red, autorización y límites de la API;
- conservación del `deletehash` de subidas anónimas para poder eliminarlas;
- historial local con permisos apropiados y sin credenciales.

La petición utilizará conceptualmente:

```text
POST https://api.imgur.com/3/image
Authorization: Client-ID SU_CLIENT_ID
```

La forma exacta del cuerpo y la respuesta debe implementarse conforme a la API
oficial disponible cuando se retome el trabajo.

## Configuración y seguridad

- El repositorio no debe contener credenciales reales.
- Las pruebas automatizadas deben usar respuestas simuladas.
- El `Client ID` puede ser configurable, pero no debe aparecer en registros de
  depuración innecesarios.
- Un `Client Secret`, token de acceso o token de renovación requiere un almacén
  de secretos adecuado; no debe guardarse como texto plano en `QSettings` sin
  una decisión de seguridad explícita.
- Antes de subir debe respetarse la confirmación configurada, pues la imagen se
  enviará a un servicio externo.
- La interfaz debe explicar que una subida anónima no equivale necesariamente a
  una imagen privada.

## Segunda fase opcional: cuenta de usuario

La integración con una cuenta requiere OAuth2 y amplía considerablemente el
alcance:

- autorización en el navegador;
- recepción o introducción segura del resultado de autorización;
- tokens de acceso y renovación;
- renovación de tokens expirados;
- subida asociada a la cuenta;
- cierre de sesión y eliminación local de credenciales;
- revisión del almacenamiento seguro en Linux, Windows y macOS.

Esta fase no debe mezclarse con la primera subida anónima salvo que se decida
explícitamente asumir ese alcance.

## Pruebas necesarias

Antes de declarar terminado el port se deben comprobar:

1. Respuesta exitosa simulada con enlace y `deletehash`.
2. `Client ID` ausente o inválido.
3. Imagen nula o imposible de convertir a PNG.
4. Respuesta JSON inválida o incompleta.
5. Errores HTTP 400, 401, 403, 429 y 5xx.
6. Fallo de DNS, TLS, desconexión y tiempo de espera.
7. Cancelación sin congelar la interfaz.
8. Copia al portapapeles y apertura en navegador.
9. Enlace directo frente a página de Imgur.
10. Una subida real autorizada por el desarrollador con una imagen de prueba que
    no contenga información privada.

## Estado actual

- La implementación C++ original fue revisada como referencia.
- La API oficial continúa exigiendo el registro de cada aplicación.
- ksnip_py todavía no contiene un uploader nativo de Imgur.
- No se han añadido credenciales al repositorio.
- El trabajo está aplazado y puede retomarse desde este documento.
