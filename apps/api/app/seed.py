from datetime import date, time, timedelta
from decimal import Decimal

from app.db import get_store
from app.init_db import initialize
from app.models import Availability, Practitioner, VerificationStatus

PEOPLE = [
    ("Adaeze", "Okafor", "Dermatology", "Consultant Dermatologist", "Awka", "Anambra", 18000, 9),
    (
        "Tunde",
        "Balogun",
        "General Physician",
        "Family Medicine Physician",
        "Awka",
        "Anambra",
        12000,
        12,
    ),
    ("Amara", "Eze", "Pediatrics", "Consultant Paediatrician", "Onitsha", "Anambra", 15000, 8),
    ("Chidi", "Nwosu", "Cardiology", "Consultant Cardiologist", "Enugu", "Enugu", 24000, 15),
    ("Zainab", "Musa", "Gynecology", "Consultant Gynaecologist", "Abuja", "FCT", 22000, 11),
    ("Emeka", "Ibe", "Orthopedics", "Orthopaedic Surgeon", "Port Harcourt", "Rivers", 25000, 14),
    ("Halima", "Bello", "Mental Health", "Consultant Psychiatrist", "Lagos", "Lagos", 20000, 10),
    ("Kelechi", "Obi", "General Physician", "Medical Officer", "Awka", "Anambra", 10000, 6),
    ("Ifeoma", "Udeh", "Dermatology", "Dermatology Specialist", "Enugu", "Enugu", 17000, 7),
    ("Boma", "George", "Pediatrics", "Paediatrician", "Port Harcourt", "Rivers", 16000, 9),
    ("Amina", "Yusuf", "Cardiology", "Cardiology Specialist", "Abuja", "FCT", 23000, 13),
    ("Ngozi", "Onyema", "Gynecology", "Gynaecologist", "Onitsha", "Anambra", 19000, 10),
    ("Femi", "Adeyemi", "Orthopedics", "Orthopaedic Specialist", "Lagos", "Lagos", 26000, 16),
    ("Nneka", "Okoli", "Mental Health", "Clinical Psychiatrist", "Awka", "Anambra", 17500, 8),
    ("Sani", "Abdullahi", "General Physician", "Primary Care Physician", "Abuja", "FCT", 13000, 9),
]


def run():
    with get_store() as db:
        initialize(db.database)
        if db.find_one(Practitioner):
            return
        for n, (first, last, specialty, title, city, state, fee, years) in enumerate(PEOPLE, 1):
            p = Practitioner(
                first_name=first,
                last_name=last,
                specialty=specialty,
                professional_title=title,
                license_number=f"DEMO-NG-{n:04}",
                country="Nigeria",
                state=state,
                city=city,
                consultation_fee=Decimal(fee),
                years_of_experience=years,
                verification_status=VerificationStatus.verified,
                bio="Fictional demonstration practitioner profile for product testing only.",
                rating=Decimal("4.8"),
                profile_image_url=None,
            )
            db.insert(p)
            for day in range(1, 8):
                for hour in (9, 11, 14):
                    db.insert(
                        Availability(
                            practitioner_id=p.id,
                            date=date.today() + timedelta(days=day),
                            start_time=time(hour),
                            end_time=time(hour + 1),
                        )
                    )


if __name__ == "__main__":
    run()
