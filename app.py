import sqlite3
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for, request, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    init_db, seed_data, email_exists, create_user, get_user_by_email,
    get_movies_with_shows,
)
from validators import validate_registration

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

init_db()
seed_data()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", errors={}, form={}, success=None)

    form = {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "phone": request.form.get("phone", "").strip(),
    }
    password = request.form.get("password", "")

    errors = validate_registration(form["name"], form["email"], form["phone"], password)

    if "email" not in errors and email_exists(form["email"]):
        errors["email"] = "This email is already registered."

    if errors:
        return render_template("register.html", errors=errors, form=form, success=None), 400

    try:
        create_user(
            form["name"],
            form["email"],
            form["phone"],
            generate_password_hash(password),
        )
    except sqlite3.IntegrityError:
        errors["email"] = "This email is already registered."
        return render_template("register.html", errors=errors, form=form, success=None), 400

    return render_template(
        "register.html",
        errors={},
        form={},
        success="Registration successful! You can now log in.",
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None, form={})

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    form = {"email": email}

    if not email or not password:
        return render_template(
            "login.html", error="Email and password are required.", form=form
        ), 400

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template(
            "login.html", error="Invalid email or password.", form=form
        ), 401

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/movies")
@login_required
def movies():
    return render_template("movies.html", movie_list=get_movies_with_shows())


if __name__ == "__main__":
    app.run(debug=True, port=5001)