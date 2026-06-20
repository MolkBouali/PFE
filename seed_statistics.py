import random
from datetime import date, timedelta
from backend.database.connection import SessionLocal
from sqlalchemy import text

def seed_stats():
    db = SessionLocal()
    try:
        print("Starting statistics data seeding...")

        regions = ["Tunis", "Enfidha", "Monastir", "Djerba", "Sfax", "Tozeur", "Gafsa", "Tabarka", "Gabès"]
        statuts = ["en_attente", "en_cours", "traite"]
        avis_options = ["Favorable", "Favorable avec balisage", "Défavorable"]
        
        # Generate a range of dates for 2025 and 2026
        start_date = date(2025, 1, 1)
        end_date = date(2026, 12, 31)
        delta_days = (end_date - start_date).days

        num_dossiers = 500 # Sufficient amount for a realistic dashboard
        
        created_count = 0
        for i in range(num_dossiers):
            # Random date within range
            random_days = random.randint(0, delta_days)
            depot_date = start_date + timedelta(days=random_days)
            
            # Random region and status
            region = random.choice(regions)
            statut = random.choice(statuts)
            numero = f"DOSS-{depot_date.year}-{i:04d}"
            
            # Insert Dossier
            # Using raw SQL for simplicity in seeding script to avoid complex ORM model imports if not fully established
            db.execute(
                text("INSERT INTO dossiers (numero_dossier, nom_demandeur, region, statut, date_depot, identifiant_depositaire) "
                     "VALUES (:num, :nom, :reg, :stat, :date, :id_dep)"),
                {"num": numero, "nom": f"Demandeur {i}", "reg": region, "stat": statut, "date": depot_date, "id_dep": "ADMIN_SEED"}
            )
            
            # If traite, insert into decisions_avis
            if statut == "traite":
                # We need the id of the inserted dossier. 
                # Since SERIAL, we can get current val or just search by numero.
                res = db.execute(text("SELECT id FROM dossiers WHERE numero_dossier = :num"), {"num": numero}).fetchone()
                if res:
                    dossier_id = res[0]
                    avis = random.choice(avis_options)
                    db.execute(
                        text("INSERT INTO decisions_avis (dossier_id, type_avis) VALUES (:id, :avis)"),
                        {"id": dossier_id, "avis": avis}
                    )
            
            created_count += 1

        db.commit()
        print(f"Successfully seeded {created_count} dossiers and corresponding decisions.")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_stats()