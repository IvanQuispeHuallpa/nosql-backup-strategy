# Checklist del equipo (2 integrantes)

Hecho: app, scripts de backup/restore, Docker, workflows, imágenes, borradores de los 2 artículos y guion del video.

## Integrante 1 (repo y despliegue)
1. Repo público en GitHub con el proyecto.
2. Cluster gratis en MongoDB Atlas (M0), usuario de BD, Network Access `0.0.0.0/0`.
3. Render: Blueprint desde el repo, `MONGODB_URI`, Deploy Hook.
4. Secretos de GitHub: `RENDER_DEPLOY_HOOK_URL`, `MONGODB_URI`, `BACKUP_PASSPHRASE`.
5. Ejecutar manualmente `Scheduled backup` y `Weekly restore drill`.
6. Grabar y subir el video a YouTube (público).
7. Publicar el Artículo 1 en Medium (imágenes 01 y 04).

## Integrante 2
1. Publicar el Artículo 2 en Medium (imágenes 02 y 03; la 03 mejor tomada de la app desplegada).
2. Ajustar el texto con sus propias palabras.

## Entre los dos
1. Reemplazar los `{{...}}` en los artículos y los TODO del README.
2. Enviar los links (2 artículos, video, repo, app) al grupo de Telegram.
3. Subir a la tarea un zip con un `.txt` con esos links.
