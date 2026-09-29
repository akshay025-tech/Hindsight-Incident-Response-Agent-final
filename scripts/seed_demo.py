"""Seed demo incidents and data into SQLite database."""
import json
import os
import sys
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.database import create_tables, SessionLocal, IncidentDB, utc_now
from app.models.incident import Severity, IncidentStatus


def seed_demo_data():
    create_tables()
    db = SessionLocal()

    incidents_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../backend/app/data/incidents.json")
    )
    if not os.path.exists(incidents_path):
        print(f"Error: {incidents_path} not found.")
        return

    with open(incidents_path, "r", encoding="utf-8") as f:
        incidents_data = json.load(f)

    count_added = 0
    for inc in incidents_data:
        existing = db.query(IncidentDB).filter(IncidentDB.id == inc["id"]).first()
        if not existing:
            db_inc = IncidentDB(
                id=inc["id"],
                title=inc["title"],
                service=inc["service"],
                severity=inc.get("severity", Severity.HIGH.value),
                status=inc.get("status", IncidentStatus.OPEN.value),
                description=inc.get("description", ""),
                symptoms=inc.get("symptoms", []),
                metrics=inc.get("metrics", {}),
                logs=inc.get("logs", []),
                deployment=inc.get("deployment", {}),
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(db_inc)
            count_added += 1

    db.commit()
    db.close()
    print(f"✅ Successfully seeded {count_added} demo incident(s) into database.")


if __name__ == "__main__":
    seed_demo_data()
