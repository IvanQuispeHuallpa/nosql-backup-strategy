# Estrategia de backup NoSQL (MongoDB)

App de demostración Flask + MongoDB con una estrategia completa de backup: backups lógicos con `mongodump`, manifiestos SHA-256, retención, restauración, simulacro de restauración y automatización con GitHub Actions. Desplegada con Docker en Render usando MongoDB Atlas.

- App en vivo: https://nosql-backup-strategy.onrender.com

## Ejecutar en local

```bash
docker compose up -d --build
docker compose exec app python scripts/seed.py
# abrir http://localhost:8000  (token de admin: change-me)
```

## CLI de backup

```bash
docker compose exec app python -m app.backup create
docker compose exec app python -m app.backup list
docker compose exec app python -m app.backup verify <nombre>   # simulacro en una BD temporal
docker compose exec app python -m app.backup restore <nombre>  # reemplaza los datos actuales
docker compose exec app python -m app.backup prune --keep 7
```

Variables de entorno: ver `.env.example`.

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Automatización

| Workflow | Disparador | Qué hace |
|---|---|---|
| `ci-cd.yml` | push / PR | pruebas, backup+verify real contra MongoDB, despliegue a Render (solo main) |
| `backup.yml` | diario 06:00 UTC | hace dump de Atlas, cifra (AES-256) y guarda el artefacto 30 días |
| `restore-drill.yml` | lunes | restaura el último backup en un MongoDB desechable y comprueba los conteos |

Secretos de GitHub requeridos: `RENDER_DEPLOY_HOOK_URL`, `MONGODB_URI`, `BACKUP_PASSPHRASE`.

## Despliegue

1. Crear un cluster gratuito en MongoDB Atlas, un usuario de base de datos y permitir el acceso de red desde `0.0.0.0/0`.
2. En Render: **New → Blueprint** con este repositorio (`render.yaml`). Definir `MONGODB_URI`.
3. Copiar el *Deploy Hook* del servicio y guardarlo como secreto `RENDER_DEPLOY_HOOK_URL` en GitHub.
