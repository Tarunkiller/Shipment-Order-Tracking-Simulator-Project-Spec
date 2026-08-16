-- This file contains the schema details, including views and indexes,
-- which are either automatically created by the ORM or should be run manually
-- after ORM table creation.

-- 1. Unique constraint to prevent duplicate events for the same shipment status
-- Note: This is defined in models.py as __table_args__ = (UniqueConstraint('shipment_id', 'status'),)
-- but in pure SQL it looks like:
-- ALTER TABLE shipment_events ADD CONSTRAINT _shipment_status_uc UNIQUE (shipment_id, status);

-- 2. Index for query performance on tracking endpoints
-- Note: This is created automatically by SQLAlchemy (index=True on the column)
-- CREATE INDEX ix_shipment_events_shipment_id ON shipment_events (shipment_id);

-- 3. View calculating SLA breach
-- This view filters shipments where the actual delivery date is after the expected delivery date.
CREATE VIEW sla_breaches_view AS
SELECT 
    s.shipment_id,
    s.order_id,
    c.name AS carrier_name,
    s.origin,
    s.destination,
    s.expected_delivery,
    s.actual_delivery,
    -- Calculate delay in hours (SQLite specific date manipulation for demo, adjust for Postgres/MySQL)
    (julianday(s.actual_delivery) - julianday(s.expected_delivery)) * 24 AS delay_hours
FROM 
    shipments s
JOIN 
    carriers c ON s.carrier_id = c.carrier_id
WHERE 
    s.actual_delivery IS NOT NULL 
    AND s.actual_delivery > s.expected_delivery;
