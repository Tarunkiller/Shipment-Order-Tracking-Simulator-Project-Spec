from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from database import Base
import datetime

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"

class ShipmentStatus(str, enum.Enum):
    BOOKED = "BOOKED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELAYED = "DELAYED"
    DELIVERED = "DELIVERED"

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    region = Column(String)

    orders = relationship("Order", back_populates="customer")

class Carrier(Base):
    __tablename__ = "carriers"
    carrier_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    mode = Column(String) # road/air/rail
    sla_hours = Column(Integer)

    shipments = relationship("Shipment", back_populates="carrier")

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    order_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    status = Column(String, default=OrderStatus.PENDING)
    priority = Column(String)

    customer = relationship("Customer", back_populates="orders")
    shipments = relationship("Shipment", back_populates="order")

class Shipment(Base):
    __tablename__ = "shipments"
    shipment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    carrier_id = Column(Integer, ForeignKey("carriers.carrier_id"))
    origin = Column(String)
    destination = Column(String)
    ship_date = Column(DateTime)
    expected_delivery = Column(DateTime)
    actual_delivery = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="shipments")
    carrier = relationship("Carrier", back_populates="shipments")
    events = relationship("ShipmentEvent", back_populates="shipment", order_by="ShipmentEvent.event_timestamp")

class ShipmentEvent(Base):
    __tablename__ = "shipment_events"
    event_id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.shipment_id"), index=True)
    status = Column(String)
    event_timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    location = Column(String)

    shipment = relationship("Shipment", back_populates="events")

    __table_args__ = (
        UniqueConstraint('shipment_id', 'status', name='_shipment_status_uc'),
    )
