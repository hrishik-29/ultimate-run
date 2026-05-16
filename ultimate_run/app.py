from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Change to something secure
app.permanent_session_lifetime = timedelta(days=7)

DB_NAME = "ultimate_run.db"

# Helper: create table if not exists
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room TEXT NOT NULL,
            contact TEXT NOT NULL,
            items TEXT NOT NULL,
            tip REAL,
            status TEXT DEFAULT 'Open',
            helper_name TEXT,
            helper_contact TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/request_item", methods=["GET", "POST"])
def request_item():
    if request.method == "POST":
        name = request.form["name"]
        room = request.form["room"]
        contact = request.form["contact"]
        items = request.form["items"]
        tip = request.form.get("tip", None)

        # Validation checks
        if not name or not room or not contact or not items:
            flash("All fields except Tip are required. Please fill them out.")
            return render_template("request_item.html", name=name, room=room, contact=contact, items=items)
        
        if not contact.isdigit():
            flash("Contact number must contain only digits.")
            return render_template("request_item.html", name=name, room=room, contact=contact, items=items)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO requests (name, room, contact, items, tip) VALUES (?, ?, ?, ?, ?)",
            (name, room, contact, items, tip)
        )
        conn.commit()
        new_id = c.lastrowid
        conn.close()

        # Store request id in session
        if "my_request_ids" not in session:
            session["my_request_ids"] = []
        session["my_request_ids"].append(new_id)
        session.modified = True

        return redirect(url_for("my_requests"))
    
    return render_template("request_item.html")

@app.route("/my_requests")
def my_requests():
    ids = session.get("my_request_ids", [])
    if not ids:
        requests_list = []
    else:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        query = "SELECT * FROM requests WHERE id IN ({})".format(",".join("?"*len(ids)))
        c.execute(query, ids)
        requests_list = c.fetchall()
        conn.close()
    return render_template("my_requests.html", requests=requests_list)

@app.route("/open_requests")
def open_requests():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, contact, items, room, tip FROM requests WHERE status='Open'")
    requests_list = c.fetchall()
    conn.close()
    return render_template("open_requests.html", requests=requests_list)

@app.route("/accept_request/<int:request_id>", methods=["POST"])
def accept_request(request_id):
    helper_name = request.form["helper_name"]
    helper_contact = request.form["helper_contact"]

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE requests
        SET status='Accepted', helper_name=?, helper_contact=?
        WHERE id=?
    """, (helper_name, helper_contact, request_id))
    conn.commit()
    conn.close()

    return redirect(url_for("open_requests"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")