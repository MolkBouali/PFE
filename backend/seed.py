import datetime
from backend.database.connection import SessionLocal
from backend.core.security import hash_password
from backend.models.utilisateur import Utilisateur


def get_password_hash(password):
    try:
        return hash_password(password)
    except Exception:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def seed_users():
    db = SessionLocal()
    try:
        print("Seeding users...")

        # Check if users already exist
        existing_admin = db.query(Utilisateur).filter(Utilisateur.identifiant == "admin").first()
        existing_agent = db.query(Utilisateur).filter(Utilisateur.identifiant == "agent1").first()

        if not existing_admin:
            admin = Utilisateur(
                identifiant="admin",
                mot_de_passe_hash=get_password_hash("admin123"),
                nom="Administrateur",
                prenom="Système",
                matricule="ADM001",
                role="admin",
                statut=True
            )
            db.add(admin)
            print("  ✓ Created admin user (admin / admin123)")
        else:
            print("  - admin user already exists, skipping")

        if not existing_agent:
            agent = Utilisateur(
                identifiant="agent1",
                mot_de_passe_hash=get_password_hash("agent123"),
                nom="Dupont",
                prenom="Jean",
                matricule="AGT001",
                role="agent",
                statut=True
            )
            db.add(agent)
            print("  ✓ Created agent user (agent1 / agent123)")
        else:
            print("  - agent1 user already exists, skipping")

        db.commit()
        print("Users seeded successfully!")

    except Exception as e:
        print(f"Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()