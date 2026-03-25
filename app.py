"""
app.py — Flask REST API for the StreakSankalp habit tracker.

Endpoints
---------
GET  /api/habits   →  List all habits with completion stats.
POST /api/habits   →  Create a new habit.
POST /api/logs     →  Log a habit completion for a specific date.
"""

from flask import Flask, g, jsonify, render_template, request
import sqlite3

from db_manager import DatabaseManager

# ------------------------------------------------------------------ #
#  App setup
# ------------------------------------------------------------------ #

app = Flask(__name__)

DB_PATH = "tracker.db"

# Ensure the tables exist once at startup.
DatabaseManager(DB_PATH).close()


# ------------------------------------------------------------------ #
#  Per-request database connection
# ------------------------------------------------------------------ #

def get_db() -> DatabaseManager:
    """
    Return a DatabaseManager scoped to the current request.

    A new connection is created on the first call within a request
    and reused for any subsequent calls in the same request.
    The connection is automatically closed at teardown (see below).
    """
    if "db" not in g:
        g.db = DatabaseManager(DB_PATH)
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close the database connection when the request context ends."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ------------------------------------------------------------------ #
#  Helper — consistent error responses
# ------------------------------------------------------------------ #

def error_response(message: str, status_code: int = 400):
    """Return a JSON error envelope with the given HTTP status code."""
    return jsonify({"error": message}), status_code


# ------------------------------------------------------------------ #
#  GET / — serve the frontend
# ------------------------------------------------------------------ #

@app.route("/")
def index():
    """Serve the single-page frontend."""
    return render_template("index.html")


# ------------------------------------------------------------------ #
#  GET /api/habits — list all habits + completion stats
# ------------------------------------------------------------------ #

@app.route("/api/habits", methods=["GET"])
def list_habits():
    """
    Fetch every habit and attach its current completion percentage.

    Response (200)
    --------------
    {
        "habits": [
            {
                "id": 1,
                "name": "Meditate 10 min",
                "created_at": "2026-03-25 06:30:00",
                "completion_pct": 75.0
            },
            ...
        ]
    }
    """
    try:
        db = get_db()
        habits = db.get_all_habits()

        # Enrich each habit dict with its completion percentage.
        for habit in habits:
            habit["completion_pct"] = db.get_completion_percentage(habit["id"])

        return jsonify({"habits": habits}), 200

    except Exception as e:
        return error_response(f"Failed to retrieve habits: {str(e)}", 500)


# ------------------------------------------------------------------ #
#  POST /api/habits — create a new habit
# ------------------------------------------------------------------ #

@app.route("/api/habits", methods=["POST"])
def create_habit():
    """
    Create a new habit.

    Request body (JSON)
    -------------------
    { "name": "Meditate 10 min" }

    Response (201)
    --------------
    { "id": 1, "name": "Meditate 10 min", "message": "Habit created successfully" }
    """
    data = request.get_json(silent=True)

    # --- Validate payload ---
    if data is None:
        return error_response("Request body must be valid JSON.")

    name = data.get("name", "").strip()
    if not name:
        return error_response("The 'name' field is required and cannot be empty.")

    # --- Persist ---
    try:
        db = get_db()
        habit_id = db.add_habit(name)
        return jsonify({
            "id": habit_id,
            "name": name,
            "message": "Habit created successfully",
        }), 201

    except sqlite3.IntegrityError:
        return error_response(f"A habit named '{name}' already exists.", 409)

    except Exception as e:
        return error_response(f"Failed to create habit: {str(e)}", 500)


# ------------------------------------------------------------------ #
#  POST /api/logs — log a habit completion
# ------------------------------------------------------------------ #

@app.route("/api/logs", methods=["POST"])
def log_completion():
    """
    Log a completion entry for a habit on a given date.

    Request body (JSON)
    -------------------
    {
        "habit_id": 1,
        "date": "2026-03-25"       // optional — defaults to today
    }

    Response (201)
    --------------
    { "log_id": 5, "message": "Habit logged successfully" }
    """
    data = request.get_json(silent=True)

    # --- Validate payload ---
    if data is None:
        return error_response("Request body must be valid JSON.")

    habit_id = data.get("habit_id")
    if habit_id is None:
        return error_response("The 'habit_id' field is required.")

    if not isinstance(habit_id, int):
        return error_response("'habit_id' must be an integer.")

    log_date = data.get("date")  # None → DatabaseManager defaults to today

    # --- Persist ---
    try:
        db = get_db()
        log_id = db.log_habit(habit_id, log_date)
        return jsonify({
            "log_id": log_id,
            "message": "Habit logged successfully",
        }), 201

    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "foreign key" in err_msg:
            return error_response(f"No habit found with id {habit_id}.", 404)
        if "unique" in err_msg:
            return error_response(
                f"Habit {habit_id} has already been logged for {log_date or 'today'}.",
                409,
            )
        return error_response(f"Integrity error: {str(e)}", 400)

    except Exception as e:
        return error_response(f"Failed to log habit: {str(e)}", 500)


# ------------------------------------------------------------------ #
#  Entry point
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    # debug=True gives auto-reload + detailed tracebacks during development.
    app.run(debug=True, port=5000)
