# StreakSankalp
 
A lightweight, full-stack habit tracker that computes real consecutive-day streaks (with a one-day grace period) and completion percentages, built without relying on any ORM or frontend framework.
 
**Live demo:** https://streaksankalp.onrender.com
*(hosted on Render's free tier — see [Known Limitations](#known-limitations--roadmap) below before judging an empty list as a bug)*
 
This project was built to practice core backend fundamentals: REST API design, relational schema design with raw SQL, server-side input validation, and shipping a small app to a real deployment.
 
## Tech Stack
* **Backend:** Python 3, Flask
* **Database:** SQLite3 (raw SQL, no ORM)
* **Frontend:** HTML5, CSS3, vanilla JavaScript (Fetch API, no framework)
* **Production server:** Gunicorn (WSGI), deployed on Render
## Features
* **Real streak calculation** — current streak (with a one-day grace period, so it doesn't falsely reset before the day is over) and best-ever streak, computed from raw log dates, not derived from percentages.
* **Server-side date validation** — rejects future-dated logs, logs predating a habit's creation, and malformed date strings.
* **Normalized relational schema** — `habits` and `logs` tables with foreign keys, `ON DELETE CASCADE`, and a `UNIQUE(habit_id, log_date)` constraint to prevent duplicate same-day logs.
* **RESTful API** — standardized JSON responses with correct status codes (200, 201, 400, 404, 409).
* **XSS-safe rendering** — habit names are escaped before being injected into the DOM.
## Known Limitations & Roadmap
 
Scoped deliberately for a mini-project MVP — listed here instead of left for someone else to find:
 
* **Single shared data model, no accounts.** There's currently no `user_id` scoping — every visitor shares one list of habits. Habit names are globally unique, so two different people can't both have a habit called "Gym." Next step: add basic auth and scope all queries by user.
* **Ephemeral storage on the free tier.** Render's free web services don't persist a local SQLite file across redeploys or after an idle spin-down — so demo data will periodically reset. A production version would move to a managed Postgres instance.
* **No edit or delete for habits** once created.
* **No automated test suite yet** — current correctness is verified via manual `curl`/unit-test scripts during development, not a checked-in test file.
## Local Setup & Installation
 
1. Clone the repository:
```bash
   git clone https://github.com/Asonvar/StreakSankalp.git
   cd StreakSankalp
```
 
2. Create and activate a virtual environment:
```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
```
 
3. Install dependencies:
```bash
   pip install -r requirements.txt
```
 
4. Run the application (development server):
```bash
   python app.py
```
 
5. To run it the way it's actually deployed (production WSGI server):
```bash
   gunicorn app:app --bind 0.0.0.0:5000
```
 
<!-- # StreakSankalp

A lightweight, decoupled full-stack habit tracker designed to persist daily goals and calculate completion metrics without relying on heavy external frameworks. 

This project was built to demonstrate core backend engineering principles, specifically REST API design, relational database management using raw SQL, and frontend-backend separation.

## Tech Stack
* **Backend:** Python 3, Flask
* **Database:** SQLite3 (Raw SQL, no ORM)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API)

## Features
* **Normalized Data Persistence:** Uses a relational SQLite schema (`habits` and `logs` tables) with enforced foreign key constraints.
* **RESTful API:** Flask routes handle all HTTP methods (GET, POST) and return standardized JSON responses with appropriate HTTP status codes (200, 201, 400, 404, 409).
* **Decoupled Client:** The frontend is a static Vanilla JS application that dynamically updates the DOM by consuming the Flask API endpoints.

## Local Setup & Installation

1. **Clone the repository:**

2. Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate

3. Install dependencies:
pip install Flask

4. Run the application:
python app.py -->