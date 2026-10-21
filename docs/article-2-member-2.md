# Automatizando backups y despliegues de MongoDB con GitHub Actions, Docker y Render

*Artículo 2 de 2. Imágenes: `docs/img/02-pipeline.png` y `docs/img/03-app-ui.png` (los lugares están marcados en el texto).*

Un backup que depende de que alguien se acuerde de ejecutarlo fallará el día que lo necesites. En este artículo tomo una app Flask + MongoDB y automatizo todo lo que la rodea: pruebas, una verificación real de backup y restauración en cada push, despliegue en una nube pública, backups diarios cifrados y un simulacro semanal de restauración.

- Código fuente: https://github.com/IvanQuispeHuallpa/nosql-backup-strategy
- App en vivo: {{APP_URL}}
- Video: {{VIDEO_URL}}
- Artículo complementario (herramienta y estrategia de backup): {{ARTICLE_1_URL}}

## El stack

- **App:** API Flask con una pequeña interfaz web, empaquetada en una imagen Docker que incluye `mongodump` y `mongorestore`.
- **Base de datos:** MongoDB Atlas M0 (gratis). No tiene backups en la nube, justamente por eso automatizamos los nuestros.
- **Hosting:** Render (servicio web Docker, plan gratuito).
- **Automatización:** GitHub Actions.

**[Insertar imagen: 03-app-ui.png]** *La app desplegada: notas en vivo y el panel de backups.*

## Reproducible con Docker

`docker compose up` levanta MongoDB 7 y la app con un healthcheck, de modo que la base está lista antes de que arranque la app. El Dockerfile instala las MongoDB Database Tools oficiales para la arquitectura de CPU correcta, así que la misma imagen funciona en un portátil y en la nube, y corre como usuario sin privilegios.

## El pipeline

**[Insertar imagen: 02-pipeline.png]**

`.github/workflows/ci-cd.yml` se ejecuta en cada push:

1. **Pruebas unitarias** con pytest.
2. **Simulacro de backup contra un MongoDB real** (un contenedor de servicio): carga datos, `app.backup create` y luego `app.backup verify`. Si un cambio rompe la herramienta de backup, el pipeline falla *antes* de desplegar.
3. **Despliegue** (solo en `main`): un `curl` al deploy hook de Render, guardado como el secreto `RENDER_DEPLOY_HOOK_URL`.

```yaml
deploy:
  needs: test
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  steps:
    - run: curl -fsS -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
```

## Backups programados

El plan gratuito de Render no tiene cron jobs y su disco es desechable, así que los backups los toma un workflow programado de GitHub Actions (`backup.yml`, a diario a las 06:00 UTC):

1. Instala las Database Tools y ejecuta `python -m app.backup create` contra Atlas (secreto `MONGODB_URI`).
2. **Cifra** el archivo con `openssl enc -aes-256-cbc -pbkdf2`. Los artefactos de repositorios públicos los puede descargar cualquiera, así que un dump sin cifrar sería una fuga de datos.
3. Lo sube como artefacto con 30 días de retención.

## El simulacro semanal de restauración

`restore-drill.yml` cierra el ciclo cada lunes: descarga el último backup, lo descifra, lo restaura en un contenedor MongoDB desechable y comprueba que los conteos coinciden con el manifiesto. Si se pierde la contraseña, el archivo se corrompe o cambia el formato, te enteras el lunes por la mañana y no durante un incidente.

## Desplegar en Render

1. Crea un cluster gratuito en MongoDB Atlas, un usuario de base de datos y permite el acceso de red desde `0.0.0.0/0` (las instancias gratuitas de Render no tienen IP fija).
2. Sube el repositorio a GitHub. En Render elige **New → Blueprint** y selecciónalo; `render.yaml` define el servicio.
3. Define `MONGODB_URI` en Render y copia la URL del **Deploy Hook** del servicio.
4. Agrega los secretos de GitHub: `RENDER_DEPLOY_HOOK_URL`, `MONGODB_URI` y `BACKUP_PASSPHRASE`.

Desde entonces, `git push` es todo el proceso de release.

## Lecciones aprendidas

- Verifica las restauraciones, no solo los backups. Los conteos en un manifiesto son una comprobación barata y eficaz.
- Prueba las herramientas en CI contra una base real: una ejecución real descubrió que `mongodump` no tiene la opción `--nsInclude` (`mongorestore` sí).
- Trata los secretos y los dumps como información sensible desde el primer día.

Lee la estrategia detrás de la herramienta en el artículo complementario: {{ARTICLE_1_URL}}. Código completo: https://github.com/IvanQuispeHuallpa/nosql-backup-strategy.

*Etiquetas para Medium: MongoDB, GitHubActions, DevOps, Docker, Backup*
