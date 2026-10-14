"""
Module 1 test suite: User Registration & Login
Project : Movie Ticket Booking System (CineBook)
Run     : pytest tests/ -v

Every test carries its Test Case ID (TCxx), which matches the Test Case sheet
(MTB_Module1_Test_Cases.xlsx). Read PASSED / FAILED next to each ID and copy it
into the "Actual Result" and "Status" columns.
"""
import os
import sys

import pytest

# Make the project root importable when pytest is run from any folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from app import app as flask_app
from validators import (
    validate_name,
    validate_email,
    validate_phone,
    validate_password,
)


# =====================================================================
# PART 1: UNIT TESTS (validators.py)
# Techniques: Equivalence Partitioning, Boundary Value Analysis,
#             Validation Testing
# =====================================================================

# (test case id, validator function, input value, should the input be accepted?)
UNIT_CASES = [
    # ---- Name (FR2: 3 to 30 characters, alphabets and spaces only) ----
    ("TC02", validate_name, "", False),
    ("TC03", validate_name, "Sr", False),                      # length 2  (min - 1)
    ("TC04", validate_name, "Sri", True),                      # length 3  (min)
    ("TC05", validate_name, "A" * 30, True),                   # length 30 (max)
    ("TC06", validate_name, "A" * 31, False),                  # length 31 (max + 1)
    ("TC07", validate_name, "Sriram99", False),                # digits
    ("TC08", validate_name, "Sriram@Iyer", False),             # special character
    ("TC09", validate_name, "     ", False),                   # only spaces
    # ---- Email (FR3: valid format) ----
    ("TC10", validate_email, "", False),
    ("TC11", validate_email, "sriramtest.com", False),         # no @
    ("TC12", validate_email, "sriram@test", False),            # no domain extension
    ("TC13", validate_email, "sri..ram@test.com", False),      # consecutive dots
    ("TC14", validate_email, "sriram+pbl@test.co.in", True),   # valid, plus sign + sub-domain
    # ---- Phone (FR4: exactly 10 digits) ----
    ("TC15", validate_phone, "", False),
    ("TC16", validate_phone, "987654321", False),              # 9 digits  (min - 1)
    ("TC17", validate_phone, "9876543210", True),              # 10 digits
    ("TC18", validate_phone, "98765432101", False),            # 11 digits (max + 1)
    ("TC19", validate_phone, "98765abcde", False),             # letters
    ("TC20", validate_phone, "98765-43210", False),            # hyphen
    ("TC21", validate_phone, "\u0669\u0668\u0667\u0666\u0665\u0664\u0663\u0662\u0661\u0660", False),  # Arabic-Indic digits
    # ---- Password (FR5: 8 to 20 chars, upper, lower, digit, special) ----
    ("TC22", validate_password, "", False),
    ("TC23", validate_password, "Pa@1abc", False),             # length 7  (min - 1)
    ("TC24", validate_password, "Pass@123", True),             # length 8  (min)
    ("TC25", validate_password, "Pass@1234567890abcde", True),   # length 20 (max)
    ("TC26", validate_password, "Pass@1234567890abcdef", False),  # length 21 (max + 1)
    ("TC27", validate_password, "pass@1234", False),           # no uppercase
    ("TC28", validate_password, "PASS@1234", False),           # no lowercase
    ("TC29", validate_password, "Pass@word", False),           # no digit
    ("TC30", validate_password, "Pass1234", False),            # no special character
]


@pytest.mark.parametrize(
    "tc_id, validator, value, should_be_valid",
    UNIT_CASES,
    ids=[case[0] for case in UNIT_CASES],
)
def test_unit_validators(tc_id, validator, value, should_be_valid):
    result = validator(value)
    if should_be_valid:
        assert result is None, f"{tc_id}: input should be accepted but got error: {result}"
    else:
        assert result is not None, f"{tc_id}: input should be rejected but it was accepted"


# =====================================================================
# PART 2: FUNCTIONAL AND INTEGRATION TESTS (Flask routes + database)
# Each test uses a fresh temporary database, so your real data is untouched.
# =====================================================================

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_NAME", str(tmp_path / "test_movie_booking.db"))
    database.init_db()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client


VALID_USER = {
    "name": "Sriram Iyer",
    "email": "sriram@test.com",
    "phone": "9876543210",
    "password": "Pass@1234",
}


def register(client, **overrides):
    data = {**VALID_USER, **overrides}
    return client.post("/register", data=data)


def login(client, email="sriram@test.com", password="Pass@1234", follow=False):
    return client.post(
        "/login", data={"email": email, "password": password}, follow_redirects=follow
    )


def test_TC01_register_with_valid_details(client):
    response = register(client)
    assert response.status_code == 200
    assert b"Registration successful" in response.data
    assert database.get_user_by_email("sriram@test.com") is not None


def test_TC31_duplicate_email_is_rejected(client):
    register(client)
    response = register(client)
    assert response.status_code == 400
    assert b"already registered" in response.data


def test_TC32_duplicate_email_with_different_case_is_rejected(client):
    register(client)
    response = register(client, email="SRIRAM@TEST.COM")
    assert response.status_code == 400
    assert b"already registered" in response.data


def test_TC33_password_is_stored_as_hash(client):
    register(client)
    user = database.get_user_by_email("sriram@test.com")
    assert user["password_hash"] != "Pass@1234"
    assert "Pass@1234" not in user["password_hash"]


def test_TC34_login_with_valid_credentials(client):
    register(client)
    response = login(client)
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


def test_TC35_login_email_is_case_insensitive(client):
    register(client)
    response = login(client, email="SRIRAM@TEST.COM")
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


def test_TC36_login_with_wrong_password(client):
    register(client)
    response = login(client, password="Wrong@123")
    assert response.status_code == 401
    assert b"Invalid email or password." in response.data


def test_TC37_login_with_unregistered_email(client):
    response = login(client, email="nobody@test.com")
    assert response.status_code == 401
    assert b"Invalid email or password." in response.data


def test_TC38_login_with_empty_fields(client):
    response = login(client, email="", password="")
    assert response.status_code == 400
    assert b"required" in response.data


def test_TC39_login_rejects_sql_injection_attempt(client):
    register(client)
    response = login(client, email="' OR '1'='1", password="anything")
    assert response.status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_TC40_logout_clears_session_and_shows_message(client):
    register(client)
    login(client)
    response = client.get("/logout", follow_redirects=True)
    assert b"You have been logged out." in response.data
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_TC41_dashboard_blocked_without_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_TC42_dashboard_blocked_after_logout(client):
    register(client)
    login(client)
    client.get("/logout")
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_TC43_register_then_login_end_to_end(client):
    register(client)
    response = login(client, follow=True)
    assert response.status_code == 200
    assert b"Welcome, Sriram Iyer" in response.data
