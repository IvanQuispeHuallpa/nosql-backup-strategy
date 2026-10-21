import os
from datetime import datetime, timezone

from bson import ObjectId
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient

from . import backup


def _uri() -> str:
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017")


def _db_name() -> str:
    return os.getenv("MONGODB_DB", "notesdb")


def create_app(db=None) -> Flask:
    app = Flask(__name__, template_folder="../templates")
    app.config["DB"] = db if db is not None else MongoClient(_uri(), serverSelectionTimeoutMS=8000)[_db_name()]

    def notes():
        return app.config["DB"]["notes"]

    def authorized() -> bool:
        token = os.getenv("ADMIN_TOKEN")
        return bool(token) and request.headers.get("X-Admin-Token") == token

    def serialize(doc):
        doc["_id"] = str(doc["_id"])
        return doc

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        app.config["DB"].command("ping")
        return {"status": "ok"}

    @app.get("/api/notes")
    def list_notes():
        return jsonify([serialize(n) for n in notes().find().sort("created_at", -1)])

    @app.post("/api/notes")
    def add_note():
        body = request.get_json(silent=True) or {}
        text = str(body.get("text", "")).strip()
        if not text:
            return {"error": "text is required"}, 400
        doc = {"text": text, "created_at": datetime.now(timezone.utc).isoformat()}
        doc["_id"] = notes().insert_one(doc).inserted_id
        return serialize(doc), 201

    @app.delete("/api/notes/<note_id>")
    def delete_note(note_id):
        if not ObjectId.is_valid(note_id):
            return {"error": "invalid id"}, 400
        if notes().delete_one({"_id": ObjectId(note_id)}).deleted_count:
            return {"deleted": True}
        return {"error": "not found"}, 404

    # Los endpoints de backup se protegen con ADMIN_TOKEN (deshabilitados si no está definido).
    @app.get("/api/backups")
    def backups():
        if not authorized():
            return {"error": "forbidden"}, 403
        return jsonify(backup.list_backups())

    @app.post("/api/backups")
    def make_backup():
        if not authorized():
            return {"error": "forbidden"}, 403
        return backup.create_backup(_uri(), _db_name()), 201

    @app.post("/api/backups/<name>/verify")
    def verify(name):
        if not authorized():
            return {"error": "forbidden"}, 403
        return backup.verify_backup(_uri(), name)

    @app.post("/api/backups/<name>/restore")
    def restore(name):
        if not authorized():
            return {"error": "forbidden"}, 403
        return backup.restore_backup(_uri(), name)

    return app
