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

app = Flask(__name__)
app.secret_key = "tripmoreee"

# ================= MYSQL CONFIG =================
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root@127.0.0.1:3306/tripmoree"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= API KEYS =================
PEXELS_API_KEY    = "2FXZxN3XYCGsDWAxbHlezqynJMbac58HaXbevYpyGWq02Ba727W3tY7M"
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"  # https://console.anthropic.com
UPI_ID            = "9925092253@fam"
UPI_NAME          = "TripMore Travel"

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
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100))
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    phone      = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Destination(db.Model):
    __tablename__ = "destination"
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), unique=True)
    country_type = db.Column(db.String(50))
    category     = db.Column(db.String(50))
    vacation_type= db.Column(db.String(50))
    image        = db.Column(db.String(500))
    rating       = db.Column(db.Float)
    best_time    = db.Column(db.String(50))
    latitude     = db.Column(db.Float)
    longitude    = db.Column(db.Float)

hotel_amenities = db.Table(
    "hotel_amenities",
    db.Column("hotel_id",  db.Integer, db.ForeignKey("hotel.id")),
    db.Column("amenity_id",db.Integer, db.ForeignKey("amenity.id"))
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
        return self.total_rooms - self.booked_rooms

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
    final_payable   = db.Column(db.Integer)
    payment_status  = db.Column(db.String(20), default="pending")
    upi_ref         = db.Column(db.String(100))
    created_at      = db.Column(db.DateTime)

class Coupon(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    code             = db.Column(db.String(50), unique=True)
    discount_percent = db.Column(db.Integer)
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

# ── NEW MODELS ──
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


# ================= HELPERS =================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))


def get_pexels_images(query, count=4):
    """Return list of image URLs from Pexels for a query."""
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


# ================= ROUTES =================

# ── ADMIN ──
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
    return redirect(url_for("admin_users"))

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
def admin_dashboard():
    if "admin_id" not in session:
        return redirect("/admin/login")
    total_users    = User.query.count()
    total_hotels   = Hotel.query.count()
    total_bookings = BookingHistory.query.count()
    hotel_rev  = db.session.query(func.sum(HotelBooking.final_payable)).scalar() or 0
    trans_rev  = db.session.query(func.sum(TransportBooking.price)).scalar() or 0
    cab_rev    = db.session.query(func.sum(CabBooking.price)).scalar() or 0
    total_revenue = hotel_rev + trans_rev + cab_rev
    active    = BookingHistory.query.filter_by(status="active").count()
    completed = BookingHistory.query.filter_by(status="completed").count()
    top_destinations = db.session.query(
        BookingHistory.destination, func.count(BookingHistory.id)
    ).group_by(BookingHistory.destination).all()
    return render_template("admin_dashboard.html",
        users=total_users, hotels=total_hotels, bookings=total_bookings,
        revenue=total_revenue, active=active, completed=completed,
        top_destinations=top_destinations)


# ── HOME ──
@app.route("/")
def home():
    featured = Destination.query.order_by(Destination.rating.desc()).limit(6).all()

    # Attach Pexels images to destinations that don't have one
    for d in featured:
        if not d.image or not d.image.startswith("http"):
            d.pexels_img = get_pexels_single(d.name + " destination")
        else:
            d.pexels_img = d.image

    total_bookings     = BookingHistory.query.count()
    total_users        = User.query.count()
    total_destinations = Destination.query.count()

    popular_raw = db.session.query(
        BookingHistory.destination,
        func.count(BookingHistory.id).label("cnt")
    ).group_by(BookingHistory.destination).order_by(
        func.count(BookingHistory.id).desc()
    ).limit(4).all()

    popular_dests = []
    for row in popular_raw:
        d = Destination.query.filter_by(name=row.destination).first()
        if d:
            img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name)
            popular_dests.append({"dest": d, "bookings": row.cnt, "img": img})

    wishlist_ids = []
    if "user_id" in session:
        wishlist_ids = [w.destination_id for w in Wishlist.query.filter_by(user_id=session["user_id"]).all()]

    return render_template("home.html",
        featured=featured, total_bookings=total_bookings,
        total_users=total_users, total_destinations=total_destinations,
        popular_dests=popular_dests, wishlist_ids=wishlist_ids)


# ── DESTINATIONS ──
@app.route("/destinations")
def destinations_page():
    categories   = db.session.query(Destination.category).distinct().all()
    vac_types    = db.session.query(Destination.vacation_type).distinct().all()
    wishlist_ids = []
    if "user_id" in session:
        wishlist_ids = [w.destination_id for w in Wishlist.query.filter_by(user_id=session["user_id"]).all()]
    return render_template("destinations.html",
        categories=[c[0] for c in categories if c[0]],
        vac_types=[v[0] for v in vac_types if v[0]],
        wishlist_ids=wishlist_ids)

@app.route("/api/destinations")
def get_destinations():
    vacation_type = request.args.get("type")
    query = Destination.query
    if vacation_type:
        query = query.filter_by(vacation_type=vacation_type)
    destinations = query.all()
    result = []
    for d in destinations:
        img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name + " travel")
        result.append({
            "id": d.id, "name": d.name, "rating": d.rating,
            "image": img, "best_time": d.best_time,
            "category": d.category, "country_type": d.country_type,
            "vacation_type": d.vacation_type
        })
    return jsonify(result)


# ── SMART SEARCH ──
@app.route("/api/search")
def smart_search():
    q            = request.args.get("q", "").lower()
    vac_type     = request.args.get("type", "")
    category     = request.args.get("category", "")
    sort_by      = request.args.get("sort", "rating")

    query = Destination.query
    if vac_type:
        query = query.filter_by(vacation_type=vac_type)
    if category:
        query = query.filter_by(category=category)
    destinations = query.all()

    if q:
        keywords = q.split()
        budget = None
        for i, kw in enumerate(keywords):
            if kw in ("under", "below", "within") and i + 1 < len(keywords):
                try:
                    budget = int(keywords[i+1].replace(",", "").replace("₹", ""))
                except:
                    pass

        def relevance(d):
            score = 0
            text = f"{d.name} {d.category or ''} {d.vacation_type or ''} {d.best_time or ''} {d.country_type or ''}".lower()
            for kw in keywords:
                if kw in text: score += 3
                if kw in d.name.lower(): score += 5
            return score

        destinations = [d for d in destinations if relevance(d) > 0]
        if budget:
            filtered = []
            for d in destinations:
                min_h = db.session.query(func.min(Hotel.starting_price)).filter_by(destination_id=d.id).scalar() or 999999
                if min_h <= budget:
                    filtered.append(d)
            if filtered:
                destinations = filtered
        destinations.sort(key=relevance, reverse=True)

    if sort_by == "rating":
        destinations.sort(key=lambda d: d.rating or 0, reverse=True)
    elif sort_by == "popular":
        pop = {row.destination: row.cnt for row in db.session.query(
            BookingHistory.destination, func.count(BookingHistory.id).label("cnt")
        ).group_by(BookingHistory.destination).all()}
        destinations.sort(key=lambda d: pop.get(d.name, 0), reverse=True)

    result = []
    for d in destinations:
        img = d.image if (d.image and d.image.startswith("http")) else get_pexels_single(d.name + " travel")
        result.append({
            "id": d.id, "name": d.name, "rating": d.rating,
            "image": img, "category": d.category,
            "best_time": d.best_time, "country_type": d.country_type,
            "vacation_type": d.vacation_type
        })
    return jsonify(result)


# ── AI CHATBOT ──
@app.route("/api/chat", methods=["POST"])
def ai_chat():
    data     = request.json
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please type a message."})
    destinations = Destination.query.all()
    dest_names   = ", ".join(d.name for d in destinations)
    system_prompt = f"""You are TripMore AI, a friendly expert travel assistant for TripMore — an Indian travel booking platform.
Available destinations: {dest_names}
Rules: Keep replies under 150 words. Suggest TripMore destinations. Use INR. Be warm and enthusiastic."""
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
    except Exception as e:
        reply = "Sorry, I'm having trouble right now. Please try again!"
    if "user_id" in session:
        db.session.add(ChatHistory(user_id=session["user_id"], role="user", message=user_msg))
        db.session.add(ChatHistory(user_id=session["user_id"], role="assistant", message=reply))
        db.session.commit()
    return jsonify({"reply": reply})


# ── RECOMMENDATIONS ──
@app.route("/api/recommendations")
def get_recommendations():
    all_dests = Destination.query.all()
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

# ── ANALYTICS ──
@app.route("/analytics")
@login_required
def analytics():
    from datetime import datetime, timedelta
    from collections import Counter

    uid  = session["user_id"]
    user = User.query.get(uid)

    my_bookings = BookingHistory.query.filter_by(user_id=uid).all()
    booking_ids = [b.id for b in my_bookings]

    total_trips = len(my_bookings)

    total_spent = (
        db.session.query(func.sum(HotelBooking.final_payable))
        .filter(HotelBooking.booking_id.in_(booking_ids))
        .scalar() or 0
    )

    total_spent += (
        db.session.query(func.sum(TransportBooking.price))
        .filter(TransportBooking.booking_id.in_(booking_ids))
        .scalar() or 0
    )

    # Favourite destinations
    dest_counter = Counter(b.destination for b in my_bookings)
    fav_dest     = dest_counter.most_common(5)

    # Monthly data
    monthly = {}
    for i in range(5, -1, -1):
        dt    = datetime.now() - timedelta(days=30 * i)
        label = dt.strftime("%b %Y")

        count = sum(
            1 for b in my_bookings
            if b.created_at and
               b.created_at.month == dt.month and
               b.created_at.year == dt.year
        )
        monthly[label] = count

    # 🔥 FIX 1: global_top (Row → dict)
    global_top_raw = db.session.query(
        BookingHistory.destination,
        func.count(BookingHistory.id)
    ).group_by(BookingHistory.destination)\
     .order_by(func.count(BookingHistory.id).desc())\
     .limit(5).all()

    global_top = [
        {"destination": t[0], "cnt": t[1]}
        for t in global_top_raw
    ]

    # 🔥 FIX 2: transport_types (Row → dict)
    transport_types_raw = db.session.query(
        TransportBooking.transport_type,
        func.count(TransportBooking.id)
    ).filter(
        TransportBooking.booking_id.in_(booking_ids)
    ).group_by(TransportBooking.transport_type).all()

    transport_types = [
        {"type": t[0], "count": t[1]}
        for t in transport_types_raw
    ]

    return render_template(
        "analytics.html",
        user=user,
        total_trips=total_trips,
        total_spent=total_spent,
        fav_dest=fav_dest,
        monthly=monthly,
        global_top=global_top,
        transport_types=transport_types
    )
@app.route("/api/analytics-data")
@login_required
def analytics_data():
    from datetime import datetime, timedelta
    uid = session["user_id"]
    my_bookings = BookingHistory.query.filter_by(user_id=uid).all()
    labels, data = [], []
    for i in range(5, -1, -1):
        dt    = datetime.now() - timedelta(days=30 * i)
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
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"status": "removed"})
    db.session.add(Wishlist(user_id=uid, destination_id=dest_id))
    db.session.commit()
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
    db.session.add(Review(user_id=session["user_id"], destination=destination, rating=rating, comment=comment))
    db.session.commit()
    flash("Review submitted!", "success")
    return redirect(request.referrer or url_for("my_bookings"))

@app.route("/api/reviews/<destination>")
def get_reviews(destination):
    reviews = Review.query.filter_by(destination=destination).order_by(Review.created_at.desc()).limit(10).all()
    result  = []
    for r in reviews:
        user = User.query.get(r.user_id)
        result.append({"name": user.name if user else "Traveller", "rating": r.rating, "comment": r.comment,
                        "date": r.created_at.strftime("%b %Y") if r.created_at else ""})
    return jsonify(result)


# ── HOTELS ──
@app.route("/api/hotels/<int:destination_id>")
def api_hotels(destination_id):
    hotels = Hotel.query.filter_by(destination_id=destination_id).all()
    data   = []
    for h in hotels:
        prices = [r.base_price for r in h.rooms if r.base_price is not None]
        # Get multiple Pexels images for hotel variety
        imgs = get_pexels_images(h.name + " hotel resort", 3)
        data.append({
            "id": h.id, "hotel": h.name, "stars": h.stars,
            "price": min(prices) if prices else 0,
            "available_rooms": sum((r.total_rooms - r.booked_rooms) for r in h.rooms if r.total_rooms and r.booked_rooms is not None),
            "amenities": [a.name for a in h.amenities],
            "images": imgs,
            "rooms": [{"type": r.room_type, "available": (r.total_rooms - r.booked_rooms) if r.total_rooms and r.booked_rooms is not None else 0, "price": r.base_price} for r in h.rooms]
        })
    return jsonify(data)

@app.route("/hotels/<int:destination_id>")
def hotels_by_destination(destination_id):
    destination = Destination.query.get_or_404(destination_id)
    hotels      = Hotel.query.filter_by(destination_id=destination_id).all()
    # Attach Pexels images to each hotel
    for h in hotels:
        h.pexels_images = get_pexels_images(h.name + " hotel", 3)
        h.pexels_main   = h.pexels_images[0] if h.pexels_images else ""
    # Destination image
    dest_img = destination.image if (destination.image and destination.image.startswith("http")) else get_pexels_single(destination.name + " travel")
    return render_template("hotels.html", destination=destination, hotels=hotels, dest_img=dest_img)


# ── HOTEL BOOKING ──
import re
from datetime import datetime

@app.route("/book-hotel/<int:hotel_id>", methods=["GET", "POST"])
@login_required
def hotel_booking(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    # Get hotel images from Pexels
    hotel_images = get_pexels_images(hotel.name + " hotel room", 4)
    error = None

    if request.method == "POST":
        try:
            persons     = int(request.form.get("persons", 1))
            room_id     = int(request.form.get("room_id"))
            checkin     = request.form.get("checkin")
            checkout    = request.form.get("checkout")
            name        = request.form.get("name", "").strip()
            email       = request.form.get("email", "").strip()
            phone       = request.form.get("phone", "").strip()
            id_type     = request.form.get("id_type")
            id_number   = request.form.get("id_number", "").strip().upper()
            lunch       = request.form.get("lunch")
            dinner      = request.form.get("dinner")
            pickup      = request.form.get("pickup")
            bank_name   = request.form.get("bank_name", "")
            card_number = request.form.get("card_number", "").strip()

            today         = datetime.today().date()
            checkin_date  = datetime.strptime(checkin,  "%Y-%m-%d").date()
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()

            if persons <= 0:                                                       error = "Persons must be at least 1"
            elif checkin_date < today:                                             error = "Check-in cannot be in the past"
            elif checkout_date < checkin_date:                                     error = "Check-out cannot be before Check-in"
            elif not re.match(r"^[6-9]\d{9}$", phone):                            error = "Invalid phone number"
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):                      error = "Invalid email address"
            elif id_type == "aadhaar" and not re.match(r"^\d{12}$", id_number):   error = "Aadhaar must be 12 digits"
            elif id_type == "pan" and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", id_number): error = "Invalid PAN format"

            if error:
                return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images,
                    form_data=request.form, error=error, applied_discount=0)

            room            = Room.query.get_or_404(room_id)
            required_rooms  = math.ceil(persons / 2)
            available_rooms = room.total_rooms - room.booked_rooms

            if available_rooms <= 0:              error = "No rooms available"
            elif available_rooms < required_rooms: error = f"Only {available_rooms} rooms available"

            if error:
                return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images,
                    form_data=request.form, error=error, applied_discount=0)

            nights       = max((checkout_date - checkin_date).days, 1)
            base_price   = nights * room.base_price * required_rooms
            extra_price  = 0
            if lunch:  extra_price += hotel.lunch_price  * persons
            if dinner: extra_price += hotel.dinner_price * persons
            if pickup: extra_price += hotel.pickup_price

            total_price   = base_price + extra_price
            bank_map      = {"hdfc": 10, "sbi": 15, "icici": 12}
            bank_discount = (total_price * bank_map.get(bank_name, 0)) // 100
            final_payable = total_price - bank_discount

            destination = Destination.query.get(hotel.destination_id)
            main_booking = BookingHistory(user_id=session["user_id"], destination=destination.name, status="active")
            db.session.add(main_booking)
            db.session.commit()

            booking = HotelBooking(
                booking_id=main_booking.id, hotel_id=hotel.id, room_id=room_id,
                persons=persons, check_in=checkin_date, check_out=checkout_date,
                base_price=base_price, extra_price=extra_price, total_price=total_price,
                bank_name=bank_name, card_number="", bank_discount=bank_discount,
                final_payable=final_payable, lunch_added=bool(lunch),
                dinner_added=bool(dinner), pickup_added=bool(pickup),
                id_type=id_type, id_number=id_number,
                name=name, email=email, phone=phone,
                payment_status="pending", created_at=datetime.now()
            )
            db.session.add(booking)
            room.booked_rooms += required_rooms
            db.session.commit()

            session["hotel_booking_id"] = booking.id
            session["booking_id"]       = main_booking.id

            # Redirect to payment page
            return redirect(url_for("payment_page", booking_id=booking.id))

        except Exception as e:
            db.session.rollback()
            print("BOOKING ERROR:", e)
            return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images,
                form_data=request.form, error="Something went wrong. Please try again.", applied_discount=0)

    return render_template("book_hotel.html", hotel=hotel, hotel_images=hotel_images)


# ── PAYMENT ──
@app.route("/payment/<int:booking_id>")
@login_required
def payment_page(booking_id):
    booking      = HotelBooking.query.get_or_404(booking_id)
    main_booking = BookingHistory.query.get(booking.booking_id)
    hotel        = Hotel.query.get(booking.hotel_id)
    if not booking or booking.booking_id not in [b.id for b in BookingHistory.query.filter_by(user_id=session["user_id"]).all()]:
        return redirect(url_for("home"))
    # Generate UPI payment link
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={booking.final_payable}&cu=INR&tn=TripMore+Booking+{booking_id}"
    return render_template("payment.html",
        booking=booking, hotel=hotel, main_booking=main_booking,
        upi_id=UPI_ID, upi_name=UPI_NAME, upi_link=upi_link,
        amount=booking.final_payable)

@app.route("/payment/confirm/<int:booking_id>", methods=["POST"])
@login_required
def confirm_payment(booking_id):
    booking  = HotelBooking.query.get_or_404(booking_id)
    upi_ref  = request.form.get("upi_ref", "").strip()
    booking.payment_status = "paid"
    booking.upi_ref        = upi_ref
    db.session.commit()
    flash("Payment confirmed! Your booking is now active.", "success")
    return redirect(url_for("transport_choice",
        destination=BookingHistory.query.get(booking.booking_id).destination,
        booked="1"))

@app.route("/payment/skip/<int:booking_id>")
@login_required
def skip_payment(booking_id):
    """Allow skip for demo purposes"""
    booking = HotelBooking.query.get_or_404(booking_id)
    booking.payment_status = "demo"
    db.session.commit()
    destination = BookingHistory.query.get(booking.booking_id).destination
    return redirect(url_for("transport_choice", destination=destination, booked="1"))


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
        flash(f"Welcome back, {user.name}!", "success")
        # Smart redirect — go back to where user was, or dashboard
        next_url = session.pop("next_url", None)
        if next_url:
            return redirect(next_url)
        return redirect(url_for("user_dashboard"))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name     = request.form.get("name")
        email    = request.form.get("email")
        password = request.form.get("password")
        if not name or not email or not password:
            flash("All fields are required", "error")
            return render_template("signup.html", name=name, email=email)
        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("signup.html", name=name, email=email)
        if not any(c.isdigit() for c in password):
            flash("Password must contain at least 1 number", "error")
            return render_template("signup.html", name=name, email=email)
        if not any(c.isupper() for c in password):
            flash("Password must contain at least 1 uppercase letter", "error")
            return render_template("signup.html", name=name, email=email)
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return render_template("signup.html", name=name, email=email)
        new_user = User(name=name, email=email, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        flash(f"Welcome to TripMore, {name}!", "success")
        return redirect(url_for("user_dashboard"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ── USER DASHBOARD ──
@app.route("/dashboard")
@login_required
def user_dashboard():
    from datetime import datetime, timedelta
    uid  = session["user_id"]
    user = User.query.get(uid)
    my_bookings  = BookingHistory.query.filter_by(user_id=uid).order_by(BookingHistory.created_at.desc()).limit(5).all()
    total_trips  = BookingHistory.query.filter_by(user_id=uid).count()
    booking_ids  = [b.id for b in BookingHistory.query.filter_by(user_id=uid).all()]
    total_spent  = (db.session.query(func.sum(HotelBooking.final_payable)).filter(HotelBooking.booking_id.in_(booking_ids)).scalar() or 0)
    wishlist_cnt = Wishlist.query.filter_by(user_id=uid).count()
    # Upcoming bookings
    upcoming = []
    for b in my_bookings:
        hb = HotelBooking.query.filter_by(booking_id=b.id).first()
        if hb and hb.check_in and hb.check_in >= datetime.today().date():
            upcoming.append({"booking": b, "hotel": hb})
    return render_template("user_dashboard.html",
        user=user, my_bookings=my_bookings, total_trips=total_trips,
        total_spent=total_spent, wishlist_cnt=wishlist_cnt, upcoming=upcoming)


# ── MY BOOKINGS ──
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
        cab      = CabBooking.query.filter_by(booking_id=b.id).first()
        cab_days = []
        cab_total= 0
        if cab:
            cab_total = cab.price or 0
            for d in CabBookingDay.query.filter_by(cab_booking_id=cab.id).order_by(CabBookingDay.day_number).all():
                spots_rel  = CabBookingDaySpot.query.filter_by(cab_booking_day_id=d.id).all()
                spot_names = [HypeSpot.query.get(s.spot_id).spot_name for s in spots_rel if HypeSpot.query.get(s.spot_id)]
                cab_days.append({"day": d.day_number, "arrival": d.arrival_time, "departure": d.departure_time,
                                  "pickup": d.pickup_type, "drop": d.drop_type, "spots": spot_names, "km": d.day_km, "price": d.day_price})
        grand_total = hotel_total + transport_total + cab_total
        result.append({"booking": b, "hotel": hotel, "transports": transport_data, "cab": cab, "cab_days": cab_days,
                        "hotel_total": hotel_total, "transport_total": transport_total, "cab_total": cab_total, "grand_total": grand_total})
    total_spent = sum(b["grand_total"] for b in result)
    return render_template("my_bookings.html", bookings=result, total_spent=total_spent)


# ── TRANSPORT ──
@app.route("/after-hotel-booking/<int:hotel_id>")
def after_hotel_booking(hotel_id):
    if "user_id" not in session:
        return redirect("/login")
    hotel = Hotel.query.get_or_404(hotel_id)
    return render_template("after_hotel_booking.html", hotel=hotel, destination=Destination.query.get(hotel.destination_id))

@app.route("/transport-choice/<destination>")
def transport_choice(destination):
    return render_template("transport_choice.html", destination=destination)

@app.route("/flight/<destination>", methods=["GET", "POST"])
@login_required
def flight(destination):
    persons = session.get("persons", 1)
    if not session.get("booking_id"):
        return redirect(url_for("home"))
    flights = []
    if request.method == "POST":
        flights = Flight.query.filter_by(source=request.form.get("source"), destination=destination, flight_class=request.form.get("flight_class")).all()
    return render_template("flights.html", destination=destination, persons=persons, flights=flights)

@app.route("/confirm-flight/<int:flight_id>")
@login_required
def confirm_flight(flight_id):
    booking_id = session.get("booking_id")
    persons    = session.get("persons", 1)
    if not booking_id: return redirect(url_for("home"))
    flight = Flight.query.get_or_404(flight_id)
    if flight.available_seats < persons: return "Not enough seats"
    flight.available_seats -= persons
    db.session.add(TransportBooking(booking_id=booking_id, transport_type="flight", source=flight.source,
        destination=flight.destination, persons=persons, price=flight.price * persons))
    db.session.commit()
    hotel_booking = HotelBooking.query.filter_by(booking_id=booking_id).first()
    return redirect(url_for("hype_spots", hotel_booking_id=hotel_booking.id))

@app.route("/bus/<destination>", methods=["GET", "POST"])
@login_required
def bus(destination):
    if not session.get("booking_id"): return redirect(url_for("home"))
    buses = []
    if request.method == "POST":
        buses = Bus.query.filter_by(source=request.form.get("source"), destination=destination,
            ac_type=request.form.get("ac_type"), seat_type=request.form.get("seat_type")).all()
    return render_template("bus.html", destination=destination, persons=session.get("persons", 1), buses=buses)

@app.route("/confirm-bus/<int:bus_id>")
@login_required
def confirm_bus(bus_id):
    booking_id = session.get("booking_id")
    persons    = session.get("persons", 1)
    if not booking_id: return redirect(url_for("home"))
    bus = Bus.query.get_or_404(bus_id)
    if bus.available_seats < persons: return "Not enough seats"
    bus.available_seats -= persons
    db.session.add(TransportBooking(booking_id=booking_id, transport_type="bus", source=bus.source,
        destination=bus.destination, persons=persons, price=bus.price * persons))
    db.session.commit()
    hotel_booking = HotelBooking.query.filter_by(booking_id=booking_id).first()
    return redirect(url_for("hype_spots", hotel_booking_id=hotel_booking.id))

@app.route("/train/<destination>", methods=["GET", "POST"])
@login_required
def train(destination):
    if not session.get("booking_id"): return redirect(url_for("home"))
    trains = []
    if request.method == "POST":
        trains = Train.query.filter_by(source=request.form.get("source"), destination=destination,
            ac_type=request.form.get("ac_type"), seat_type=request.form.get("seat_type")).all()
    return render_template("train.html", destination=destination, persons=session.get("persons", 1), trains=trains)

@app.route("/confirm-train/<int:train_id>")
@login_required
def confirm_train(train_id):
    booking_id = session.get("booking_id")
    persons    = session.get("persons", 1)
    if not booking_id: return redirect(url_for("home"))
    train = Train.query.get_or_404(train_id)
    if train.available_seats < persons: return "Not enough seats"
    train.available_seats -= persons
    db.session.add(TransportBooking(booking_id=booking_id, transport_type="train", source=train.source,
        destination=train.destination, persons=persons, price=train.price * persons))
    db.session.commit()
    flash("Transport booked!", "success")
    hotel_booking = HotelBooking.query.filter_by(booking_id=booking_id).first()
    return redirect(url_for("hype_spots", hotel_booking_id=hotel_booking.id))

@app.route("/api/calculate-transport", methods=["POST"])
@login_required
def calculate_transport():
    data           = request.json
    hotel_id       = data.get("hotel_id")
    spot_ids       = data.get("spot_ids", [])
    total_days     = int(data.get("total_days", 1))
    arrival_time   = data.get("arrival_time")
    departure_time = data.get("departure_time")
    if not hotel_id or not spot_ids: return jsonify([])
    hotel       = Hotel.query.get_or_404(hotel_id)
    current_lat = float(hotel.latitude)
    current_lon = float(hotel.longitude)
    total_dist  = 0
    for sid in spot_ids:
        spot = HypeSpot.query.get(int(sid))
        if not spot: continue
        total_dist  += haversine(current_lat, current_lon, float(spot.latitude), float(spot.longitude))
        current_lat  = float(spot.latitude)
        current_lon  = float(spot.longitude)
    total_dist += haversine(current_lat, current_lon, float(hotel.latitude), float(hotel.longitude))
    total_dist  = round(total_dist, 2)
    total_hours = 8
    if arrival_time and departure_time:
        t1 = datetime.strptime(arrival_time, "%H:%M")
        t2 = datetime.strptime(departure_time, "%H:%M")
        total_hours = round((t2 - t1).seconds / 3600, 2)
    result = []
    for v in Transport.query.all():
        price = round(total_dist * float(v.price_per_km) + 1200 * total_days + total_hours * 100, 2)
        result.append({"vehicle": v.vehicle_name, "type": v.vehicle_type, "ac": v.ac_type,
                        "price": price, "cab_id": v.id, "distance": total_dist, "days": total_days, "hours": total_hours})
    return jsonify(result)

@app.route("/book-cab/<int:hotel_booking_id>", methods=["POST"])
@login_required
def book_cab(hotel_booking_id):
    cab_id = request.form.get("cab_id")
    if not cab_id:
        flash("Please select a cab.", "danger")
        return redirect(request.referrer)
    total_days    = int(request.form.get("total_days"))
    hotel_booking = HotelBooking.query.get_or_404(hotel_booking_id)
    transport     = Transport.query.get_or_404(cab_id)
    hotel         = Hotel.query.get_or_404(hotel_booking.hotel_id)
    cab_booking   = CabBooking(booking_id=hotel_booking.booking_id, transport_id=transport.id, days=total_days, total_km=0, price=0)
    db.session.add(cab_booking)
    db.session.commit()
    total_km = total_price = 0
    for day in range(1, total_days + 1):
        arrival    = request.form.get(f"arrival_time_{day}")
        departure  = request.form.get(f"departure_time_{day}")
        pickup_type= request.form.get(f"pickup_type_{day}")
        drop_type  = request.form.get(f"drop_type_{day}")
        spot_ids   = request.form.getlist(f"day_{day}_spots")
        cur_lat = float(hotel.latitude); cur_lon = float(hotel.longitude)
        day_km  = 0
        for sid in spot_ids:
            spot = HypeSpot.query.get(int(sid))
            if not spot: continue
            day_km += haversine(cur_lat, cur_lon, float(spot.latitude), float(spot.longitude))
            cur_lat = float(spot.latitude); cur_lon = float(spot.longitude)
        day_km    += haversine(cur_lat, cur_lon, float(hotel.latitude), float(hotel.longitude))
        day_km     = round(day_km, 2)
        day_price  = day_km * float(transport.price_per_km)
        if pickup_type == "custom":  day_price += 500
        if drop_type   == "custom":  day_price += 500
        if pickup_type == "airport": day_price += 300
        if drop_type   == "airport": day_price += 300
        day_price  = round(day_price, 2)
        total_km  += day_km; total_price += day_price
        booking_day = CabBookingDay(cab_booking_id=cab_booking.id, day_number=day,
            arrival_time=datetime.strptime(arrival, "%H:%M").time(),
            departure_time=datetime.strptime(departure, "%H:%M").time(),
            pickup_type=pickup_type, drop_type=drop_type,
            custom_pickup=request.form.get(f"custom_pickup_{day}"),
            custom_drop=request.form.get(f"custom_drop_{day}"),
            day_km=day_km, day_price=day_price)
        db.session.add(booking_day)
        db.session.commit()
        for sid in spot_ids:
            db.session.add(CabBookingDaySpot(cab_booking_day_id=booking_day.id, spot_id=int(sid)))
    cab_booking.total_km = total_km; cab_booking.price = total_price
    db.session.commit()
    flash("Cab booked successfully!", "success")
    return redirect(url_for("my_bookings"))

@app.route("/hype-spots/<int:hotel_booking_id>")
@login_required
def hype_spots(hotel_booking_id):
    hotel_booking = HotelBooking.query.get_or_404(hotel_booking_id)
    hotel         = Hotel.query.get_or_404(hotel_booking.hotel_id)
    destination   = Destination.query.get_or_404(hotel.destination_id)
    spots         = HypeSpot.query.filter_by(destination_id=destination.id).all()
    transports    = Transport.query.all()
    return render_template("hype_spots.html", spots=spots, transports=transports,
        destination_name=destination.name, hotel_id=hotel.id, hotel_booking_id=hotel_booking.id)

@app.route("/book-train/<int:id>")
def book_train(id):
    train = Train.query.get(id)
    db.session.add(TransportBooking(booking_id=session["booking_id"], transport_type="train",
        source=train.source, destination=train.destination, persons=session.get("persons", 1), price=train.price))
    db.session.commit()
    return redirect(url_for("hype_spots", destination_id=session.get("destination")))

@app.route("/book-flight/<int:id>")
def book_flight(id):
    flight = Flight.query.get(id)
    db.session.add(TransportBooking(booking_id=session["booking_id"], transport_type="flight",
        source=flight.source, destination=flight.destination, persons=session.get("persons", 1), price=flight.price))
    db.session.commit()
    return redirect(url_for("hype_spots", destination_id=session.get("destination")))


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
    foods      = HiddenStreetFood.query.filter_by(location_name=location).all()
    safety     = NightSafetyZones.query.filter_by(location_name=location).all()
    etiquettes = LocalEtiquettes.query.filter_by(location_name=location).all()
    alerts     = TouristAlertsTips.query.filter_by(location_name=location).all()
    essentials = LocationEssentials.query.filter_by(location_name=location).first()
    return render_template("information.html", location=location, foods=foods, safety=safety,
        etiquettes=etiquettes, alerts=alerts, essentials=essentials)


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


# ── MISC ──
@app.route("/coming-soon")
def coming_soon():
    return "<h2 style='text-align:center;margin-top:100px;font-family:Arial;'>Coming Soon!</h2>"

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


# ── INVOICE ──
@app.route("/download-invoice/<int:booking_id>")
@login_required
def download_invoice(booking_id):
    booking = BookingHistory.query.get_or_404(booking_id)
    if booking.user_id != session["user_id"]: return "Unauthorized", 403
    return send_file(generate_invoice_pdf(booking_id), as_attachment=True)

@app.route("/send-invoice/<int:booking_id>")
@login_required
def send_invoice_email(booking_id):
    booking = BookingHistory.query.get_or_404(booking_id)
    if booking.user_id != session["user_id"]: return "Unauthorized", 403
    user      = User.query.get(session["user_id"])
    file_path = generate_invoice_pdf(booking_id)
    msg = EmailMessage()
    msg["Subject"] = f"TripMore Invoice #{booking_id}"
    msg["From"]    = "prathukakadiya7x@gmail.com"
    msg["To"]      = user.email
    msg.set_content("Thank you for booking with TripMore. Invoice attached.")
    with open(file_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=f"Invoice_{booking_id}.pdf")
    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.starttls()
    smtp.login("prathukakadiya7x@gmail.com", "csftedtyotxuwxgu")
    smtp.send_message(msg)
    smtp.quit()
    os.remove(file_path)
    return jsonify({"success": True, "message": "Invoice sent!"})


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import random

def generate_invoice_pdf(booking_id):
    booking        = BookingHistory.query.get_or_404(booking_id)
    hotel_booking  = HotelBooking.query.filter_by(booking_id=booking.id).first()
    cab            = CabBooking.query.filter_by(booking_id=booking.id).first()
    transport_list = TransportBooking.query.filter_by(booking_id=booking.id).all()
    file_path = f"invoice_{booking_id}.pdf"
    doc       = SimpleDocTemplate(file_path, pagesize=A4)
    elements  = []
    styles    = getSampleStyleSheet()
    big_title = ParagraphStyle('BigTitle', parent=styles['Title'], fontSize=30, spaceAfter=10)
    elements.append(Paragraph("<b>TRIPMOREEE</b>", big_title))
    elements.append(Paragraph("TripMore Travel Pvt Ltd · Surat, Gujarat · +91 98765 43210", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Table([[""]], colWidths=[500], rowHeights=[2], style=TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.black)])))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f"<b>Invoice #{booking.id}</b> | Date: {datetime.now().strftime('%d-%m-%Y')} | Destination: {booking.destination}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    total_amount = 0
    if hotel_booking:
        hotel = Hotel.query.get(hotel_booking.hotel_id)
        room  = Room.query.get(hotel_booking.room_id)
        elements.append(Paragraph("<b>Hotel Details</b>", styles["Heading3"]))
        t = Table([["Hotel", hotel.name if hotel else "N/A"], ["Room", room.room_type if room else "N/A"],
                   ["Room No.", str(random.randint(100,999))], ["Guest", hotel_booking.name],
                   ["Check-In", str(hotel_booking.check_in)], ["Check-Out", str(hotel_booking.check_out)],
                   ["Persons", str(hotel_booking.persons)], ["Payment", hotel_booking.payment_status or "pending"],
                   ["Amount", f"Rs. {hotel_booking.final_payable}"]], colWidths=[250, 250])
        t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.grey)]))
        elements.append(t); elements.append(Spacer(1, 0.3*inch))
        total_amount += hotel_booking.final_payable or 0
    for tb in transport_list:
        elements.append(Paragraph("<b>Transport</b>", styles["Heading3"]))
        t = Table([[tb.transport_type.capitalize(), f"{tb.source} → {tb.destination}"], ["Passengers", str(tb.persons)], ["Amount", f"Rs. {tb.price}"]], colWidths=[250, 250])
        t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.grey)]))
        elements.append(t); elements.append(Spacer(1, 0.3*inch))
        total_amount += tb.price or 0
    if cab:
        vehicle = Transport.query.get(cab.transport_id)
        elements.append(Paragraph("<b>Cab</b>", styles["Heading3"]))
        t = Table([["Vehicle", vehicle.vehicle_name if vehicle else "N/A"], ["KM", str(cab.total_km)], ["Days", str(cab.days)], ["Amount", f"Rs. {cab.price}"]], colWidths=[250, 250])
        t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.grey)]))
        elements.append(t); elements.append(Spacer(1, 0.3*inch))
        total_amount += cab.price or 0
    t = Table([["GRAND TOTAL", f"Rs. {total_amount}"]], colWidths=[300, 200])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.black), ('TEXTCOLOR',(0,0),(-1,-1),colors.white), ('FONTSIZE',(0,0),(-1,-1),14)]))
    elements.append(t)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Computer generated invoice. No signature required.", styles["Normal"]))
    doc.build(elements)
    return file_path
@app.route("/api/pexels-image")
def pexels_image():
    query = request.args.get("q", "hotel room")
    page  = int(request.args.get("page", 1))
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 1, "page": page, "orientation": "landscape"},
            timeout=5
        )
        photos = resp.json().get("photos", [])
        url = photos[0]["src"]["large"] if photos else ""
    except Exception as e:
        url = ""
    return jsonify({"url": url})

# ================================================================
#  PHASE 2 — NEW ROUTES
#  Add ALL of these BEFORE the `if __name__ == "__main__":` line
#  Also add these NEW SQL tables (run in phpMyAdmin first)
# ================================================================

# ── SQL TO RUN IN PHPMYADMIN FIRST ───────────────────────────
SQL_TO_RUN = """
CREATE TABLE IF NOT EXISTS community_photos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  destination VARCHAR(100),
  image_url VARCHAR(500),
  caption TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
# ─────────────────────────────────────────────────────────────

# ADD THIS MODEL after your existing models:
# class CommunityPhoto(db.Model):
#     __tablename__ = "community_photos"
#     id          = db.Column(db.Integer, primary_key=True)
#     user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
#     destination = db.Column(db.String(100))
#     image_url   = db.Column(db.String(500))
#     caption     = db.Column(db.Text)
#     created_at  = db.Column(db.DateTime, server_default=db.func.now())

# ─────────────────────────────────────────────────────────────
# PASTE THESE ROUTES INTO app.py BEFORE if __name__ == "__main__"
# ─────────────────────────────────────────────────────────────

# ── TRANSPORT AVAILABILITY API (for transport_choice.html) ───

@app.route("/api/transport-availability")
def transport_availability():
    destination = request.args.get("destination", "")

    # Check flights
    flights = Flight.query.filter_by(destination=destination).all()
    trains  = Train.query.filter_by(destination=destination).all()
    buses   = Bus.query.filter_by(destination=destination).all()

    flight_prices = [f.price for f in flights if f.price]
    train_prices  = [t.price for t in trains  if t.price]
    bus_prices    = [b.price for b in buses   if b.price]

    # Smart routing: if no direct bus/train, suggest via hub
    smart_route = None
    INTERNATIONAL = ["Bali","Paris","Dubai","Singapore","Switzerland","New Zealand",
                     "Mecca","Vatican City","Iceland","Amsterdam"]

    if destination in INTERNATIONAL:
        # Only flights for international
        smart_route = None
        # Mark bus/train as not available
    elif not buses and not trains:
        # Suggest via Delhi or Mumbai
        hubs = ["Delhi", "Mumbai", "Ahmedabad"]
        for hub in hubs:
            hub_to_dest_bus   = Bus.query.filter_by(source=hub,   destination=destination).first()
            hub_to_dest_train = Train.query.filter_by(source=hub, destination=destination).first()
            if hub_to_dest_bus or hub_to_dest_train:
                smart_route = ["Your City", hub, destination]
                break

    return jsonify({
        "flights": {
            "count":     len(flights),
            "min_price": min(flight_prices) if flight_prices else 0,
            "available": len(flights) > 0
        },
        "trains": {
            "count":     len(trains),
            "min_price": min(train_prices) if train_prices else 0,
            "available": len(trains) > 0
        },
        "buses": {
            "count":     len(buses),
            "min_price": min(bus_prices) if bus_prices else 0,
            "available": len(buses) > 0
        },
        "is_international": destination in INTERNATIONAL,
        "smart_route": smart_route
    })


# ── AI TRIP PLANNER ──────────────────────────────────────────

@app.route("/trip-planner")
def trip_planner():
    return render_template("trip_planner.html")


@app.route("/api/ai-trip-plan", methods=["POST"])
def ai_trip_plan():
    data  = request.json
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"plan": "Please enter a trip query."})

    # Extract destination from query
    all_dests     = Destination.query.all()
    dest_names    = [d.name for d in all_dests]
    found_dest    = None
    query_lower   = query.lower()
    for name in dest_names:
        if name.lower() in query_lower:
            found_dest = name
            break

    # Get matching hotels
    matching_hotels = []
    if found_dest:
        dest_obj = Destination.query.filter_by(name=found_dest).first()
        if dest_obj:
            hotels = Hotel.query.filter_by(destination_id=dest_obj.id).order_by(Hotel.starting_price).limit(5).all()
            for h in hotels:
                prices = [r.base_price for r in h.rooms if r.base_price]
                avail  = sum((r.total_rooms - r.booked_rooms) for r in h.rooms if r.total_rooms and r.booked_rooms is not None)
                matching_hotels.append({
                    "id":    h.id,
                    "name":  h.name,
                    "stars": h.stars,
                    "price": min(prices) if prices else 0,
                    "rooms": avail
                })

    # Get matching flights
    matching_flights = []
    if found_dest:
        flights = Flight.query.filter_by(destination=found_dest).order_by(Flight.price).limit(3).all()
        for f in flights:
            matching_flights.append({
                "airline":      f.airline,
                "price":        f.price,
                "source":       f.source,
                "destination":  f.destination,
                "flight_class": f.flight_class
            })

    # Extract budget from query
    import re
    budget_match = re.search(r'(?:under|below|within|₹|rs\.?)\s*(\d[\d,]*)', query_lower)
    budget = int(budget_match.group(1).replace(',', '')) if budget_match else None

    # Build AI prompt
    system_prompt = """You are TripMore's AI trip planner. When given a trip request, respond with a JSON object only (no markdown, no explanation) with this exact structure:
{
  "plan": "A detailed day-by-day itinerary as a formatted string with \\n for newlines",
  "destination": "destination name",
  "budget": {
    "Hotel (per night)": "amount",
    "Transport": "amount",
    "Food (per day)": "amount",
    "Activities": "amount",
    "Miscellaneous": "amount",
    "total": "total amount"
  },
  "tips": ["tip1", "tip2", "tip3"]
}
Keep the plan practical, fun and within the budget. Include specific recommendations for food, places, timing."""

    user_msg = f"""Plan this trip: {query}
Available destinations on TripMore: {', '.join(dest_names[:15])}
{"Budget: ₹" + str(budget) if budget else ""}
{"Destination detected: " + found_dest if found_dest else ""}"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_msg}]
            },
            timeout=20
        )
        text = resp.json()["content"][0]["text"].strip()
        # Clean JSON
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
    except Exception as e:
        print(f"AI Plan error: {e}")
        result = {
            "plan": f"🌟 Trip Plan for: {query}\n\nDay 1: Arrival & Check-in\n• Arrive and settle into your hotel\n• Evening: Explore local market\n• Dinner at local restaurant\n\nDay 2: Sightseeing\n• Morning: Top attractions\n• Afternoon: Local cuisine & shopping\n• Evening: Sunset views\n\nBest tip: Book early for best prices!",
            "destination": found_dest or "Your destination",
            "budget": {
                "Hotel (per night)": str(budget // 3 if budget else 3000),
                "Transport": str(budget // 5 if budget else 2000),
                "Food (per day)": str(budget // 6 if budget else 1500),
                "Activities": str(budget // 8 if budget else 1000),
                "Miscellaneous": "500",
                "total": str(budget or 8000)
            },
            "tips": ["Book hotels in advance", "Carry cash for local markets", "Try street food safely"]
        }

    result["hotels"]  = matching_hotels[:4]
    result["flights"] = matching_flights[:3]
    return jsonify(result)


# ── COMMUNITY ────────────────────────────────────────────────

@app.route("/community")
def community():
    # All reviews with user names
    reviews_raw = db.session.query(
        Review, User.name.label("user_name")
    ).join(User, Review.user_id == User.id, isouter=True
    ).order_by(Review.created_at.desc()).limit(20).all()

    reviews = []
    for r, uname in reviews_raw:
        reviews.append({
            "destination": r.destination,
            "rating":      r.rating,
            "comment":     r.comment,
            "created_at":  r.created_at,
            "user_name":   uname or "Traveller"
        })

    # Community photos
    photos_raw = []
    try:
        photos_raw = db.session.execute(
            text("SELECT cp.image_url, cp.destination, cp.caption, u.name as user_name FROM community_photos cp LEFT JOIN users u ON cp.user_id=u.id ORDER BY cp.created_at DESC LIMIT 12")
        ).fetchall()
    except:
        pass

    photos = [{"image_url": p.image_url, "destination": p.destination,
               "user_name": p.user_name} for p in photos_raw]

    # Trending destinations
    trending = db.session.query(
        BookingHistory.destination,
        func.count(BookingHistory.id).label("cnt")
    ).group_by(BookingHistory.destination).order_by(
        func.count(BookingHistory.id).desc()
    ).limit(8).all()

    # Top reviewers
    top_reviewers_raw = db.session.query(
        User.name,
        func.count(Review.id).label("review_count")
    ).join(Review, User.id == Review.user_id, isouter=True
    ).group_by(User.id).order_by(func.count(Review.id).desc()).limit(5).all()

    top_reviewers = []
    for name, rc in top_reviewers_raw:
        trip_count = BookingHistory.query.filter_by(user_id=User.query.filter_by(name=name).first().id if User.query.filter_by(name=name).first() else 0).count()
        top_reviewers.append({"name": name, "review_count": rc, "trip_count": trip_count})

    # Visited destinations for logged-in user
    visited_destinations = []
    if "user_id" in session:
        bookings = BookingHistory.query.filter_by(user_id=session["user_id"]).all()
        visited_destinations = list({b.destination for b in bookings})

    all_destinations = Destination.query.all()

    return render_template("community.html",
        reviews=reviews, photos=photos,
        trending=trending, top_reviewers=top_reviewers,
        visited_destinations=visited_destinations,
        all_destinations=all_destinations,
        total_reviews=Review.query.count(),
        total_photos=len(photos),
        total_users=User.query.count(),
        total_destinations=Destination.query.count(),
        enumerate=enumerate
    )


@app.route("/upload-community-photo", methods=["POST"])
@login_required
def upload_community_photo():
    import base64
    photos      = request.files.getlist("photos")
    destination = request.form.get("destination", "")
    caption     = request.form.get("caption", "")

    for photo in photos:
        if photo and photo.filename:
            # Convert to base64 data URL for storage (simple approach)
            ext      = photo.filename.rsplit('.', 1)[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                continue
            data     = photo.read()
            b64      = base64.b64encode(data).decode()
            data_url = f"data:image/{ext};base64,{b64}"
            # Store in DB
            try:
                db.session.execute(text(
                    "INSERT INTO community_photos (user_id, destination, image_url, caption) VALUES (:uid, :dest, :url, :cap)"
                ), {"uid": session["user_id"], "dest": destination, "url": data_url, "cap": caption})
                db.session.commit()
            except Exception as e:
                print(f"Photo upload error: {e}")
                db.session.rollback()

    flash("Photos shared with the community!", "success")
    return redirect(url_for("community"))


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)