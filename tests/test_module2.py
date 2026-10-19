"""
Module 2 test suite: Seat Selection & Booking
Project : Movie Ticket Booking System (CineBook)
Run     : python -m pytest tests/test_module2.py -v

Every test carries its Test Case ID (M2_TCxx), which matches the Test Case sheet
(MTB_Module2_Test_Cases.xlsx). Read PASSED / FAILED next to each ID and copy it
into the "Actual Result" and "Status" columns.
"""
import os
import sys

import pytest

# Make the project root importable when pytest is run from any folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from app import app as flask_app
from validators import validate_seat_selection, ALL_SEATS


# =====================================================================
# PART 1: UNIT TESTS (validators.validate_seat_selection)
# Techniques: Boundary Value Analysis, Equivalence Partitioning,
#             Error Guessing
# =====================================================================

# (test case id, selected seats, already booked seats, should the selection be accepted?)
UNIT_CASES = [
    ("M2_TC01", [], set(), False),                                        # 0 seats  (min - 1)
    ("M2_TC02", ["A1"], set(), True),                                     # 1 seat   (min)
    ("M2_TC03", ["A1", "A2", "A3"], set(), True),                         # 3 seats  (valid class)
    ("M2_TC04", ["B1", "B2", "B3", "B4", "B5", "B6"], set(), True),       # 6 seats  (max)
    ("M2_TC05", ["B1", "B2", "B3", "B4", "B5", "B6", "B7"], set(), False),  # 7 seats (max + 1)
    ("M2_TC06", ["Z9"], set(), False),                                    # unknown row
    ("M2_TC07", ["A9"], set(), False),                                    # seat number above 8
    ("M2_TC08", ["A0"], set(), False),                                    # seat number below 1
    ("M2_TC09", ["A1", "E8"], set(), True),                               # first and last seat
    ("M2_TC10", ["A1", "A1"], set(), False),                              # duplicate seat
    ("M2_TC11", ["C3"], {"C3"}, False),                                   # already booked seat
    ("M2_TC12", ["a1"], set(), False),                                    # lowercase label
    ("M2_TC13", [""], set(), False),                                      # empty seat label
    ("M2_TC14", ["D1", "D2"], {"D2"}, False),                             # one free, one booked
]


@pytest.mark.parametrize(
    "tc_id, selected, booked, should_be_valid",
    UNIT_CASES,
    ids=[case[0] for case in UNIT_CASES],
)
def test_unit_seat_selection(tc_id, selected, booked, should_be_valid):
    result = validate_seat_selection(selected, booked)
    if should_be_valid:
        assert result is None, f"{tc_id}: selection should be accepted but got error: {result}"
    else:
        assert result is not None, f"{tc_id}: selection should be rejected but it was accepted"


# =====================================================================
# PART 2: FUNCTIONAL AND INTEGRATION TESTS (Flask routes + database)
# Each test uses a fresh temporary database with sample movies and shows.
# Show 1 costs Rs. 200 per seat, show 2 costs Rs. 250 per seat.
# =====================================================================

USER_A = {"name": "Sriram Iyer", "email": "a@test.com", "phone": "9876543210", "password": "Pass@1234"}
USER_B = {"name": "Bhavya Rao", "email": "b@test.com", "phone": "9123456780", "password": "Pass@1234"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_NAME", str(tmp_path / "test_movie_booking.db"))
    database.init_db()
    database.seed_data()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client


def logged_in_client(user):
    test_client = flask_app.test_client()
    test_client.post("/register", data=user)
    test_client.post("/login", data={"email": user["email"], "password": user["password"]})
    return test_client


def book(test_client, seats, show_id=1):
    return test_client.post(f"/shows/{show_id}/book", data={"seats": seats})


def count_rows(table):
    conn = database.get_connection()
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return count


def test_M2_TC15_movies_page_requires_login(client):
    response = client.get("/movies")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_M2_TC16_movies_page_lists_all_movies_and_shows(client):
    user = logged_in_client(USER_A)
    html = user.get("/movies").data.decode()
    for title in ("Midnight Express", "Tales of the Tiger", "Laugh Out Loud"):
        assert title in html
    assert html.count('class="show-pill"') == 12


def test_M2_TC17_seat_page_requires_login(client):
    response = client.get("/shows/1/seats")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_M2_TC18_seat_page_shows_40_selectable_seats(client):
    user = logged_in_client(USER_A)
    html = user.get("/shows/1/seats").data.decode()
    assert html.count('type="checkbox"') == 40


def test_M2_TC19_booked_seats_are_not_selectable(client):
    user = logged_in_client(USER_A)
    book(user, ["A1", "A2"])
    html = user.get("/shows/1/seats").data.decode()
    assert html.count('type="checkbox"') == 38
    assert html.count('<span class="seat booked"') == 2


def test_M2_TC20_valid_booking_redirects_to_confirmation(client):
    user = logged_in_client(USER_A)
    response = book(user, ["A1", "A2"])
    assert response.status_code == 302
    assert "/bookings/1/confirmation" in response.headers["Location"]


def test_M2_TC21_total_price_for_three_seats(client):
    user = logged_in_client(USER_A)
    response = book(user, ["A1", "A2", "A3"], show_id=1)
    html = user.get(response.headers["Location"]).data.decode()
    assert "Rs. 600" in html


def test_M2_TC22_total_price_uses_show_price(client):
    user = logged_in_client(USER_A)
    response = book(user, ["A1", "A2"], show_id=2)
    html = user.get(response.headers["Location"]).data.decode()
    assert "Rs. 500" in html


def test_M2_TC23_confirmation_shows_booking_id_and_seats(client):
    user = logged_in_client(USER_A)
    response = book(user, ["C4", "C5"])
    html = user.get(response.headers["Location"]).data.decode()
    assert "Booking ID" in html
    assert "C4, C5" in html
    assert "Midnight Express" in html


def test_M2_TC24_second_user_cannot_book_taken_seat(client):
    user_a = logged_in_client(USER_A)
    user_b = logged_in_client(USER_B)
    book(user_a, ["A1"])
    response = book(user_b, ["A1"])
    assert response.status_code == 400
    assert b"already booked" in response.data
    assert count_rows("booking_seats") == 1


def test_M2_TC25_same_user_cannot_book_taken_seat_again(client):
    user = logged_in_client(USER_A)
    book(user, ["A1"])
    response = book(user, ["A1"])
    assert response.status_code == 400
    assert count_rows("bookings") == 1


def test_M2_TC26_database_blocks_double_booking_without_partial_save(client):
    user_a = logged_in_client(USER_A)
    book(user_a, ["A2"])
    result = database.create_booking(1, 1, ["A2", "A3"], 200)
    assert result is None
    assert count_rows("bookings") == 1
    assert count_rows("booking_seats") == 1


def test_M2_TC27_seven_seats_are_rejected_and_nothing_is_saved(client):
    user = logged_in_client(USER_A)
    response = book(user, ["A1", "A2", "A3", "A4", "A5", "A6", "A7"])
    assert response.status_code == 400
    assert b"maximum of 6" in response.data
    assert count_rows("bookings") == 0


def test_M2_TC28_six_seats_are_accepted(client):
    user = logged_in_client(USER_A)
    response = book(user, ["A1", "A2", "A3", "A4", "A5", "A6"])
    assert response.status_code == 302
    assert count_rows("booking_seats") == 6


def test_M2_TC29_seats_left_decreases_after_booking(client):
    user = logged_in_client(USER_A)
    book(user, ["A1", "A2"])
    html = user.get("/movies").data.decode()
    assert "38 seats left" in html


def test_M2_TC30_fully_booked_show_shows_sold_out(client):
    user = logged_in_client(USER_A)
    all_seats = sorted(ALL_SEATS)
    for start in range(0, len(all_seats), 5):
        database.create_booking(1, 1, all_seats[start:start + 5], 200)
    html = user.get("/movies").data.decode()
    assert "Sold out" in html
    response = book(user, ["A1"])
    assert response.status_code == 400


def test_M2_TC31_seat_page_for_unknown_show_returns_404(client):
    user = logged_in_client(USER_A)
    assert user.get("/shows/999/seats").status_code == 404


def test_M2_TC32_booking_for_unknown_show_returns_404(client):
    user = logged_in_client(USER_A)
    assert book(user, ["A1"], show_id=999).status_code == 404


def test_M2_TC33_my_bookings_requires_login(client):
    response = client.get("/bookings")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_M2_TC34_my_bookings_shows_only_own_bookings(client):
    user_a = logged_in_client(USER_A)
    user_b = logged_in_client(USER_B)
    book(user_a, ["A1"])
    book(user_b, ["B1", "B2"])
    html_a = user_a.get("/bookings").data.decode()
    assert "Seats: A1" in html_a
    assert "B1, B2" not in html_a


def test_M2_TC35_my_bookings_empty_state_for_new_user(client):
    user = logged_in_client(USER_A)
    html = user.get("/bookings").data.decode()
    assert "You have no bookings yet." in html


def test_M2_TC36_my_bookings_shows_booking_details(client):
    user = logged_in_client(USER_A)
    book(user, ["A1", "A2"])
    html = user.get("/bookings").data.decode()
    assert "Midnight Express" in html
    assert "A1, A2" in html
    assert "Rs. 400" in html


def test_M2_TC37_confirmation_of_another_user_returns_404(client):
    user_a = logged_in_client(USER_A)
    user_b = logged_in_client(USER_B)
    book(user_a, ["A1"])
    assert user_b.get("/bookings/1/confirmation").status_code == 404


def test_M2_TC38_end_to_end_login_book_confirm_and_list(client):
    user = logged_in_client(USER_A)
    assert user.get("/movies").status_code == 200
    assert user.get("/shows/1/seats").status_code == 200
    response = book(user, ["D4", "D5"])
    confirmation = user.get(response.headers["Location"])
    assert b"Booking Confirmed" in confirmation.data
    assert b"D4, D5" in user.get("/bookings").data


def test_M2_TC39_booking_without_login_saves_nothing(client):
    response = book(client, ["A1"])
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert count_rows("bookings") == 0


def test_M2_TC40_injection_in_seat_value_is_rejected(client):
    user = logged_in_client(USER_A)
    response = book(user, ["A1'; DROP TABLE users;--"])
    assert response.status_code == 400
    assert count_rows("users") >= 1
    assert count_rows("bookings") == 0


def make_show_past(show_id=1):
    conn = database.get_connection()
    conn.execute("UPDATE shows SET show_date = '2020-01-01' WHERE id = ?", (show_id,))
    conn.commit()
    conn.close()


def test_M2_TC41_past_show_is_not_listed(client):
    make_show_past(1)
    user = logged_in_client(USER_A)
    html = user.get("/movies").data.decode()
    assert "2020-01-01" not in html


def test_M2_TC42_past_show_cannot_be_booked(client):
    make_show_past(1)
    user = logged_in_client(USER_A)
    response = book(user, ["A1"])
    assert response.status_code in (400, 404)
    assert count_rows("bookings") == 0
