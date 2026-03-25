# StreakSankalp

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
   ```bash
   git clone [https://github.com/yourusername/StreakSankalp.git](https://github.com/yourusername/StreakSankalp.git)
   cd StreakSankalp


2. Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate

3. Install dependencies:
pip install Flask

4. Run the application:
python app.py
