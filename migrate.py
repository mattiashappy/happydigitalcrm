"""
Run once to apply schema changes:
  heroku run python migrate.py --app happydigital
"""
from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(db.text("ALTER TABLE contact ADD COLUMN monthly_fee FLOAT"))
            conn.commit()
            print("Added monthly_fee to contact.")
        except Exception as e:
            conn.rollback()
            print(f"monthly_fee already exists or error: {e}")

        try:
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS cost (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    amount FLOAT NOT NULL,
                    category VARCHAR(50) DEFAULT 'Other',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
            print("Created cost table.")
        except Exception as e:
            conn.rollback()
            print(f"cost table error: {e}")

    print("Done.")
