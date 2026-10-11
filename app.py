from flask import Flask, render_template, redirect, url_for
from database import init_db

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

init_db()


@app.route("/")
def home():
    return redirect(url_for("register"))


@app.route("/register")
def register():
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)