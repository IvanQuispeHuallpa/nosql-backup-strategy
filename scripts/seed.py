"""Inserta notas de demo para que el backup tenga algo que proteger."""
import os
from datetime import datetime, timezone

from pymongo import MongoClient

db = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))[os.getenv("MONGODB_DB", "notesdb")]
now = datetime.now(timezone.utc).isoformat()
db.notes.insert_many([{"text": f"Nota de demo {i}", "created_at": now} for i in range(1, 11)])
print("insertadas", db.notes.count_documents({}), "notes")
