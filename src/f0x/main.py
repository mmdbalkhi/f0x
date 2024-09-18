import os
import pathlib
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, send_file
from nanoid import generate
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
uploads_dir = pathlib.Path("/home/mmdbalkhi/w/f0x/uploads")
uploads_dir.mkdir(exist_ok=True)

# 5 MB (100 * 1024 * 1024 bytes) why hardcode?
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# HACK: not a good practice, but for simplicity that's hardcoded
README = """<pre>f0x
===========
f0x is a minimal application designed to simplify file uploads and retrievals. It allows users to upload files and retrieve them via a unique URL.
Uploading a File
To upload a file, send a POST request to the <code>/</code> endpoint with the file included in the request body

Example using curl
                curl -F 'file=@/path/to/your/file' 127.0.0.1:5000
gh: <a href=https://github.com/mmdbalkhi/f0x.git>https://github.com/mmdbalkhi/f0x.git</a> </pre>
"""


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return "File is too large. Maximum file size is 100 MB.", 413


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "POST":
        if "file" not in request.files:
            return (
                """File not found. Please send a file with the key 'file' in the form data.
            hint: The curl command line requires an @ before local file names.""",
                400,
            )

        file = request.files["file"]
        if file is None or file.filename == "":
            return "No selected file", 400

        file_id = generate(size=5)
        file_path = uploads_dir / (file_id + pathlib.Path(file.filename).suffix)
        file.save(file_path)

        app.logger.debug(
            f"File uploaded successfully. Access it at {request.url_root}{file_path.name}"
        )
        return (
            f"File uploaded successfully. Access it at {request.url_root}{file_path.name}",
            200,
        )

    return README


@app.route("/<path:path>", methods=["GET"])
def get_file(path):
    file = uploads_dir / path
    if not file.exists():
        return "File not found", 404
    return send_file(file)


def delete_old_files():
    now = datetime.now()
    cutoff = now - timedelta(days=30)
    for file in uploads_dir.iterdir():
        if file.is_file() and datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
            app.logger.debug(f"Deleting file: {file}")
            file.unlink()


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_old_files, "interval", hours=2)
    scheduler.start()
    try:
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
