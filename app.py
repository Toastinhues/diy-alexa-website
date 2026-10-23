import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)
PACKAGE_NAME = "com.toastinhues.alexatap"
latest_track = {
    "title": "",
    "artist": "",
    "source": "",
    "received_at": "",
    "device": "DIY Alexa",
}

@app.get("/")
def home():
    return render_template("index.html", track=latest_track)

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "Alexa Tap"})

@app.get("/tap")
def tap():
    # If the app isn't installed, verified App Links leave this URL in the browser.
    return render_template("index.html", track=latest_track, tap_page=True)

@app.post("/api/tap")
def receive_tap():
    global latest_track
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()[:300]
    artist = str(data.get("artist", "")).strip()[:300]
    source = str(data.get("source", "")).strip()[:100]
    if not title and not artist:
        title = "No music notification available"
        artist = "Play music and make sure its media notification is visible"
    latest_track = {
        "title": title,
        "artist": artist,
        "source": source,
        "received_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "device": "DIY Alexa",
    }
    app.logger.info("Track received: %s — %s (%s)", title, artist, source)
    return jsonify({"ok": True, "track": latest_track})

@app.get("/api/last-track")
def last_track():
    return jsonify(latest_track)

@app.get("/.well-known/assetlinks.json")
def assetlinks():
    fingerprint = os.environ.get("ANDROID_SHA256_CERT_FINGERPRINT", "").strip()
    if not fingerprint:
        return jsonify({
            "error": "Set ANDROID_SHA256_CERT_FINGERPRINT in Render environment variables."
        }), 503
    fingerprints = [item.strip() for item in fingerprint.split(",") if item.strip()]
    statement = [{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": PACKAGE_NAME,
            "sha256_cert_fingerprints": fingerprints,
        },
    }]
    return app.response_class(
        response=json.dumps(statement),
        status=200,
        mimetype="application/json",
    )

@app.get("/download")
def download_apk():
    apk_path = Path(app.root_path) / "static" / "downloads" / "AlexaTap.apk"
    if not apk_path.exists():
        return render_template("download_missing.html"), 404
    return send_from_directory(apk_path.parent, apk_path.name, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
