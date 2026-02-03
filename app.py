from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = "tripmoreee"

# ================= MYSQL CONFIG =================
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/tripmoreee"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= MAIN MODELS =================

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


hotel_amenities = db.Table(
    "hotel_amenities",
    db.Column("hotel_id", db.Integer, db.ForeignKey("hotel.id")),
    db.Column("amenity_id", db.Integer, db.ForeignKey("amenity.id"))
)


class Hotel(db.Model):
    __tablename__ = "hotel"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))
    stars = db.Column(db.Float)
    starting_price = db.Column(db.Integer)

    destination = db.relationship("Destination", backref="hotels")
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


# ================= GUIDE MODELS =================

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
            "image": d.image
        } for d in Destination.query.all()
    ])


def calculate_score(hotel):
    availability = sum(r.available_rooms for r in hotel.rooms)
    return (
        hotel.stars * 10
        + availability
        + len(hotel.amenities) * 2
        - hotel.starting_price / 1000
    )


@app.route("/api/hotels/<int:destination_id>")
def get_hotels_by_destination(destination_id):
    hotels = Hotel.query.filter_by(destination_id=destination_id).all()

    result = []
    for h in hotels:
        result.append({
            "hotel": h.name,
            "stars": h.stars,
            "price": h.starting_price,
            "amenities": [a.name for a in h.amenities],
            "available_rooms": sum(r.available_rooms for r in h.rooms),
            "images": [img.image_url for img in h.images],
            "score": calculate_score(h)
        })

    return jsonify(sorted(result, key=lambda x: x["score"], reverse=True))


@app.route("/hotels/<int:destination_id>")
def hotels_page(destination_id):
    return render_template("hotels.html", destination_id=destination_id)


# ================= GUIDE PAGE =================

@app.route("/guide/<location>")
def guide(location):

    foods = HiddenStreetFood.query.filter(
        func.lower(HiddenStreetFood.location_name) == location.lower()
    ).all()

    safety = NightSafetyZones.query.filter(
        func.lower(NightSafetyZones.location_name) == location.lower()
    ).all()

    etiquettes = LocalEtiquettes.query.filter(
        func.lower(LocalEtiquettes.location_name) == location.lower()
    ).all()

    alerts = TouristAlertsTips.query.filter(
        func.lower(TouristAlertsTips.location_name) == location.lower()
    ).all()

    essentials = LocationEssentials.query.filter(
        func.lower(LocationEssentials.location_name) == location.lower()
    ).first()

    return render_template(
        "information.html",
        location=location,
        foods=foods,
        safety=safety,
        etiquettes=etiquettes,
        alerts=alerts,
        essentials=essentials
    )


@app.route("/login")
def login():
    return render_template("login.html")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
