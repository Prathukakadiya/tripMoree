from app import db, app, Destination, Hotel, Amenity, Room, HotelImage

# ---------------- DESTINATION META ----------------
DESTINATION_META = {
    "Goa": ("national", "beach", "honeymoon", "https://images.pexels.com/photos/457882/pexels-photo-457882.jpeg", 4.6, "Oct–Mar"),
    "Manali": ("national", "mountain", "honeymoon", "https://images.pexels.com/photos/753626/pexels-photo-753626.jpeg", 4.5, "Dec–Feb"),
    "Udaipur": ("national", "heritage", "honeymoon", "https://images.pexels.com/photos/189833/pexels-photo-189833.jpeg", 4.7, "Sep–Mar"),
    "Bali": ("international", "beach", "honeymoon", "https://images.pexels.com/photos/2474689/pexels-photo-2474689.jpeg", 4.8, "Apr–Oct"),
    "Paris": ("international", "heritage", "honeymoon", "https://images.pexels.com/photos/338515/pexels-photo-338515.jpeg", 4.6, "Apr–Jun"),
    "Jaipur": ("national", "heritage", "family", "https://images.pexels.com/photos/3672388/pexels-photo-3672388.jpeg", 4.5, "Oct–Mar"),
    "Shimla": ("national", "mountain", "family", "https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg", 4.4, "Mar–Jun"),
    "Kerala": ("national", "nature", "family", "https://images.pexels.com/photos/572897/pexels-photo-572897.jpeg", 4.8, "Sep–Mar"),
    "Dubai": ("international", "city", "family", "https://images.pexels.com/photos/2044434/pexels-photo-2044434.jpeg", 4.7, "Nov–Feb"),
    "Singapore": ("international", "city", "family", "https://images.pexels.com/photos/466685/pexels-photo-466685.jpeg", 4.6, "Feb–Apr"),
    "Ladakh": ("national", "mountain", "adventure", "https://images.pexels.com/photos/5205083/pexels-photo-5205083.jpeg", 4.9, "Jun–Sep"),
    "Rishikesh": ("national", "river", "adventure", "https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg", 4.6, "Sep–Apr"),
    "Spiti Valley": ("national", "mountain", "adventure", "https://images.pexels.com/photos/2437291/pexels-photo-2437291.jpeg", 4.8, "May–Oct"),
    "Switzerland": ("international", "mountain", "adventure", "https://images.pexels.com/photos/417074/pexels-photo-417074.jpeg", 4.9, "May–Sep"),
    "New Zealand": ("international", "nature", "adventure", "https://images.pexels.com/photos/355508/pexels-photo-355508.jpeg", 4.8, "Nov–Apr"),
    "Kedarnath": ("national", "spiritual", "spiritual", "https://images.unsplash.com/photo-1623323849124-58c4b91e5f28", 4.8, "May–Oct"),
    "Varanasi": ("national", "spiritual", "spiritual", "https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg", 4.6, "Oct–Mar"),
    "Rameshwaram": ("national", "spiritual", "spiritual", "https://images.unsplash.com/photo-1600932717369-7b8b5e76e3a6", 4.7, "Oct–Apr"),
    "Mecca": ("international", "spiritual", "spiritual", "https://images.unsplash.com/photo-1591608971362-f08b2a75731a", 5.0, "Nov–Feb"),
    "Vatican City": ("international", "spiritual", "spiritual", "https://images.pexels.com/photos/208739/pexels-photo-208739.jpeg", 4.7, "Mar–Jun"),
    "Kasol": ("national", "mountain", "solo", "https://images.pexels.com/photos/2437291/pexels-photo-2437291.jpeg", 4.5, "Mar–Jun"),
    "Pondicherry": ("national", "beach", "solo", "https://images.pexels.com/photos/753626/pexels-photo-753626.jpeg", 4.4, "Oct–Mar"),
    "Hampi": ("national", "heritage", "solo", "https://images.pexels.com/photos/189833/pexels-photo-189833.jpeg", 4.6, "Oct–Feb"),
    "Amsterdam": ("international", "city", "solo", "https://images.pexels.com/photos/417074/pexels-photo-417074.jpeg", 4.7, "Apr–Jun"),
    "Iceland": ("international", "nature", "solo", "https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg", 4.8, "Jun–Aug"),
}

# ---------------- HOTELS ----------------
DATA = {
    "Goa": [
        ("Taj Resort Goa",5.0,12000),
        ("Leela Palace Goa",5.0,15000),
        ("Goa Marriott",4.8,11000),
        ("Radisson Blu Goa",4.5,9000),
        ("Zostel Goa",3.5,2500),
    ],
    "Manali": [
        ("Snow Valley Manali",4.6,8500),
        ("The Himalayan",4.8,12000),
        ("Manali Heights",4.5,7800),
        ("Zostel Manali",3.6,2300),
    ],
    "Udaipur": [
        ("Taj Lake Palace",5.0,18000),
        ("Trident Udaipur",4.8,12000),
        ("Jagat Niwas Palace",4.4,6500),
    ],
    "Bali": [
        ("Four Seasons Bali",5.0,22000),
        ("Alila Ubud",4.8,16000),
        ("Hard Rock Bali",4.6,11000),
    ],
    # (बाकी locations already covered in META; hotels can be extended later)
}

IMAGES = [
    "https://images.pexels.com/photos/261102/pexels-photo-261102.jpeg",
    "https://images.pexels.com/photos/189296/pexels-photo-189296.jpeg",
    "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg",
]

AMENITIES = ["Pool", "Free WiFi", "Parking", "Gym", "Spa"]

# ---------------- SEED LOGIC ----------------
with app.app_context():

    # Amenities
    for a in AMENITIES:
        if not Amenity.query.filter_by(name=a).first():
            db.session.add(Amenity(name=a))
    db.session.commit()

    amenities = Amenity.query.all()

    # Destinations
    for name, meta in DESTINATION_META.items():
        if not Destination.query.filter_by(name=name).first():
            ct, cat, vt, img, rating, bt = meta
            db.session.add(
                Destination(
                    name=name,
                    country_type=ct,
                    category=cat,
                    vacation_type=vt,
                    image=img,
                    rating=rating,
                    best_time=bt
                )
            )
    db.session.commit()

    # Hotels
    for location, hotels in DATA.items():
        dest = Destination.query.filter_by(name=location).first()

        for hname, stars, price in hotels:
            if Hotel.query.filter_by(name=hname, destination_id=dest.id).first():
                continue

            h = Hotel(
                name=hname,
                destination_id=dest.id,
                stars=stars,
                starting_price=price
            )
            db.session.add(h)
            db.session.commit()

            h.amenities = amenities[:4]

            db.session.add(Room(hotel_id=h.id, room_type="Standard", total_rooms=20, booked_rooms=5))
            db.session.add(Room(hotel_id=h.id, room_type="Deluxe", total_rooms=10, booked_rooms=3))

            for img in IMAGES:
                db.session.add(HotelImage(hotel_id=h.id, image_url=img))

        db.session.commit()

    print("✅ ALL 25 DESTINATIONS SEEDED + HOTELS ADDED SUCCESSFULLY")
