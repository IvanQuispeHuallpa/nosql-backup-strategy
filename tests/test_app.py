import json
from unittest import mock

import mongomock
import pytest

from app import backup
from app.main import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "secret")
    return create_app(db=mongomock.MongoClient()["notesdb"]).test_client()


def test_notes_crud(client):
    created = client.post("/api/notes", json={"text": "hello"})
    assert created.status_code == 201
    note_id = created.get_json()["_id"]
    assert [n["text"] for n in client.get("/api/notes").get_json()] == ["hello"]
    assert client.delete(f"/api/notes/{note_id}").status_code == 200
    assert client.get("/api/notes").get_json() == []


def test_empty_note_rejected(client):
    assert client.post("/api/notes", json={"text": "  "}).status_code == 400


def test_backup_endpoints_require_token(client, tmp_path, monkeypatch):
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
    assert client.get("/api/backups").status_code == 403
    assert client.get("/api/backups", headers={"X-Admin-Token": "secret"}).status_code == 200


def _fake_backup(tmp_path, name, created):
    (tmp_path / f"{name}.archive.gz").write_bytes(b"x")
    (tmp_path / f"{name}.json").write_text(json.dumps({"name": name, "created_at": created, "sha256": "x"}))


def test_retention_keeps_newest(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
    for i in range(5):
        _fake_backup(tmp_path, f"b{i}", f"2026-01-0{i + 1}")
    assert sorted(backup.prune(2)) == ["b0", "b1", "b2"]
    assert [m["name"] for m in backup.list_backups()] == ["b4", "b3"]


def test_server_uri_strips_database():
    assert backup._server_uri("mongodb+srv://u:p@c.mongodb.net/notesdb?retryWrites=true") == "mongodb+srv://u:p@c.mongodb.net/?retryWrites=true"
    assert backup._server_uri("mongodb://mongo:27017/notesdb") == "mongodb://mongo:27017/"
    assert backup._server_uri("mongodb://mongo:27017") == "mongodb://mongo:27017"


def test_restore_rejects_corrupted_backup(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
    _fake_backup(tmp_path, "bad", "2026-01-01")
    with pytest.raises(ValueError):
        backup.restore_backup("mongodb://x", "bad")


def test_create_backup_runs_mongodump(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
    monkeypatch.setattr(backup, "_counts", lambda uri, db: {"notes": 3})

    def fake_run(cmd, **kwargs):
        assert cmd[0] == "mongodump" and "--gzip" in cmd
        archive = next(c for c in cmd if c.startswith("--archive="))[len("--archive="):]
        with open(archive, "wb") as fh:
            fh.write(b"dump")

    with mock.patch.object(backup.subprocess, "run", fake_run):
        manifest = backup.create_backup("mongodb://x", "notesdb")
    assert manifest["counts"] == {"notes": 3}
    assert backup._load(manifest["name"])[0]["sha256"] == manifest["sha256"]
