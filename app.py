import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# Fetch database connection string from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        return None
    # Fix URL scheme if needed for SQLAlchemy/psycopg2
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)

def init_db():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        conn.close()

# Auto-initialize database tables on first launch
try:
    init_db()
except Exception as e:
    print(f"Database initialization note: {e}")

@app.route("/")
def index():
    records = []
    db_status = "Disconnected / Local Fallback"
    
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT content, created_at FROM messages ORDER BY id DESC LIMIT 10;")
                records = cur.fetchall()
            conn.close()
            db_status = "Connected (Render Managed PostgreSQL)"
        except Exception as e:
            db_status = f"Error querying database: {e}"
    else:
        db_status = "DATABASE_URL not detected"

    return render_template("index.html", records=records, db_status=db_status)

@app.route("/add", methods=["POST"])
def add():
    content = request.form.get("note")
    if content:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO messages (content) VALUES (%s);", (content,))
                conn.commit()
            conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
