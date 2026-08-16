import datetime
from sqlalchemy.orm import Session
from database import engine, get_db
import models

def init_db():
    models.Base.metadata.create_all(bind=engine)
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            with open("schema.sql", "r") as f:
                for stmt in f.read().split(";"):
                    if stmt.strip():
                        conn.execute(text(stmt.strip()))
            conn.commit()
        except Exception as e:
            print("Schema error (might exist):", e)

def seed_data():
    init_db()
    db = Session(bind=engine)
    
    # 1. Customers
    c1 = models.Customer(name="Acme Corp", region="North America")
    c2 = models.Customer(name="Global Tech", region="Europe")
    db.add_all([c1, c2])
    db.commit()

    # 2. Carriers
    car1 = models.Carrier(name="Speedy Express", mode="road", sla_hours=48)
    car2 = models.Carrier(name="AirFreight Pro", mode="air", sla_hours=24)
    car3 = models.Carrier(name="RailLogistics", mode="rail", sla_hours=96)
    db.add_all([car1, car2, car3])
    db.commit()

    # 3. Create some dummy Orders (which in a real system could be created via API)
    o1 = models.Order(customer_id=c1.customer_id, priority="HIGH")
    o2 = models.Order(customer_id=c2.customer_id, priority="NORMAL")
    db.add_all([o1, o2])
    db.commit()

    print("Database seeded with customers, carriers, and orders successfully!")

if __name__ == "__main__":
    seed_data()
