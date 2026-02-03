import sqlite3
import pymysql

# -------- SQLITE (OLD DB) --------
sqlite_conn = sqlite3.connect("instance/tripmoreee.db")
sqlite_cur = sqlite_conn.cursor()

# -------- MYSQL (NEW DB) --------
mysql_conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="tripmoreee"
)
mysql_cur = mysql_conn.cursor()

print("🔄 Connected to both databases")

# ---------- DESTINATION ----------
sqlite_cur.execute("SELECT * FROM destination")
destinations = sqlite_cur.fetchall()

for d in destinations:
    mysql_cur.execute(
        "INSERT IGNORE INTO destination VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        d
    )

mysql_conn.commit()
print("✅ Destination migrated")

# ---------- HOTEL ----------
sqlite_cur.execute("SELECT * FROM hotel")
hotels = sqlite_cur.fetchall()

for h in hotels:
    mysql_cur.execute(
        "INSERT IGNORE INTO hotel VALUES (%s,%s,%s,%s,%s)",
        h
    )

mysql_conn.commit()
print("✅ Hotel migrated")

# ---------- AMENITY ----------
# ---------- AMENITY ----------
sqlite_cur.execute("SELECT * FROM amenity")
amenities = sqlite_cur.fetchall()

for a in amenities:
    mysql_cur.execute(
        "INSERT IGNORE INTO amenity VALUES (%s,%s)",
        a
    )

mysql_conn.commit()
print("✅ Amenity migrated")
# ---------- HOTEL_AMENITIES ----------
sqlite_cur.execute("SELECT * FROM hotel_amenities")
rows = sqlite_cur.fetchall()

for r in rows:
    mysql_cur.execute(
        "INSERT IGNORE INTO hotel_amenities VALUES (%s,%s)",
        r
    )

mysql_conn.commit()
print("✅ Hotel_amenities migrated")
# ---------- ROOM ----------
sqlite_cur.execute("SELECT * FROM room")
rooms = sqlite_cur.fetchall()

for r in rooms:
    mysql_cur.execute(
        "INSERT IGNORE INTO room VALUES (%s,%s,%s,%s,%s,%s)",
        r
    )

mysql_conn.commit()
print("✅ Room migrated")
# ---------- HOTEL_IMAGE ----------
sqlite_cur.execute("SELECT * FROM hotel_image")
images = sqlite_cur.fetchall()

for i in images:
    mysql_cur.execute(
        "INSERT IGNORE INTO hotel_image VALUES (%s,%s,%s)",
        i
    )

mysql_conn.commit()
print("✅ Hotel_image migrated")


# ---------- CLOSE CONNECTIONS (ONLY ONCE, AT END) ----------
sqlite_conn.close()
mysql_conn.close()

print("🎉 ALL MIGRATION DONE")
