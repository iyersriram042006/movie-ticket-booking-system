import sqlite3
from datetime import date, timedelta

DB_NAME = "movie_booking.db"
TOTAL_SEATS = 40  # 5 rows (A to E) x 8 seats


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            duration_min INTEGER NOT NULL,
            language TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL REFERENCES movies(id),
            show_date TEXT NOT NULL,
            show_time TEXT NOT NULL,
            screen TEXT NOT NULL,
            price INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            show_id INTEGER NOT NULL REFERENCES shows(id),
            total_amount INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS booking_seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL REFERENCES bookings(id),
            show_id INTEGER NOT NULL REFERENCES shows(id),
            seat_label TEXT NOT NULL,
            UNIQUE (show_id, seat_label)
        );
    """)
    conn.commit()
    conn.close()


def seed_data():
    """Adds sample movies and shows once (only if the movies table is empty)."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO movies (title, genre, duration_min, language) VALUES (?, ?, ?, ?)",
            [
                ("Midnight Express", "Thriller", 128, "Hindi"),
                ("Tales of the Tiger", "Adventure", 142, "English"),
                ("Laugh Out Loud", "Comedy", 115, "Hindi"),
            ],
        )
        movie_ids = [r["id"] for r in conn.execute("SELECT id FROM movies ORDER BY id")]
        slots = [("14:00", "Screen 1", 200), ("19:30", "Screen 2", 250)]
        for movie_id in movie_ids:
            for offset in (1, 2):
                show_date = (date.today() + timedelta(days=offset)).isoformat()
                for show_time, screen, price in slots:
                    conn.execute(
                        "INSERT INTO shows (movie_id, show_date, show_time, screen, price) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (movie_id, show_date, show_time, screen, price),
                    )
        conn.commit()
    conn.close()


def get_movies_with_shows():
    conn = get_connection()
    movies = conn.execute("SELECT * FROM movies ORDER BY title").fetchall()
    result = []
    for movie in movies:
        shows = conn.execute(
            """
            SELECT s.*,
                   ? - (SELECT COUNT(*) FROM booking_seats bs WHERE bs.show_id = s.id) AS seats_left
            FROM shows s
            WHERE s.movie_id = ?
            ORDER BY s.show_date, s.show_time
            """,
            (TOTAL_SEATS, movie["id"]),
        ).fetchall()
        result.append({"movie": movie, "shows": shows})
    conn.close()
    return result


def email_exists(email):
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row is not None


def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row


def create_user(name, email, phone, password_hash):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (name, email, phone, password_hash) VALUES (?, ?, ?, ?)",
            (name, email, phone, password_hash),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    seed_data()
    print("Database initialised.")