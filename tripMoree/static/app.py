from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "tripmoreee"

# --------- DATABASE CONFIG (SQLite – no XAMPP needed) ---------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tripmoreee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- DATABASE TABLES ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    country_type = db.Column(db.String(50))      # national / international
    category = db.Column(db.String(50))          # beach, mountain, heritage
    vacation_type = db.Column(db.String(50))     # honeymoon, family, adventure
    image = db.Column(db.String(200))


class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    location = db.Column(db.String(100))


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer)
    room_type = db.Column(db.String(50))
    price = db.Column(db.Integer)
    available_rooms = db.Column(db.Integer)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    room_type = db.Column(db.String(50))
    days = db.Column(db.Integer)
    total_price = db.Column(db.Integer)

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/destinations")
def destinations():
    return render_template("destinations.html")


@app.route("/test")
def test():
    return "Server Working"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            return "Email already exists"

        hashed = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed)

        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_name"] = user.name
            return redirect("/dashboard")

        return "Wrong email or password"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_name" in session:
        return f"Welcome {session['user_name']}"
    return redirect("/login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- DESTINATION SEED ----------------

@app.route("/seed_destinations")
def seed_destinations():
    destinations = [
        Destination(name="Goa", country_type="national", category="beach", vacation_type="honeymoon", image="goa.jpg"),
        Destination(name="Manali", country_type="national", category="mountain", vacation_type="family", image="manali.jpg"),
        Destination(name="Ladakh", country_type="national", category="mountain", vacation_type="adventure", image="ladakh.jpg"),
        Destination(name="Jaipur", country_type="national", category="heritage", vacation_type="family", image="jaipur.jpg"),
        Destination(name="Dubai", country_type="international", category="city", vacation_type="friends", image="dubai.jpg"),
        Destination(name="Bali", country_type="international", category="beach", vacation_type="honeymoon", image="bali.jpg"),
        Destination(name="Maldives", country_type="international", category="beach", vacation_type="honeymoon", image="maldives.jpg"),
        Destination(name="Paris", country_type="international", category="heritage", vacation_type="couple", image="paris.jpg"),
    ]

    db.session.bulk_save_objects(destinations)
    db.session.commit()
    return "Destinations inserted successfully!"

from flask import jsonify

@app.route("/api/destinations")
def get_destinations():
    vacation_type = request.args.get("vacation_type")
    country_type = request.args.get("country_type")
    category = request.args.get("category")

    query = Destination.query

    if vacation_type:
        query = query.filter_by(vacation_type=vacation_type)
    if country_type:
        query = query.filter_by(country_type=country_type)
    if category:
        query = query.filter_by(category=category)

    destinations = query.all()

    data = []
    for d in destinations:
        data.append({
            "id": d.id,
            "name": d.name,
            "country_type": d.country_type,
            "category": d.category,
            "vacation_type": d.vacation_type,
            "image": d.image
        })

    return jsonify(data)



# ---------------- RUN ----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
