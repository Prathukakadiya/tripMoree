from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import math
from flask import url_for

from sqlalchemy import func, text
import math

app = Flask(__name__)
app.secret_key = "tripmoreee"

# ================= MYSQL CONFIG =================
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root@127.0.0.1:3306/tripmoreee"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= LOGIN HELPER =================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ================= MAIN MODELS =================

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Destination(db.Model):
    __tablename__ = "destination"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    country_type = db.Column(db.String(50))
    category = db.Column(db.String(50))
    vacation_type = db.Column(db.String(50))
    image = db.Column(db.String(500))
    rating = db.Column(db.Float)
    best_time = db.Column(db.String(50))
    latitude = db.Column(db.Float)    
    longitude = db.Column(db.Float)

hotel_amenities = db.Table(
    "hotel_amenities",
    db.Column("hotel_id", db.Integer, db.ForeignKey("hotel.id")),
    db.Column("amenity_id", db.Integer, db.ForeignKey("amenity.id"))
)

class Hotel(db.Model):
    __tablename__ = "hotel"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))

    # ✅ FIXED FOREIGN KEY (ONLY CHANGE)
    destination_id = db.Column(
        db.Integer,
        db.ForeignKey("destination.id")
    )

    stars = db.Column(db.Float)
    starting_price = db.Column(db.Integer)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    amenities = db.relationship("Amenity", secondary=hotel_amenities)
    rooms = db.relationship("Room", backref="hotel")
    images = db.relationship("HotelImage", backref="hotel")


class Amenity(db.Model):
    __tablename__ = "amenity"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Room(db.Model):
    __tablename__ = "room"
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey("hotel.id"))
    room_type = db.Column(db.String(50))
    total_rooms = db.Column(db.Integer)
    booked_rooms = db.Column(db.Integer)
    base_price = db.Column(db.Integer)

    @property
    def available_rooms(self):
        return self.total_rooms - self.booked_rooms


class HotelImage(db.Model):
    __tablename__ = "hotel_image"
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey("hotel.id"))
    image_url = db.Column(db.String(300))

# ================= GUIDE / SPOTS =================

class HiddenStreetFood(db.Model):
    __tablename__ = "hidden_street_food"
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    food_name = db.Column(db.String(150))
    description = db.Column(db.Text)
    rating = db.Column(db.Float)
    place = db.Column(db.String(100))


class NightSafetyZones(db.Model):
    __tablename__ = "night_safety_zones"
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)


class LocalEtiquettes(db.Model):
    __tablename__ = "local_etiquettes"
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)


class TouristAlertsTips(db.Model):
    __tablename__ = "tourist_alerts_tips"
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    title = db.Column(db.String(120))
    description = db.Column(db.Text)


class LocationEssentials(db.Model):
    __tablename__ = "location_essentials"
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    doctor1_name = db.Column(db.String(100))
    doctor1_phone = db.Column(db.String(20))
    doctor2_name = db.Column(db.String(100))
    doctor2_phone = db.Column(db.String(20))
    scam_alert = db.Column(db.Text)
    weather_alert = db.Column(db.Text)


class HypeSpot(db.Model):
    __tablename__ = "hype_spots"
    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))
    spot_name = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)


class Transport(db.Model):
    __tablename__ = "transport"
    id = db.Column(db.Integer, primary_key=True)
    vehicle_name = db.Column(db.String(100))
    vehicle_type = db.Column(db.String(50))
    ac_type = db.Column(db.String(20))
    price_per_km = db.Column(db.Integer)


# ================= TRANSPORT BOOKING MODELS =================

class Bus(db.Model):
    __tablename__ = "buses"
    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(20))
    operator = db.Column(db.String(50))
    source = db.Column(db.String(50))
    destination = db.Column(db.String(50))
    departure_time = db.Column(db.String(20))
    arrival_time = db.Column(db.String(20))
    bus_type = db.Column(db.String(20))
    price = db.Column(db.Integer)
    total_seats = db.Column(db.Integer)
    available_seats = db.Column(db.Integer)


class Train(db.Model):
    __tablename__ = "trains"
    id = db.Column(db.Integer, primary_key=True)
    train_number = db.Column(db.String(20))
    train_name = db.Column(db.String(100))
    source = db.Column(db.String(50))
    destination = db.Column(db.String(50))
    departure_time = db.Column(db.String(20))
    arrival_time = db.Column(db.String(20))
    price = db.Column(db.Integer)
    train_type = db.Column(db.String(30))
    total_seats = db.Column(db.Integer)
    available_seats = db.Column(db.Integer)


class Flight(db.Model):
    __tablename__ = "flights"
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20))
    airline = db.Column(db.String(50))
    source = db.Column(db.String(50))
    destination = db.Column(db.String(50))
    departure_time = db.Column(db.String(20))
    arrival_time = db.Column(db.String(20))
    duration = db.Column(db.String(20))
    price = db.Column(db.Integer)
    total_seats = db.Column(db.Integer)
    available_seats = db.Column(db.Integer)
    
class BookingHistory(db.Model):
    __tablename__ = "booking_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)

    destination = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="active")  
    # active / completed / cancelled

    created_at = db.Column(db.DateTime, server_default=db.func.now())
class TransportBooking(db.Model):
    __tablename__ = "transport_bookings"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking_history.id"))

    transport_type = db.Column(db.String(20))  # bus / train / flight / cab
    source = db.Column(db.String(50))
    destination = db.Column(db.String(50))
    persons = db.Column(db.Integer)
    price = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

class HotelBooking(db.Model):
    __tablename__ = "hotel_bookings"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking_history.id"))

    hotel_name = db.Column(db.String(100))
    check_in = db.Column(db.Date, nullable=True)
    check_out = db.Column(db.Date, nullable=True)
    price = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
class BookingHypeSpot(db.Model):
    __tablename__ = "booking_hype_spots"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking_history.id"))
    spot_id = db.Column(db.Integer)


# ================= ROUTES =================

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/destinations")
def destinations_page():
    return render_template("destinations.html")


@app.route("/api/destinations")
def get_destinations():
    return jsonify([
        {
            "id": d.id,
            "name": d.name,
            "rating": d.rating,
            "image": d.image,
            "best_time": d.best_time,
            "category": d.category,
            "country_type": d.country_type,
            "vacation_type": d.vacation_type
        }
        for d in Destination.query.all()
    ])

@app.route("/api/hotels/<int:destination_id>")
def api_hotels(destination_id):
    hotels = Hotel.query.filter_by(destination_id=destination_id).all()

    data = []
    for h in hotels:
        data.append({
            "id": h.id,                      # ✅ THIS WAS MISSING
            "hotel": h.name,
            "stars": h.stars,
            "price": h.starting_price,
            "available_rooms": sum(r.available_rooms for r in h.rooms),
            "amenities": [a.name for a in h.amenities],
            "images": [img.image_url for img in h.images]
        })

    return jsonify(data)

@app.route("/book-hotel/<int:hotel_id>", methods=["GET", "POST"])
def book_hotel(hotel_id):

    if "user_id" not in session:
        return redirect("/login")

    hotel = Hotel.query.get_or_404(hotel_id)
    destination = Destination.query.get(hotel.destination_id)

    if request.method == "POST":

        total_price = hotel.starting_price

        # 1️⃣ CREATE MAIN BOOKING (TRIP)
        booking = BookingHistory(
            user_id=session["user_id"],
            destination=destination.name
        )
        db.session.add(booking)
        db.session.commit()

        # 🔑 VERY IMPORTANT
        session["booking_id"] = booking.id

        # 2️⃣ SAVE HOTEL BOOKING
        hotel_booking = HotelBooking(
            booking_id=booking.id,
            hotel_name=hotel.name,
            price=total_price
        )
        db.session.add(hotel_booking)
        db.session.commit()

        return redirect(f"/after-hotel-booking/{hotel.id}")

    return render_template("book_hotel.html", hotel=hotel)



@app.route("/guide/<location>")
def guide(location):
    foods = HiddenStreetFood.query.filter(func.lower(HiddenStreetFood.location_name) == location.lower()).all()
    safety = NightSafetyZones.query.filter(func.lower(NightSafetyZones.location_name) == location.lower()).all()
    etiquettes = LocalEtiquettes.query.filter(func.lower(LocalEtiquettes.location_name) == location.lower()).all()
    alerts = TouristAlertsTips.query.filter(func.lower(TouristAlertsTips.location_name) == location.lower()).all()
    essentials = LocationEssentials.query.filter(func.lower(LocationEssentials.location_name) == location.lower()).first()

    return render_template(
        "information.html",
        location=location,
        foods=foods,
        safety=safety,
        etiquettes=etiquettes,
        alerts=alerts,
        essentials=essentials
    )
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return redirect("/login")

        session["user_id"] = user.id
        session["is_logged_in"] = True   # ✅ THIS IS THE KEY

        return redirect("/")

    return render_template("login.html")






@app.route("/hotels/<int:destination_id>")
def hotels_by_destination(destination_id):
    destination = Destination.query.get_or_404(destination_id)
    hotels = Hotel.query.filter_by(destination_id=destination_id).all()

    return render_template(
        "hotels.html",
        destination=destination,
        hotels=hotels
    )
@app.route("/signup", methods=["GET", "POST"])
def signup():
    next_page = request.args.get("next")

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            return redirect(url_for("login", next=next_page))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id

        if next_page:
            return redirect(next_page)

        return redirect("/")

    return render_template("signup.html")
@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login")

    bookings = BookingHistory.query.filter_by(
        user_id=session["user_id"]
    ).order_by(BookingHistory.created_at.desc()).all()

    result = []

    for b in bookings:
        hotel = HotelBooking.query.filter_by(booking_id=b.id).first()
        transport = TransportBooking.query.filter_by(booking_id=b.id).first()
        spots = BookingHypeSpot.query.filter_by(booking_id=b.id).all()

        result.append({
            "booking": b,
            "hotel": hotel,
            "transport": transport,
            "spots": spots
        })

    return render_template("my_bookings.html", data=result)

@app.route("/after-hotel-booking/<int:hotel_id>")
def after_hotel_booking(hotel_id):

    if "user_id" not in session:
        return redirect("/login")

    hotel = Hotel.query.get_or_404(hotel_id)
    destination = Destination.query.get(hotel.destination_id)

    return render_template(
        "after_hotel_booking.html",
        hotel=hotel,
        destination=destination
    )

@app.route("/transport-choice/<destination>")
def transport_choice(destination):
    return render_template(
        "transport_choice.html",
        destination=destination
    )
@app.route("/flight/<destination>", methods=["GET", "POST"])
def flight(destination):

    if request.method == "POST":

        transport = TransportBooking(
            booking_id=session["booking_id"],
            transport_type="flight",
            source=request.form["source"],
            destination=request.form["destination"],
            persons=int(request.form["persons"]),
            price=5000
        )

        db.session.add(transport)
        db.session.commit()

        dest = Destination.query.filter_by(name=destination).first()
        return redirect(url_for("hype_spots", destination_id=dest.id))


    return render_template("flight.html", destination=destination)
@app.route("/bus/<destination>", methods=["GET", "POST"])
def bus(destination):

    if request.method == "POST":

        transport = TransportBooking(
            booking_id=session["booking_id"],
            transport_type="bus",
            source=request.form["source"],
            destination=request.form["destination"],
            persons=int(request.form["persons"]),
            price=1200
        )

        db.session.add(transport)
        db.session.commit()

        dest = Destination.query.filter_by(name=destination).first()
        return redirect(url_for("hype_spots", destination_id=dest.id))


    return render_template("bus.html", destination=destination)
@app.route("/train/<destination>", methods=["GET", "POST"])
def train(destination):

    if request.method == "POST":

        transport = TransportBooking(
            booking_id=session["booking_id"],
            transport_type="train",
            source=request.form["source"],
            destination=request.form["destination"],
            persons=int(request.form["persons"]),
            price=800
        )

        db.session.add(transport)
        db.session.commit()

        dest = Destination.query.filter_by(name=destination).first()
        return redirect(url_for("hype_spots", destination_id=dest.id))

    return render_template("train.html", destination=destination)


@app.route("/add-transport", methods=["POST"])
def add_transport():
    data = request.json

    booking_id = data["booking_id"]
    transport_type = data["transport_type"]
    cab_id = data["cab_id"]

    cursor.execute("""
      INSERT INTO transport_bookings
      (booking_id, transport_type, provider, price, status)
      VALUES (%s, %s, %s, %s, 'confirmed')
    """, (booking_id, "cab", "local cab", 1500))

    db.commit()
    return {"success": True}

@app.route("/hype-spots/<int:destination_id>")
def hype_spots(destination_id):

    destination = Destination.query.get_or_404(destination_id)
    spots = BookingHypeSpot.query.filter_by(booking_id=b.id).all() or []


    return render_template(
    "hype_spots.html",
    spots=spots,
    destination_name=destination.name
)
from math import radians, cos, sin, asin, sqrt
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

@app.route("/api/calculate-distance", methods=["POST"])
def calculate_distance():
    data = request.json
    spot_ids = data.get("spots", [])

    if not spot_ids:
        return jsonify({"distance_km": 0})

    spots = HypeSpot.query.filter(HypeSpot.id.in_(spot_ids)).all()
    destination = Destination.query.get(spots[0].destination_id)

    total_distance = 0
    for spot in spots:
        total_distance += haversine(
            destination.latitude,
            destination.longitude,
            spot.latitude,
            spot.longitude
        )

    return jsonify({"distance_km": round(total_distance, 2)})



@app.route("/api/calculate-transport", methods=["POST"])
def calculate_transport():
    data = request.json
    distance = float(data["distance"])

    vehicles = Transport.query.all()

    result = []
    for v in vehicles:
        result.append({
            "vehicle": v.vehicle_name,
            "type": v.vehicle_type,
            "ac": v.ac_type,
            "price": int(distance * v.price_per_km)
        })

    return jsonify(result)
@app.route("/book-cab", methods=["POST"])
def book_cab():

    data = request.json

    # 🔹 get hotel booking to decide persons
    hotel_booking = HotelBooking.query.filter_by(
        booking_id=session["booking_id"]
    ).first()

    persons = 1
    if hotel_booking:
        persons = 2   # simple logic (future ma improve kari saksho)

    cab = TransportBooking(
        booking_id=session["booking_id"],
        transport_type="cab",
        source="hotel",
        destination="spots",
        persons=persons,
        price=data["price"]
    )

    db.session.add(cab)
    db.session.commit()

    return jsonify({"success": True})


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
