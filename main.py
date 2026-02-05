import hashlib
import random
import sqlite3
import string
import os
from flask import Flask, Response, abort, request

app = Flask(__name__)
DB_PATH = "pastes.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS pastes (
            short_id TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """
    )
    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_content_hash ON pastes(content_hash)
    """
    )
    db.commit()
    db.close()


def generate_short_id(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def canonicalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


@app.route("/", methods=["POST"])
def post_paste():
    if "file" not in request.files:
        abort(400)

    file = request.files["file"]
    if not file.filename:
        abort(400)

    raw = file.read().decode("utf-8")

    _, ext = os.path.splitext(file.filename)
    ext = ext if ext else ""

    canonical = canonicalize(raw)
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    db = get_db()

    existing = db.execute(
        "SELECT short_id FROM pastes WHERE content_hash = ?", (h,)
    ).fetchone()

    if existing:
        short_id = existing["short_id"]
    else:
        while True:
            short_id = generate_short_id() + ext
            collision_check = db.execute(
                "SELECT 1 FROM pastes WHERE short_id = ?", (short_id,)
            ).fetchone()
            if not collision_check:
                break

        db.execute(
            "INSERT INTO pastes (short_id, content_hash, content) VALUES (?, ?, ?)",
            (short_id, h, canonical),
        )
        db.commit()

    db.close()
    return Response(short_id + "\n", mimetype="text/plain")


@app.route("/<short_id>", methods=["GET"])
def get_paste(short_id):
    db = get_db()
    row = db.execute(
        "SELECT content FROM pastes WHERE short_id = ?", (short_id,)
    ).fetchone()
    db.close()

    if not row:
        return Response("Not Found\n", status=404)

    return Response(row["content"], mimetype="text/plain; charset=utf-8")


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
