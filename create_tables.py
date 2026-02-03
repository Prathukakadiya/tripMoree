from app import app, db

print("Starting table creation...")

with app.app_context():
    db.create_all()

print("Tables created successfully")
