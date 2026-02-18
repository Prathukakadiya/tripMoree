from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import math
from flask import url_for
from math import radians, cos, sin, asin, sqrt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
import os
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, session, jsonify, send_file


from sqlalchemy import func, text

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
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


# ================= MAIN MODELS =================
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

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

    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))

    stars = db.Column(db.Float)
    starting_price = db.Column(db.Integer)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # 🔥 ADD THESE
    lunch_price = db.Column(db.Integer, default=500)
    dinner_price = db.Column(db.Integer, default=600)
    pickup_price = db.Column(db.Integer, default=800)

    amenities = db.relationship("Amenity", secondary=hotel_amenities)
    rooms = db.relationship("Room", backref="hotel")


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
class CabBooking(db.Model):
    __tablename__ = "cab_bookings"

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("booking_history.id"),
        nullable=False
    )

    transport_id = db.Column(   # ✅ MATCH DATABASE COLUMN
        db.Integer,
        db.ForeignKey("transport.id"),
        nullable=False
    )

    days = db.Column(db.Integer, nullable=False)
    total_km = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


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

    ac_type = db.Column(db.String(20))      # AC / Non-AC
    seat_type = db.Column(db.String(20))    # Sleeper / Seater

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

    ac_type = db.Column(db.String(20))      # ADD
    seat_type = db.Column(db.String(20))    # ADD

    price = db.Column(db.Integer)
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

    flight_class = db.Column(db.String(20))   # MUST EXIST

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

    booking_id = db.Column(db.Integer)

    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'))
    room_id = db.Column(db.Integer)

    persons = db.Column(db.Integer)

    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)

    base_price = db.Column(db.Integer)
    extra_price = db.Column(db.Integer)
    total_price = db.Column(db.Integer)

    lunch_added = db.Column(db.Boolean, default=False)
    dinner_added = db.Column(db.Boolean, default=False)
    pickup_added = db.Column(db.Boolean, default=False)

    id_type = db.Column(db.String(20))
    id_number = db.Column(db.String(50))

    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(15))

    coupon_code = db.Column(db.String(50))
    coupon_discount = db.Column(db.Integer, default=0)

    bank_name = db.Column(db.String(50))
    card_number = db.Column(db.String(20))
    bank_discount = db.Column(db.Integer, default=0)

    final_payable = db.Column(db.Integer)

    created_at = db.Column(db.DateTime)

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    discount_percent = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)


    created_at = db.Column(db.DateTime, server_default=db.func.now())
class BookingHypeSpot(db.Model):
    __tablename__ = "booking_hype_spots"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("transport_bookings.id", ondelete="CASCADE"),
        nullable=False
    )
    spot_id = db.Column(
        db.Integer,
        db.ForeignKey("hype_spots.id", ondelete="CASCADE"),
        nullable=False
    )
class CabBookingDay(db.Model):
    __tablename__ = "cab_booking_days"

    id = db.Column(db.Integer, primary_key=True)
    cab_booking_id = db.Column(db.Integer, db.ForeignKey("cab_bookings.id"))
    day_number = db.Column(db.Integer)

    arrival_time = db.Column(db.Time)
    departure_time = db.Column(db.Time)

    pickup_type = db.Column(db.String(50))
    drop_type = db.Column(db.String(50))

    custom_pickup = db.Column(db.String(255))
    custom_drop = db.Column(db.String(255))

    day_km = db.Column(db.Float)
    day_price = db.Column(db.Float)


class CabBookingDaySpot(db.Model):
    __tablename__ = "cab_booking_day_spots"

    id = db.Column(db.Integer, primary_key=True)
    cab_booking_day_id = db.Column(
        db.Integer,
        db.ForeignKey("cab_booking_days.id")
    )
    spot_id = db.Column(db.Integer, db.ForeignKey("hype_spots.id"))


# ================= ROUTES =================
# ================= ADMIN MANAGE USERS =================

@app.route("/admin/users")
@admin_required
def admin_users():

    search = request.args.get("search")

    if search:
        users = User.query.filter(
            (User.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        ).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()

    return render_template("admin_users.html", users=users)


@app.route("/admin/delete-user/<int:user_id>")
@admin_required
def admin_delete_user(user_id):

    user = User.query.get_or_404(user_id)

    # OPTIONAL: prevent deleting yourself if admin email same
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin_users"))

# ================= ADMIN =================
from flask import render_template, request, redirect, session, flash, url_for
from werkzeug.security import check_password_hash

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    # Already logged in hoy to dashboard par moklo
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Please enter username and password", "danger")
            return redirect(url_for("admin_login"))

        admin = Admin.query.filter_by(username=username).first()

        # 🔐 SECURE PASSWORD CHECK
        if admin and admin.password == password:

            session["admin_id"] = admin.id
            session["admin_logged_in"] = True

            flash("Login Successful!", "success")
            return redirect(url_for("admin_dashboard"))

        else:
            flash("Invalid Username or Password", "danger")
            return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    return redirect("/admin/login")


@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect("/admin/login")

    total_users = User.query.count()
    total_hotels = Hotel.query.count()
    total_bookings = BookingHistory.query.count()

    hotel_revenue = db.session.query(func.sum(HotelBooking.final_payable)).scalar() or 0
    transport_revenue = db.session.query(func.sum(TransportBooking.price)).scalar() or 0
    cab_revenue = db.session.query(func.sum(CabBooking.price)).scalar() or 0

    total_revenue = hotel_revenue + transport_revenue + cab_revenue

    active = BookingHistory.query.filter_by(status="active").count()
    completed = BookingHistory.query.filter_by(status="completed").count()

    top_destinations = db.session.query(
        BookingHistory.destination,
        func.count(BookingHistory.id)
    ).group_by(BookingHistory.destination).all()

    return render_template(
        "admin_dashboard.html",
        users=total_users,
        hotels=total_hotels,
        bookings=total_bookings,
        revenue=total_revenue,
        active=active,
        completed=completed,
        top_destinations=top_destinations
    )

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/destinations")
def destinations_page():
    return render_template("destinations.html")

@app.route("/api/destinations")
def get_destinations():

    vacation_type = request.args.get("type")

    query = Destination.query

    if vacation_type:
        query = query.filter_by(vacation_type=vacation_type)

    destinations = query.all()

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
        for d in destinations
    ])
@app.route("/api/hotels/<int:destination_id>")
def api_hotels(destination_id):

    hotels = Hotel.query.filter_by(destination_id=destination_id).all()
    data = []

    for h in hotels:

        prices = [r.base_price for r in h.rooms if r.base_price is not None]

        data.append({
            "id": h.id,
            "hotel": h.name,
            "stars": h.stars,
            "price": min(prices) if prices else 0,
            "available_rooms": sum(
                (r.total_rooms - r.booked_rooms)
                for r in h.rooms
                if r.total_rooms is not None and r.booked_rooms is not None
            ),
            "amenities": [a.name for a in h.amenities],
            "rooms": [
                {
                    "type": r.room_type,
                    "available": (r.total_rooms - r.booked_rooms)
                        if r.total_rooms and r.booked_rooms is not None else 0,
                    "price": r.base_price
                }
                for r in h.rooms
            ]
        })

    return jsonify(data)

from datetime import datetime
import math
from flask import request, redirect, url_for, render_template, session, flash
from datetime import datetime
import math
import re



import re
from datetime import datetime
from flask import flash, redirect, request, render_template

import re
from datetime import datetime
@app.route("/book-hotel/<int:hotel_id>", methods=["GET", "POST"])
@login_required
def hotel_booking(hotel_id):

    hotel = Hotel.query.get_or_404(hotel_id)
    error = None

    if request.method == "POST":
        try:
            persons = int(request.form.get("persons", 1))
            room_id = int(request.form.get("room_id"))
            checkin = request.form.get("checkin")
            checkout = request.form.get("checkout")

            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()

            id_type = request.form.get("id_type")
            id_number = request.form.get("id_number", "").strip().upper()

            lunch = request.form.get("lunch")
            dinner = request.form.get("dinner")
            pickup = request.form.get("pickup")

            bank_name = request.form.get("bank_name", "")
            card_number = request.form.get("card_number", "").strip()

            today = datetime.today().date()
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()

            # ================= VALIDATIONS =================

            if checkin_date < today:
                error = "Check-in date cannot be in the past"

            elif checkout_date < checkin_date:
                error = "Check-out cannot be before Check-in"

            elif not re.match(r"^[6-9]\d{9}$", phone):
                error = "Invalid phone number"

            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                error = "Invalid email address"

            elif id_type == "aadhaar" and not re.match(r"^\d{12}$", id_number):
                error = "Aadhaar must be 12 digits"

            elif id_type == "pan" and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", id_number):
                error = "Invalid PAN format"

            elif not re.match(r"^\d{16}$", card_number):
                error = "Card number must be 16 digits"

            if error:
                return render_template(
                    "book_hotel.html",
                    hotel=hotel,
                    form_data=request.form,
                    error=error,
                    applied_discount=0
                )

            # ================= PRICE CALCULATION =================

            nights = (checkout_date - checkin_date).days
            if nights == 0:
                nights = 1

            room = Room.query.get_or_404(room_id)
            required_rooms = math.ceil(persons / 2)

            base_price = nights * room.base_price * required_rooms

            extra_price = 0
            if lunch:
                extra_price += hotel.lunch_price * persons
            if dinner:
                extra_price += hotel.dinner_price * persons
            if pickup:
                extra_price += hotel.pickup_price

            total_price = base_price + extra_price

            bank_map = {"hdfc": 10, "sbi": 15, "icici": 12}
            bank_percent = bank_map.get(bank_name, 0)

            bank_discount = (total_price * bank_percent) // 100
            final_payable = total_price - bank_discount

            # ================= CREATE BOOKING HISTORY =================

            destination = Destination.query.get(hotel.destination_id)

            main_booking = BookingHistory(
                user_id=session["user_id"],
                destination=destination.name,
                status="active"
            )

            db.session.add(main_booking)
            db.session.commit()   # Generate ID

            # Save in session for transport
            session["booking_id"] = main_booking.id
            session["persons"] = persons
            session["destination_name"] = destination.name

            # ================= SAVE HOTEL BOOKING =================

            booking = HotelBooking(
                booking_id=main_booking.id,
                hotel_id=hotel.id,
                room_id=room_id,
                persons=persons,
                check_in=checkin_date,
                check_out=checkout_date,
                base_price=base_price,
                extra_price=extra_price,
                total_price=total_price,
                bank_name=bank_name,
                card_number=card_number,
                bank_discount=bank_discount,
                final_payable=final_payable,
                lunch_added=bool(lunch),
                dinner_added=bool(dinner),
                pickup_added=bool(pickup),
                id_type=id_type,
                id_number=id_number,
                name=name,
                email=email,
                phone=phone,
                created_at=datetime.now()
            )

            db.session.add(booking)
            db.session.commit()

            return redirect(url_for(
                "transport_choice",
                destination=destination.name,
                booked="1"
            ))

        except Exception as e:
            return render_template(
                "book_hotel.html",
                hotel=hotel,
                form_data=request.form,
                error="Something went wrong",
                applied_discount=0
            )

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
from werkzeug.security import check_password_hash

@app.route("/login", methods=["GET", "POST"])
def login():

    next_page = request.args.get("next")

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Email and password required"

        user = User.query.filter_by(email=email).first()

        if not user:
            return "User not found"

        if not check_password_hash(user.password, password):
            return "Incorrect password"

        # 🔥 LOGIN SUCCESS
        session["user_id"] = user.id
        session["is_logged_in"] = True

        if next_page:
            return redirect(next_page)

        return redirect(url_for("home"))

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
from werkzeug.security import generate_password_hash
import re

@app.route("/signup", methods=["GET", "POST"])
def signup():
    next_page = request.args.get("next")

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # 🔥 BASIC VALIDATION
        if not name or not email or not password:
            return "All fields are required"

        # 🔥 PASSWORD RULES
        if len(password) < 6:
            return "Password must be at least 6 characters"

        if not any(char.isdigit() for char in password):
            return "Password must contain at least 1 number"

        if not any(char.isupper() for char in password):
            return "Password must contain at least 1 uppercase letter"

        # 🔥 CHECK EMAIL EXISTS
        user = User.query.filter_by(email=email).first()
        if user:
            return "Email already registered"

        # 🔥 HASH PASSWORD
        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        # 🔥 AUTO LOGIN AFTER SIGNUP
        session["user_id"] = new_user.id

        # 🔥 SAFE REDIRECT
        if next_page:
            return redirect(next_page)

        return redirect(url_for("home"))

    return render_template("signup.html")


@app.route("/my-bookings")
@login_required
def my_bookings():

    bookings = BookingHistory.query.filter_by(
        user_id=session["user_id"]
    ).order_by(BookingHistory.created_at.desc()).all()

    result = []

    for b in bookings:

        # ================= HOTEL =================
        hotel = HotelBooking.query.filter_by(
            booking_id=b.id
        ).first()

        hotel_total = hotel.final_payable if hotel and hotel.final_payable else 0

        # ================= TRANSPORT =================
        transports = TransportBooking.query.filter_by(
            booking_id=b.id
        ).all()

        transport_data = []
        transport_total = 0

        for t in transports:

            transport_total += t.price or 0

            transport_data.append({
                "transport": t
            })

        # ================= CAB =================
        cab = CabBooking.query.filter_by(
            booking_id=b.id
        ).first()

        cab_days = []
        cab_total = 0

        if cab:

            cab_total = cab.price or 0

            days = CabBookingDay.query.filter_by(
                cab_booking_id=cab.id
            ).order_by(CabBookingDay.day_number).all()

            for d in days:

                spots_rel = CabBookingDaySpot.query.filter_by(
                    cab_booking_day_id=d.id
                ).all()

                spot_names = []

                for s in spots_rel:
                    spot = HypeSpot.query.get(s.spot_id)
                    if spot:
                        spot_names.append(spot.spot_name)

                cab_days.append({
                    "day": d.day_number,
                    "arrival": d.arrival_time,
                    "departure": d.departure_time,
                    "pickup": d.pickup_type,
                    "drop": d.drop_type,
                    "spots": spot_names,
                    "km": d.day_km,
                    "price": d.day_price
                })

        # ================= GRAND TOTAL =================
        grand_total = hotel_total + transport_total + cab_total

        result.append({
            "booking": b,
            "hotel": hotel,
            "transports": transport_data,
            "cab": cab,
            "cab_days": cab_days,
            "hotel_total": hotel_total,
            "transport_total": transport_total,
            "cab_total": cab_total,
            "grand_total": grand_total
        })

    return render_template("my_bookings.html", bookings=result)


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
@login_required
def flight(destination):

    persons = session.get("persons", 1)
    booking_id = session.get("booking_id")

    if not booking_id:
        return redirect(url_for("home"))

    flights = []

    if request.method == "POST":
        source = request.form.get("source")
        flight_class = request.form.get("flight_class")

        flights = Flight.query.filter_by(
            source=source,
            destination=destination,
            flight_class=flight_class
        ).all()

    return render_template(
        "flights.html",
        destination=destination,
        persons=persons,
        flights=flights
    )

@app.route("/confirm-flight/<int:flight_id>")
@login_required
def confirm_flight(flight_id):

    booking_id = session.get("booking_id")
    persons = session.get("persons", 1)

    if not booking_id:
        return redirect(url_for("home"))

    flight = Flight.query.get_or_404(flight_id)

    if flight.available_seats < persons:
        return "Not enough seats available"

    flight.available_seats -= persons

    transport_booking = TransportBooking(
        booking_id=booking_id,
        transport_type="flight",
        source=flight.source,
        destination=flight.destination,
        persons=persons,
        price=flight.price * persons
    )

    db.session.add(transport_booking)
    db.session.commit()

    hotel_booking = HotelBooking.query.filter_by(
        booking_id=booking_id
    ).first()

    return redirect(url_for("hype_spots", hotel_booking_id=hotel_booking.id))


# ================= BUS =================

@app.route("/bus/<destination>", methods=["GET", "POST"])
@login_required
def bus(destination):

    booking_id = session.get("booking_id")

    if not booking_id:
        return redirect(url_for("home"))

    persons = session.get("persons", 1)

    buses = []

    if request.method == "POST":
        source = request.form.get("source")
        ac_type = request.form.get("ac_type")
        seat_type = request.form.get("seat_type")

        buses = Bus.query.filter_by(
            source=source,
            destination=destination,
            ac_type=ac_type,
            seat_type=seat_type
        ).all()

    return render_template(
        "bus.html",
        destination=destination,
        persons=persons,
        buses=buses
    )
@app.route("/confirm-bus/<int:bus_id>")
@login_required
def confirm_bus(bus_id):

    booking_id = session.get("booking_id")

    if not booking_id:
        return redirect(url_for("home"))

    bus = Bus.query.get_or_404(bus_id)
    persons = session.get("persons", 1)

    if bus.available_seats < persons:
        return "Not enough seats available"

    bus.available_seats -= persons

    transport = TransportBooking(
        booking_id=booking_id,
        transport_type="bus",
        source=bus.source,
        destination=bus.destination,
        persons=persons,
        price=bus.price * persons
    )

    db.session.add(transport)
    db.session.commit()

    hotel_booking = HotelBooking.query.filter_by(
        booking_id=booking_id
    ).first()
    flash("Bus booked successfully!", "success")
    return redirect(url_for("hype_spots", hotel_booking_id=hotel_booking.id))
@app.route("/train/<destination>", methods=["GET", "POST"])
@login_required
def train(destination):

    persons = session.get("persons", 1)
    booking_id = session.get("booking_id")

    if not booking_id:
        return redirect(url_for("home"))

    trains = []

    if request.method == "POST":
        source = request.form.get("source")
        ac_type = request.form.get("ac_type")
        seat_type = request.form.get("seat_type")

        trains = Train.query.filter_by(
            source=source,
            destination=destination,
            ac_type=ac_type,
            seat_type=seat_type
        ).all()

    return render_template(
        "train.html",
        destination=destination,
        persons=persons,
        trains=trains
    )


@app.route("/confirm-train/<int:train_id>")
@login_required
def confirm_train(train_id):

    booking_id = session.get("booking_id")
    persons = session.get("persons", 1)

    if not booking_id:
        return redirect(url_for("home"))

    train = Train.query.get_or_404(train_id)

    if train.available_seats < persons:
        return "Not enough seats available"

    train.available_seats -= persons

    transport_booking = TransportBooking(
        booking_id=booking_id,
        transport_type="train",
        source=train.source,
        destination=train.destination,
        persons=persons,
        price=train.price * persons
    )

    db.session.add(transport_booking)
    db.session.commit()

    hotel_booking = HotelBooking.query.filter_by(
        booking_id=booking_id
    ).first()

    return redirect(url_for("hype_spots", hotel_booking_id=hotel_booking.id))

@app.route("/api/calculate-transport", methods=["POST"])
@login_required
def calculate_transport():

    data = request.json

    hotel_id = data.get("hotel_id")
    spot_ids = data.get("spot_ids", [])
    total_days = int(data.get("total_days", 1))
    arrival_time = data.get("arrival_time")
    departure_time = data.get("departure_time")

    if not hotel_id or not spot_ids:
        return jsonify([])

    hotel = Hotel.query.get_or_404(hotel_id)

    current_lat = float(hotel.latitude)
    current_lon = float(hotel.longitude)

    total_distance = 0

    # 🔹 HOTEL → SPOTS → HOTEL DISTANCE
    for sid in spot_ids:
        spot = HypeSpot.query.get(int(sid))
        if not spot:
            continue

        spot_lat = float(spot.latitude)
        spot_lon = float(spot.longitude)

        distance = haversine(
            current_lat,
            current_lon,
            spot_lat,
            spot_lon
        )

        total_distance += distance

        current_lat = spot_lat
        current_lon = spot_lon

    # 🔹 Return to hotel
    return_distance = haversine(
        current_lat,
        current_lon,
        float(hotel.latitude),
        float(hotel.longitude)
    )

    total_distance += return_distance

    total_distance = round(total_distance, 2)

    # 🔥 TIME CALCULATION (Optional Advanced Use)
    total_hours = 8  # default

    if arrival_time and departure_time:
        from datetime import datetime

        t1 = datetime.strptime(arrival_time, "%H:%M")
        t2 = datetime.strptime(departure_time, "%H:%M")

        diff = (t2 - t1).seconds / 3600
        total_hours = round(diff, 2)

    # 🔥 PRICING LOGIC
    vehicles = Transport.query.all()

    result = []

    DRIVER_CHARGE_PER_DAY = 1200

    for v in vehicles:

        distance_cost = total_distance * float(v.price_per_km)

        driver_cost = DRIVER_CHARGE_PER_DAY * total_days

        # optional waiting charge
        waiting_cost = total_hours * 100

        total_price = distance_cost + driver_cost + waiting_cost

        result.append({
            "vehicle": v.vehicle_name,
            "type": v.vehicle_type,
            "ac": v.ac_type,
            "price": round(total_price, 2),
            "cab_id": v.id,
            "distance": total_distance,
            "days": total_days,
            "hours": total_hours
        })

    return jsonify(result)


@app.route("/book-train/<int:id>")
def book_train(id):

    train = Train.query.get(id)

    booking = TransportBooking(
        booking_id=session["booking_id"],
        transport_type="train",
        source=train.source,
        destination=train.destination,
        persons=session["persons"],
        price=train.price
    )

    db.session.add(booking)
    db.session.commit()

    return redirect(url_for("hype_spots", destination_id=session["destination"]))
@app.route("/book-flight/<int:id>")
def book_flight(id):

    flight = Flight.query.get(id)

    booking = TransportBooking(
        booking_id=session["booking_id"],
        transport_type="flight",
        source=flight.source,
        destination=flight.destination,
        persons=session["persons"],
        price=flight.price
    )

    db.session.add(booking)
    db.session.commit()

    return redirect(url_for("hype_spots", destination_id=session["destination"]))


@app.route("/book-cab/<int:hotel_booking_id>", methods=["POST"])
@login_required
def book_cab(hotel_booking_id):
    cab_id = request.form.get("cab_id")

    if not cab_id:
        flash("Please select a cab.", "danger")
        return redirect(request.referrer)


    from datetime import datetime

    cab_id = request.form.get("cab_id")
    total_days = int(request.form.get("total_days"))

    hotel_booking = HotelBooking.query.get_or_404(hotel_booking_id)
    transport = Transport.query.get_or_404(cab_id)
    hotel = Hotel.query.get_or_404(hotel_booking.hotel_id)

    cab_booking = CabBooking(
        booking_id=hotel_booking.booking_id,
        transport_id=transport.id,
        days=total_days,
        total_km=0,
        price=0
    )

    db.session.add(cab_booking)
    db.session.commit()

    total_km = 0
    total_price = 0

    CUSTOM_CHARGE = 500
    AIRPORT_CHARGE = 300

    for day in range(1, total_days+1):

        arrival = request.form.get(f"arrival_time_{day}")
        departure = request.form.get(f"departure_time_{day}")

        pickup_type = request.form.get(f"pickup_type_{day}")
        drop_type = request.form.get(f"drop_type_{day}")

        custom_pickup = request.form.get(f"custom_pickup_{day}")
        custom_drop = request.form.get(f"custom_drop_{day}")

        spot_ids = request.form.getlist(f"day_{day}_spots")

        current_lat = float(hotel.latitude)
        current_lon = float(hotel.longitude)

        day_km = 0

        for sid in spot_ids:
            spot = HypeSpot.query.get(int(sid))
            if not spot:
                continue

            distance = haversine(
                current_lat,
                current_lon,
                float(spot.latitude),
                float(spot.longitude)
            )

            day_km += distance
            current_lat = float(spot.latitude)
            current_lon = float(spot.longitude)

        day_km += haversine(
            current_lat,
            current_lon,
            float(hotel.latitude),
            float(hotel.longitude)
        )

        day_km = round(day_km,2)

        day_price = day_km * float(transport.price_per_km)

        if pickup_type == "custom":
            day_price += CUSTOM_CHARGE
        if drop_type == "custom":
            day_price += CUSTOM_CHARGE
        if pickup_type == "airport":
            day_price += AIRPORT_CHARGE
        if drop_type == "airport":
            day_price += AIRPORT_CHARGE

        day_price = round(day_price,2)

        total_km += day_km
        total_price += day_price

        booking_day = CabBookingDay(
            cab_booking_id=cab_booking.id,
            day_number=day,
            arrival_time=datetime.strptime(arrival,"%H:%M").time(),
            departure_time=datetime.strptime(departure,"%H:%M").time(),
            pickup_type=pickup_type,
            drop_type=drop_type,
            custom_pickup=custom_pickup,
            custom_drop=custom_drop,
            day_km=day_km,
            day_price=day_price
        )

        db.session.add(booking_day)
        db.session.commit()

        for sid in spot_ids:
            db.session.add(
                CabBookingDaySpot(
                    cab_booking_day_id=booking_day.id,
                    spot_id=int(sid)
                )
            )

    cab_booking.total_km = total_km
    cab_booking.price = total_price
    db.session.commit()

    flash("Cab booked successfully!", "success")
    return redirect(url_for("my_bookings"))




@app.route("/hype-spots/<int:hotel_booking_id>")
@login_required
def hype_spots(hotel_booking_id):

    hotel_booking = HotelBooking.query.get_or_404(hotel_booking_id)
    hotel = Hotel.query.get_or_404(hotel_booking.hotel_id)
    destination = Destination.query.get_or_404(hotel.destination_id)

    spots = HypeSpot.query.filter_by(
        destination_id=destination.id
    ).all()

    transports = Transport.query.all()

    return render_template(
    "hype_spots.html",
    spots=spots,
    transports=transports,  
    destination_name=destination.name,
    hotel_id=hotel.id,
    hotel_booking_id=hotel_booking.id
)



def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return R * c
@app.route("/experience/mountain")
@login_required
def mountain_experience():
    return render_template("mountain_experience.html")

@app.route("/experience/backwater")
@login_required
def backwater_experience():
    return render_template("backwater_experience.html")

@app.route("/experience/beach")
@login_required
def beach_experience():
    return render_template("beach_experience.html")

@app.route("/coming-soon")
def coming_soon():
    return """
    <h2 style='text-align:center;margin-top:100px;font-family:Arial;'>
    🚀 Social Media Pages Coming Soon!
    </h2>
    """
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/download-invoice/<int:booking_id>")
@login_required
def download_invoice(booking_id):

    booking = BookingHistory.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"]:
        return "Unauthorized", 403

    file_path = generate_invoice_pdf(booking_id)

    return send_file(file_path, as_attachment=True)


from email.message import EmailMessage
import smtplib
@app.route("/send-invoice/<int:booking_id>")
@login_required
def send_invoice_email(booking_id):

    booking = BookingHistory.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"]:
        return "Unauthorized", 403

    user = User.query.get(session["user_id"])

    file_path = generate_invoice_pdf(booking_id)

    msg = EmailMessage()
    msg["Subject"] = f"TripMoreee Invoice #{booking_id}"
    msg["From"] = "prathukakadiya7x@gmail.com"
    msg["To"] = user.email

    msg.set_content("Thank you for booking with TripMoreee. Invoice attached.")

    with open(file_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=f"Invoice_{booking_id}.pdf"
        )

    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.starttls()

    # 🔥 AHIA PASSWORD MUKVO
    smtp.login("prathukakadiya7x@gmail.com", "csftedtyotxuwxgu")

    smtp.send_message(msg)
    smtp.quit()

    os.remove(file_path)

    return "Invoice Sent Successfully!"



from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
import os

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from datetime import datetime
import random


def generate_invoice_pdf(booking_id):

    booking = BookingHistory.query.get_or_404(booking_id)
    hotel_booking = HotelBooking.query.filter_by(booking_id=booking.id).first()
    cab = CabBooking.query.filter_by(booking_id=booking.id).first()
    transport_list = TransportBooking.query.filter_by(booking_id=booking.id).all()

    file_path = f"invoice_{booking_id}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ================= HEADER =================
    big_title = ParagraphStyle(
        'BigTitle',
        parent=styles['Title'],
        fontSize=30,
        spaceAfter=10
    )

    elements.append(Paragraph("<b>TRIPMOREEE</b>", big_title))
    elements.append(Paragraph("---------------------------------------Explore Beautiful Destinations with us !-------------------------------", styles["Normal"]))
    elements.append(Paragraph("TripMoreee Travel Pvt Ltd", styles["Normal"]))
    elements.append(Paragraph("Surat, Gujarat, India", styles["Normal"]))
    elements.append(Paragraph("Contact: +91 98765 43210", styles["Normal"]))
    elements.append(Paragraph("Email: support@tripmoreee.com", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    # Divider
    elements.append(Table([[""]], colWidths=[500], rowHeights=[2],
                          style=TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.black)])))
    elements.append(Spacer(1, 0.3 * inch))

    # ================= BASIC INFO =================
    elements.append(Paragraph(f"<b>Invoice ID:</b> {booking.id}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d-%m-%Y')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Destination:</b> {booking.destination}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    total_amount = 0

    # ================= HOTEL SECTION =================
    if hotel_booking:

        hotel = Hotel.query.get(hotel_booking.hotel_id)
        room = Room.query.get(hotel_booking.room_id)

        random_room_number = random.randint(100, 999)

        elements.append(Paragraph("<b>Hotel Details</b>", styles["Heading3"]))
        elements.append(Spacer(1, 0.2 * inch))

        hotel_data = [
            ["Hotel Name", hotel.name if hotel else "N/A"],
            ["Room Type", room.room_type if room else "N/A"],
            ["Room Number", str(random_room_number)],
            ["Guest Name", hotel_booking.name],
            ["ID Type", hotel_booking.id_type],
            ["ID Number", hotel_booking.id_number],
            ["Persons", str(hotel_booking.persons)],
            ["Check-In", str(hotel_booking.check_in)],
            ["Check-Out", str(hotel_booking.check_out)],
            ["Hotel Amount", f"Rs. {hotel_booking.final_payable}"]
        ]

        table = Table(hotel_data, colWidths=[250, 250])
        table.setStyle(TableStyle([
            ('GRID',(0,0),(-1,-1),1,colors.grey),
            ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.4 * inch))

        total_amount += hotel_booking.final_payable

    # ================= TRANSPORT SECTION =================
    for t in transport_list:
        elements.append(Paragraph("<b>Transport Details</b>", styles["Heading3"]))
        elements.append(Spacer(1, 0.2 * inch))

        transport_data = [
            ["Transport Type", t.transport_type.capitalize()],
            ["From", t.source],
            ["To", t.destination],
            ["Passengers", str(t.persons)],
            ["Amount", f"Rs. {t.price}"]
        ]

        table = Table(transport_data, colWidths=[250, 250])
        table.setStyle(TableStyle([
            ('GRID',(0,0),(-1,-1),1,colors.grey),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.4 * inch))

        total_amount += t.price

    # ================= CAB SECTION =================
    if cab:
        vehicle = Transport.query.get(cab.transport_id)

        elements.append(Paragraph("<b>Cab Details</b>", styles["Heading3"]))
        elements.append(Spacer(1, 0.2 * inch))

        cab_data = [
            ["Vehicle Name", vehicle.vehicle_name if vehicle else "N/A"],
            ["Total KM", str(cab.total_km)],
            ["Total Days", str(cab.days)],
            ["Cab Amount", f"₹ {cab.price}"]
        ]

        table = Table(cab_data, colWidths=[250, 250])
        table.setStyle(TableStyle([
            ('GRID',(0,0),(-1,-1),1,colors.grey),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.4 * inch))

        total_amount += cab.price

    # ================= GRAND TOTAL =================
    elements.append(Spacer(1, 0.5 * inch))

    grand_total_table = [
        ["Grand Total", f"Rs. {total_amount}"]
    ]

    table = Table(grand_total_table, colWidths=[300, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.black),
        ('TEXTCOLOR',(0,0),(-1,-1),colors.white),
        ('ALIGN',(1,0),(1,0),'RIGHT'),
        ('FONTSIZE',(0,0),(-1,-1),14),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph(
        "This is a computer generated invoice. No signature required.",
        styles["Normal"]
    ))

    doc.build(elements)

    return file_path




# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)