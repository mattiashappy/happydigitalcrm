"""
Run once on Heroku to seed all Happy Digital clients and tasks:
  heroku run python seed_data.py --app happydigital
"""
from app import app, db, seed_users
from models import User, Contact, Task
from datetime import date

CLIENTS = [
    # Mattias solo
    {"name": "Strängnäs Bilskrot",          "company": "Strängnäs Bilskrot",             "notes": "Services: SEO, Clickease\nAssigned: Mattias"},
    {"name": "Acceptus AB",                  "company": "Acceptus AB",                    "notes": "Services: Google Ads, SEO\nAssigned: Mattias"},
    {"name": "Din Egen tid AB",              "company": "Din Egen tid AB",                "notes": "Services: Google Ads\nAssigned: Mattias\nContact: Fredrik (tracking/boka.egentid.se)"},
    {"name": "Ekmans Bilskrot AB",           "company": "Ekmans Bilskrot AB",             "notes": "Services: Google Ads\nAssigned: Mattias"},
    {"name": "Motor-Center i Gröndal AB",   "company": "Motor-Center i Gröndal AB",      "notes": "Services: Google Ads\nAssigned: Mattias"},
    {"name": "Hélène Stolt Psykoterapi",    "company": "Hélène Stolt Psykoterapi",       "notes": "Services: Google Ads\nAssigned: Mattias"},
    {"name": "Connect flytt och städ",       "company": "Connect flytt och städ",         "notes": "Services: Google Ads\nAssigned: Mattias"},
    {"name": "Askari Juristbyrå AB",         "company": "Askari Juristbyrå AB",           "notes": "Services: Google Ads\nAssigned: Mattias"},
    {"name": "Söderorts VVS och Bygg AB",   "company": "Söderorts VVS och Bygg AB",      "notes": "Services: SEO\nAssigned: Mattias"},
    {"name": "LP ekonomi & konsulting AB",  "company": "LP ekonomi & konsulting AB",     "notes": "Services: Google Ads\nAssigned: Mattias"},
    {"name": "Svensk Fastighetsbesiktning AB", "company": "Svensk Fastighetsbesiktning AB", "notes": "Services: Google Ads\nAssigned: Mattias"},
    # Daniel solo
    {"name": "BeerPLZ AB",                   "company": "BeerPLZ AB",                     "notes": "Services: Meta\nAssigned: Daniel\nStatus: Fail — decide if churned"},
    {"name": "Petfeed / BugHug",             "company": "Petfeed / BugHug",               "notes": "Services: Facebook\nAssigned: Daniel\nStatus: Ett till möte"},
    {"name": "Breeze Academy",               "company": "Breeze Academy",                 "notes": "Services: Meta\nAssigned: Daniel\nStatus: Ett till möte"},
    {"name": "Morse Studios",                "company": "Morse Studios (0011morse)",      "notes": "Services: Meta\nAssigned: Daniel\nStatus: Väntar på kund"},
    {"name": "Benjamin Cadette",             "company": "Benjamin Cadette",               "notes": "Services: Meta\nAssigned: Daniel\nStatus: Dubbelkolla"},
    {"name": "Arlandastad Golf",             "company": "Arlandastad Golf",               "notes": "Services: Meta\nAssigned: Daniel\nStatus: Ett till möte"},
    # Shared
    {"name": "Ackermann Comfort AB",         "company": "Ackermann Comfort AB",           "notes": "Services: Google Ads (Mattias) + Meta (Daniel)\nStatus: Går bra\nLast invoice: 2026-04-01"},
    {"name": "Dahlbacka Bil AB",             "company": "Dahlbacka Bil AB",               "notes": "Services: Google Ads (Mattias) + Meta (Daniel)\nStatus: Oklart — dubbelkolla med Daniel\nLast invoice: 2026-04-01"},
    {"name": "Nynäs Städhjälp & Service AB","company": "Nynäs Städhjälp & Service AB",   "notes": "Services: Google Ads (Mattias) + Facebook (Daniel)\nStatus: Dubbelkolla\nLast invoice: 2026-04-02"},
    {"name": "Sveda & Värk AB",              "company": "Sveda & Värk AB",                "notes": "Services: Google Ads (Mattias) + Facebook (Daniel)\nStatus: Dubbelkolla\nLast invoice: 2026-04-01"},
    {"name": "Olles Bilrekond Gävleborg AB", "company": "Olles Bilrekond Gävleborg AB",   "notes": "Services: Google Ads (Mattias) + Facebook (Daniel)\nStatus: Bra"},
]

TASKS = [
    {
        "title": "Aprilloptimering – Mattias klienter",
        "description": "Document April optimization for all 12 Google Ads/SEO clients: Strängnäs Bilskrot, Acceptus, Din Egen tid, Ekmans Bilskrot, Motor-Center, Hélène Stolt, Connect, Askari, Söderorts VVS, LP ekonomi, Svensk Fastighetsbesiktning",
        "due_date": date(2026, 4, 30),
        "assigned_to": "Mattias",
    },
    {
        "title": "Aprilloptimering – Gemensamma kunder",
        "description": "Document April optimization for 5 shared clients (Google Ads side): Ackermann, Dahlbacka, Nynäs Städ, Sveda & Värk, Olles Bilrekond Gävleborg. Coordinate Meta side with Daniel.",
        "due_date": date(2026, 4, 30),
        "assigned_to": "Mattias",
    },
    {
        "title": "Dubbelkolla Nynäs Städ",
        "description": "Flagged in 2026 Hub as needing review. Check both Google Ads and Facebook channels.",
        "due_date": date(2026, 4, 30),
        "assigned_to": "Mattias",
    },
    {
        "title": "Dubbelkolla Sveda & Värk AB",
        "description": "Flagged in 2026 Hub as needing review. Check both channels.",
        "due_date": date(2026, 4, 30),
        "assigned_to": "Mattias",
    },
    {
        "title": "Dubbelkolla Benjamin Cadette",
        "description": "Flagged on Daniel's Meta side, worth syncing with Daniel.",
        "due_date": date(2026, 4, 30),
        "assigned_to": "Daniel",
    },
    {
        "title": "Följa upp BeerPLZ",
        "description": "Hub note says 'Fail' — decide if client has churned.",
        "due_date": date(2026, 4, 30),
        "assigned_to": "Daniel",
    },
]


def run():
    with app.app_context():
        db.create_all()
        seed_users()

        if Contact.query.count() > 0:
            print("Contacts already seeded — skipping.")
            return

        mattias = User.query.filter(User.name.ilike('%Mattias%')).first()
        daniel = User.query.filter(User.name.ilike('%Daniel%')).first()

        # Seed contacts
        contact_map = {}
        for c in CLIENTS:
            contact = Contact(name=c["name"], company=c["company"], notes=c["notes"])
            db.session.add(contact)
            db.session.flush()
            contact_map[c["name"]] = contact
        print(f"Added {len(CLIENTS)} contacts.")

        # Seed tasks
        for t in TASKS:
            assigned = mattias if t["assigned_to"] == "Mattias" else daniel
            task = Task(
                title=t["title"],
                description=t["description"],
                due_date=t["due_date"],
                assigned_to_id=assigned.id if assigned else None,
            )
            db.session.add(task)
        print(f"Added {len(TASKS)} tasks.")

        db.session.commit()
        print("Done.")


if __name__ == "__main__":
    run()
