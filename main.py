from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import xmltodict
from pydantic import BaseModel
import datetime

import models
from database import engine, get_db

# Create all tables (in a real app, use Alembic migrations)
models.Base.metadata.create_all(bind=engine)

# Create Views after tables are created
with engine.connect() as conn:
    try:
        # Read and execute schema.sql
        with open("schema.sql", "r") as f:
            statements = f.read().split(";")
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement.strip()))
        conn.commit()
    except Exception as e:
        print("Schema/views might already exist or failed to create:", e)

app = FastAPI(title="OTM Shipment Tracking API")

# --- Pydantic Schemas ---

class OrderCreate(BaseModel):
    customer_id: int
    priority: str = "NORMAL"

class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    status: str
    priority: str
    order_date: datetime.datetime

    class Config:
        orm_mode = True

class ShipmentCreate(BaseModel):
    order_id: int
    carrier_id: int
    origin: str
    destination: str
    expected_delivery: datetime.datetime

class ShipmentResponse(BaseModel):
    shipment_id: int
    order_id: int
    carrier_id: int
    origin: str
    destination: str
    status: Optional[str] = None

    class Config:
        orm_mode = True

class EventCreate(BaseModel):
    status: str
    location: str

class EventResponse(BaseModel):
    event_id: int
    shipment_id: int
    status: str
    location: str
    event_timestamp: datetime.datetime

    class Config:
        orm_mode = True

class TrackingResponse(BaseModel):
    shipment_id: int
    current_status: Optional[str]
    events: List[EventResponse]

# --- API Endpoints ---

@app.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = models.Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.post("/shipments", response_model=ShipmentResponse)
def create_shipment(shipment: ShipmentCreate, db: Session = Depends(get_db)):
    # Check if order exists
    order = db.query(models.Order).filter(models.Order.order_id == shipment.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if carrier exists
    carrier = db.query(models.Carrier).filter(models.Carrier.carrier_id == shipment.carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    db_shipment = models.Shipment(
        **shipment.dict(),
        ship_date=datetime.datetime.now(datetime.UTC)
    )
    db.add(db_shipment)
    
    # Update order status to booked
    order.status = models.OrderStatus.BOOKED
    
    db.commit()
    db.refresh(db_shipment)
    
    # Add initial BOOKED event
    initial_event = models.ShipmentEvent(
        shipment_id=db_shipment.shipment_id,
        status=models.ShipmentStatus.BOOKED,
        location=db_shipment.origin
    )
    db.add(initial_event)
    db.commit()

    return db_shipment

@app.post("/shipments/{shipment_id}/events")
async def create_event(shipment_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint that accepts both JSON and XML payloads from Carriers.
    """
    content_type = request.headers.get('Content-Type', '')
    
    # Check if shipment exists
    shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    status = None
    location = None

    if 'application/json' in content_type:
        data = await request.json()
        status = data.get('status')
        location = data.get('location')
    elif 'application/xml' in content_type or 'text/xml' in content_type:
        body = await request.body()
        try:
            data = xmltodict.parse(body)
            # Expecting <Event><status>...</status><location>...</location></Event>
            event_data = data.get('Event', {})
            status = event_data.get('status')
            location = event_data.get('location')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid XML payload: {str(e)}")
    else:
        raise HTTPException(status_code=415, detail="Unsupported Media Type. Use JSON or XML.")

    if not status or not location:
        raise HTTPException(status_code=422, detail="Missing status or location in payload")

    # Prevent duplicate events for the same status (based on the UniqueConstraint)
    existing_event = db.query(models.ShipmentEvent).filter(
        models.ShipmentEvent.shipment_id == shipment_id,
        models.ShipmentEvent.status == status
    ).first()
    
    if existing_event:
        # Idempotent response for webhooks
        return {"msg": "Event already recorded", "event_id": existing_event.event_id}

    new_event = models.ShipmentEvent(
        shipment_id=shipment_id,
        status=status,
        location=location
    )
    db.add(new_event)
    
    # If delivered, set actual delivery date
    if status == models.ShipmentStatus.DELIVERED:
        shipment.actual_delivery = datetime.datetime.now(datetime.UTC)

    db.commit()
    db.refresh(new_event)
    
    return {"msg": "Event created", "event_id": new_event.event_id}

@app.get("/shipments/{shipment_id}/track", response_model=TrackingResponse)
def track_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
        
    events = db.query(models.ShipmentEvent).filter(models.ShipmentEvent.shipment_id == shipment_id).order_by(models.ShipmentEvent.event_timestamp.desc()).all()
    
    current_status = events[0].status if events else None
    
    return {
        "shipment_id": shipment_id,
        "current_status": current_status,
        "events": events
    }

@app.get("/shipments/sla-breaches")
def get_sla_breaches(db: Session = Depends(get_db)):
    """
    Returns shipments that missed SLA by querying the SQL view `sla_breaches_view`.
    """
    try:
        result = db.execute(text("SELECT * FROM sla_breaches_view"))
        breaches = [dict(row._mapping) for row in result]
        return {"breaches": breaches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
