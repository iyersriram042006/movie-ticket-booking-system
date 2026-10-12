import sqlite3

from flask import Flask, render_template, redirect, url_for, request
from werkzeug.security import generate_password_hash

from database import init_db, email_exists, create_user
from validators import validate_registration

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

init_db()


@app.route("/")
def home():
    return redirect(url_for("register"))


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


if __name__ == "__main__":
    app.run(debug=True, port=5001)