# Uso de IA en la ES3

## Herramienta que utilicé

Para desarrollar la ES3 utilicé Cursor, trabajando sobre el mismo proyecto que había realizado en la ES2. Fui consultando mis dudas por partes, principalmente para resolver problemas con la API, la seguridad y las reglas de negocio.

La IA me sirvió como apoyo, pero no todo lo que me recomendó estaba correcto para mi proyecto. Por eso tuve que revisar las respuestas, hacer algunos cambios y descartar las soluciones que no me parecían adecuadas.

A continuación, explico algunos ejemplos de lo que consulté y cómo lo resolví.

## 1. Seguridad: probar la API sin token

**¿Qué le pregunté a la IA?**

Le pregunté por qué me aparecía un error 401 al ingresar a `/api/registros/` y si el problema podía ser la ruta o el token.

**¿Qué me respondió?**

Me recomendó usar `AllowAny` para permitir el acceso sin autenticación mientras hacía las pruebas.

**¿Qué problema encontré?**

Me di cuenta de que esa opción dejaba la API abierta para cualquier persona. Si se me olvidaba quitarla después, podía terminar entregando el proyecto sin la seguridad correspondiente.

Además, el error 401 no significaba que la API estuviera mala, sino que estaba intentando ingresar sin enviar un token.

**¿Qué hice finalmente?**

Decidí mantener la autenticación con `IsAuthenticated` y obtener el token desde `/api/token/`. Después hice las pruebas enviando el token en la cabecera `Authorization: Bearer`.

También dejé registrada una prueba para comprobar que, al intentar ingresar sin token, la API responde con un error 401, que es lo esperado.

## 2. Seguridad: los campos del registro

**¿Qué le pregunté a la IA?**

Le pedí ayuda para crear el serializer del modelo `Registro`.

**¿Qué me respondió?**

Me propuso utilizar `fields = "__all__"`, que permite incluir automáticamente todos los campos del modelo.

**¿Qué problema encontré?**

Al revisar esa solución, vi que se podían exponer campos que no necesitaba mostrar, como `eliminado`, `usuario` y `liberada`.

También existía el riesgo de que alguien enviara un resultado directamente desde el JSON, por ejemplo, indicando que un registro estaba aceptado, aunque no cumpliera con las condiciones del sistema.

**¿Qué hice finalmente?**

Preferí definir los campos manualmente y dejar `resultado` y `fecha` como campos de solo lectura.

De esta manera, el resultado no depende de lo que envíe el usuario, sino de la función `decidir()`, que aplica las reglas del proyecto.

Para comprobarlo, hice una prueba enviando el resultado como "Aceptado", pero con cuatro inasistencias. La API respondió "Rechazado", demostrando que se estaba aplicando la regla de negocio correctamente.

## 3. Seguridad: dónde guardar el token

**¿Qué le pregunté a la IA?**

Le consulté cómo podía guardar el token para realizar mis pruebas con `curl`.

**¿Qué me respondió?**

Me sugirió guardarlo en una variable dentro del script o enviarlo como parámetro en la URL.

**¿Qué problema encontré?**

No me pareció una buena idea porque el token podía quedar expuesto en el código, en el historial de consultas o en los registros del sistema.

Además, revisé que los tokens simples de DRF no tienen una fecha de expiración predeterminada, por lo que podían seguir funcionando si alguien los obtenía.

**¿Qué hice finalmente?**

Decidí trabajar con JWT utilizando `simplejwt`. Así, el token de acceso dura 30 minutos y se puede renovar mediante `/api/token/refresh/`.

También dejé el token en la cabecera `Authorization` y configuré las credenciales de prueba mediante un archivo `.env`, evitando dejar las claves directamente en el código.

Con esto mejoré la seguridad de las pruebas y dejé una forma más ordenada de manejar la autenticación.

## 4. Aplicar las reglas del proyecto en el ViewSet

**¿Qué le pregunté a la IA?**

Le pregunté cómo podía utilizar mi función `decidir()` dentro de `perform_create()`.

**¿Qué me respondió?**

Me entregó un ejemplo que utilizaba `edad` y `cupos_libres()`, siguiendo una estructura genérica.

**¿Qué problema encontré?**

El ejemplo no coincidía completamente con mi proyecto. Mi modelo utiliza el campo `inasistencias`, no `edad`. Además, mi función `cupos_libres()` necesita recibir una lista de datos y no podía utilizarla directamente de esa manera.

También me faltaba considerar qué pasaría si se modificaban las inasistencias de un registro, porque el resultado anterior podía quedar desactualizado.

**¿Qué hice finalmente?**

Adapté la solución a la estructura que ya tenía desarrollada. Utilicé `cupos_para()` para calcular los cupos disponibles a partir de los datos de la base de datos.

También agregué `perform_update()` para recalcular el resultado cuando se modifica un registro y `perform_destroy()` para utilizar `soft_delete()`, de modo que los registros no se eliminen definitivamente.

Así pude mantener la lógica del proyecto y evitar copiar un ejemplo que no estaba preparado para mi caso.

## ¿Qué aprendí al utilizar IA?

En este trabajo aprendí que la inteligencia artificial puede ayudar bastante a resolver dudas y avanzar más rápido, pero sus respuestas no siempre se ajustan a lo que uno está desarrollando.

En mi caso, tuve que revisar las recomendaciones, entender qué problemas podían generar y adaptarlas a la estructura de mi proyecto.

Por ejemplo, descarté la opción de dejar la API abierta para hacer pruebas, evité exponer todos los campos del modelo y cambié la forma de manejar los tokens para mejorar la seguridad.

También entendí que no basta con que el código funcione. Es importante comprobar que respete las reglas de negocio y que se comporte correctamente cuando se crean, modifican o eliminan registros.

En conclusión, utilicé la IA como una herramienta de apoyo, pero las decisiones finales las tomé revisando el código y probando las soluciones dentro de mi propio proyecto.