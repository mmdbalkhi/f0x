import hashlib
import os
import random
import sqlite3
import string

from flask import Flask, Response, abort, request
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
DB_PATH = "pastes.db"


app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


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


@app.route("/", methods=["POST", "GET"])
def post_paste():
    if request.method == "GET":
        return "there is nothing for u!\n", 404

    raw = request.get_data(as_text=True)
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
            short_id = generate_short_id()
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
    return Response(request.url_root + short_id + "\n", mimetype="text/plain")


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
    app.run(host="127.0.0.1", port=5000, debug=True)


@app.before_first_request
def _init():
    init_db()
