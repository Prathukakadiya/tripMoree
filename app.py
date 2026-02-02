from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "tripmoreee"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tripmoreee.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class Destination(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))
    stars = db.Column(db.Float)
    starting_price = db.Column(db.Integer)

    destination = db.relationship("Destination", backref="hotels")
    amenities = db.relationship("Amenity", secondary=hotel_amenities)


class Amenity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey("hotel.id"))
    room_type = db.Column(db.String(50))
    total_rooms = db.Column(db.Integer)
    booked_rooms = db.Column(db.Integer)
    base_price = db.Column(db.Integer)

    hotel = db.relationship("Hotel", backref="rooms")

    @property
    def available_rooms(self):
        return self.total_rooms - self.booked_rooms


class HotelImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey("hotel.id"))
    image_url = db.Column(db.String(300))

    hotel = db.relationship("Hotel", backref="images")

# ================= ROUTES =================

@app.route("/")
def home():
    return "✅ TripMoree Backend Running Successfully"


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

@app.route("/api/compare_hotels/<int:destination_id>")
def compare_hotels(destination_id):
    hotels = Hotel.query.filter_by(destination_id=destination_id).all()

    result = []
    for h in hotels:
        result.append({
            "hotel": h.name,
            "stars": h.stars,
            "starting_price": h.starting_price,
            "amenities": [a.name for a in h.amenities],
            "images": [img.image_url for img in h.images],
            "available_rooms": sum(
                (r.total_rooms - r.booked_rooms) for r in h.rooms
            )
        })

    return jsonify(result)
@app.route("/hotels/<int:destination_id>")
def hotels_page(destination_id):
    return render_template(
        "hotels.html",
        destination_id=destination_id
    )
@app.route("/destinations")
def destinations_page():
    return render_template("destinations.html")

# ================= RUN =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
