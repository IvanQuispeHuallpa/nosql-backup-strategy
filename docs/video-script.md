# Guion del video (máx. 5 min, YouTube)

Título: *Estrategia de backup NoSQL con MongoDB: backup, desastre y restauración (GitHub Actions + Render)*
Graba la pantalla con OBS (o Win+G) narrando. Objetivo: 4:00 a 4:30.

| Tiempo | Pantalla | Qué decir |
|---|---|---|
| 0:00 | Portada/README | Quiénes somos, tema y objetivo: una estrategia de backup para MongoDB, construida, automatizada y desplegada. |
| 0:20 | `docs/img/01-architecture.png` | Explicar app, Atlas y el job programado que extrae dumps cifrados. |
| 0:50 | Repo público en GitHub | Mostrar `app/backup.py`, `Dockerfile`, `.github/workflows`. |
| 1:20 | Terminal: `docker compose up -d --build`, `seed.py` | App corriendo en local con 10 notas. |
| 1:50 | Terminal: `app.backup create` | Mostrar el manifiesto (sha256, conteos). |
| 2:15 | Terminal: `db.dropDatabase()`, luego `restore` y `verify` | El desastre y la recuperación: conteo de vuelta a 10 y `ok: true`. |
| 2:55 | Pestaña Actions de GitHub | Ejecución verde de CI/CD, el backup programado y su artefacto cifrado. |
| 3:30 | Panel de Render y la URL de la app | Desplegada por el pipeline; crear un backup desde la UI con el token de admin. |
| 4:15 | Cierre | Enlaces a los dos artículos de Medium y al repo. |

Súbelo a YouTube como **Público**.
