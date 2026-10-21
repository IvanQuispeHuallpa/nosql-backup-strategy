"""Estrategia de backup para MongoDB: backups lógicos con mongodump, manifiesto
de integridad, retención, restauración y simulacro automático de restauración."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient

SCRATCH_DB = "restore_check"


def _backup_dir() -> Path:
    path = Path(os.getenv("BACKUP_DIR", "./backups"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _server_uri(uri: str) -> str:
    """Quita la base de datos de la URI para poder pasarla con --db."""
    return re.sub(r"^(mongodb(?:\+srv)?://[^/?]+)/[^?]*", r"\1/", uri)


def _counts(uri: str, db: str) -> dict:
    database = MongoClient(uri, serverSelectionTimeoutMS=8000)[db]
    return {name: database[name].count_documents({}) for name in sorted(database.list_collection_names())}


def create_backup(uri: str, db: str) -> dict:
    """Hace dump de `db` en un archivo gzip y escribe un manifiesto al lado."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{db}-{stamp}"
    archive = _backup_dir() / f"{name}.archive.gz"
    subprocess.run(
        ["mongodump", f"--uri={_server_uri(uri)}", f"--db={db}", "--gzip", f"--archive={archive}"],
        check=True, capture_output=True, text=True,
    )
    manifest = {
        "name": name,
        "db": db,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": archive.stat().st_size,
        "sha256": _sha256(archive),
        "counts": _counts(uri, db),
    }
    (_backup_dir() / f"{name}.json").write_text(json.dumps(manifest, indent=2))
    _upload(archive, manifest)
    prune(int(os.getenv("BACKUP_KEEP", "7")))
    return manifest


def _upload(archive: Path, manifest: dict) -> None:
    bucket = os.getenv("BACKUP_S3_BUCKET")
    if not bucket:
        return
    import boto3

    s3 = boto3.client("s3", endpoint_url=os.getenv("BACKUP_S3_ENDPOINT") or None)
    s3.upload_file(str(archive), bucket, f"{manifest['name']}.archive.gz")
    s3.put_object(Bucket=bucket, Key=f"{manifest['name']}.json", Body=json.dumps(manifest).encode())


def list_backups() -> list:
    items = [json.loads(p.read_text()) for p in _backup_dir().glob("*.json")]
    return sorted(items, key=lambda m: m["created_at"], reverse=True)


def prune(keep: int) -> list:
    """Política de retención: conserva solo los `keep` backups más recientes."""
    removed = []
    for manifest in list_backups()[keep:]:
        for suffix in (".archive.gz", ".json"):
            (_backup_dir() / f"{manifest['name']}{suffix}").unlink(missing_ok=True)
        removed.append(manifest["name"])
    return removed


def _load(name: str) -> tuple:
    manifest = json.loads((_backup_dir() / f"{name}.json").read_text())
    archive = _backup_dir() / f"{name}.archive.gz"
    if _sha256(archive) != manifest["sha256"]:
        raise ValueError(f"checksum mismatch for {name}: the backup is corrupted")
    return manifest, archive


def restore_backup(uri: str, name: str, target_db: str = None) -> dict:
    """Restaura un backup reemplazando las colecciones existentes (--drop)."""
    manifest, archive = _load(name)
    cmd = ["mongorestore", f"--uri={uri}", "--gzip", f"--archive={archive}", "--drop"]
    if target_db and target_db != manifest["db"]:
        cmd += [f"--nsFrom={manifest['db']}.*", f"--nsTo={target_db}.*"]
    else:
        cmd += [f"--nsInclude={manifest['db']}.*"]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return manifest


def verify_backup(uri: str, name: str) -> dict:
    """Simulacro: restaura en una BD temporal y compara los conteos de documentos."""
    manifest = restore_backup(uri, name, target_db=SCRATCH_DB)
    restored = _counts(uri, SCRATCH_DB)
    MongoClient(uri).drop_database(SCRATCH_DB)
    return {"name": name, "ok": restored == manifest["counts"], "expected": manifest["counts"], "restored": restored}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MongoDB backup tool")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("create")
    sub.add_parser("list")
    for cmd in ("restore", "verify"):
        sub.add_parser(cmd).add_argument("name")
    sub.add_parser("prune").add_argument("--keep", type=int, default=7)
    args = parser.parse_args(argv)

    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db = os.getenv("MONGODB_DB", "notesdb")
    if args.cmd == "create":
        result = create_backup(uri, db)
    elif args.cmd == "list":
        result = list_backups()
    elif args.cmd == "restore":
        result = restore_backup(uri, args.name)
    elif args.cmd == "verify":
        result = verify_backup(uri, args.name)
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    else:
        result = prune(args.keep)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
