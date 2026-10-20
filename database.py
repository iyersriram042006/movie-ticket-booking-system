import sqlite3
from datetime import date, datetime, timedelta

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


def is_show_in_past(show):
    """True when the show has already started."""
    start = datetime.strptime(f"{show['show_date']} {show['show_time']}", "%Y-%m-%d %H:%M")
    return start < datetime.now()


def get_movies_with_shows():
    """Movies with their upcoming shows (shows that already started are hidden)."""
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
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
              AND (s.show_date || ' ' || s.show_time) >= ?
            ORDER BY s.show_date, s.show_time
            """,
            (TOTAL_SEATS, movie["id"], now_text),
        ).fetchall()
        result.append({"movie": movie, "shows": shows})
    conn.close()
    return result

def get_show(show_id):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT s.*, m.title, m.genre, m.language, m.duration_min
        FROM shows s JOIN movies m ON m.id = s.movie_id
        WHERE s.id = ?
        """,
        (show_id,),
    ).fetchone()
    conn.close()
    return row


def get_booked_seats(show_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT seat_label FROM booking_seats WHERE show_id = ?", (show_id,)
    ).fetchall()
    conn.close()
    return {row["seat_label"] for row in rows}


def create_booking(user_id, show_id, seat_labels, price_per_seat):
    """Saves booking and its seats in one transaction.
    Returns the booking id, or None if any seat was taken meanwhile."""
    conn = get_connection()
    try:
        total = price_per_seat * len(seat_labels)
        cursor = conn.execute(
            "INSERT INTO bookings (user_id, show_id, total_amount) VALUES (?, ?, ?)",
            (user_id, show_id, total),
        )
        booking_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO booking_seats (booking_id, show_id, seat_label) VALUES (?, ?, ?)",
            [(booking_id, show_id, seat) for seat in seat_labels],
        )
        conn.commit()
        return booking_id
    except sqlite3.IntegrityError:
        conn.rollback()
        return None
    finally:
        conn.close()


def get_booking(booking_id, user_id):
    """Returns the booking only if it belongs to this user."""
    conn = get_connection()
    booking = conn.execute(
        """
        SELECT b.*, s.show_date, s.show_time, s.screen, s.price, m.title
        FROM bookings b
        JOIN shows s ON s.id = b.show_id
        JOIN movies m ON m.id = s.movie_id
        WHERE b.id = ? AND b.user_id = ?
        """,
        (booking_id, user_id),
    ).fetchone()
    seats = []
    if booking is not None:
        rows = conn.execute(
            "SELECT seat_label FROM booking_seats WHERE booking_id = ? ORDER BY seat_label",
            (booking_id,),
        ).fetchall()
        seats = [row["seat_label"] for row in rows]
    conn.close()
    return booking, seats

def get_user_bookings(user_id):
    """All bookings of one user, newest first, each with its seat labels."""
    conn = get_connection()
    bookings = conn.execute(
        """
        SELECT b.id, b.total_amount, b.created_at,
               s.show_date, s.show_time, s.screen, m.title
        FROM bookings b
        JOIN shows s ON s.id = b.show_id
        JOIN movies m ON m.id = s.movie_id
        WHERE b.user_id = ?
        ORDER BY b.id DESC
        """,
        (user_id,),
    ).fetchall()
    result = []
    for booking in bookings:
        rows = conn.execute(
            "SELECT seat_label FROM booking_seats WHERE booking_id = ? ORDER BY seat_label",
            (booking["id"],),
        ).fetchall()
        result.append({"booking": booking, "seats": [row["seat_label"] for row in rows]})
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