from flask import Flask, redirect, request, jsonify, render_template, abort
from database import get_db, init_db
import string, random

app = Flask(__name__)

# ✅ Initialize DB on startup (IMPORTANT for deployment)
init_db()

# ─── Helper: Generate a random 6-char short code ───────────────────────
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

# ─── Home Page ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ─── Shorten a URL ─────────────────────────────────────────────────────
@app.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json()

    # ✅ SAFETY CHECK (prevents crash)
    if not data or "url" not in data:
        return jsonify({"error": "Invalid request"}), 400

    original_url = data.get("url", "").strip()

    if not original_url.startswith(("http://", "https://")):
        return jsonify({"error": "Please enter a valid URL (with http/https)"}), 400

    # Generate a unique short code
    db = get_db()
    while True:
        code = generate_short_code()
        exists = db.execute(
            "SELECT id FROM urls WHERE short_code = ?", (code,)
        ).fetchone()
        if not exists:
            break

    db.execute(
        "INSERT INTO urls (original, short_code) VALUES (?, ?)",
        (original_url, code)
    )
    db.commit()
    db.close()

    short_url = f"{request.host_url}{code}"
    return jsonify({"short_url": short_url, "code": code})

# ─── Redirect to Original URL ──────────────────────────────────────────
@app.route("/<short_code>")
def redirect_to_url(short_code):
    db = get_db()
    row = db.execute(
        "SELECT original FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()

    if not row:
        abort(404)

    # Track the click
    db.execute(
        "UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?",
        (short_code,)
    )
    db.execute(
        "INSERT INTO clicks (short_code) VALUES (?)",
        (short_code,)
    )
    db.commit()
    db.close()

    return redirect(row["original"])

# ─── Analytics Page ────────────────────────────────────────────────────
@app.route("/analytics/<short_code>")
def analytics(short_code):
    db = get_db()
    row = db.execute(
        "SELECT * FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()

    if not row:
        abort(404)

    return render_template("analytics.html", url=row)

# ─── Analytics API ─────────────────────────────────────────────────────
@app.route("/api/analytics/<short_code>")
def analytics_api(short_code):
    db = get_db()

    rows = db.execute("""
        SELECT DATE(clicked_at) as day, COUNT(*) as count
        FROM clicks
        WHERE short_code = ?
        GROUP BY day
        ORDER BY day ASC
    """, (short_code,)).fetchall()

    db.close()

    labels = [row["day"] for row in rows]
    values = [row["count"] for row in rows]

    return jsonify({"labels": labels, "values": values})

# ─── Run the App (local only) ──────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)