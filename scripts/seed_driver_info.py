import csv
from pathlib import Path

from app.core.database import SessionLocal
from app.models.driver_info import DriverInfo

try:
    from werkzeug.security import generate_password_hash
except ImportError:
    generate_password_hash = None


CSV_PATH = Path("seed_data/driver.csv")


def hash_password(password: str) -> str:
    if generate_password_hash:
        return generate_password_hash(password)
    return password  # fallback (not recommended for production)


def run():
    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        if not CSV_PATH.exists():
            raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

        with CSV_PATH.open("r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row in reader:
                name = (row.get("name") or "").strip()
                email = (row.get("email") or "").strip().lower()
                password = (row.get("password") or "").strip()
                phone = (row.get("phone") or "").strip() or None

                # basic validation
                if not name or not email or not password:
                    print(f"Skipping invalid row: {row}")
                    skipped += 1
                    continue

                # check if already exists
                existing = (
                    db.query(DriverInfo)
                    .filter(DriverInfo.email == email)
                    .first()
                )

                if existing:
                    print(f"Skipping existing driver: {email}")
                    skipped += 1
                    continue

                driver = DriverInfo(
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    phone=phone,
                )

                db.add(driver)
                inserted += 1

            db.commit()
            print(f"DriverInfo seed complete. Inserted: {inserted}, Skipped: {skipped}")

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()


if __name__ == "__main__":
    run()