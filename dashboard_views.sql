-- These views are intended to be consumed by Power BI or other BI tools.

-- 1. Shipment Status Funnel
-- Shows the count of shipments at each stage of the funnel.
CREATE VIEW v_shipment_funnel AS
SELECT 
    '1_Booked' AS stage, COUNT(*) AS shipment_count FROM shipments
UNION ALL
SELECT 
    '2_In_Transit' AS stage, COUNT(*) AS shipment_count FROM shipment_events WHERE status = 'IN_TRANSIT'
UNION ALL
SELECT 
    '3_Delivered' AS stage, COUNT(*) AS shipment_count FROM shipment_events WHERE status = 'DELIVERED'
UNION ALL
SELECT 
    '4_Delayed' AS stage, COUNT(*) AS shipment_count FROM shipment_events WHERE status = 'DELAYED';

-- 2. SLA Compliance % By Carrier
-- Calculates the percentage of shipments that met their SLA (delivered on or before expected time).
CREATE VIEW v_carrier_sla_compliance AS
SELECT 
    c.name AS carrier_name,
    COUNT(s.shipment_id) AS total_shipments,
    SUM(CASE WHEN s.actual_delivery <= s.expected_delivery THEN 1 ELSE 0 END) AS on_time_shipments,
    (CAST(SUM(CASE WHEN s.actual_delivery <= s.expected_delivery THEN 1 ELSE 0 END) AS FLOAT) / COUNT(s.shipment_id)) * 100 AS compliance_percentage
FROM 
    carriers c
JOIN 
    shipments s ON c.carrier_id = s.carrier_id
WHERE 
    s.actual_delivery IS NOT NULL
GROUP BY 
    c.name;

-- 3. Average Transit Time By Lane (Origin - Destination)
-- Calculates the average time a shipment takes from Ship Date to Actual Delivery for a specific lane.
CREATE VIEW v_avg_transit_time_by_lane AS
SELECT 
    origin,
    destination,
    origin || ' to ' || destination AS lane,
    COUNT(shipment_id) AS total_shipments,
    -- Average transit time in hours (SQLite syntax, for Postgres use EXTRACT(EPOCH...))
    AVG((julianday(actual_delivery) - julianday(ship_date)) * 24) AS avg_transit_time_hours
FROM 
    shipments
WHERE 
    actual_delivery IS NOT NULL AND ship_date IS NOT NULL
GROUP BY 
    origin, destination;
