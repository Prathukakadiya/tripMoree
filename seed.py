from app import app, db
from app import HiddenStreetFood, NightSafetyZones, LocalEtiquettes, TouristAlertsTips

with app.app_context():

    db.session.add(HiddenStreetFood(
        location_name="Goa",
        food_name="Kokni Kanteen",
        description="Authentic Goan seafood & fish thalis.",
        rating=4.8,
        place="Panaji"
    ))

    db.session.add(NightSafetyZones(
        location_name="Goa",
        title="Safe at Night",
        description="Tourist beaches & city areas are lively and patrolled."
    ))

    db.session.add(LocalEtiquettes(
        location_name="Goa",
        title="Dress Code",
        description="Wear decent clothes in villages & churches."
    ))

    db.session.add(TouristAlertsTips(
        location_name="Goa",
        title="Common Scams",
        description="Avoid fake tour guides & overpriced activities."
    ))

    db.session.commit()

print("✅ Goa demo data inserted")
