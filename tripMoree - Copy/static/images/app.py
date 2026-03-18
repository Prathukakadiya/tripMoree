from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "tripmoreee"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/tripmoreee_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- DATABASE TABLES ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

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


@app.route("/")
def home():
    return render_template("home.html")
# ---------------- TEST ROUTE ----------------
@app.route("/test")
def test():
    return "Server Working"

# ---------------- ROUTES ----------------



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user:
            return "Email already exists"

        hashed = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed)

        db.session.add(new_user)
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

@app.route("/add_hotel", methods=["GET", "POST"])
def add_hotel():
    if request.method == "POST":
        name = request.form["name"]
        location = request.form["location"]

        hotel = Hotel(name=name, location=location)
        db.session.add(hotel)
        db.session.commit()
        return redirect("/hotels")

    return render_template("add_hotel.html")

@app.route("/hotels")
def hotels():
    return render_template("hotels.html", hotels=Hotel.query.all())

@app.route("/add_room", methods=["GET", "POST"])
def add_room():
    hotels = Hotel.query.all()

    if request.method == "POST":
        room = Room(
            hotel_id=request.form["hotel_id"],
            room_type=request.form["room_type"],
            price=request.form["price"],
            available_rooms=request.form["available"]
        )
        db.session.add(room)
        db.session.commit()
        return redirect("/rooms")

    return render_template("add_room.html", hotels=hotels)

@app.route("/rooms")
def rooms():
    return render_template("rooms.html", rooms=Room.query.all())

@app.route("/book/<int:room_id>", methods=["GET", "POST"])
def book(room_id):
    room = Room.query.get(room_id)

    if request.method == "POST":
        days = int(request.form["days"])

        if room.available_rooms > 0:
            room.available_rooms -= 1
            total = room.price * days

            booking = Booking(
                user_name=session.get("user_name"),
                room_type=room.room_type,
                days=days,
                total_price=total
            )

            db.session.add(booking)
            db.session.commit()
            return f"Booking Successful! Total ₹{total}"

        return "Room Not Available"

    return render_template("book.html", room=room)

@app.route("/my_bookings")
def my_bookings():
    return render_template("bookings.html", bookings=Booking.query.all())

# ---------------- RUN ----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
