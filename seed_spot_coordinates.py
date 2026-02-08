from app import app, db
from sqlalchemy import text
import random

DEST_BASE = {
    1:(15.50,73.80), 2:(32.25,77.18), 3:(24.58,73.68),
    4:(-8.65,115.22), 5:(48.85,2.35), 6:(26.91,75.78),
    7:(31.10,77.17), 8:(9.59,76.52), 9:(25.20,55.27),
    10:(1.35,103.82), 11:(34.15,77.58), 12:(30.10,78.29),
    13:(32.30,78.00), 14:(46.80,8.23), 15:(-45.03,168.66),
    16:(30.73,79.06), 17:(25.31,83.01), 18:(9.28,79.31),
    19:(21.42,39.82), 20:(41.90,12.45), 21:(32.00,77.31),
    22:(11.93,79.83), 23:(15.33,76.46), 24:(52.37,4.90),
    25:(64.13,-21.90)
}

with app.app_context():
    spots = db.session.execute(
        text("SELECT id, destination_id FROM hype_spots")
    ).fetchall()

    for s in spots:
        base_lat, base_lng = DEST_BASE[s.destination_id]
        lat = base_lat + random.uniform(0.01, 0.05)
        lng = base_lng + random.uniform(0.01, 0.05)

        db.session.execute(
            text("""
                UPDATE hype_spots
                SET latitude = :lat, longitude = :lng
                WHERE id = :id
            """),
            {"lat": lat, "lng": lng, "id": s.id}
        )

    db.session.commit()
    print("✅ ALL SPOTS UPDATED WITH DUMMY COORDINATES")
