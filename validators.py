import re
import string


def validate_name(name):
    name = name.strip()
    if not name:
        return "Name is required."
    if len(name) < 3 or len(name) > 30:
        return "Name must be between 3 and 30 characters."
    if not re.fullmatch(r"[A-Za-z ]+", name):
        return "Name can contain only alphabets and spaces."
    return None


def validate_email(email):
    email = email.strip()
    if not email:
        return "Email is required."
    if ".." in email:
        return "Enter a valid email address."
    if not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email):
        return "Enter a valid email address."
    return None


def validate_phone(phone):
    phone = phone.strip()
    if not phone:
        return "Phone number is required."
    if not (phone.isascii() and phone.isdigit()):
        return "Phone number must contain only digits."
    if len(phone) != 10:
        return "Phone number must be exactly 10 digits."
    return None


def validate_password(password):
    if not password:
        return "Password is required."
    if len(password) < 8 or len(password) > 20:
        return "Password must be between 8 and 20 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one digit."
    if not any(c in string.punctuation for c in password):
        return "Password must contain at least one special character."
    return None


def validate_registration(name, email, phone, password):
    errors = {}
    checks = {
        "name": validate_name(name),
        "email": validate_email(email),
        "phone": validate_phone(phone),
        "password": validate_password(password),
    }
    for field, message in checks.items():
        if message:
            errors[field] = message
    return errors




# ---------------- Module 2: seat selection ----------------
SEAT_ROWS = "ABCDE"
SEATS_PER_ROW = 8
MAX_SEATS = 6
ALL_SEATS = {f"{row}{num}" for row in SEAT_ROWS for num in range(1, SEATS_PER_ROW + 1)}


def validate_seat_selection(selected, booked):
    """Returns an error message, or None when the selection is valid."""
    if not selected:
        return "Select at least 1 seat."
    if len(selected) > MAX_SEATS:
        return "You can book a maximum of 6 seats at a time."
    if len(set(selected)) != len(selected):
        return "Duplicate seats selected."
    if any(seat not in ALL_SEATS for seat in selected):
        return "Invalid seat selected."
    taken = sorted(seat for seat in selected if seat in booked)
    if taken:
        return "Seat(s) already booked: " + ", ".join(taken) + "."
    return None