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
from flask import flash
from sqlalchemy import func, text
from collections import Counter
import requests
import json
import re
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.secret_key = "tripmoreee"

# ================= MYSQL CONFIG =================
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root@127.0.0.1:3306/tripmoree"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= CONTEXT PROCESSOR =================
@app.context_processor
def inject_globals():
    from datetime import datetime
    return {"now": datetime.now()}

# ================= API KEYS =================
PEXELS_API_KEY    = "2FXZxN3XYCGsDWAxbHlezqynJMbac58HaXbevYpyGWq02Ba727W3tY7M"
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"
WEATHER_API_KEY   = "bd5e378503939ddaee76f12ad7a97608"
UPI_ID            = "9925092253@fam"
UPI_NAME          = "TripMoree Travel"
EMAIL_FROM        = "prathukakadiya7x@gmail.com"
EMAIL_PASS        = "csftedtyotxuwxgu"

# ================= LOGIN HELPERS =================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            session["next_url"] = request.url
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


# ================= MODELS =================

class Admin(db.Model):
    __tablename__ = "admins"
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100))
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(200), nullable=False)
    phone         = db.Column(db.String(20))
    profile_pic   = db.Column(db.String(500), default="")
    bio           = db.Column(db.Text, default="")
    city          = db.Column(db.String(100), default="")
    loyalty_points= db.Column(db.Integer, default=0)
    referral_code = db.Column(db.String(20), unique=True)
    referred_by   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    is_verified   = db.Column(db.Boolean, default=False)
    otp           = db.Column(db.String(6))
    otp_expiry    = db.Column(db.DateTime)
    newsletter    = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, server_default=db.func.now())

class Destination(db.Model):
    __tablename__ = "destination"
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), unique=True)
    country_type  = db.Column(db.String(50))
    category      = db.Column(db.String(50))
    vacation_type = db.Column(db.String(50))
    image         = db.Column(db.String(500))
    rating        = db.Column(db.Float)
    best_time     = db.Column(db.String(50))
    latitude      = db.Column(db.Float)
    longitude     = db.Column(db.Float)
    description   = db.Column(db.Text, default="")
    language      = db.Column(db.String(50), default="")
    currency      = db.Column(db.String(50), default="INR")
    timezone      = db.Column(db.String(50), default="IST")
    is_featured   = db.Column(db.Boolean, default=False)
    is_active     = db.Column(db.Boolean, default=True)

hotel_amenities = db.Table(
    "hotel_amenities",
    db.Column("hotel_id",   db.Integer, db.ForeignKey("hotel.id")),
    db.Column("amenity_id", db.Integer, db.ForeignKey("amenity.id"))
)

class Hotel(db.Model):
    __tablename__  = "hotel"
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(120))
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))
    stars          = db.Column(db.Float)
    starting_price = db.Column(db.Integer)
    latitude       = db.Column(db.Float)
    longitude      = db.Column(db.Float)
    lunch_price    = db.Column(db.Integer, default=500)
    dinner_price   = db.Column(db.Integer, default=600)
    pickup_price   = db.Column(db.Integer, default=800)
    description    = db.Column(db.Text, default="")
    address        = db.Column(db.String(255), default="")
    is_active      = db.Column(db.Boolean, default=True)
    amenities      = db.relationship("Amenity", secondary=hotel_amenities)
    rooms          = db.relationship("Room", backref="hotel")

class Amenity(db.Model):
    __tablename__ = "amenity"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class Room(db.Model):
    __tablename__ = "room"
    id           = db.Column(db.Integer, primary_key=True)
    hotel_id     = db.Column(db.Integer, db.ForeignKey("hotel.id"))
    room_type    = db.Column(db.String(50))
    total_rooms  = db.Column(db.Integer)
    booked_rooms = db.Column(db.Integer)
    base_price   = db.Column(db.Integer)

    @property
    def available_rooms(self):
        return (self.total_rooms or 0) - (self.booked_rooms or 0)

class HiddenStreetFood(db.Model):
    __tablename__ = "hidden_street_food"
    id            = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    food_name     = db.Column(db.String(150))
    description   = db.Column(db.Text)
    rating        = db.Column(db.Float)
    place         = db.Column(db.String(100))

class NightSafetyZones(db.Model):
    __tablename__ = "night_safety_zones"
    id            = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    title         = db.Column(db.String(100))
    description   = db.Column(db.Text)

class LocalEtiquettes(db.Model):
    __tablename__ = "local_etiquettes"
    id            = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    title         = db.Column(db.String(100))
    description   = db.Column(db.Text)

class TouristAlertsTips(db.Model):
    __tablename__ = "tourist_alerts_tips"
    id            = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    title         = db.Column(db.String(120))
    description   = db.Column(db.Text)

class LocationEssentials(db.Model):
    __tablename__ = "location_essentials"
    id            = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    doctor1_name  = db.Column(db.String(100))
    doctor1_phone = db.Column(db.String(20))
    doctor2_name  = db.Column(db.String(100))
    doctor2_phone = db.Column(db.String(20))
    scam_alert    = db.Column(db.Text)
    weather_alert = db.Column(db.Text)

class HypeSpot(db.Model):
    __tablename__  = "hype_spots"
    id             = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))
    spot_name      = db.Column(db.String(100))
    latitude       = db.Column(db.Float)
    longitude      = db.Column(db.Float)

class Transport(db.Model):
    __tablename__ = "transport"
    id            = db.Column(db.Integer, primary_key=True)
    vehicle_name  = db.Column(db.String(100))
    vehicle_type  = db.Column(db.String(50))
    ac_type       = db.Column(db.String(20))
    price_per_km  = db.Column(db.Integer)

class CabBooking(db.Model):
    __tablename__ = "cab_bookings"
    id            = db.Column(db.Integer, primary_key=True)
    booking_id    = db.Column(db.Integer, db.ForeignKey("booking_history.id"), nullable=False)
    transport_id  = db.Column(db.Integer, db.ForeignKey("transport.id"), nullable=False)
    days          = db.Column(db.Integer, nullable=False)
    total_km      = db.Column(db.Integer, nullable=False)
    price         = db.Column(db.Integer, nullable=False)
    created_at    = db.Column(db.DateTime, server_default=db.func.now())

class Bus(db.Model):
    __tablename__   = "buses"
    id              = db.Column(db.Integer, primary_key=True)
    bus_number      = db.Column(db.String(20))
    operator        = db.Column(db.String(50))
    source          = db.Column(db.String(50))
    destination     = db.Column(db.String(50))
    departure_time  = db.Column(db.String(20))
    arrival_time    = db.Column(db.String(20))
    ac_type         = db.Column(db.String(20))
    seat_type       = db.Column(db.String(20))
    price           = db.Column(db.Integer)
    total_seats     = db.Column(db.Integer)
    available_seats = db.Column(db.Integer)

class Train(db.Model):
    __tablename__   = "trains"
    id              = db.Column(db.Integer, primary_key=True)
    train_number    = db.Column(db.String(20))
    train_name      = db.Column(db.String(100))
    source          = db.Column(db.String(50))
    destination     = db.Column(db.String(50))
    departure_time  = db.Column(db.String(20))
    arrival_time    = db.Column(db.String(20))
    ac_type         = db.Column(db.String(20))
    seat_type       = db.Column(db.String(20))
    price           = db.Column(db.Integer)
    total_seats     = db.Column(db.Integer)
    available_seats = db.Column(db.Integer)

class Flight(db.Model):
    __tablename__   = "flights"
    id              = db.Column(db.Integer, primary_key=True)
    flight_number   = db.Column(db.String(20))
    airline         = db.Column(db.String(50))
    source          = db.Column(db.String(50))
    destination     = db.Column(db.String(50))
    departure_time  = db.Column(db.String(20))
    arrival_time    = db.Column(db.String(20))
    flight_class    = db.Column(db.String(20))
    price           = db.Column(db.Integer)
    total_seats     = db.Column(db.Integer)
    available_seats = db.Column(db.Integer)

class BookingHistory(db.Model):
    __tablename__ = "booking_history"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    status      = db.Column(db.String(20), default="active")
    cancel_reason = db.Column(db.String(255), default="")
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

class TransportBooking(db.Model):
    __tablename__  = "transport_bookings"
    id             = db.Column(db.Integer, primary_key=True)
    booking_id     = db.Column(db.Integer, db.ForeignKey("booking_history.id"))
    transport_type = db.Column(db.String(20))
    source         = db.Column(db.String(50))
    destination    = db.Column(db.String(50))
    persons        = db.Column(db.Integer)
    price          = db.Column(db.Integer)
    created_at     = db.Column(db.DateTime, server_default=db.func.now())

class HotelBooking(db.Model):
    __tablename__   = "hotel_bookings"
    id              = db.Column(db.Integer, primary_key=True)
    booking_id      = db.Column(db.Integer)
    hotel_id        = db.Column(db.Integer, db.ForeignKey('hotel.id'))
    room_id         = db.Column(db.Integer)
    persons         = db.Column(db.Integer)
    check_in        = db.Column(db.Date)
    check_out       = db.Column(db.Date)
    base_price      = db.Column(db.Integer)
    extra_price     = db.Column(db.Integer)
    total_price     = db.Column(db.Integer)
    lunch_added     = db.Column(db.Boolean, default=False)
    dinner_added    = db.Column(db.Boolean, default=False)
    pickup_added    = db.Column(db.Boolean, default=False)
    id_type         = db.Column(db.String(20))
    id_number       = db.Column(db.String(50))
    name            = db.Column(db.String(100))
    email           = db.Column(db.String(100))
    phone           = db.Column(db.String(15))
    coupon_code     = db.Column(db.String(50))
    coupon_discount = db.Column(db.Integer, default=0)
    bank_name       = db.Column(db.String(50))
    card_number     = db.Column(db.String(20))
    bank_discount   = db.Column(db.Integer, default=0)
    loyalty_discount= db.Column(db.Integer, default=0)
    insurance_id    = db.Column(db.Integer, db.ForeignKey("insurance_plans.id"), nullable=True)
    insurance_price = db.Column(db.Integer, default=0)
    final_payable   = db.Column(db.Integer)
    payment_status  = db.Column(db.String(20), default="pending")
    payment_method  = db.Column(db.String(30), default="upi")
    upi_ref         = db.Column(db.String(100))
    special_request = db.Column(db.Text, default="")
    created_at      = db.Column(db.DateTime)

class Coupon(db.Model):
    __tablename__    = "coupons"
    id               = db.Column(db.Integer, primary_key=True)
    code             = db.Column(db.String(50), unique=True)
    discount_percent = db.Column(db.Integer)
    max_discount     = db.Column(db.Integer, default=5000)
    min_amount       = db.Column(db.Integer, default=0)
    usage_limit      = db.Column(db.Integer, default=100)
    used_count       = db.Column(db.Integer, default=0)
    valid_from       = db.Column(db.Date)
    valid_till       = db.Column(db.Date)
    active           = db.Column(db.Boolean, default=True)
    created_at       = db.Column(db.DateTime, server_default=db.func.now())

class BookingHypeSpot(db.Model):
    __tablename__ = "booking_hype_spots"
    id         = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("transport_bookings.id", ondelete="CASCADE"), nullable=False)
    spot_id    = db.Column(db.Integer, db.ForeignKey("hype_spots.id", ondelete="CASCADE"), nullable=False)

class CabBookingDay(db.Model):
    __tablename__  = "cab_booking_days"
    id             = db.Column(db.Integer, primary_key=True)
    cab_booking_id = db.Column(db.Integer, db.ForeignKey("cab_bookings.id"))
    day_number     = db.Column(db.Integer)
    arrival_time   = db.Column(db.Time)
    departure_time = db.Column(db.Time)
    pickup_type    = db.Column(db.String(50))
    drop_type      = db.Column(db.String(50))
    custom_pickup  = db.Column(db.String(255))
    custom_drop    = db.Column(db.String(255))
    day_km         = db.Column(db.Float)
    day_price      = db.Column(db.Float)

class CabBookingDaySpot(db.Model):
    __tablename__      = "cab_booking_day_spots"
    id                 = db.Column(db.Integer, primary_key=True)
    cab_booking_day_id = db.Column(db.Integer, db.ForeignKey("cab_booking_days.id"))
    spot_id            = db.Column(db.Integer, db.ForeignKey("hype_spots.id"))

class Review(db.Model):
    __tablename__ = "reviews"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    destination = db.Column(db.String(100))
    rating      = db.Column(db.Integer)
    comment     = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

class Wishlist(db.Model):
    __tablename__  = "wishlist"
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"))
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))
    created_at     = db.Column(db.DateTime, server_default=db.func.now())

class ChatHistory(db.Model):
    __tablename__ = "chat_history"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    role       = db.Column(db.String(20))
    message    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class InsurancePlan(db.Model):
    __tablename__  = "insurance_plans"
    id             = db.Column(db.Integer, primary_key=True)
    plan_name      = db.Column(db.String(100))
    coverage       = db.Column(db.Text)
    price_per_day  = db.Column(db.Integer)
    max_coverage   = db.Column(db.Integer)
    is_active      = db.Column(db.Boolean, default=True)

class LoyaltyTransaction(db.Model):
    __tablename__ = "loyalty_transactions"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    points      = db.Column(db.Integer)
    action      = db.Column(db.String(100))
    booking_id  = db.Column(db.Integer, nullable=True)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

class Referral(db.Model):
    __tablename__  = "referrals"
    id             = db.Column(db.Integer, primary_key=True)
    referrer_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    referred_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    bonus_given    = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, server_default=db.func.now())

class FlashSale(db.Model):
    __tablename__  = "flash_sales"
    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(150))
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"), nullable=True)
    hotel_id       = db.Column(db.Integer, db.ForeignKey("hotel.id"), nullable=True)
    discount_pct   = db.Column(db.Integer)
    starts_at      = db.Column(db.DateTime)
    ends_at        = db.Column(db.DateTime)
    banner_color   = db.Column(db.String(20), default="#e74c3c")
    is_active      = db.Column(db.Boolean, default=True)

class TravelPackage(db.Model):
    __tablename__  = "travel_packages"
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(150))
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))
    hotel_id       = db.Column(db.Integer, db.ForeignKey("hotel.id"), nullable=True)
    days           = db.Column(db.Integer)
    nights         = db.Column(db.Integer)
    includes       = db.Column(db.Text)
    price          = db.Column(db.Integer)
    original_price = db.Column(db.Integer)
    is_active      = db.Column(db.Boolean, default=True)
    created_at     = db.Column(db.DateTime, server_default=db.func.now())

class HotelReview(db.Model):
    __tablename__ = "hotel_reviews"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    hotel_id    = db.Column(db.Integer, db.ForeignKey("hotel.id"))
    rating      = db.Column(db.Integer)
    comment     = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

class Newsletter(db.Model):
    __tablename__ = "newsletter"
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True)
    name       = db.Column(db.String(100), default="Traveller")
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class SupportTicket(db.Model):
    __tablename__ = "support_tickets"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    booking_id  = db.Column(db.Integer, nullable=True)
    subject     = db.Column(db.String(200))
    message     = db.Column(db.Text)
    status      = db.Column(db.String(20), default="open")
    admin_reply = db.Column(db.Text, default="")
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

class Notification(db.Model):
    __tablename__ = "notifications"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    message    = db.Column(db.Text)
    link       = db.Column(db.String(300), default="")
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class CompareList(db.Model):
    __tablename__  = "compare_list"
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"))
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"))
    created_at     = db.Column(db.DateTime, server_default=db.func.now())

class CommunityPhoto(db.Model):
    __tablename__ = "community_photos"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    destination = db.Column(db.String(100))
    image_url   = db.Column(db.String(500))
    caption     = db.Column(db.Text)
    likes       = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())


# ================= HELPERS =================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))

def get_pexels_images(query, count=4):
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query + " travel", "per_page": count, "orientation": "landscape"},
            timeout=5
        )
        photos = resp.json().get("photos", [])
        return [p["src"]["large"] for p in photos]
    except Exception as e:
        print(f"Pexels error: {e}")
        return []

def get_pexels_single(query):
    imgs = get_pexels_images(query, 1)
    return imgs[0] if imgs else ""

def generate_referral_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def add_notification(user_id, message, link=""):
    try:
        db.session.add(Notification(user_id=user_id, message=message, link=link))
        db.session.commit()
    except:
        db.session.rollback()

def award_points(user_id, points, action, booking_id=None):
    try:
        user = User.query.get(user_id)
        if user:
            user.loyalty_points = (user.loyalty_points or 0) + points
            db.session.add(LoyaltyTransaction(user_id=user_id, points=points, action=action, booking_id=booking_id))
            db.session.commit()
    except:
        db.session.rollback()

def send_email(to, subject, body, attachment_path=None):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"]    = EMAIL_FROM
        msg["To"]      = to
        msg.set_content(body)
        if attachment_path:
            with open(attachment_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                                   filename=os.path.basename(attachment_path))
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(EMAIL_FROM, EMAIL_PASS)
        smtp.send_message(msg)
        smtp.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# ================= ROUTES =================

# ── WEATHER ──────────────────────────────────────────────
@app.route("/api/weather")
def weather_api():
    city = request.args.get("city", "")
    if not city:
        return jsonify({"error": "No city"})
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city + ",IN", "appid": WEATHER_API_KEY, "units": "metric"},
            timeout=5
        )
        data = resp.json()
        if data.get("cod") == 200:
            return jsonify({
                "temp":       round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "desc":       data["weather"][0]["description"].title(),
                "icon":       data["weather"][0]["icon"],
                "humidity":   data["main"]["humidity"],
                "wind":       round(data["wind"]["speed"] * 3.6),
                "city":       data["name"]
            })
    except Exception as e:
        print(f"Weather error: {e}")
    return jsonify({"error": "Weather not available"})

# ── CURRENCY ──────────────────────────────────────────────
@app.route("/currency")
def currency_page():
    return render_template("currency.html")

@app.route("/api/currency-convert")
def currency_convert():
    amount   = float(request.args.get("amount", 1))
    from_cur = request.args.get("from", "INR")
    to_cur   = request.args.get("to", "USD")
    INR_RATES = {
        "USD": 0.012, "EUR": 0.011, "GBP": 0.0095, "JPY": 1.78,
        "AED": 0.044, "SGD": 0.016, "AUD": 0.019, "CAD": 0.016,
        "THB": 0.43, "IDR": 187.5, "MYR": 0.057, "INR": 1.0,
        "SAR": 0.045, "CHF": 0.011
    }
    try:
        if from_cur == "INR":
            result = amount * INR_RATES.get(to_cur, 1)
        elif to_cur == "INR":
            result = amount / INR_RATES.get(from_cur, 1)
        else:
            inr_val = amount / INR_RATES.get(from_cur, 1)
            result  = inr_val * INR_RATES.get(to_cur, 1)
        return jsonify({"result": round(result, 4), "from": from_cur, "to": to_cur})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/budget-track")
@login_required
def budget_track():
    uid = session["user_id"]
    booking_ids = [b.id for b in BookingHistory.query.filter_by(user_id=uid).all()]
    hotel_spent = db.session.query(func.sum(HotelBooking.final_payable)).filter(
        HotelBooking.booking_id.in_(booking_ids)).scalar() or 0
    trans_spent = db.session.query(func.sum(TransportBooking.price)).filter(
        TransportBooking.booking_id.in_(booking_ids)).scalar() or 0
    cab_spent   = db.session.query(func.sum(CabBooking.price)).filter(
        CabBooking.booking_id.in_(booking_ids)).scalar() or 0
    return jsonify({
        "hotel": int(hotel_spent), "transport": int(trans_spent),
        "cab": int(cab_spent), "total": int(hotel_spent + trans_spent + cab_spent)
    })

# ── ADMIN ──────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password == password:
            session["admin_id"] = admin.id
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    return redirect("/admin/login")

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    total_users    = User.query.count()
    total_hotels   = Hotel.query.count()
    total_bookings = BookingHistory.query.count()
    hotel_rev  = db.session.query(func.sum(HotelBooking.final_payable)).scalar() or 0
    trans_rev  = db.session.query(func.sum(TransportBooking.price)).scalar() or 0
    cab_rev    = db.session.query(func.sum(CabBooking.price)).scalar() or 0
    total_revenue = hotel_rev + trans_rev + cab_rev
    active    = BookingHistory.query.filter_by(status="active").count()
    completed = BookingHistory.query.filter_by(status="completed").count()
    cancelled = BookingHistory.query.filter_by(status="cancelled").count()
    top_destinations = db.session.query(
        BookingHistory.destination, func.count(BookingHistory.id)
    ).group_by(BookingHistory.destination).all()
    open_tickets = SupportTicket.query.filter_by(status="open").count()
    flash_sales  = FlashSale.query.filter_by(is_active=True).count()
    return render_template("admin_dashboard.html",
        users=total_users, hotels=total_hotels, bookings=total_bookings,
        revenue=total_revenue, active=active, completed=completed, cancelled=cancelled,
        top_destinations=top_destinations, open_tickets=open_tickets, flash_sales=flash_sales)

@app.route("/admin/users")
@admin_required
def admin_users():
    search = request.args.get("search")
    if search:
        users = User.query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        ).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users)

@app.route("/admin/delete-user/<int:user_id>")
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    status = request.args.get("status", "")
    query  = BookingHistory.query
    if status:
        query = query.filter_by(status=status)
    bookings = query.order_by(BookingHistory.created_at.desc()).all()
    result   = []
    for b in bookings:
        user  = User.query.get(b.user_id)
        hotel = HotelBooking.query.filter_by(booking_id=b.id).first()
        result.append({"booking": b, "user": user, "hotel": hotel})
    return render_template("admin_bookings.html", bookings=result, current_status=status)

@app.route("/admin/booking/status/<int:booking_id>", methods=["POST"])
@admin_required
def admin_update_booking_status(booking_id):
    booking = BookingHistory.query.get_or_404(booking_id)
    new_status = request.form.get("status")
    booking.status = new_status
    db.session.commit()
    add_notification(booking.user_id, f"Your booking #{booking_id} to {booking.destination} is now {new_status}.",
                     url_for("my_bookings"))
    flash("Booking status updated.", "success")
    return redirect(url_for("admin_bookings"))

@app.route("/admin/destinations")
@admin_required
def admin_destinations():
    dests = Destination.query.order_by(Destination.name).all()
    return render_template("admin_destinations.html", destinations=dests)

@app.route("/admin/destination/add", methods=["GET", "POST"])
@admin_required
def admin_add_destination():
    if request.method == "POST":
        d = Destination(
            name=request.form.get("name"), country_type=request.form.get("country_type"),
            category=request.form.get("category"), vacation_type=request.form.get("vacation_type"),
            image=request.form.get("image", ""), rating=float(request.form.get("rating", 4.0)),
            best_time=request.form.get("best_time", ""),
            latitude=float(request.form.get("latitude", 0)), longitude=float(request.form.get("longitude", 0)),
            description=request.form.get("description", ""), language=request.form.get("language", ""),
            currency=request.form.get("currency", "INR"), is_featured=bool(request.form.get("is_featured")),
        )
        db.session.add(d)
        db.session.commit()
        flash("Destination added!", "success")
        return redirect(url_for("admin_destinations"))
    return render_template("admin_destination_form.html", dest=None)

@app.route("/admin/destination/edit/<int:dest_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_destination(dest_id):
    d = Destination.query.get_or_404(dest_id)
    if request.method == "POST":
        d.name=request.form.get("name"); d.country_type=request.form.get("country_type")
        d.category=request.form.get("category"); d.vacation_type=request.form.get("vacation_type")
        d.image=request.form.get("image", d.image); d.rating=float(request.form.get("rating", d.rating))
        d.best_time=request.form.get("best_time", d.best_time)
        d.latitude=float(request.form.get("latitude", d.latitude or 0))
        d.longitude=float(request.form.get("longitude", d.longitude or 0))
        d.description=request.form.get("description", ""); d.language=request.form.get("language", "")
        d.currency=request.form.get("currency", "INR"); d.is_featured=bool(request.form.get("is_featured"))
        d.is_active=bool(request.form.get("is_active"))
        db.session.commit()
        flash("Destination updated!", "success")
        return redirect(url_for("admin_destinations"))
    return render_template("admin_destination_form.html", dest=d)

@app.route("/admin/destination/delete/<int:dest_id>")
@admin_required
def admin_delete_destination(dest_id):
    d = Destination.query.get_or_404(dest_id)
    d.is_active = False
    db.session.commit()
    flash("Destination deactivated.", "warning")
    return redirect(url_for("admin_destinations"))

@app.route("/admin/hotels")
@admin_required
def admin_hotels():
    hotels = Hotel.query.order_by(Hotel.name).all()
    return render_template("admin_hotels.html", hotels=hotels)

@app.route("/admin/hotel/add", methods=["GET", "POST"])
@admin_required
def admin_add_hotel():
    dests = Destination.query.filter_by(is_active=True).all()
    if request.method == "POST":
        h = Hotel(
            name=request.form.get("name"), destination_id=int(request.form.get("destination_id")),
            stars=float(request.form.get("stars", 3)), starting_price=int(request.form.get("starting_price", 1000)),
            latitude=float(request.form.get("latitude", 0)), longitude=float(request.form.get("longitude", 0)),
            lunch_price=int(request.form.get("lunch_price", 500)), dinner_price=int(request.form.get("dinner_price", 600)),
            pickup_price=int(request.form.get("pickup_price", 800)),
            description=request.form.get("description", ""), address=request.form.get("address", ""),
        )
        db.session.add(h)
        db.session.commit()
        flash("Hotel added!", "success")
        return redirect(url_for("admin_hotels"))
    return render_template("admin_hotel_form.html", hotel=None, destinations=dests)

@app.route("/admin/hotel/edit/<int:hotel_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_hotel(hotel_id):
    h     = Hotel.query.get_or_404(hotel_id)
    dests = Destination.query.filter_by(is_active=True).all()
    if request.method == "POST":
        h.name=request.form.get("name"); h.destination_id=int(request.form.get("destination_id"))
        h.stars=float(request.form.get("stars", h.stars)); h.starting_price=int(request.form.get("starting_price", h.starting_price))
        h.latitude=float(request.form.get("latitude", h.latitude or 0)); h.longitude=float(request.form.get("longitude", h.longitude or 0))
        h.lunch_price=int(request.form.get("lunch_price", h.lunch_price)); h.dinner_price=int(request.form.get("dinner_price", h.dinner_price))
        h.pickup_price=int(request.form.get("pickup_price", h.pickup_price))
        h.description=request.form.get("description", ""); h.address=request.form.get("address", "")
        h.is_active=bool(request.form.get("is_active"))
        db.session.commit()
        flash("Hotel updated!", "success")
        return redirect(url_for("admin_hotels"))
    return render_template("admin_hotel_form.html", hotel=h, destinations=dests)

@app.route("/admin/coupons")
@admin_required
def admin_coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template("admin_coupons.html", coupons=coupons)

@app.route("/admin/coupon/add", methods=["POST"])
@admin_required
def admin_add_coupon():
    c = Coupon(
        code=request.form.get("code", "").upper().strip(),
        discount_percent=int(request.form.get("discount_percent", 10)),
        max_discount=int(request.form.get("max_discount", 5000)),
        min_amount=int(request.form.get("min_amount", 0)),
        usage_limit=int(request.form.get("usage_limit", 100)),
        valid_from=datetime.strptime(request.form.get("valid_from"), "%Y-%m-%d").date() if request.form.get("valid_from") else None,
        valid_till=datetime.strptime(request.form.get("valid_till"), "%Y-%m-%d").date() if request.form.get("valid_till") else None,
        active=True,
    )
    db.session.add(c)
    db.session.commit()
    flash("Coupon created!", "success")
    return redirect(url_for("admin_coupons"))

@app.route("/admin/coupon/toggle/<int:coupon_id>")
@admin_required
def admin_toggle_coupon(coupon_id):
    c = Coupon.query.get_or_404(coupon_id)
    c.active = not c.active
    db.session.commit()
    flash("Coupon status updated.", "info")
    return redirect(url_for("admin_coupons"))

@app.route("/admin/flash-sales")
@admin_required
def admin_flash_sales():
    sales = FlashSale.query.order_by(FlashSale.starts_at.desc()).all()
    dests = Destination.query.filter_by(is_active=True).all()
    return render_template("admin_flash_sales.html", sales=sales, destinations=dests)

@app.route("/admin/flash-sale/add", methods=["POST"])
@admin_required
def admin_add_flash_sale():
    s = FlashSale(
        title=request.form.get("title"),
        destination_id=int(request.form.get("destination_id")) if request.form.get("destination_id") else None,
        discount_pct=int(request.form.get("discount_pct", 20)),
        starts_at=datetime.strptime(request.form.get("starts_at"), "%Y-%m-%dT%H:%M"),
        ends_at=datetime.strptime(request.form.get("ends_at"), "%Y-%m-%dT%H:%M"),
        banner_color=request.form.get("banner_color", "#e74c3c"), is_active=True,
    )
    db.session.add(s)
    db.session.commit()
    flash("Flash sale created!", "success")
    return redirect(url_for("admin_flash_sales"))

@app.route("/admin/flash-sale/toggle/<int:sale_id>")
@admin_required
def admin_toggle_flash_sale(sale_id):
    s = FlashSale.query.get_or_404(sale_id)
    s.is_active = not s.is_active
    db.session.commit()
    flash("Flash sale status updated.", "info")
    return redirect(url_for("admin_flash_sales"))

@app.route("/admin/support")
@admin_required
def admin_support():
    status  = request.args.get("status", "open")
    tickets = SupportTicket.query.filter_by(status=status).order_by(SupportTicket.created_at.desc()).all()
    result  = [{"ticket": t, "user": User.query.get(t.user_id)} for t in tickets]
    return render_template("admin_support.html", tickets=result, current_status=status)

@app.route("/admin/support/reply/<int:ticket_id>", methods=["POST"])
@admin_required
def admin_reply_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.admin_reply = request.form.get("reply", "").strip()
    ticket.status      = request.form.get("status", "replied")
    db.session.commit()
    add_notification(ticket.user_id, f"Admin replied to your support ticket: '{ticket.subject}'", url_for("my_support"))
    flash("Reply sent.", "success")
    return redirect(url_for("admin_support"))

@app.route("/admin/packages")
@admin_required
def admin_packages():
    packages = TravelPackage.query.order_by(TravelPackage.created_at.desc()).all()
    dests    = Destination.query.filter_by(is_active=True).all()
    hotels   = Hotel.query.filter_by(is_active=True).all()
    return render_template("admin_packages.html", packages=packages, destinations=dests, hotels=hotels)

@app.route("/admin/package/add", methods=["POST"])
@admin_required
def admin_add_package():
    includes_raw = request.form.getlist("includes")
    p = TravelPackage(
        name=request.form.get("name"), destination_id=int(request.form.get("destination_id")),
        hotel_id=int(request.form.get("hotel_id")) if request.form.get("hotel_id") else None,
        days=int(request.form.get("days", 3)), nights=int(request.form.get("nights", 2)),
        includes=json.dumps(includes_raw), price=int(request.form.get("price", 10000)),
        original_price=int(request.form.get("original_price", 12000)), is_active=True,
    )
    db.session.add(p)
    db.session.commit()
    flash("Package added!", "success")
    return redirect(url_for("admin_packages"))

@app.route("/admin/package/toggle/<int:pkg_id>")
@admin_required
def admin_toggle_package(pkg_id):
    p = TravelPackage.query.get_or_404(pkg_id)
    p.is_active = not p.is_active
    db.session.commit()
    return redirect(url_for("admin_packages"))

@app.route("/admin/insurance")
@admin_required
def admin_insurance():
    plans = InsurancePlan.query.all()
    return render_template("admin_insurance.html", plans=plans)

@app.route("/admin/insurance/add", methods=["POST"])
@admin_required
def admin_add_insurance():
    p = InsurancePlan(
        plan_name=request.form.get("plan_name"), coverage=request.form.get("coverage"),
        price_per_day=int(request.form.get("price_per_day", 50)),
        max_coverage=int(request.form.get("max_coverage", 500000)), is_active=True,
    )
    db.session.add(p)
    db.session.commit()
    flash("Insurance plan added!", "success")
    return redirect(url_for("admin_insurance"))

@app.route("/admin/insurance/toggle/<int:plan_id>")
@admin_required
def admin_toggle_insurance(plan_id):
    p = InsurancePlan.query.get_or_404(plan_id)
    p.is_active = not p.is_active
    db.session.commit()
    return redirect(url_for("admin_insurance"))

@app.route("/admin/newsletter", methods=["GET", "POST"])
@admin_required
def admin_newsletter():
    subscribers = Newsletter.query.filter_by(is_active=True).count()
    if request.method == "POST":
        subject  = request.form.get("subject")
        body     = request.form.get("body")
        all_subs = Newsletter.query.filter_by(is_active=True).all()
        sent = sum(1 for sub in all_subs if send_email(sub.email, subject, body))
        flash(f"Newsletter sent to {sent} subscribers!", "success")
        return redirect(url_for("admin_newsletter"))
    return render_template("admin_newsletter.html", subscribers=subscribers)

@app.route("/admin/analytics")
@admin_required
def admin_analytics():
    monthly_labels, monthly_rev = [], []
    for i in range(5, -1, -1):
        dt    = datetime.now() - timedelta(days=30 * i)
        label = dt.strftime("%b %Y")
        rev   = db.session.query(func.sum(HotelBooking.final_payable)).filter(
            func.month(HotelBooking.created_at) == dt.month,
            func.year(HotelBooking.created_at)  == dt.year
        ).scalar() or 0
        monthly_labels.append(label)
        monthly_rev.append(rev)
    top_dest = db.session.query(
        BookingHistory.destination, func.count(BookingHistory.id).label("cnt")
    ).group_by(BookingHistory.destination).order_by(func.count(BookingHistory.id).desc()).limit(10).all()
    return render_template("admin_analytics.html",
        monthly_labels=monthly_labels, monthly_rev=monthly_rev, top_dest=top_dest)


# ── HOME ──────────────────────────────────────────────────

@app.route("/")
def home():
    featured = Destination.query.filter_by(is_active=True).order_by(Destination.rating.desc()).limit(6).all()
    for d in featured:
        d.pexels_img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name + " destination")

    total_bookings     = BookingHistory.query.count()
    total_users        = User.query.count()
    total_destinations = Destination.query.filter_by(is_active=True).count()

    popular_raw = db.session.query(
        BookingHistory.destination, func.count(BookingHistory.id).label("cnt")
    ).group_by(BookingHistory.destination).order_by(func.count(BookingHistory.id).desc()).limit(4).all()

    popular_dests = []
    for row in popular_raw:
        d = Destination.query.filter_by(name=row.destination).first()
        if d:
            img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name)
            popular_dests.append({"dest": d, "bookings": row.cnt, "img": img})

    wishlist_ids = []
    if "user_id" in session:
        wishlist_ids = [w.destination_id for w in Wishlist.query.filter_by(user_id=session["user_id"]).all()]

    now         = datetime.now()
    flash_sales = FlashSale.query.filter(
        FlashSale.is_active == True, FlashSale.starts_at <= now, FlashSale.ends_at >= now
    ).order_by(FlashSale.ends_at).limit(3).all()

    packages = TravelPackage.query.filter_by(is_active=True).order_by(TravelPackage.created_at.desc()).limit(4).all()
    for p in packages:
        d = Destination.query.get(p.destination_id)
        img = ""
        if d:
            img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name)
        p.dest_img = img
        p.includes_list = json.loads(p.includes) if p.includes else []

    return render_template("home.html",
        featured=featured, total_bookings=total_bookings,
        total_users=total_users, total_destinations=total_destinations,
        popular_dests=popular_dests, wishlist_ids=wishlist_ids,
        flash_sales=flash_sales, packages=packages)


# ── DESTINATIONS ──────────────────────────────────────────

@app.route("/destinations")
def destinations_page():
    categories   = db.session.query(Destination.category).distinct().all()
    vac_types    = db.session.query(Destination.vacation_type).distinct().all()
    wishlist_ids = []
    compare_ids  = []
    if "user_id" in session:
        wishlist_ids = [w.destination_id for w in Wishlist.query.filter_by(user_id=session["user_id"]).all()]
        compare_ids  = [c.destination_id for c in CompareList.query.filter_by(user_id=session["user_id"]).all()]
    return render_template("destinations.html",
        categories=[c[0] for c in categories if c[0]],
        vac_types=[v[0] for v in vac_types if v[0]],
        wishlist_ids=wishlist_ids, compare_ids=compare_ids)

@app.route("/api/destinations")
def get_destinations():
    vacation_type = request.args.get("type")
    query = Destination.query.filter_by(is_active=True)
    if vacation_type:
        query = query.filter_by(vacation_type=vacation_type)
    destinations = query.all()
    result = []
    for d in destinations:
        img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name + " travel")
        result.append({
            "id": d.id, "name": d.name, "rating": d.rating, "image": img,
            "best_time": d.best_time, "category": d.category, "country_type": d.country_type,
            "vacation_type": d.vacation_type, "description": d.description or ""
        })
    return jsonify(result)

@app.route("/destination/<int:dest_id>")
def destination_detail(dest_id):
    d = Destination.query.get_or_404(dest_id)
    if not d.is_active:
        flash("This destination is currently unavailable.", "warning")
        return redirect(url_for("destinations_page"))
    images  = get_pexels_images(d.name + " travel", 6)
    hotels  = Hotel.query.filter_by(destination_id=d.id, is_active=True).all()
    spots   = HypeSpot.query.filter_by(destination_id=d.id).all()
    reviews = Review.query.filter_by(destination=d.name).order_by(Review.created_at.desc()).limit(5).all()
    avg_rating = db.session.query(func.avg(Review.rating)).filter_by(destination=d.name).scalar() or d.rating
    packages   = TravelPackage.query.filter_by(destination_id=d.id, is_active=True).all()
    in_wishlist = in_compare = has_booked = False
    if "user_id" in session:
        in_wishlist = bool(Wishlist.query.filter_by(user_id=session["user_id"], destination_id=d.id).first())
        in_compare  = bool(CompareList.query.filter_by(user_id=session["user_id"], destination_id=d.id).first())
        has_booked  = bool(BookingHistory.query.filter_by(user_id=session["user_id"], destination=d.name).first())
    foods      = HiddenStreetFood.query.filter(func.lower(HiddenStreetFood.location_name) == d.name.lower()).all()
    etiquettes = LocalEtiquettes.query.filter(func.lower(LocalEtiquettes.location_name) == d.name.lower()).all()
    return render_template("destination_detail.html",
        dest=d, images=images, hotels=hotels, spots=spots,
        reviews=reviews, avg_rating=round(avg_rating, 1),
        packages=packages, in_wishlist=in_wishlist, in_compare=in_compare,
        has_booked=has_booked, foods=foods, etiquettes=etiquettes)

@app.route("/api/search")
def smart_search():
    q        = request.args.get("q", "").lower()
    vac_type = request.args.get("type", "")
    category = request.args.get("category", "")
    sort_by  = request.args.get("sort", "rating")
    min_price= request.args.get("min_price", "")
    max_price= request.args.get("max_price", "")
    query = Destination.query.filter_by(is_active=True)
    if vac_type: query = query.filter_by(vacation_type=vac_type)
    if category: query = query.filter_by(category=category)
    destinations = query.all()
    if q:
        keywords = q.split()
        budget   = None
        for i, kw in enumerate(keywords):
            if kw in ("under", "below", "within") and i + 1 < len(keywords):
                try: budget = int(keywords[i+1].replace(",", "").replace("₹", ""))
                except: pass
        def relevance(d):
            score = 0
            text  = f"{d.name} {d.category or ''} {d.vacation_type or ''} {d.best_time or ''} {d.country_type or ''} {d.description or ''}".lower()
            for kw in keywords:
                if kw in text: score += 3
                if kw in d.name.lower(): score += 5
            return score
        destinations = [d for d in destinations if relevance(d) > 0]
        if budget:
            filtered = [d for d in destinations if (db.session.query(func.min(Hotel.starting_price)).filter_by(destination_id=d.id).scalar() or 999999) <= budget]
            if filtered: destinations = filtered
        destinations.sort(key=relevance, reverse=True)
    if min_price or max_price:
        filtered = []
        for d in destinations:
            min_h = db.session.query(func.min(Hotel.starting_price)).filter_by(destination_id=d.id).scalar() or 0
            if min_price and min_h < int(min_price): continue
            if max_price and min_h > int(max_price): continue
            filtered.append(d)
        destinations = filtered
    if sort_by == "rating": destinations.sort(key=lambda d: d.rating or 0, reverse=True)
    elif sort_by == "popular":
        pop = {row.destination: row.cnt for row in db.session.query(BookingHistory.destination, func.count(BookingHistory.id).label("cnt")).group_by(BookingHistory.destination).all()}
        destinations.sort(key=lambda d: pop.get(d.name, 0), reverse=True)
    elif sort_by == "price_low": destinations.sort(key=lambda d: db.session.query(func.min(Hotel.starting_price)).filter_by(destination_id=d.id).scalar() or 999999)
    elif sort_by == "price_high": destinations.sort(key=lambda d: db.session.query(func.min(Hotel.starting_price)).filter_by(destination_id=d.id).scalar() or 0, reverse=True)
    result = []
    for d in destinations:
        img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name + " travel")
        min_hotel = db.session.query(func.min(Hotel.starting_price)).filter_by(destination_id=d.id).scalar() or 0
        result.append({"id": d.id, "name": d.name, "rating": d.rating, "image": img, "category": d.category,
                       "best_time": d.best_time, "country_type": d.country_type, "vacation_type": d.vacation_type,
                       "min_price": min_hotel, "description": d.description or ""})
    return jsonify(result)

@app.route("/compare/toggle/<int:dest_id>", methods=["POST"])
@login_required
def toggle_compare(dest_id):
    uid      = session["user_id"]
    existing = CompareList.query.filter_by(user_id=uid, destination_id=dest_id).first()
    if existing:
        db.session.delete(existing); db.session.commit()
        return jsonify({"status": "removed"})
    count = CompareList.query.filter_by(user_id=uid).count()
    if count >= 3:
        return jsonify({"status": "limit", "message": "You can compare up to 3 destinations only."})
    db.session.add(CompareList(user_id=uid, destination_id=dest_id)); db.session.commit()
    return jsonify({"status": "added"})

@app.route("/compare")
@login_required
def compare_destinations():
    uid   = session["user_id"]
    items = CompareList.query.filter_by(user_id=uid).all()
    dests = [Destination.query.get(c.destination_id) for c in items]
    dests = [d for d in dests if d]
    data  = []
    for d in dests:
        img    = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name)
        hotels = Hotel.query.filter_by(destination_id=d.id, is_active=True).all()
        min_h  = min((h.starting_price for h in hotels if h.starting_price), default=0)
        avg_r  = db.session.query(func.avg(Review.rating)).filter_by(destination=d.name).scalar() or d.rating
        data.append({"dest": d, "img": img, "min_price": min_h, "avg_rating": round(avg_r or 0, 1), "hotel_count": len(hotels)})
    return render_template("compare.html", data=data)

# ── AI CHATBOT ──

@app.route("/api/chat", methods=["POST"])
def ai_chat():
    data     = request.json
    user_msg = data.get("message", "").strip()
    if not user_msg: return jsonify({"reply": "Please type a message."})
    destinations = Destination.query.filter_by(is_active=True).all()
    dest_names   = ", ".join(d.name for d in destinations)
    system_prompt = f"""You are TripMoree AI, a friendly expert travel assistant for TripMoree — an Indian travel booking platform.
Available destinations: {dest_names}
Rules: Keep replies under 150 words. Suggest TripMoree destinations. Use INR. Be warm and enthusiastic."""
    history = []
    if "user_id" in session:
        past = ChatHistory.query.filter_by(user_id=session["user_id"]).order_by(ChatHistory.id.desc()).limit(6).all()
        for h in reversed(past):
            history.append({"role": h.role, "content": h.message})
    history.append({"role": "user", "content": user_msg})
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 300, "system": system_prompt, "messages": history},
            timeout=15
        )
        reply = resp.json()["content"][0]["text"]
    except:
        reply = "Sorry, I'm having trouble right now. Please try again!"
    if "user_id" in session:
        db.session.add(ChatHistory(user_id=session["user_id"], role="user", message=user_msg))
        db.session.add(ChatHistory(user_id=session["user_id"], role="assistant", message=reply))
        db.session.commit()
    return jsonify({"reply": reply})

@app.route("/api/recommendations")
def get_recommendations():
    all_dests = Destination.query.filter_by(is_active=True).all()
    if "user_id" not in session:
        top = sorted(all_dests, key=lambda d: d.rating or 0, reverse=True)[:4]
    else:
        uid           = session["user_id"]
        user_bookings = BookingHistory.query.filter_by(user_id=uid).all()
        visited       = {b.destination for b in user_bookings}
        visited_objs  = [d for d in all_dests if d.name in visited]
        pref_cats     = Counter(d.category for d in visited_objs if d.category)
        top_cats      = [c for c, _ in pref_cats.most_common(3)]
        pop           = [row.destination for row in db.session.query(
            BookingHistory.destination, func.count(BookingHistory.id).label("cnt")
        ).group_by(BookingHistory.destination).order_by(func.count(BookingHistory.id).desc()).all()]
        scored = []
        for d in all_dests:
            if d.name in visited: continue
            score = (3 if d.category in top_cats else 0) + (2 if d.name in pop else 0) + (d.rating or 0) * 0.5
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [d for _, d in scored[:4]]
        if len(top) < 4:
            extras = sorted([d for d in all_dests if d not in top], key=lambda d: d.rating or 0, reverse=True)
            top += extras[:4 - len(top)]
    result = []
    for d in top:
        img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name + " travel")
        result.append({"id": d.id, "name": d.name, "rating": d.rating, "image": img, "category": d.category, "best_time": d.best_time})
    return jsonify(result)

@app.route("/analytics")
@login_required
def analytics():
    uid  = session["user_id"]
    user = User.query.get(uid)
    my_bookings = BookingHistory.query.filter_by(user_id=uid).all()
    booking_ids = [b.id for b in my_bookings]
    total_trips = len(my_bookings)
    total_spent = (
        db.session.query(func.sum(HotelBooking.final_payable)).filter(HotelBooking.booking_id.in_(booking_ids)).scalar() or 0
    ) + (
        db.session.query(func.sum(TransportBooking.price)).filter(TransportBooking.booking_id.in_(booking_ids)).scalar() or 0
    )
    dest_counter = Counter(b.destination for b in my_bookings)
    fav_dest     = dest_counter.most_common(5)
    monthly = {}
    for i in range(5, -1, -1):
        dt    = datetime.now() - timedelta(days=30 * i)
        label = dt.strftime("%b %Y")
        count = sum(1 for b in my_bookings if b.created_at and b.created_at.month == dt.month and b.created_at.year == dt.year)
        monthly[label] = count
    global_top_raw = db.session.query(BookingHistory.destination, func.count(BookingHistory.id)).group_by(BookingHistory.destination).order_by(func.count(BookingHistory.id).desc()).limit(5).all()
    global_top = [{"destination": t[0], "cnt": t[1]} for t in global_top_raw]
    transport_types_raw = db.session.query(TransportBooking.transport_type, func.count(TransportBooking.id)).filter(TransportBooking.booking_id.in_(booking_ids)).group_by(TransportBooking.transport_type).all()
    transport_types = [{"type": t[0], "count": t[1]} for t in transport_types_raw]
    loyalty_history = LoyaltyTransaction.query.filter_by(user_id=uid).order_by(LoyaltyTransaction.created_at.desc()).limit(10).all()
    return render_template("analytics.html", user=user, total_trips=total_trips, total_spent=total_spent,
        fav_dest=fav_dest, monthly=monthly, global_top=global_top, transport_types=transport_types, loyalty_history=loyalty_history)

@app.route("/api/analytics-data")
@login_required
def analytics_data():
    uid = session["user_id"]
    my_bookings = BookingHistory.query.filter_by(user_id=uid).all()
    labels, data = [], []
    for i in range(5, -1, -1):
        dt = datetime.now() - timedelta(days=30 * i)
        labels.append(dt.strftime("%b"))
        data.append(sum(1 for b in my_bookings if b.created_at and b.created_at.month == dt.month and b.created_at.year == dt.year))
    dest_counter = Counter(b.destination for b in my_bookings)
    top5 = dest_counter.most_common(5)
    return jsonify({"monthly_labels": labels, "monthly_data": data, "dest_labels": [d[0] for d in top5], "dest_data": [d[1] for d in top5]})

# ── WISHLIST ──

@app.route("/wishlist/toggle/<int:dest_id>", methods=["POST"])
@login_required
def toggle_wishlist(dest_id):
    uid      = session["user_id"]
    existing = Wishlist.query.filter_by(user_id=uid, destination_id=dest_id).first()
    if existing:
        db.session.delete(existing); db.session.commit()
        return jsonify({"status": "removed"})
    db.session.add(Wishlist(user_id=uid, destination_id=dest_id)); db.session.commit()
    return jsonify({"status": "added"})

@app.route("/wishlist")
@login_required
def my_wishlist():
    uid   = session["user_id"]
    items = Wishlist.query.filter_by(user_id=uid).order_by(Wishlist.created_at.desc()).all()
    dests = [Destination.query.get(w.destination_id) for w in items]
    dests = [d for d in dests if d]
    return render_template("wishlist.html", destinations=dests)

# ── REVIEWS ──

@app.route("/review/add", methods=["POST"])
@login_required
def add_review():
    destination = request.form.get("destination")
    rating      = int(request.form.get("rating", 5))
    comment     = request.form.get("comment", "").strip()
    if not destination or not comment:
        flash("Please fill all fields", "error")
        return redirect(request.referrer or url_for("home"))
    booked = BookingHistory.query.filter_by(user_id=session["user_id"], destination=destination).first()
    if not booked:
        flash("You can only review destinations you have booked", "error")
        return redirect(request.referrer or url_for("home"))
    existing = Review.query.filter_by(user_id=session["user_id"], destination=destination).first()
    if existing:
        existing.rating = rating; existing.comment = comment
    else:
        db.session.add(Review(user_id=session["user_id"], destination=destination, rating=rating, comment=comment))
        award_points(session["user_id"], 20, f"Review for {destination}")
    db.session.commit()
    flash("Review submitted! +20 loyalty points", "success")
    return redirect(request.referrer or url_for("my_bookings"))

@app.route("/api/reviews/<destination>")
def get_reviews(destination):
    reviews = Review.query.filter_by(destination=destination).order_by(Review.created_at.desc()).limit(10).all()
    result  = []
    for r in reviews:
        user = User.query.get(r.user_id)
        result.append({"name": user.name if user else "Traveller", "rating": r.rating, "comment": r.comment, "date": r.created_at.strftime("%b %Y") if r.created_at else ""})
    return jsonify(result)

@app.route("/hotel-review/add", methods=["POST"])
@login_required
def add_hotel_review():
    hotel_id = int(request.form.get("hotel_id"))
    rating   = int(request.form.get("rating", 5))
    comment  = request.form.get("comment", "").strip()
    existing = HotelReview.query.filter_by(user_id=session["user_id"], hotel_id=hotel_id).first()
    if existing:
        existing.rating = rating; existing.comment = comment
    else:
        db.session.add(HotelReview(user_id=session["user_id"], hotel_id=hotel_id, rating=rating, comment=comment))
    db.session.commit()
    flash("Hotel review submitted!", "success")
    return redirect(request.referrer or url_for("home"))

@app.route("/api/hotel-reviews/<int:hotel_id>")
def get_hotel_reviews(hotel_id):
    reviews = HotelReview.query.filter_by(hotel_id=hotel_id).order_by(HotelReview.created_at.desc()).limit(10).all()
    result  = []
    for r in reviews:
        user = User.query.get(r.user_id)
        result.append({"name": user.name if user else "Traveller", "rating": r.rating, "comment": r.comment, "date": r.created_at.strftime("%b %Y") if r.created_at else ""})
    return jsonify(result)

# ── HOTELS ──

@app.route("/api/hotels/<int:destination_id>")
def api_hotels(destination_id):
    hotels = Hotel.query.filter_by(destination_id=destination_id, is_active=True).all()
    data   = []
    for h in hotels:
        prices = [r.base_price for r in h.rooms if r.base_price is not None]
        imgs   = get_pexels_images(h.name + " hotel resort", 3)
        avg_r  = db.session.query(func.avg(HotelReview.rating)).filter_by(hotel_id=h.id).scalar()
        data.append({
            "id": h.id, "hotel": h.name, "stars": h.stars,
            "price": min(prices) if prices else 0,
            "available_rooms": sum(((r.total_rooms or 0) - (r.booked_rooms or 0)) for r in h.rooms),
            "amenities": [a.name for a in h.amenities], "images": imgs, "description": h.description or "",
            "avg_rating": round(avg_r, 1) if avg_r else None,
            "rooms": [{"type": r.room_type, "available": (r.total_rooms or 0) - (r.booked_rooms or 0), "price": r.base_price} for r in h.rooms]
        })
    return jsonify(data)

@app.route("/hotels/<int:destination_id>")
def hotels_by_destination(destination_id):
    destination = Destination.query.get_or_404(destination_id)
    hotels      = Hotel.query.filter_by(destination_id=destination_id, is_active=True).all()
    for h in hotels:
        h.pexels_images = get_pexels_images(h.name + " hotel", 3)
        h.pexels_main   = h.pexels_images[0] if h.pexels_images else ""
        h.avg_rating    = db.session.query(func.avg(HotelReview.rating)).filter_by(hotel_id=h.id).scalar()
    dest_img = destination.image if (destination.image and destination.image.startswith("http")) else get_pexels_single(destination.name + " travel")
    return render_template("hotels.html", destination=destination, hotels=hotels, dest_img=dest_img)


# ── HOTEL BOOKING ──────────────────────────────────────────
# FIX: Pre-fill user data, fix None room check, save persons to session

@app.route("/book-hotel/<int:hotel_id>", methods=["GET", "POST"])
@login_required
def hotel_booking(hotel_id):
    hotel           = Hotel.query.get_or_404(hotel_id)
    hotel_images    = get_pexels_images(hotel.name + " hotel room", 4)
    insurance_plans = InsurancePlan.query.filter_by(is_active=True).all()
    # FIX: Get logged-in user for pre-filling form
    current_user    = User.query.get(session["user_id"])
    error           = None

    if request.method == "POST":
        try:
            persons        = int(request.form.get("persons", 1))
            room_id        = int(request.form.get("room_id"))
            checkin        = request.form.get("checkin")
            checkout       = request.form.get("checkout")
            name           = request.form.get("name", "").strip()
            email          = request.form.get("email", "").strip()
            phone          = request.form.get("phone", "").strip()
            id_type        = request.form.get("id_type")
            id_number      = request.form.get("id_number", "").strip().upper()
            lunch          = request.form.get("lunch")
            dinner         = request.form.get("dinner")
            pickup         = request.form.get("pickup")
            bank_name      = request.form.get("bank_name", "")
            special_req    = request.form.get("special_request", "").strip()
            coupon_code    = request.form.get("coupon_code", "").strip().upper()
            insurance_id   = request.form.get("insurance_id")
            use_points     = request.form.get("use_loyalty_points")
            payment_method = request.form.get("payment_method", "upi")

            today         = datetime.today().date()
            checkin_date  = datetime.strptime(checkin, "%Y-%m-%d").date()
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()

            if persons <= 0:                                                                    error = "Persons must be at least 1"
            elif checkin_date < today:                                                          error = "Check-in cannot be in the past"
            elif checkout_date < checkin_date:                                                  error = "Check-out cannot be before check-in"
            elif not re.match(r"^[6-9]\d{9}$", phone):                                         error = "Invalid phone number (must be 10 digits starting with 6-9)"
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):                                   error = "Invalid email address"
            elif id_type == "aadhaar" and not re.match(r"^\d{12}$", id_number):                error = "Aadhaar must be 12 digits"
            elif id_type == "pan" and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", id_number):    error = "Invalid PAN format (e.g. ABCDE1234F)"

            if error:
                return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images,
                    form_data=request.form, error=error, applied_discount=0,
                    insurance_plans=insurance_plans, current_user=current_user)

            room = Room.query.get_or_404(room_id)
            required_rooms  = math.ceil(persons / 2)
            # FIX: handle None booked_rooms and total_rooms
            available_rooms = (room.total_rooms or 0) - (room.booked_rooms or 0)

            if available_rooms <= 0:
                error = f"No rooms available for {room.room_type}. Please choose a different room type."
            elif available_rooms < required_rooms:
                error = f"Only {available_rooms} room(s) available, but {required_rooms} needed for {persons} guests."

            if error:
                return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images,
                    form_data=request.form, error=error, applied_discount=0,
                    insurance_plans=insurance_plans, current_user=current_user)

            # FIX: same-day checkout = 1 night charge
            nights     = (checkout_date - checkin_date).days
            nights     = nights if nights > 0 else 1
            base_price = nights * room.base_price * required_rooms
            extra_price = 0
            if lunch:  extra_price += hotel.lunch_price  * persons
            if dinner: extra_price += hotel.dinner_price * persons
            if pickup: extra_price += hotel.pickup_price

            ins_price = 0; ins_id = None
            if insurance_id:
                plan = InsurancePlan.query.get(int(insurance_id))
                if plan:
                    ins_price = plan.price_per_day * nights * persons
                    ins_id    = plan.id

            total_price = base_price + extra_price + ins_price

            coupon_discount = 0; applied_coupon = ""
            if coupon_code:
                coupon = Coupon.query.filter_by(code=coupon_code, active=True).first()
                today_date = datetime.today().date()
                if not coupon:                                                    error = "Invalid coupon code"
                elif coupon.valid_till and coupon.valid_till < today_date:        error = "Coupon has expired"
                elif coupon.valid_from and coupon.valid_from > today_date:        error = "Coupon is not active yet"
                elif coupon.used_count >= coupon.usage_limit:                     error = "Coupon usage limit reached"
                elif total_price < coupon.min_amount:                             error = f"Minimum booking ₹{coupon.min_amount} required"
                else:
                    coupon_discount = min((total_price * coupon.discount_percent) // 100, coupon.max_discount)
                    applied_coupon  = coupon_code
                    coupon.used_count += 1

            if error:
                return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images,
                    form_data=request.form, error=error, applied_discount=0,
                    insurance_plans=insurance_plans, current_user=current_user)

            bank_map      = {"hdfc": 10, "sbi": 15, "icici": 12, "axis": 8, "kotak": 7}
            bank_discount = ((total_price - coupon_discount) * bank_map.get(bank_name, 0)) // 100

            loyalty_discount = 0
            user = User.query.get(session["user_id"])
            if use_points and user and user.loyalty_points:
                max_pts_usable   = min(user.loyalty_points, (total_price - coupon_discount - bank_discount) // 2)
                loyalty_discount = max_pts_usable
                user.loyalty_points -= max_pts_usable

            final_payable = max(total_price - coupon_discount - bank_discount - loyalty_discount, 0)

            destination  = Destination.query.get(hotel.destination_id)
            main_booking = BookingHistory(user_id=session["user_id"], destination=destination.name, status="active")
            db.session.add(main_booking)
            db.session.commit()

            booking = HotelBooking(
                booking_id=main_booking.id, hotel_id=hotel.id, room_id=room_id,
                persons=persons, check_in=checkin_date, check_out=checkout_date,
                base_price=base_price, extra_price=extra_price, total_price=total_price,
                bank_name=bank_name, card_number="", bank_discount=bank_discount,
                coupon_code=applied_coupon, coupon_discount=coupon_discount,
                loyalty_discount=loyalty_discount, insurance_id=ins_id, insurance_price=ins_price,
                final_payable=final_payable, lunch_added=bool(lunch), dinner_added=bool(dinner),
                pickup_added=bool(pickup), id_type=id_type, id_number=id_number,
                name=name, email=email, phone=phone, payment_method=payment_method,
                special_request=special_req, payment_status="pending", created_at=datetime.now()
            )
            db.session.add(booking)
            room.booked_rooms = (room.booked_rooms or 0) + required_rooms
            db.session.commit()

            pts = final_payable // 100
            award_points(session["user_id"], pts, f"Booking #{main_booking.id}", main_booking.id)
            add_notification(session["user_id"], f"Booking confirmed for {destination.name}! Check-in: {checkin_date}", url_for("my_bookings"))

            try:
                send_email(email, "TripMoree — Booking Confirmed! 🎉",
                    f"Hi {name},\n\nYour booking at {hotel.name} is confirmed!\n"
                    f"Check-in: {checkin_date} | Check-out: {checkout_date}\n"
                    f"Guests: {persons} | Nights: {nights}\n"
                    f"Amount Paid: ₹{final_payable:,}\n\nThank you for choosing TripMoree! 🌍")
            except:
                pass

            # FIX: Save persons to session
            session["persons"]          = persons
            session["hotel_booking_id"] = booking.id
            session["booking_id"]       = main_booking.id
            return redirect(url_for("payment_page", booking_id=booking.id))

        except Exception as e:
            db.session.rollback()
            print("BOOKING ERROR:", e)
            return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images,
                form_data=request.form, error="Something went wrong. Please try again.", applied_discount=0,
                insurance_plans=insurance_plans, current_user=current_user)

    # FIX: Pass current_user for pre-fill on GET
    return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images,
        insurance_plans=insurance_plans, current_user=current_user)


# ── COUPON VALIDATE API ──

@app.route("/api/validate-coupon", methods=["POST"])
@login_required
def validate_coupon():
    data   = request.json
    code   = data.get("code", "").upper().strip()
    amount = int(data.get("amount", 0))
    coupon = Coupon.query.filter_by(code=code, active=True).first()
    today  = datetime.today().date()
    if not coupon: return jsonify({"valid": False, "message": "Invalid coupon code"})
    if coupon.valid_till and coupon.valid_till < today: return jsonify({"valid": False, "message": "Coupon has expired"})
    if coupon.valid_from and coupon.valid_from > today: return jsonify({"valid": False, "message": "Coupon not active yet"})
    if coupon.used_count >= coupon.usage_limit: return jsonify({"valid": False, "message": "Coupon usage limit reached"})
    if amount < coupon.min_amount: return jsonify({"valid": False, "message": f"Minimum amount ₹{coupon.min_amount} required"})
    discount = min((amount * coupon.discount_percent) // 100, coupon.max_discount)
    return jsonify({"valid": True, "discount": discount, "message": f"{coupon.discount_percent}% off! You save ₹{discount}"})


# ── PAYMENT ──

@app.route("/payment/<int:booking_id>")
@login_required
def payment_page(booking_id):
    booking      = HotelBooking.query.get_or_404(booking_id)
    main_booking = BookingHistory.query.get(booking.booking_id)
    hotel        = Hotel.query.get(booking.hotel_id)
    if main_booking.user_id != session["user_id"]:
        return redirect(url_for("home"))
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={booking.final_payable}&cu=INR&tn=TripMoree+Booking+{booking_id}"
    return render_template("payment.html",
        booking=booking, hotel=hotel, main_booking=main_booking,
        upi_id=UPI_ID, upi_name=UPI_NAME, upi_link=upi_link,
        amount=booking.final_payable)

@app.route("/payment/confirm/<int:booking_id>", methods=["POST"])
@login_required
def confirm_payment(booking_id):
    booking = HotelBooking.query.get_or_404(booking_id)
    # Prevent double payment (back button fix)
    if booking.payment_status == "paid":
        dest = BookingHistory.query.get(booking.booking_id).destination
        return redirect(url_for("transport_choice", destination=dest, booked="1", hotel_booking_id=booking.id))
    booking.payment_status = "paid"
    booking.upi_ref        = request.form.get("upi_ref", "").strip()
    db.session.commit()
    flash("Payment confirmed! Booking is active. ✅", "success")
    dest = BookingHistory.query.get(booking.booking_id).destination
    return redirect(url_for("transport_choice", destination=dest, booked="1", hotel_booking_id=booking.id))

@app.route("/payment/skip/<int:booking_id>")
@login_required
def skip_payment(booking_id):
    booking = HotelBooking.query.get_or_404(booking_id)
    if booking.payment_status not in ("paid", "demo"):
        booking.payment_status = "demo"
        db.session.commit()
    dest = BookingHistory.query.get(booking.booking_id).destination
    return redirect(url_for("transport_choice", destination=dest, booked="1", hotel_booking_id=booking.id))


# ── FLIGHT PAYMENT ─────────────────────────────────────────
# FIX: Added separate flight payment page

@app.route("/flight-payment/<int:transport_booking_id>")
@login_required
def flight_payment(transport_booking_id):
    tb           = TransportBooking.query.get_or_404(transport_booking_id)
    main_booking = BookingHistory.query.get(tb.booking_id)
    hb           = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    if main_booking.user_id != session["user_id"]:
        return redirect(url_for("home"))
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={tb.price}&cu=INR&tn=TripMoree+Flight+{transport_booking_id}"
    return render_template("flight_payment.html",
        tb=tb, main_booking=main_booking, hb=hb,
        upi_id=UPI_ID, upi_name=UPI_NAME, upi_link=upi_link,
        hotel_booking_id=hb.id if hb else 0)

@app.route("/flight-payment/confirm/<int:transport_booking_id>", methods=["POST"])
@login_required
def confirm_flight_payment(transport_booking_id):
    tb  = TransportBooking.query.get_or_404(transport_booking_id)
    hb  = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    flash(f"Flight payment confirmed! ✈️ ₹{tb.price:,} paid.", "success")
    if hb:
        return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
    return redirect(url_for("my_bookings"))

@app.route("/flight-payment/skip/<int:transport_booking_id>")
@login_required
def skip_flight_payment(transport_booking_id):
    tb  = TransportBooking.query.get_or_404(transport_booking_id)
    hb  = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    if hb:
        return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
    return redirect(url_for("my_bookings"))


# ── BOOKING CANCELLATION ──

@app.route("/booking/cancel/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = BookingHistory.query.get_or_404(booking_id)
    if booking.user_id != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403
    if booking.status == "cancelled":
        return jsonify({"error": "Already cancelled"})
    reason = request.form.get("reason", "Cancelled by user")
    booking.status = "cancelled"; booking.cancel_reason = reason
    hb = HotelBooking.query.filter_by(booking_id=booking_id).first()
    if hb:
        room = Room.query.get(hb.room_id)
        if room:
            released = math.ceil((hb.persons or 1) / 2)
            room.booked_rooms = max(0, (room.booked_rooms or 0) - released)
    db.session.commit()
    add_notification(session["user_id"], f"Booking #{booking_id} to {booking.destination} has been cancelled.", url_for("my_bookings"))
    flash("Booking cancelled successfully.", "info")
    return redirect(url_for("my_bookings"))


# ── PACKAGES ──

@app.route("/packages")
def packages_page():
    packages = TravelPackage.query.filter_by(is_active=True).all()
    for p in packages:
        d = Destination.query.get(p.destination_id)
        img = ""
        if d:
            img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name)
        p.dest_img = img; p.dest = d
        p.includes_list = json.loads(p.includes) if p.includes else []
    return render_template("packages.html", packages=packages)

@app.route("/package/<int:pkg_id>")
def package_detail(pkg_id):
    p = TravelPackage.query.get_or_404(pkg_id)
    if not p.is_active:
        flash("This package is no longer available.", "warning")
        return redirect(url_for("packages_page"))
    dest = Destination.query.get(p.destination_id)
    hotel= Hotel.query.get(p.hotel_id) if p.hotel_id else None
    imgs = get_pexels_images((dest.name if dest else "travel") + " landscape", 5)
    p.includes_list = json.loads(p.includes) if p.includes else []
    return render_template("package_detail.html", package=p, dest=dest, hotel=hotel, images=imgs)


# ── AUTH ──

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            flash("Email and password required", "error")
            return render_template("login.html", email=email)
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found", "error")
            return render_template("login.html", email=email)
        if not check_password_hash(user.password, password):
            flash("Incorrect password", "error")
            return render_template("login.html", email=email)
        session["user_id"]      = user.id
        session["is_logged_in"] = True
        flash(f"Welcome back, {user.name}! 👋", "success")
        next_url = session.pop("next_url", None)
        if next_url: return redirect(next_url)
        return redirect(url_for("user_dashboard"))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name     = request.form.get("name")
        email    = request.form.get("email")
        password = request.form.get("password")
        referral = request.form.get("referral_code", "").strip().upper()
        if not name or not email or not password:
            flash("All fields are required", "error"); return render_template("signup.html", name=name, email=email)
        if len(password) < 6:
            flash("Password must be at least 6 characters", "error"); return render_template("signup.html", name=name, email=email)
        if not any(c.isdigit() for c in password):
            flash("Password must contain at least 1 number", "error"); return render_template("signup.html", name=name, email=email)
        if not any(c.isupper() for c in password):
            flash("Password must contain at least 1 uppercase letter", "error"); return render_template("signup.html", name=name, email=email)
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error"); return render_template("signup.html", name=name, email=email)
        ref_user = None
        if referral:
            ref_user = User.query.filter_by(referral_code=referral).first()
            if not ref_user: flash("Invalid referral code", "warning")
        new_user = User(name=name, email=email, password=generate_password_hash(password),
                        referral_code=generate_referral_code(), referred_by=ref_user.id if ref_user else None)
        db.session.add(new_user); db.session.commit()
        if ref_user:
            award_points(ref_user.id, 100, f"Referral bonus — {name} joined")
            award_points(new_user.id, 50, "Welcome bonus (referral)")
            add_notification(ref_user.id, f"{name} joined using your referral! +100 points.")
        else:
            award_points(new_user.id, 50, "Welcome bonus")
        session["user_id"] = new_user.id
        flash(f"Welcome to TripMoree, {name}! 🎉 You earned 50 loyalty points.", "success")
        return redirect(url_for("user_dashboard"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user  = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with this email.", "error")
            return render_template("forgot_password.html")
        otp = ''.join(random.choices(string.digits, k=6))
        user.otp = otp; user.otp_expiry = datetime.now() + timedelta(minutes=10)
        db.session.commit()
        send_email(email, "TripMoree — Password Reset OTP",
                   f"Hi {user.name},\n\nYour OTP is: {otp}\nValid for 10 minutes.\n\nTripMoree Team")
        session["otp_email"] = email
        flash("OTP sent to your email!", "success")
        return redirect(url_for("verify_otp"))
    return render_template("forgot_password.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    email = session.get("otp_email")
    if not email: return redirect(url_for("forgot_password"))
    if request.method == "POST":
        otp          = request.form.get("otp", "").strip()
        new_password = request.form.get("new_password", "").strip()
        user = User.query.filter_by(email=email).first()
        if not user or user.otp != otp:
            flash("Invalid OTP.", "error"); return render_template("verify_otp.html")
        if user.otp_expiry and datetime.now() > user.otp_expiry:
            flash("OTP expired.", "error"); return redirect(url_for("forgot_password"))
        if len(new_password) < 6:
            flash("Password too short.", "error"); return render_template("verify_otp.html")
        user.password = generate_password_hash(new_password)
        user.otp = None; user.otp_expiry = None
        db.session.commit()
        flash("Password reset successfully! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("verify_otp.html")

# ── USER DASHBOARD ──

@app.route("/dashboard")
@login_required
def user_dashboard():
    uid  = session["user_id"]
    user = User.query.get(uid)
    my_bookings  = BookingHistory.query.filter_by(user_id=uid).order_by(BookingHistory.created_at.desc()).limit(5).all()
    total_trips  = BookingHistory.query.filter_by(user_id=uid).count()
    booking_ids  = [b.id for b in BookingHistory.query.filter_by(user_id=uid).all()]
    total_spent  = db.session.query(func.sum(HotelBooking.final_payable)).filter(HotelBooking.booking_id.in_(booking_ids)).scalar() or 0
    wishlist_cnt = Wishlist.query.filter_by(user_id=uid).count()
    upcoming = []
    for b in my_bookings:
        hb = HotelBooking.query.filter_by(booking_id=b.id).first()
        if hb and hb.check_in and hb.check_in >= datetime.today().date():
            upcoming.append({"booking": b, "hotel": hb})
    notifications = Notification.query.filter_by(user_id=uid, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    loyalty_tier  = "Bronze"
    if user.loyalty_points >= 5000:   loyalty_tier = "Gold"
    elif user.loyalty_points >= 1000: loyalty_tier = "Silver"
    return render_template("user_dashboard.html",
        user=user, my_bookings=my_bookings, total_trips=total_trips,
        total_spent=total_spent, wishlist_cnt=wishlist_cnt, upcoming=upcoming,
        notifications=notifications, loyalty_tier=loyalty_tier)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def user_profile():
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        user.name       = request.form.get("name", user.name).strip()
        user.phone      = request.form.get("phone", user.phone or "").strip()
        user.city       = request.form.get("city", "").strip()
        user.bio        = request.form.get("bio", "").strip()
        user.newsletter = bool(request.form.get("newsletter"))
        new_pass = request.form.get("new_password", "").strip()
        if new_pass:
            if len(new_pass) < 6:
                flash("Password must be at least 6 characters.", "error")
                return render_template("profile.html", user=user)
            user.password = generate_password_hash(new_pass)
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("user_profile"))
    return render_template("profile.html", user=user)

@app.route("/notifications")
@login_required
def notifications():
    uid    = session["user_id"]
    notifs = Notification.query.filter_by(user_id=uid).order_by(Notification.created_at.desc()).limit(30).all()
    Notification.query.filter_by(user_id=uid, is_read=False).update({"is_read": True})
    db.session.commit()
    return render_template("notifications.html", notifications=notifs)

@app.route("/api/notifications/unread-count")
@login_required
def unread_notification_count():
    count = Notification.query.filter_by(user_id=session["user_id"], is_read=False).count()
    return jsonify({"count": count})

@app.route("/my-bookings")
@login_required
def my_bookings():
    bookings = BookingHistory.query.filter_by(user_id=session["user_id"]).order_by(BookingHistory.created_at.desc()).all()
    result   = []
    for b in bookings:
        hotel           = HotelBooking.query.filter_by(booking_id=b.id).first()
        hotel_total     = hotel.final_payable if hotel and hotel.final_payable else 0
        transports      = TransportBooking.query.filter_by(booking_id=b.id).all()
        transport_total = sum(t.price or 0 for t in transports)
        transport_data  = [{"transport": t} for t in transports]
        cab = CabBooking.query.filter_by(booking_id=b.id).first()
        cab_days = []; cab_total = 0
        if cab:
            cab_total = cab.price or 0
            for d in CabBookingDay.query.filter_by(cab_booking_id=cab.id).order_by(CabBookingDay.day_number).all():
                spots_rel  = CabBookingDaySpot.query.filter_by(cab_booking_day_id=d.id).all()
                spot_names = [HypeSpot.query.get(s.spot_id).spot_name for s in spots_rel if HypeSpot.query.get(s.spot_id)]
                cab_days.append({"day": d.day_number, "arrival": d.arrival_time, "departure": d.departure_time,
                                  "pickup": d.pickup_type, "drop": d.drop_type, "spots": spot_names, "km": d.day_km, "price": d.day_price})
        grand_total = hotel_total + transport_total + cab_total
        result.append({"booking": b, "hotel": hotel, "transports": transport_data,
                        "cab": cab, "cab_days": cab_days, "hotel_total": hotel_total,
                        "transport_total": transport_total, "cab_total": cab_total, "grand_total": grand_total})
    total_spent = sum(b["grand_total"] for b in result)
    return render_template("my_bookings.html", bookings=result, total_spent=total_spent)

@app.route("/support", methods=["GET", "POST"])
@login_required
def my_support():
    uid = session["user_id"]
    if request.method == "POST":
        ticket = SupportTicket(
            user_id=uid, booking_id=request.form.get("booking_id") or None,
            subject=request.form.get("subject", "").strip(),
            message=request.form.get("message", "").strip(), status="open",
        )
        db.session.add(ticket); db.session.commit()
        flash("Support ticket raised! We'll reply soon.", "success")
        return redirect(url_for("my_support"))
    tickets  = SupportTicket.query.filter_by(user_id=uid).order_by(SupportTicket.created_at.desc()).all()
    bookings = BookingHistory.query.filter_by(user_id=uid).order_by(BookingHistory.created_at.desc()).all()
    return render_template("support.html", tickets=tickets, bookings=bookings)

@app.route("/loyalty")
@login_required
def loyalty_page():
    uid  = session["user_id"]
    user = User.query.get(uid)
    history = LoyaltyTransaction.query.filter_by(user_id=uid).order_by(LoyaltyTransaction.created_at.desc()).limit(20).all()
    tier = "Bronze"; next_tier = "Silver"; pts_needed = max(0, 1000 - (user.loyalty_points or 0))
    if user.loyalty_points >= 5000:   tier = "Gold";   next_tier = "Platinum (Coming soon)"; pts_needed = 0
    elif user.loyalty_points >= 1000: tier = "Silver"; next_tier = "Gold"; pts_needed = max(0, 5000 - user.loyalty_points)
    return render_template("loyalty.html", user=user, history=history, tier=tier, next_tier=next_tier, pts_needed=pts_needed)

@app.route("/loyalty/redeem", methods=["POST"])
@login_required
def redeem_loyalty():
    uid    = session["user_id"]
    user   = User.query.get(uid)
    points = int(request.form.get("points", 0))
    if points <= 0 or points > (user.loyalty_points or 0):
        flash("Invalid points amount.", "error"); return redirect(url_for("loyalty_page"))
    discount = points // 10
    code     = "LYL" + generate_referral_code(6)
    coupon   = Coupon(code=code, discount_percent=0, max_discount=discount, min_amount=discount,
                      usage_limit=1, active=True, valid_till=(datetime.today() + timedelta(days=30)).date())
    db.session.add(coupon)
    user.loyalty_points -= points
    db.session.add(LoyaltyTransaction(user_id=uid, points=-points, action=f"Redeemed for coupon {code}"))
    db.session.commit()
    flash(f"Coupon {code} generated! Save ₹{discount} on your next booking.", "success")
    return redirect(url_for("loyalty_page"))

@app.route("/newsletter/subscribe", methods=["POST"])
def newsletter_subscribe():
    email = request.form.get("email", "").strip()
    name  = request.form.get("name", "Traveller").strip()
    if not email: return jsonify({"success": False, "message": "Email required"})
    existing = Newsletter.query.filter_by(email=email).first()
    if existing:
        existing.is_active = True; db.session.commit()
        return jsonify({"success": True, "message": "You're already subscribed!"})
    db.session.add(Newsletter(email=email, name=name, is_active=True))
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user: user.newsletter = True
    db.session.commit()
    return jsonify({"success": True, "message": "Subscribed successfully! 🎉"})

@app.route("/newsletter/unsubscribe/<email>")
def newsletter_unsubscribe(email):
    sub = Newsletter.query.filter_by(email=email).first()
    if sub: sub.is_active = False; db.session.commit()
    flash("You have been unsubscribed from our newsletter.", "info")
    return redirect(url_for("home"))


# ── TRANSPORT ──────────────────────────────────────────────
# FIX: Bus/Train available_seats None check in confirm routes

@app.route("/transport-choice/<destination>")
def transport_choice(destination):
    hotel_booking_id = request.args.get("hotel_booking_id", "")
    booked           = request.args.get("booked", "")
    return render_template("transport_choice.html", destination=destination,
                           hotel_booking_id=hotel_booking_id, booked=booked)

@app.route("/flight/<destination>", methods=["GET", "POST"])
@login_required
def flight(destination):
    persons          = session.get("persons", 1)
    hotel_booking_id = request.args.get("hotel_booking_id") or session.get("hotel_booking_id")
    booking_id       = session.get("booking_id")
    if hotel_booking_id:
        try:
            hb = HotelBooking.query.get(int(hotel_booking_id))
            if hb:
                booking_id = hb.booking_id
                session["booking_id"]       = hb.booking_id
                session["hotel_booking_id"] = hb.id
                session["persons"]          = hb.persons or 1
        except: pass
    if not booking_id:
        flash("Please complete hotel booking first.", "warning"); return redirect(url_for("home"))
    if request.method == "POST":
        src    = request.form.get("source", "").strip()
        fclass = request.form.get("flight_class", "").strip()
        q = Flight.query.filter_by(destination=destination)
        if src:    q = q.filter_by(source=src)
        if fclass: q = q.filter_by(flight_class=fclass)
        flights = q.all()
    else:
        flights = Flight.query.filter_by(destination=destination).all()
    sources = db.session.query(Flight.source).filter_by(destination=destination).distinct().all()
    classes = db.session.query(Flight.flight_class).distinct().all()
    return render_template("flights.html", destination=destination, persons=persons,
                           flights=flights, sources=[s[0] for s in sources],
                           classes=[c[0] for c in classes], hotel_booking_id=hotel_booking_id)

@app.route("/confirm-flight/<int:flight_id>")
@login_required
def confirm_flight(flight_id):
    booking_id       = session.get("booking_id")
    hotel_booking_id = request.args.get("hotel_booking_id") or session.get("hotel_booking_id")
    persons          = session.get("persons", 1)
    if not booking_id:
        flash("Session expired. Please rebook.", "warning"); return redirect(url_for("home"))
    already = TransportBooking.query.filter_by(booking_id=booking_id, transport_type="flight").first()
    if already:
        flash("Flight already booked for this trip.", "info")
        hb = HotelBooking.query.filter_by(booking_id=booking_id).first()
        if not hb and hotel_booking_id: hb = HotelBooking.query.get(int(hotel_booking_id))
        if hb: return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
        return redirect(url_for("my_bookings"))
    f = Flight.query.get_or_404(flight_id)
    # FIX: None-safe seats check
    avail = f.available_seats or 0
    if avail < persons:
        flash(f"Only {avail} seats available.", "warning")
        return redirect(request.referrer or url_for("home"))
    f.available_seats = avail - persons
    tb = TransportBooking(booking_id=booking_id, transport_type="flight",
        source=f.source, destination=f.destination, persons=persons, price=f.price * persons)
    db.session.add(tb); db.session.commit()
    flash(f"Flight booked! {f.airline} {f.source}→{f.destination} ✈️", "success")
    # FIX: Redirect to flight payment page
    return redirect(url_for("flight_payment", transport_booking_id=tb.id))

@app.route("/bus/<destination>", methods=["GET", "POST"])
@login_required
def bus(destination):
    hotel_booking_id = request.args.get("hotel_booking_id") or session.get("hotel_booking_id")
    booking_id       = session.get("booking_id")
    if hotel_booking_id:
        try:
            hb = HotelBooking.query.get(int(hotel_booking_id))
            if hb:
                booking_id = hb.booking_id
                session["booking_id"]       = hb.booking_id
                session["hotel_booking_id"] = hb.id
                session["persons"]          = hb.persons or 1
        except: pass
    if not booking_id:
        flash("Please complete hotel booking first.", "warning")
        return redirect(url_for("home"))
    # ALWAYS show all buses on GET, filter on POST
    q = Bus.query.filter(func.lower(Bus.destination) == destination.lower())
    if request.method == "POST":
        src   = request.form.get("source", "").strip()
        ac    = request.form.get("ac_type", "").strip()
        stype = request.form.get("seat_type", "").strip()
        if src:   q = q.filter(func.lower(Bus.source) == src.lower())
        if ac:    q = q.filter_by(ac_type=ac)
        if stype: q = q.filter_by(seat_type=stype)
    buses      = q.order_by(Bus.price).all()
    sources    = db.session.query(Bus.source).filter(func.lower(Bus.destination) == destination.lower()).distinct().all()
    ac_types   = db.session.query(Bus.ac_type).distinct().all()
    seat_types = db.session.query(Bus.seat_type).distinct().all()
    return render_template("bus.html", destination=destination,
                           persons=session.get("persons", 1),
                           buses=buses, sources=[s[0] for s in sources if s[0]],
                           ac_types=[a[0] for a in ac_types if a[0]],
                           seat_types=[s[0] for s in seat_types if s[0]],
                           hotel_booking_id=hotel_booking_id or 0)

@app.route("/confirm-bus/<int:bus_id>")
@login_required
def confirm_bus(bus_id):
    booking_id       = session.get("booking_id")
    hotel_booking_id = request.args.get("hotel_booking_id") or session.get("hotel_booking_id")
    persons          = session.get("persons", 1)
    if not booking_id:
        flash("Session expired. Please rebook.", "warning"); return redirect(url_for("home"))
    already = TransportBooking.query.filter_by(booking_id=booking_id, transport_type="bus").first()
    if already:
        flash("Bus already booked for this trip.", "info")
        hb = HotelBooking.query.filter_by(booking_id=booking_id).first()
        if not hb and hotel_booking_id: hb = HotelBooking.query.get(int(hotel_booking_id))
        if hb: return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
        return redirect(url_for("my_bookings"))
    b = Bus.query.get_or_404(bus_id)
    # FIX: None-safe seats check
    avail = b.available_seats or 0
    if avail < persons:
        flash(f"Only {avail} seats available.", "warning")
        return redirect(request.referrer or url_for("home"))
    b.available_seats = avail - persons
    tb_bus = TransportBooking(booking_id=booking_id, transport_type="bus",
        source=b.source, destination=b.destination, persons=persons, price=b.price * persons)
    db.session.add(tb_bus)
    db.session.commit()
    flash(f"Bus booked! {b.operator} {b.source}→{b.destination} 🚌", "success")
    return redirect(url_for("bus_payment", transport_booking_id=tb_bus.id))

@app.route("/train/<destination>", methods=["GET", "POST"])
@login_required
def train(destination):
    hotel_booking_id = request.args.get("hotel_booking_id") or session.get("hotel_booking_id")
    booking_id       = session.get("booking_id")
    if hotel_booking_id:
        try:
            hb = HotelBooking.query.get(int(hotel_booking_id))
            if hb:
                booking_id = hb.booking_id
                session["booking_id"]       = hb.booking_id
                session["hotel_booking_id"] = hb.id
                session["persons"]          = hb.persons or 1
        except: pass
    if not booking_id:
        flash("Please complete hotel booking first.", "warning")
        return redirect(url_for("home"))
    # ALWAYS show all trains on GET, filter on POST
    q = Train.query.filter(func.lower(Train.destination) == destination.lower())
    if request.method == "POST":
        src   = request.form.get("source", "").strip()
        ac    = request.form.get("ac_type", "").strip()
        stype = request.form.get("seat_type", "").strip()
        if src:   q = q.filter(func.lower(Train.source) == src.lower())
        if ac:    q = q.filter_by(ac_type=ac)
        if stype: q = q.filter_by(seat_type=stype)
    trains     = q.order_by(Train.price).all()
    sources    = db.session.query(Train.source).filter(func.lower(Train.destination) == destination.lower()).distinct().all()
    ac_types   = db.session.query(Train.ac_type).distinct().all()
    seat_types = db.session.query(Train.seat_type).distinct().all()
    return render_template("train.html", destination=destination,
                           persons=session.get("persons", 1),
                           trains=trains, sources=[s[0] for s in sources if s[0]],
                           ac_types=[a[0] for a in ac_types if a[0]],
                           seat_types=[s[0] for s in seat_types if s[0]],
                           hotel_booking_id=hotel_booking_id or 0)

@app.route("/confirm-train/<int:train_id>")
@login_required
def confirm_train(train_id):
    booking_id       = session.get("booking_id")
    hotel_booking_id = request.args.get("hotel_booking_id") or session.get("hotel_booking_id")
    persons          = session.get("persons", 1)
    if not booking_id:
        flash("Session expired. Please rebook.", "warning"); return redirect(url_for("home"))
    already = TransportBooking.query.filter_by(booking_id=booking_id, transport_type="train").first()
    if already:
        flash("Train already booked for this trip.", "info")
        hb = HotelBooking.query.filter_by(booking_id=booking_id).first()
        if not hb and hotel_booking_id: hb = HotelBooking.query.get(int(hotel_booking_id))
        if hb: return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
        return redirect(url_for("my_bookings"))
    t = Train.query.get_or_404(train_id)
    # FIX: None-safe seats check
    avail = t.available_seats or 0
    if avail < persons:
        flash(f"Only {avail} seats available.", "warning")
        return redirect(request.referrer or url_for("home"))
    t.available_seats = avail - persons
    tb_train = TransportBooking(booking_id=booking_id, transport_type="train",
        source=t.source, destination=t.destination, persons=persons, price=t.price * persons)
    db.session.add(tb_train)
    db.session.commit()
    flash(f"Train booked! {t.train_name} {t.source}→{t.destination} 🚆", "success")
    return redirect(url_for("train_payment", transport_booking_id=tb_train.id))

@app.route("/api/transport-availability")
def transport_availability():
    destination   = request.args.get("destination", "")
    flights       = Flight.query.filter_by(destination=destination).all()
    trains        = Train.query.filter_by(destination=destination).all()
    buses         = Bus.query.filter_by(destination=destination).all()
    flight_prices = [f.price for f in flights if f.price]
    train_prices  = [t.price for t in trains  if t.price]
    bus_prices    = [b.price for b in buses   if b.price]
    INTERNATIONAL = ["Bali","Paris","Dubai","Singapore","Switzerland","New Zealand",
                     "Mecca","Vatican City","Iceland","Amsterdam"]
    smart_route = None
    if destination not in INTERNATIONAL and not buses and not trains:
        for hub in ["Delhi", "Mumbai", "Ahmedabad"]:
            if Bus.query.filter_by(source=hub, destination=destination).first() or \
               Train.query.filter_by(source=hub, destination=destination).first():
                smart_route = ["Your City", hub, destination]; break
    return jsonify({
        "flights": {"count": len(flights), "min_price": min(flight_prices) if flight_prices else 0, "available": len(flights) > 0},
        "trains":  {"count": len(trains),  "min_price": min(train_prices)  if train_prices  else 0, "available": len(trains)  > 0},
        "buses":   {"count": len(buses),   "min_price": min(bus_prices)    if bus_prices    else 0, "available": len(buses)   > 0},
        "is_international": destination in INTERNATIONAL, "smart_route": smart_route
    })

@app.route("/api/calculate-transport", methods=["POST"])
@login_required
def calculate_transport():
    data = request.json
    hotel_id = data.get("hotel_id"); spot_ids = data.get("spot_ids", [])
    total_days = int(data.get("total_days", 1)); arrival_time = data.get("arrival_time"); departure_time = data.get("departure_time")
    if not hotel_id or not spot_ids: return jsonify([])
    hotel = Hotel.query.get_or_404(hotel_id)
    current_lat = float(hotel.latitude or 0); current_lon = float(hotel.longitude or 0)
    total_dist = 0
    for sid in spot_ids:
        spot = HypeSpot.query.get(int(sid))
        if not spot: continue
        total_dist  += haversine(current_lat, current_lon, float(spot.latitude or 0), float(spot.longitude or 0))
        current_lat = float(spot.latitude or 0); current_lon = float(spot.longitude or 0)
    total_dist += haversine(current_lat, current_lon, float(hotel.latitude or 0), float(hotel.longitude or 0))
    total_dist  = round(total_dist, 2)
    total_hours = 8
    if arrival_time and departure_time:
        t1 = datetime.strptime(arrival_time, "%H:%M"); t2 = datetime.strptime(departure_time, "%H:%M")
        total_hours = round((t2 - t1).seconds / 3600, 2)
    result = []
    for v in Transport.query.all():
        price = round(total_dist * float(v.price_per_km) + 1200 * total_days + total_hours * 100, 2)
        result.append({"vehicle": v.vehicle_name, "type": v.vehicle_type, "ac": v.ac_type,
                        "price": price, "cab_id": v.id, "distance": total_dist, "days": total_days, "hours": total_hours})
    return jsonify(result)

@app.route("/hype-spots/<int:hotel_booking_id>", methods=["GET", "POST"])
@login_required
def hype_spots(hotel_booking_id):
    hotel_booking = HotelBooking.query.get_or_404(hotel_booking_id)
    hotel         = Hotel.query.get_or_404(hotel_booking.hotel_id)
    destination   = Destination.query.get_or_404(hotel.destination_id)
    spots         = HypeSpot.query.filter_by(destination_id=destination.id).all()
    transports    = Transport.query.all()
    total_days    = request.args.get("days", type=int)
    persons       = hotel_booking.persons or session.get("persons", 1)

    for s in spots:
        s.pexels_img = get_pexels_single(f"{s.spot_name} {destination.name}")

    nights = 1
    if hotel_booking.check_in and hotel_booking.check_out:
        nights = max((hotel_booking.check_out - hotel_booking.check_in).days, 1)

    return render_template("hype_spots.html",
        spots=spots, transports=transports,
        destination_name=destination.name,
        hotel_id=hotel.id,
        hotel_booking_id=hotel_booking.id,
        hotel_booking=hotel_booking,
        hotel=hotel,           # FIX: was missing — caused hotel not defined error
        hotel_name=hotel.name,
        total_days=total_days,
        nights=nights,
        persons=persons)

@app.route("/book-cab/<int:hotel_booking_id>", methods=["POST"])
@login_required
def book_cab(hotel_booking_id):
    cab_id     = request.form.get("cab_id")
    total_days = request.form.get("total_days", "1")
    if not cab_id:
        flash("Please select a vehicle.", "danger")
        return redirect(url_for("hype_spots", hotel_booking_id=hotel_booking_id))
    try: total_days = int(total_days)
    except: total_days = 1

    hotel_booking = HotelBooking.query.get_or_404(hotel_booking_id)
    transport     = Transport.query.get_or_404(int(cab_id))
    hotel         = Hotel.query.get_or_404(hotel_booking.hotel_id)

    cab_booking = CabBooking(booking_id=hotel_booking.booking_id, transport_id=transport.id,
                              days=total_days, total_km=0, price=0)
    db.session.add(cab_booking); db.session.commit()

    total_km = 0; total_price = 0

    for day in range(1, total_days + 1):
        arrival    = request.form.get(f"arrival_time_{day}", "09:00")
        departure  = request.form.get(f"departure_time_{day}", "18:00")
        pickup_type= request.form.get(f"pickup_type_{day}", "hotel")
        drop_type  = request.form.get(f"drop_type_{day}",   "hotel")
        custom_pu  = request.form.get(f"custom_pickup_{day}", "").strip()
        custom_dr  = request.form.get(f"custom_drop_{day}", "").strip()
        spot_ids   = request.form.getlist(f"day_{day}_spots")

        cur_lat = float(hotel.latitude or 0); cur_lon = float(hotel.longitude or 0)
        day_km  = 0
        for sid in spot_ids:
            try:
                spot = HypeSpot.query.get(int(sid))
                if not spot: continue
                day_km  += haversine(cur_lat, cur_lon, float(spot.latitude or 0), float(spot.longitude or 0))
                cur_lat = float(spot.latitude or 0); cur_lon = float(spot.longitude or 0)
            except: continue
        day_km += haversine(cur_lat, cur_lon, float(hotel.latitude or 0), float(hotel.longitude or 0))
        day_km  = round(day_km, 2)

        day_price = day_km * float(transport.price_per_km)
        SURCHARGE = {"airport": 350, "railway_station": 200, "bus_stand": 150, "other": 0}
        day_price += SURCHARGE.get(pickup_type, 0) + SURCHARGE.get(drop_type, 0)
        day_price  = round(max(day_price, 500), 2)

        total_km    += day_km
        total_price += day_price

        try:
            arr_t = datetime.strptime(arrival,   "%H:%M").time()
            dep_t = datetime.strptime(departure, "%H:%M").time()
        except:
            from datetime import time as dtime
            arr_t = dtime(9, 0); dep_t = dtime(18, 0)

        booking_day = CabBookingDay(
            cab_booking_id=cab_booking.id, day_number=day,
            arrival_time=arr_t, departure_time=dep_t,
            pickup_type=pickup_type, drop_type=drop_type,
            custom_pickup=custom_pu if pickup_type == "other" else "",
            custom_drop=custom_dr   if drop_type   == "other" else "",
            day_km=day_km, day_price=day_price
        )
        db.session.add(booking_day); db.session.commit()

        for sid in spot_ids:
            try: db.session.add(CabBookingDaySpot(cab_booking_day_id=booking_day.id, spot_id=int(sid)))
            except: pass

    cab_booking.total_km = round(total_km, 2); cab_booking.price = round(total_price, 2)
    db.session.commit()

    session.pop("booking_id", None); session.pop("hotel_booking_id", None); session.pop("persons", None)
    award_points(session.get("user_id", 0), int(total_price // 200), "Cab booking")
    flash(f"Cab booked! {total_days} day(s) · {round(total_km,1)} km · ₹{round(total_price,0):.0f} 🚕 Now pay to confirm.", "success")
    # Redirect to cab payment page
    return redirect(url_for("cab_payment", cab_booking_id=cab_booking.id))


# ── GUIDE / INFO ──

@app.route("/guide/<location>")
def guide(location):
    foods      = HiddenStreetFood.query.filter(func.lower(HiddenStreetFood.location_name) == location.lower()).all()
    safety     = NightSafetyZones.query.filter(func.lower(NightSafetyZones.location_name)  == location.lower()).all()
    etiquettes = LocalEtiquettes.query.filter(func.lower(LocalEtiquettes.location_name)    == location.lower()).all()
    alerts     = TouristAlertsTips.query.filter(func.lower(TouristAlertsTips.location_name)== location.lower()).all()
    essentials = LocationEssentials.query.filter(func.lower(LocationEssentials.location_name) == location.lower()).first()
    return render_template("information.html", location=location, foods=foods, safety=safety,
        etiquettes=etiquettes, alerts=alerts, essentials=essentials)

@app.route("/culture/<location>")
def culture_page(location):
    return redirect(url_for("guide", location=location))


# ── AI TRIP PLANNER ──

@app.route("/trip-planner")
def trip_planner():
    return render_template("trip_planner.html")

@app.route("/api/ai-trip-plan", methods=["POST"])
def ai_trip_plan():
    data  = request.json
    query = data.get("query", "").strip()
    if not query: return jsonify({"plan": "Please enter a trip query."})
    all_dests  = Destination.query.filter_by(is_active=True).all()
    dest_names = [d.name for d in all_dests]
    found_dest = next((name for name in dest_names if name.lower() in query.lower()), None)
    matching_hotels, matching_flights = [], []
    if found_dest:
        dest_obj = Destination.query.filter_by(name=found_dest).first()
        if dest_obj:
            for h in Hotel.query.filter_by(destination_id=dest_obj.id).order_by(Hotel.starting_price).limit(5).all():
                prices = [r.base_price for r in h.rooms if r.base_price]
                avail  = sum(((r.total_rooms or 0) - (r.booked_rooms or 0)) for r in h.rooms)
                matching_hotels.append({"id": h.id, "name": h.name, "stars": h.stars, "price": min(prices) if prices else 0, "rooms": avail})
            for f in Flight.query.filter_by(destination=found_dest).order_by(Flight.price).limit(3).all():
                matching_flights.append({"airline": f.airline, "price": f.price, "source": f.source, "flight_class": f.flight_class})
    budget = None; q_lower = query.lower().replace(",", "")
    lakh_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|l\b)', q_lower)
    if lakh_m: budget = int(float(lakh_m.group(1)) * 100000)
    else:
        k_m = re.search(r'(\d+(?:\.\d+)?)\s*k\b', q_lower)
        if k_m: budget = int(float(k_m.group(1)) * 1000)
        else:
            plain_m = re.search(r'(?:under|below|within|₹|rs\.?|budget[:\s]+)\s*(\d{4,})', q_lower)
            if plain_m: budget = int(plain_m.group(1))
    system_prompt = """You are TripMoree's expert AI trip planner for India. All amounts in INDIAN RUPEES.
Respond ONLY with valid JSON:
{"plan":"Day-by-day itinerary with \\n line breaks","destination":"name","budget":{"Hotel (per night)":"₹2500","Transport":"₹3000","Food (per day)":"₹800","Activities":"₹1500","Miscellaneous":"₹500","total":"₹15000"},"tips":["tip1","tip2","tip3"]}"""
    days_match = re.search(r'(\d+)\s*(?:day|night)', q_lower)
    est_days   = int(days_match.group(1)) if days_match else 3
    user_msg   = f"Plan: {query}\nDestinations: {', '.join(dest_names[:20])}\n{'Budget: ₹'+str(budget)+' INR' if budget else ''}\nDays: {est_days}\n{'Found: '+found_dest if found_dest else ''}"
    try:
        resp = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1200, "system": system_prompt, "messages": [{"role": "user", "content": user_msg}]},
            timeout=25)
        raw = resp.json()["content"][0]["text"].strip()
        if "```" in raw: raw = re.sub(r'```(?:json)?', '', raw).strip().rstrip('`').strip()
        result = json.loads(raw)
    except Exception as e:
        print(f"AI Plan error: {e}")
        b = budget or 15000; d = est_days or 3
        result = {
            "plan": f"🌟 Trip Plan: {query}\n\nDay 1: Arrival & Check-in\n• Arrive and check into hotel\n• Evening walk at local market\n\nDay 2: Sightseeing\n• Morning: Top landmarks\n• Afternoon: Local bazaar & street food\n\nDay 3: Adventure & Departure\n• Morning: Nature spots\n• Afternoon: Shopping & departure",
            "destination": found_dest or "Your destination",
            "budget": {"Hotel (per night)": f"₹{max(b//(d*3),1500):,}", "Transport": f"₹{max(b//5,2000):,}",
                       "Food (per day)": f"₹{max(b//(d*6),600):,}", "Activities": f"₹{max(b//(d*8),500):,}",
                       "Miscellaneous": "₹500", "total": f"₹{b:,}"},
            "tips": ["Book hotels 2–3 weeks in advance", "Carry cash for street food", "Download offline maps"]
        }
    result["hotels"] = matching_hotels[:4]; result["flights"] = matching_flights[:3]
    return jsonify(result)


# ── COMMUNITY ──

@app.route("/community")
def community():
    reviews_raw = db.session.query(Review, User.name.label("user_name")).join(
        User, Review.user_id == User.id, isouter=True
    ).order_by(Review.created_at.desc()).limit(20).all()
    reviews = [{"destination": r.destination, "rating": r.rating, "comment": r.comment,
                "created_at": r.created_at, "user_name": uname or "Traveller"}
               for r, uname in reviews_raw]
    photos = CommunityPhoto.query.order_by(CommunityPhoto.created_at.desc()).limit(12).all()
    trending = db.session.query(BookingHistory.destination, func.count(BookingHistory.id).label("cnt")).group_by(BookingHistory.destination).order_by(func.count(BookingHistory.id).desc()).limit(8).all()
    top_reviewers_raw = db.session.query(User.name, func.count(Review.id).label("review_count")).join(Review, User.id == Review.user_id, isouter=True).group_by(User.id).order_by(func.count(Review.id).desc()).limit(5).all()
    top_reviewers = []
    for name, rc in top_reviewers_raw:
        u = User.query.filter_by(name=name).first()
        trip_count = BookingHistory.query.filter_by(user_id=u.id).count() if u else 0
        top_reviewers.append({"name": name, "review_count": rc, "trip_count": trip_count})
    visited_destinations = []
    if "user_id" in session:
        bookings = BookingHistory.query.filter_by(user_id=session["user_id"]).all()
        visited_destinations = list({b.destination for b in bookings})
    return render_template("community.html",
        reviews=reviews, photos=photos, trending=trending, top_reviewers=top_reviewers,
        visited_destinations=visited_destinations,
        all_destinations=Destination.query.filter_by(is_active=True).all(),
        total_reviews=Review.query.count(), total_photos=CommunityPhoto.query.count(),
        total_users=User.query.count(), total_destinations=Destination.query.filter_by(is_active=True).count(),
        enumerate=enumerate)

@app.route("/upload-community-photo", methods=["POST"])
@login_required
def upload_community_photo():
    import base64
    photos      = request.files.getlist("photos")
    destination = request.form.get("destination", "")
    caption     = request.form.get("caption", "")
    for photo in photos:
        if photo and photo.filename:
            ext = photo.filename.rsplit('.', 1)[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']: continue
            data     = photo.read()
            b64      = base64.b64encode(data).decode()
            data_url = f"data:image/{ext};base64,{b64}"
            db.session.add(CommunityPhoto(user_id=session["user_id"], destination=destination, image_url=data_url, caption=caption))
    db.session.commit()
    award_points(session["user_id"], 10, "Shared community photo")
    flash("Photos shared! +10 loyalty points 📸", "success")
    return redirect(url_for("community"))

@app.route("/api/community-photo/like/<int:photo_id>", methods=["POST"])
@login_required
def like_community_photo(photo_id):
    photo = CommunityPhoto.query.get_or_404(photo_id)
    photo.likes = (photo.likes or 0) + 1
    db.session.commit()
    return jsonify({"likes": photo.likes})


# ── EXPERIENCES ──

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


# ── FLASH SALES ──

@app.route("/flash-sales")
def flash_sales_page():
    now   = datetime.now()
    sales = FlashSale.query.filter(FlashSale.is_active == True, FlashSale.starts_at <= now, FlashSale.ends_at >= now).order_by(FlashSale.ends_at).all()
    for s in sales:
        if s.destination_id:
            d = Destination.query.get(s.destination_id)
            s.dest_img = d.image if (d and d.image and d.image.startswith("http")) else get_pexels_single(d.name if d else "travel")
        else: s.dest_img = ""
    return render_template("flash_sales.html", sales=sales)

@app.route("/api/flash-sales")
def api_flash_sales():
    now   = datetime.now()
    sales = FlashSale.query.filter(FlashSale.is_active == True, FlashSale.starts_at <= now, FlashSale.ends_at >= now).all()
    return jsonify([{"id": s.id, "title": s.title, "discount_pct": s.discount_pct, "ends_at": s.ends_at.isoformat(), "banner_color": s.banner_color} for s in sales])


# ── MISC ──

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/gallery")
def gallery():
    # Show community photos + pexels fallback
    photos = CommunityPhoto.query.order_by(CommunityPhoto.created_at.desc()).limit(24).all()
    photo_data = []
    for p in photos:
        user = User.query.get(p.user_id)
        photo_data.append({
            "url": p.image_url,
            "destination": p.destination,
            "caption": p.caption,
            "user_name": user.name if user else "Traveller",
            "likes": p.likes or 0,
            "id": p.id
        })
    return render_template("gallery.html", photos=photo_data)

@app.route("/coming-soon")
def coming_soon():
    return "<h2 style='text-align:center;margin-top:100px;font-family:Arial;'>Coming Soon!</h2>"

@app.route("/api/pexels-image")
def pexels_image():
    query = request.args.get("q", "hotel room"); page = int(request.args.get("page", 1))
    try:
        resp   = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 1, "page": page, "orientation": "landscape"}, timeout=5)
        photos = resp.json().get("photos", [])
        url    = photos[0]["src"]["large"] if photos else ""
    except: url = ""
    return jsonify({"url": url})

@app.route("/book-train/<int:id>")
@login_required
def book_train(id):
    t = Train.query.get(id)
    db.session.add(TransportBooking(booking_id=session["booking_id"], transport_type="train",
        source=t.source, destination=t.destination, persons=session.get("persons", 1), price=t.price))
    db.session.commit()
    return redirect(url_for("my_bookings"))

@app.route("/book-flight/<int:id>")
@login_required
def book_flight(id):
    f = Flight.query.get(id)
    db.session.add(TransportBooking(booking_id=session["booking_id"], transport_type="flight",
        source=f.source, destination=f.destination, persons=session.get("persons", 1), price=f.price))
    db.session.commit()
    return redirect(url_for("my_bookings"))


# ── INVOICE ──

@app.route("/download-invoice/<int:booking_id>")
@login_required
def download_invoice(booking_id):
    booking = BookingHistory.query.get_or_404(booking_id)
    if booking.user_id != session["user_id"]: return "Unauthorized", 403
    pdf_path = generate_invoice_pdf(booking_id)
    return send_file(pdf_path, as_attachment=True,
                     download_name=f"TripMoree_Invoice_{booking_id}.pdf",
                     mimetype="application/pdf")

@app.route("/send-invoice/<int:booking_id>")
@login_required
def send_invoice_email(booking_id):
    booking = BookingHistory.query.get_or_404(booking_id)
    if booking.user_id != session["user_id"]: return "Unauthorized", 403
    user      = User.query.get(session["user_id"])
    file_path = generate_invoice_pdf(booking_id)
    success   = send_email(user.email, f"TripMoree — Invoice #{booking_id} 📄",
                           f"Hi {user.name},\n\nThank you for booking with TripMoree! Your invoice is attached.\n\nHappy Travelling! 🌍\nTripMoree Team",
                           attachment_path=file_path)
    try: os.remove(file_path)
    except: pass
    return jsonify({"success": success, "message": "Invoice sent to your email! 📧" if success else "Failed to send email."})


def generate_invoice_pdf(booking_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable)
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

    booking        = BookingHistory.query.get_or_404(booking_id)
    hotel_booking  = HotelBooking.query.filter_by(booking_id=booking.id).first()
    cab            = CabBooking.query.filter_by(booking_id=booking.id).first()
    transport_list = TransportBooking.query.filter_by(booking_id=booking.id).all()
    file_path      = f"invoice_{booking_id}.pdf"

    BRAND_DARK    = colors.HexColor("#1a1a2e")
    BRAND_PRIMARY = colors.HexColor("#e94560")
    BRAND_ACCENT  = colors.HexColor("#0f3460")
    BRAND_LIGHT   = colors.HexColor("#f5f5f5")
    TEXT_DARK     = colors.HexColor("#2d2d2d")
    TEXT_MUTED    = colors.HexColor("#666666")
    SUCCESS       = colors.HexColor("#27ae60")
    WARNING       = colors.HexColor("#e67e22")

    doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()
    def sty(name, **kw): return ParagraphStyle(name, parent=styles["Normal"], **kw)

    S_WHITE_BIG = sty("wb",  fontSize=26, textColor=colors.white, fontName="Helvetica-Bold", leading=30)
    S_SECTION   = sty("sec", fontSize=11, textColor=BRAND_ACCENT, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=8)
    S_LABEL     = sty("lbl", fontSize=8.5, textColor=TEXT_MUTED)
    S_VALUE     = sty("val", fontSize=9,   textColor=TEXT_DARK,   fontName="Helvetica-Bold")
    S_TOTAL_LBL = sty("tl",  fontSize=12,  textColor=colors.white, fontName="Helvetica-Bold")
    S_TOTAL_VAL = sty("tv",  fontSize=14,  textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_RIGHT)
    S_FOOTER    = sty("ft",  fontSize=7.5, textColor=TEXT_MUTED,  alignment=TA_CENTER)
    S_TAG       = sty("tag", fontSize=8,   textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)

    elements = []

    # HEADER
    header_data = [[
        Paragraph("<b>TripMoree</b>", S_WHITE_BIG),
        Paragraph(f"<b>INVOICE</b><br/><font color='#aaaaaa'>#{str(booking_id).zfill(6)}</font>",
                  sty("ih", fontSize=18, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_RIGHT, leading=22))
    ]]
    header_tbl = Table(header_data, colWidths=[doc.width*0.6, doc.width*0.4])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),BRAND_DARK), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(0,-1),16), ("RIGHTPADDING",(-1,0),(-1,-1),16),
        ("TOPPADDING",(0,0),(-1,-1),14), ("BOTTOMPADDING",(0,0),(-1,-1),14),
    ]))
    elements.append(header_tbl)

    pay_status   = hotel_booking.payment_status if hotel_booking else "pending"
    status_color = SUCCESS if pay_status == "paid" else (WARNING if pay_status == "demo" else colors.HexColor("#e74c3c"))
    sub_data = [[
        Paragraph("TripMoree Travel Pvt Ltd<br/><font color='#888888'>Surat, Gujarat, India · +91 99250 92253<br/>support@tripmoree.in · www.tripmoree.in</font>",
                  sty("sd", fontSize=8, textColor=TEXT_DARK, leading=12)),
        Table([[Paragraph(pay_status.upper(), S_TAG)]], colWidths=[70], rowHeights=[18],
              style=TableStyle([("BACKGROUND",(0,0),(-1,-1),status_color),("ROUNDEDCORNERS",[9,9,9,9]),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    ]]
    sub_tbl = Table(sub_data, colWidths=[doc.width*0.65, doc.width*0.35])
    sub_tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),BRAND_LIGHT), ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(0,-1),14), ("RIGHTPADDING",(-1,0),(-1,-1),14), ("VALIGN",(0,0),(-1,-1),"MIDDLE"), ("ALIGN",(1,0),(1,-1),"RIGHT"),
    ]))
    elements.append(sub_tbl)
    elements.append(Spacer(1, 4*mm))

    inv_date   = datetime.now().strftime("%d %b %Y")
    meta_items = [("Invoice Date", inv_date), ("Invoice No.", f"#{str(booking_id).zfill(6)}"),
                  ("Destination", booking.destination), ("Status", booking.status.capitalize())]
    meta_cells = [[Paragraph(k, S_LABEL), Paragraph(v, S_VALUE)] for k, v in meta_items]
    meta_tbl   = Table([[Table([mc], colWidths=[55, 85], style=TableStyle([("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)])) for mc in meta_cells]], colWidths=[doc.width/4]*4)
    meta_tbl.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e0e0e0")),("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e0e0e0")),("BACKGROUND",(0,0),(-1,-1),colors.white),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),("LEFTPADDING",(0,0),(-1,-1),8)]))
    elements.append(meta_tbl)
    elements.append(Spacer(1, 5*mm))

    if hotel_booking:
        elements.append(Paragraph("👤  Guest Information", S_SECTION))
        guest_data = [
            [Paragraph("Full Name", S_LABEL), Paragraph(hotel_booking.name or "—", S_VALUE), Paragraph("Email", S_LABEL), Paragraph(hotel_booking.email or "—", S_VALUE)],
            [Paragraph("Phone",     S_LABEL), Paragraph(hotel_booking.phone or "—", S_VALUE), Paragraph("ID Proof", S_LABEL), Paragraph(f"{(hotel_booking.id_type or '').upper()}: {hotel_booking.id_number or '—'}", S_VALUE)],
        ]
        g_tbl = Table(guest_data, colWidths=[doc.width*0.12, doc.width*0.35, doc.width*0.12, doc.width*0.38])
        g_tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.white),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e0e0e0")),("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#f0f0f0")),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),("LEFTPADDING",(0,0),(-1,-1),8)]))
        elements.append(g_tbl)
        elements.append(Spacer(1, 4*mm))

    total_amount = 0

    if hotel_booking:
        hotel = Hotel.query.get(hotel_booking.hotel_id)
        room  = Room.query.get(hotel_booking.room_id)
        elements.append(Paragraph("🏨  Hotel Booking", S_SECTION))
        nights = 1
        if hotel_booking.check_in and hotel_booking.check_out:
            nights = max((hotel_booking.check_out - hotel_booking.check_in).days, 1)
        room_num  = random.randint(100, 999)
        h_header  = [[Paragraph(t, sty("hh", fontSize=8.5, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)) for t in ["Hotel","Room Type","Room No.","Check-In","Check-Out","Nights","Guests"]]]
        h_data    = [[Paragraph(hotel.name if hotel else "—", sty("hc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                      Paragraph(room.room_type if room else "—", sty("hc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                      Paragraph(str(room_num), sty("hc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                      Paragraph(str(hotel_booking.check_in), sty("hc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                      Paragraph(str(hotel_booking.check_out), sty("hc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                      Paragraph(str(nights), sty("hc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                      Paragraph(str(hotel_booking.persons), sty("hc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK))]]
        h_tbl = Table(h_header + h_data, colWidths=[doc.width/7]*7)
        h_tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),BRAND_ACCENT),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f9f9f9")]),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#cccccc")),("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e0e0e0")),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        elements.append(h_tbl)
        elements.append(Spacer(1, 3*mm))

        price_rows = [
            [Paragraph("Room charges (base)", S_LABEL), Paragraph(f"₹{hotel_booking.base_price or 0:,}", sty("pr",fontSize=9,textColor=TEXT_DARK,alignment=TA_RIGHT))],
            [Paragraph("Meals & extras", S_LABEL), Paragraph(f"₹{hotel_booking.extra_price or 0:,}", sty("pr",fontSize=9,textColor=TEXT_DARK,alignment=TA_RIGHT))],
        ]
        if hotel_booking.insurance_price:
            price_rows.append([Paragraph("Travel insurance", S_LABEL), Paragraph(f"₹{hotel_booking.insurance_price:,}", sty("pr",fontSize=9,textColor=TEXT_DARK,alignment=TA_RIGHT))])
        if hotel_booking.coupon_discount:
            price_rows.append([Paragraph(f"Coupon ({hotel_booking.coupon_code})", sty("dis",fontSize=8.5,textColor=SUCCESS)), Paragraph(f"−₹{hotel_booking.coupon_discount:,}", sty("pr",fontSize=9,textColor=SUCCESS,alignment=TA_RIGHT))])
        if hotel_booking.bank_discount:
            price_rows.append([Paragraph(f"Bank offer ({(hotel_booking.bank_name or '').upper()})", sty("dis",fontSize=8.5,textColor=SUCCESS)), Paragraph(f"−₹{hotel_booking.bank_discount:,}", sty("pr",fontSize=9,textColor=SUCCESS,alignment=TA_RIGHT))])
        if hotel_booking.loyalty_discount:
            price_rows.append([Paragraph("Loyalty points", sty("dis",fontSize=8.5,textColor=SUCCESS)), Paragraph(f"−₹{hotel_booking.loyalty_discount:,}", sty("pr",fontSize=9,textColor=SUCCESS,alignment=TA_RIGHT))])
        p_tbl = Table(price_rows, colWidths=[doc.width*0.7, doc.width*0.28])
        p_tbl.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(0,-1),10),("RIGHTPADDING",(-1,0),(-1,-1),6),("LINEBELOW",(0,0),(-1,-2),0.3,colors.HexColor("#e8e8e8"))]))
        elements.append(p_tbl)
        hotel_total = hotel_booking.final_payable or 0
        total_amount += hotel_total
        sub_row = Table([[Paragraph("<b>Hotel Subtotal</b>", sty("hs",fontSize=9.5,textColor=BRAND_ACCENT,fontName="Helvetica-Bold")), Paragraph(f"<b>₹{hotel_total:,}</b>", sty("hs2",fontSize=9.5,textColor=BRAND_ACCENT,fontName="Helvetica-Bold",alignment=TA_RIGHT))]], colWidths=[doc.width*0.7, doc.width*0.28])
        sub_row.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#eef2ff")),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(0,-1),10),("RIGHTPADDING",(-1,0),(-1,-1),6)]))
        elements.append(sub_row)
        elements.append(Spacer(1, 4*mm))

    if transport_list:
        elements.append(Paragraph("✈️  Transport Bookings", S_SECTION))
        t_header = [[Paragraph(t, sty("th",fontSize=8.5,textColor=colors.white,fontName="Helvetica-Bold",alignment=TA_CENTER)) for t in ["Mode","From","To","Passengers","Amount"]]]
        t_rows = []
        for tb in transport_list:
            icon = {"flight":"✈️","train":"🚆","bus":"🚌"}.get(tb.transport_type,"🚗")
            t_rows.append([
                Paragraph(f"{icon} {tb.transport_type.capitalize()}", sty("tc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                Paragraph(tb.source or "—",      sty("tc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                Paragraph(tb.destination or "—", sty("tc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                Paragraph(str(tb.persons or 1),  sty("tc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                Paragraph(f"₹{tb.price or 0:,}", sty("tc",fontSize=8.5,alignment=TA_CENTER,textColor=TEXT_DARK,fontName="Helvetica-Bold")),
            ])
            total_amount += tb.price or 0
        t_tbl = Table(t_header + t_rows, colWidths=[doc.width*0.15,doc.width*0.2,doc.width*0.2,doc.width*0.15,doc.width*0.28])
        t_tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),BRAND_PRIMARY),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#fff5f5")]),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#cccccc")),("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e0e0e0")),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        elements.append(t_tbl)
        elements.append(Spacer(1, 4*mm))

    if cab:
        vehicle = Transport.query.get(cab.transport_id)
        elements.append(Paragraph("🚗  Local Cab / Sightseeing", S_SECTION))
        cab_info = [
            [Paragraph("Vehicle",S_LABEL),Paragraph(vehicle.vehicle_name if vehicle else "—",S_VALUE),Paragraph("Type",S_LABEL),Paragraph(vehicle.vehicle_type if vehicle else "—",S_VALUE),Paragraph("AC",S_LABEL),Paragraph(vehicle.ac_type if vehicle else "—",S_VALUE)],
            [Paragraph("Total KM",S_LABEL),Paragraph(f"{cab.total_km or 0} km",S_VALUE),Paragraph("Days",S_LABEL),Paragraph(str(cab.days or 1),S_VALUE),Paragraph("Amount",S_LABEL),Paragraph(f"₹{int(cab.price or 0):,}",sty("ca",fontSize=9,textColor=BRAND_PRIMARY,fontName="Helvetica-Bold"))],
        ]
        c_tbl = Table(cab_info, colWidths=[doc.width*0.1,doc.width*0.22,doc.width*0.1,doc.width*0.16,doc.width*0.1,doc.width*0.28])
        c_tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.white),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e0e0e0")),("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#f0f0f0")),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),("LEFTPADDING",(0,0),(-1,-1),8)]))
        elements.append(c_tbl)
        cab_days = CabBookingDay.query.filter_by(cab_booking_id=cab.id).order_by(CabBookingDay.day_number).all()
        if cab_days:
            elements.append(Spacer(1, 2*mm))
            day_rows = [[Paragraph(t, sty("dh",fontSize=8,textColor=colors.white,fontName="Helvetica-Bold",alignment=TA_CENTER)) for t in ["Day","Arrival","Depart","Pickup","Drop","Spots","KM","Amount"]]]
            for d in cab_days:
                spots_rel  = CabBookingDaySpot.query.filter_by(cab_booking_day_id=d.id).all()
                spot_names = ", ".join(HypeSpot.query.get(s.spot_id).spot_name for s in spots_rel if HypeSpot.query.get(s.spot_id)) or "—"
                day_rows.append([
                    Paragraph(str(d.day_number), sty("dc",fontSize=7.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                    Paragraph(str(d.arrival_time)[:5] if d.arrival_time else "—",    sty("dc",fontSize=7.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                    Paragraph(str(d.departure_time)[:5] if d.departure_time else "—",sty("dc",fontSize=7.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                    Paragraph(d.pickup_type or "hotel", sty("dc",fontSize=7.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                    Paragraph(d.drop_type   or "hotel", sty("dc",fontSize=7.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                    Paragraph(spot_names[:40],           sty("dc",fontSize=7,  alignment=TA_LEFT,  textColor=TEXT_DARK)),
                    Paragraph(f"{d.day_km or 0:.1f}",   sty("dc",fontSize=7.5,alignment=TA_CENTER,textColor=TEXT_DARK)),
                    Paragraph(f"₹{int(d.day_price or 0):,}", sty("dc",fontSize=7.5,alignment=TA_CENTER,textColor=TEXT_DARK,fontName="Helvetica-Bold")),
                ])
            d_tbl = Table(day_rows, colWidths=[doc.width*0.06,doc.width*0.09,doc.width*0.09,doc.width*0.1,doc.width*0.1,doc.width*0.3,doc.width*0.1,doc.width*0.14])
            d_tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),BRAND_DARK),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8f8f8")]),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#cccccc")),("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e0e0e0")),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
            elements.append(d_tbl)
        total_amount += int(cab.price or 0)
        elements.append(Spacer(1, 4*mm))

    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    elements.append(Spacer(1, 3*mm))
    total_tbl = Table([[Paragraph("💳  GRAND TOTAL", S_TOTAL_LBL), Paragraph(f"₹{total_amount:,}", S_TOTAL_VAL)]], colWidths=[doc.width*0.6, doc.width*0.38])
    total_tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14),("LEFTPADDING",(0,0),(0,-1),16),("RIGHTPADDING",(-1,0),(-1,-1),16),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(1,0),(1,-1),"RIGHT")]))
    elements.append(total_tbl)
    elements.append(Spacer(1, 5*mm))

    terms = [
        "• This is a computer-generated invoice. No physical signature required.",
        "• Cancellation: Free cancellation 48 hrs before check-in. 50% charge within 48 hrs.",
        "• Support: support@tripmoree.in  |  +91 99250 92253  |  Available 24×7",
        "• All prices are inclusive of applicable taxes unless stated otherwise.",
    ]
    for t in terms:
        elements.append(Paragraph(t, sty("tm", fontSize=7.5, textColor=TEXT_MUTED, leading=11)))
    elements.append(Spacer(1, 4*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("Thank you for choosing <b>TripMoree</b> — India's most loved travel platform. Happy travelling! 🌍",
                               sty("ty", fontSize=8.5, textColor=BRAND_ACCENT, alignment=TA_CENTER, fontName="Helvetica-Bold")))
    elements.append(Spacer(1, 1*mm))
    elements.append(Paragraph("© 2025 TripMoree Travel Pvt Ltd · Surat, Gujarat, India", S_FOOTER))

    doc.build(elements)
    return file_path


# ── BUS PAYMENT ───────────────────────────────────────────────

@app.route("/bus-payment/<int:transport_booking_id>")
@login_required
def bus_payment(transport_booking_id):
    tb           = TransportBooking.query.get_or_404(transport_booking_id)
    main_booking = BookingHistory.query.get(tb.booking_id)
    hb           = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    if main_booking.user_id != session["user_id"]:
        return redirect(url_for("home"))
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={tb.price}&cu=INR&tn=TripMoree+Bus+{transport_booking_id}"
    return render_template("bus_payment.html",
        tb=tb, main_booking=main_booking, hb=hb,
        upi_id=UPI_ID, upi_name=UPI_NAME, upi_link=upi_link,
        hotel_booking_id=hb.id if hb else 0)

@app.route("/bus-payment/confirm/<int:transport_booking_id>", methods=["POST"])
@login_required
def confirm_bus_payment(transport_booking_id):
    tb  = TransportBooking.query.get_or_404(transport_booking_id)
    hb  = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    upi_ref = request.form.get("upi_ref", "").strip()
    flash(f"Bus payment confirmed! 🚌 ₹{tb.price:,} paid. Ref: {upi_ref}", "success")
    if hb:
        return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
    return redirect(url_for("my_bookings"))

@app.route("/bus-payment/skip/<int:transport_booking_id>")
@login_required
def skip_bus_payment(transport_booking_id):
    tb = TransportBooking.query.get_or_404(transport_booking_id)
    hb = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    flash("Bus payment skipped (Demo mode).", "info")
    if hb:
        return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
    return redirect(url_for("my_bookings"))


# ── TRAIN PAYMENT ─────────────────────────────────────────────

@app.route("/train-payment/<int:transport_booking_id>")
@login_required
def train_payment(transport_booking_id):
    tb           = TransportBooking.query.get_or_404(transport_booking_id)
    main_booking = BookingHistory.query.get(tb.booking_id)
    hb           = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    if main_booking.user_id != session["user_id"]:
        return redirect(url_for("home"))
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={tb.price}&cu=INR&tn=TripMoree+Train+{transport_booking_id}"
    return render_template("train_payment.html",
        tb=tb, main_booking=main_booking, hb=hb,
        upi_id=UPI_ID, upi_name=UPI_NAME, upi_link=upi_link,
        hotel_booking_id=hb.id if hb else 0)

@app.route("/train-payment/confirm/<int:transport_booking_id>", methods=["POST"])
@login_required
def confirm_train_payment(transport_booking_id):
    tb  = TransportBooking.query.get_or_404(transport_booking_id)
    hb  = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    upi_ref = request.form.get("upi_ref", "").strip()
    flash(f"Train payment confirmed! 🚆 ₹{tb.price:,} paid. Ref: {upi_ref}", "success")
    if hb:
        return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
    return redirect(url_for("my_bookings"))

@app.route("/train-payment/skip/<int:transport_booking_id>")
@login_required
def skip_train_payment(transport_booking_id):
    tb = TransportBooking.query.get_or_404(transport_booking_id)
    hb = HotelBooking.query.filter_by(booking_id=tb.booking_id).first()
    flash("Train payment skipped (Demo mode).", "info")
    if hb:
        return redirect(url_for("hype_spots", hotel_booking_id=hb.id))
    return redirect(url_for("my_bookings"))


# ── CAB PAYMENT ───────────────────────────────────────────────

@app.route("/cab-payment/<int:cab_booking_id>")
@login_required
def cab_payment(cab_booking_id):
    cab          = CabBooking.query.get_or_404(cab_booking_id)
    main_booking = BookingHistory.query.get(cab.booking_id)
    hb           = HotelBooking.query.filter_by(booking_id=cab.booking_id).first()
    vehicle      = Transport.query.get(cab.transport_id)
    if main_booking.user_id != session["user_id"]:
        return redirect(url_for("home"))
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={int(cab.price)}&cu=INR&tn=TripMoree+Cab+{cab_booking_id}"
    return render_template("cab_payment.html",
        cab=cab, main_booking=main_booking, hb=hb, vehicle=vehicle,
        upi_id=UPI_ID, upi_name=UPI_NAME, upi_link=upi_link)

@app.route("/cab-payment/confirm/<int:cab_booking_id>", methods=["POST"])
@login_required
def confirm_cab_payment(cab_booking_id):
    cab     = CabBooking.query.get_or_404(cab_booking_id)
    upi_ref = request.form.get("upi_ref", "").strip()
    flash(f"Cab payment confirmed! 🚕 ₹{int(cab.price):,} paid. Ref: {upi_ref}", "success")
    return redirect(url_for("my_bookings"))

@app.route("/cab-payment/skip/<int:cab_booking_id>")
@login_required
def skip_cab_payment(cab_booking_id):
    flash("Cab payment skipped (Demo mode).", "info")
    return redirect(url_for("my_bookings"))


# ── INFORMATION / TRAVEL GUIDE PAGE ──────────────────────────
# Accessible from: navbar, destination detail, my_bookings, hype_spots
# URL: /info/<destination_name>  OR  /guide/<location> (existing alias)

@app.route("/info/<location>")
def information_page(location):
    """Travel guide & essentials for a destination — shown after booking and in navbar."""
    dest       = Destination.query.filter(func.lower(Destination.name) == location.lower()).first()
    foods      = HiddenStreetFood.query.filter(func.lower(HiddenStreetFood.location_name) == location.lower()).all()
    safety     = NightSafetyZones.query.filter(func.lower(NightSafetyZones.location_name) == location.lower()).all()
    etiquettes = LocalEtiquettes.query.filter(func.lower(LocalEtiquettes.location_name) == location.lower()).all()
    alerts     = TouristAlertsTips.query.filter(func.lower(TouristAlertsTips.location_name) == location.lower()).all()
    essentials = LocationEssentials.query.filter(func.lower(LocationEssentials.location_name) == location.lower()).first()
    spots      = HypeSpot.query.filter_by(destination_id=dest.id).all() if dest else []
    for s in spots:
        s.pexels_img = get_pexels_single(f"{s.spot_name} {location}")
    dest_img   = ""
    if dest:
        dest_img = dest.image if (dest.image and dest.image.startswith("http")) else get_pexels_single(location + " travel")
    return render_template("information.html",
        location=location, dest=dest, dest_img=dest_img,
        foods=foods, safety=safety, etiquettes=etiquettes,
        alerts=alerts, essentials=essentials, spots=spots)

@app.route("/destinations-guide")
def destinations_guide():
    """List of all destinations with guide links — shown in navbar as 'Travel Guide'."""
    dests = Destination.query.filter_by(is_active=True).order_by(Destination.name).all()
    for d in dests:
        d.pexels_img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name + " travel")
    return render_template("destinations_guide.html", destinations=dests)


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)