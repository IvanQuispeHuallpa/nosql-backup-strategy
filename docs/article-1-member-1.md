# Una estrategia práctica de backup para MongoDB: dumps, checksums y retención

*Artículo 1 de 2. Imágenes: `docs/img/01-architecture.png` y `docs/img/04-terminal-restore.png` (los lugares están marcados en el texto).*

La replicación no es un backup. Si alguien ejecuta `db.dropDatabase()` (o un bug borra los documentos equivocados), todas las réplicas aplican el error fielmente en milisegundos. Una estrategia de backup real responde tres preguntas: **¿cuántos datos podemos perder (RPO)?, ¿cuánto tiempo podemos estar caídos (RTO)? y ¿alguna vez hemos restaurado un backup de verdad?**

En este artículo construyo la primera mitad de un proyecto pequeño: una app Flask + MongoDB con una herramienta completa de backup y restauración, y explico las decisiones detrás de ella.

- Código fuente: https://github.com/IvanQuispeHuallpa/nosql-backup-strategy
- App en vivo: {{APP_URL}}
- Video: {{VIDEO_URL}}
- Artículo complementario (CI/CD, automatización y despliegue): {{ARTICLE_2_URL}}

## El escenario

El plan gratuito de MongoDB Atlas (M0) no incluye backups en la nube, así que la estrategia es nuestra responsabilidad. La app es deliberadamente pequeña (una API de notas) porque lo importante es la protección de los datos que la rodea.

**[Insertar imagen: 01-architecture.png]** *Los usuarios hablan con la app, la app con Atlas, y un job programado extrae backups lógicos cifrados de la base de datos.*

## Elegir el tipo de backup

| Método | Ideal para | Costo |
|---|---|---|
| Lógico (`mongodump`) | Datos pequeños o medianos, portable entre versiones, restauración selectiva | Más lento en datasets grandes; el punto en el tiempo es el momento del dump |
| Snapshot de disco/volumen | Despliegues grandes autoalojados | Requiere disciplina con journaling/bloqueos y depende del almacenamiento |
| Oplog / continuo (Atlas, Ops Manager) | Recuperación a un punto en el tiempo, RPO mínimo | Plan de pago o más infraestructura |

Para una base gratuita y un RPO diario, `mongodump --gzip --archive` es la herramienta adecuada: un archivo comprimido por backup, fácil de mover y de cifrar.

## La herramienta de backup

Todo vive en `app/backup.py`. Crear un backup es una llamada a un subproceso más algo de contabilidad:

```python
subprocess.run(
    ["mongodump", f"--uri={_server_uri(uri)}", f"--db={db}", "--gzip", f"--archive={archive}"],
    check=True, capture_output=True, text=True,
)
```

Junto a cada archivo escribo un **manifiesto** con el SHA-256 y el número de documentos por colección en el momento del dump:

```json
{
  "name": "notesdb-20261021T091008Z",
  "size_bytes": 460,
  "sha256": "6ed7470a…",
  "counts": { "notes": 10 }
}
```

El manifiesto da dos verificaciones baratas: el checksum detecta un archivo corrupto o alterado *antes* de restaurar (`restore_backup` se niega a correr si no coincide), y los conteos permiten demostrar que la restauración recuperó todo.

## Retención

Guardar backups para siempre cuesta dinero; guardar uno solo es una apuesta. La herramienta conserva los N más recientes (`BACKUP_KEEP`, por defecto 7) y borra el resto tras cada ejecución. Una política común en producción es 7 diarios + 4 semanales + 12 mensuales; la función `prune` es el lugar para extenderla.

## Restaurar, y el simulacro que importa

La restauración usa `mongorestore --drop`, que reemplaza las colecciones existentes por las del backup. Pero el comando más importante es `verify`: restaura en una **base temporal** (`restore_check`), compara los conteos con el manifiesto y elimina esa base. Nunca toca los datos de producción.

Este es el ciclo completo en mi máquina: backup, un desastre deliberado, restauración y verificación.

**[Insertar imagen: 04-terminal-restore.png]**

El desastre eliminó toda la base (`after disaster: 0`) y la restauración la recuperó (`after restore: 10`).

## Notas de seguridad

- Los endpoints de backup de la app están deshabilitados salvo que se defina `ADMIN_TOKEN`, y exigen ese valor en la cabecera `X-Admin-Token`. Un botón público de "restaurar" sin autenticación sería un regalo para los atacantes.
- Los dumps contienen todos tus datos: cífralos antes de guardarlos en cualquier lugar compartido (el artículo complementario lo hace con AES-256).
- Nunca subas cadenas de conexión al repositorio. Viven en variables de entorno y secretos de CI.

## Pruébalo tú mismo

```bash
git clone https://github.com/IvanQuispeHuallpa/nosql-backup-strategy
cd nosql-backup-strategy
docker compose up -d --build
docker compose exec app python scripts/seed.py
docker compose exec app python -m app.backup create
docker compose exec app python -m app.backup list
docker compose exec app python -m app.backup verify <nombre-del-backup>
```

## Lo que sigue

Una herramienta de backup que hay que acordarse de ejecutar no es una estrategia. En el artículo complementario la automatizo con GitHub Actions (backups diarios, simulacro semanal de restauración y despliegue en cada push) y despliego la app en una nube pública: {{ARTICLE_2_URL}}.

*Etiquetas para Medium: MongoDB, NoSQL, Backup, DevOps, Base de datos*
