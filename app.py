from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "tripmoreee"

# ---------------- DATABASE CONFIG ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tripmoreee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    country_type = db.Column(db.String(50))   # national / international
    category = db.Column(db.String(50))
    vacation_type = db.Column(db.String(50))
    image = db.Column(db.String(500))


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


# ---------------- API ----------------

@app.route("/api/destinations")
def get_destinations():
    vacation_type = request.args.get("vacation_type")

    query = Destination.query
    if vacation_type:
        query = query.filter_by(vacation_type=vacation_type)

    data = []
    for d in query.all():
        data.append({
            "id": d.id,
            "name": d.name,
            "country_type": d.country_type,
            "category": d.category,
            "vacation_type": d.vacation_type,
            "image": d.image
        })

    return jsonify(data)


# ---------------- SEED (ONLY ONCE) ----------------

@app.route("/seed_destinations")
def seed_destinations():

    if Destination.query.first():
        return "Destinations already seeded."

    destinations = [

        # ---------- HONEYMOON ----------
        Destination(name="Goa", country_type="national", category="beach",
                    vacation_type="honeymoon",
                    image="https://images.pexels.com/photos/457882/pexels-photo-457882.jpeg"),

        Destination(name="Manali", country_type="national", category="mountain",
                    vacation_type="honeymoon",
                    image="https://images.pexels.com/photos/753626/pexels-photo-753626.jpeg"),

        Destination(name="Udaipur", country_type="national", category="heritage",
                    vacation_type="honeymoon",
                    image="https://images.pexels.com/photos/189833/pexels-photo-189833.jpeg"),

        Destination(name="Bali", country_type="international", category="beach",
                    vacation_type="honeymoon",
                    image="https://images.pexels.com/photos/2474689/pexels-photo-2474689.jpeg"),

        Destination(name="Paris", country_type="international", category="heritage",
                    vacation_type="honeymoon",
                    image="https://images.pexels.com/photos/338515/pexels-photo-338515.jpeg"),

        # ---------- FAMILY ----------
        Destination(name="Jaipur", country_type="national", category="heritage",
                    vacation_type="family",
                    image="https://images.pexels.com/photos/3672388/pexels-photo-3672388.jpeg"),

        Destination(name="Shimla", country_type="national", category="mountain",
                    vacation_type="family",
                    image="https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg"),

        Destination(name="Kerala", country_type="national", category="nature",
                    vacation_type="family",
                    image="https://images.pexels.com/photos/572897/pexels-photo-572897.jpeg"),

        Destination(name="Dubai", country_type="international", category="city",
                    vacation_type="family",
                    image="https://images.pexels.com/photos/2044434/pexels-photo-2044434.jpeg"),

        Destination(name="Singapore", country_type="international", category="city",
                    vacation_type="family",
                    image="https://images.pexels.com/photos/466685/pexels-photo-466685.jpeg"),

        # ---------- ADVENTURE ----------
        Destination(name="Ladakh", country_type="national", category="mountain",
                    vacation_type="adventure",
                    image="https://images.pexels.com/photos/5205083/pexels-photo-5205083.jpeg"),

        Destination(name="Rishikesh", country_type="national", category="river",
                    vacation_type="adventure",
                    image="https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg"),

        Destination(name="Spiti Valley", country_type="national", category="mountain",
                    vacation_type="adventure",
                    image="https://images.pexels.com/photos/2437291/pexels-photo-2437291.jpeg"),

        Destination(name="Switzerland", country_type="international", category="mountain",
                    vacation_type="adventure",
                    image="https://images.pexels.com/photos/417074/pexels-photo-417074.jpeg"),

        Destination(name="New Zealand", country_type="international", category="nature",
                    vacation_type="adventure",
                    image="https://images.pexels.com/photos/355508/pexels-photo-355508.jpeg"),

        # ---------- SPIRITUAL ----------
        Destination(name="Kedarnath", country_type="national", category="spiritual",
                    vacation_type="spiritual",
                    image="https://images.pexels.com/photos/158607/cross-church-religion-christian-158607.jpeg"),

        Destination(name="Varanasi", country_type="national", category="spiritual",
                    vacation_type="spiritual",
                    image="https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg"),

        Destination(name="Rameshwaram", country_type="national", category="spiritual",
                    vacation_type="spiritual",
                    image="https://images.pexels.com/photos/161276/temple-india-religion-161276.jpeg"),

        Destination(name="Mecca", country_type="international", category="spiritual",
                    vacation_type="spiritual",
                    image="https://images.pexels.com/photos/7249293/pexels-photo-7249293.jpeg"),

        Destination(name="Vatican City", country_type="international", category="spiritual",
                    vacation_type="spiritual",
                    image="https://images.pexels.com/photos/208739/pexels-photo-208739.jpeg"),

        # ---------- SOLO ----------
        Destination(name="Kasol", country_type="national", category="mountain",
                    vacation_type="solo",
                    image="https://images.pexels.com/photos/2437291/pexels-photo-2437291.jpeg"),

        Destination(name="Pondicherry", country_type="national", category="beach",
                    vacation_type="solo",
                    image="https://images.pexels.com/photos/753626/pexels-photo-753626.jpeg"),

        Destination(name="Hampi", country_type="national", category="heritage",
                    vacation_type="solo",
                    image="https://images.pexels.com/photos/189833/pexels-photo-189833.jpeg"),

        Destination(name="Amsterdam", country_type="international", category="city",
                    vacation_type="solo",
                    image="https://images.pexels.com/photos/417074/pexels-photo-417074.jpeg"),

        Destination(name="Iceland", country_type="international", category="nature",
                    vacation_type="solo",
                    image="https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg"),
    ]

    db.session.bulk_save_objects(destinations)
    db.session.commit()
    return "✅ 25 destinations inserted successfully"



# ---------------- RUN ----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
