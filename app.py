from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent

# On Render, env vars come from the dashboard — do not load a local .env (can override with blanks).
if not os.environ.get("RENDER_SERVICE_ID"):
    try:
        load_dotenv(BASE_DIR / ".env")
    except OSError:
        pass


def _env_clean(key: str) -> str:
    v = os.getenv(key, "") or ""
    return v.strip().strip("\ufeff").strip()

app = Flask(__name__, static_folder=str(BASE_DIR))


def _allowed_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGIN",
        "https://imanius-dot.github.io",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


@app.after_request
def add_cors_headers(response):
    """Allow the GitHub Pages site to POST /subscribe (cross-origin)."""
    origin = request.headers.get("Origin", "")
    if origin and origin in _allowed_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/subscribe", methods=["POST", "OPTIONS"])
def subscribe():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    api_key = _env_clean("MAILCHIMP_API_KEY")
    audience_id = _env_clean("MAILCHIMP_AUDIENCE_ID")
    server_prefix = _env_clean("MAILCHIMP_SERVER_PREFIX")

    if not api_key or not audience_id or not server_prefix:
        return jsonify({"error": "Mailchimp env vars are missing."}), 500

    mailchimp_url = (
        f"https://{server_prefix}.api.mailchimp.com/3.0/lists/{audience_id}/members"
    )

    try:
        response = requests.post(
            mailchimp_url,
            auth=("anystring", api_key),
            json={
                "email_address": email,
                "status": "subscribed",
            },
            timeout=12,
        )
        data = response.json()
    except requests.RequestException:
        return jsonify({"error": "Failed to connect to Mailchimp."}), 500

    if response.ok or data.get("title") == "Member Exists":
        return jsonify({"ok": True})

    return jsonify({"error": data.get("detail", "Mailchimp error.")}), 400


@app.get("/health/mailchimp")
def mailchimp_env_health():
    """Shows whether env vars are visible to this running instance (no secrets exposed)."""
    api_key = _env_clean("MAILCHIMP_API_KEY")
    audience_id = _env_clean("MAILCHIMP_AUDIENCE_ID")
    server_prefix = _env_clean("MAILCHIMP_SERVER_PREFIX")
    return jsonify(
        {
            "on_render": bool(os.environ.get("RENDER_SERVICE_ID")),
            "configured": bool(api_key and audience_id and server_prefix),
            "value_lengths": {
                "MAILCHIMP_API_KEY": len(api_key),
                "MAILCHIMP_AUDIENCE_ID": len(audience_id),
                "MAILCHIMP_SERVER_PREFIX": len(server_prefix),
            },
        }
    )


@app.get("/<path:path>")
def static_files(path: str):
    return send_from_directory(BASE_DIR, path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    # Render/other hosts expect the app to listen on all interfaces.
    app.run(host="0.0.0.0", port=port, debug=False)
