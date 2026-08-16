# OTM Shipment Tracking API

This is a complete shipment tracking API system built with FastAPI, SQLAlchemy, and SQLite. It provides a robust backend for managing orders, shipments, and real-time tracking events (such as 'BOOKED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED').

## Features

- **Order Management:** Create and manage customer orders.
- **Shipment Management:** Assign orders to carriers and create shipments.
- **Webhook Integration:** A unified endpoint to receive real-time shipment status updates from carriers. It supports both `application/json` and `application/xml` payloads.
- **Idempotency:** Webhook endpoints are designed to handle duplicate events gracefully.
- **Shipment Tracking:** Retrieve the complete history and current status of any shipment.
- **SLA Monitoring:** SQL views to calculate SLA breaches (when actual delivery exceeds expected delivery).
- **BI/Dashboard Views:** Pre-built SQL views for Business Intelligence tools (e.g., Power BI, Tableau) to analyze shipment funnels, carrier SLA compliance, and average transit times.
- **Event Simulator:** A built-in Python script to simulate real-world carrier traffic, automatically generating shipments and sending mixed JSON/XML webhooks.

## Project Structure

- `main.py`: The core FastAPI application containing all REST API endpoints.
- `models.py`: SQLAlchemy ORM definitions for `Customer`, `Carrier`, `Order`, `Shipment`, and `ShipmentEvent`.
- `database.py`: Database connection and session management (SQLite).
- `schema.sql`: SQL script to create specific views (like `sla_breaches_view`) required by the API.
- `dashboard_views.sql`: Extra SQL views designed for external BI reporting tools.
- `seed.py`: A utility script to initialize the database schema and populate it with initial seed data (customers, carriers, orders).
- `simulate_events.py`: A standalone simulator that runs a loop to create shipments and post randomized tracking events (via JSON and XML) to the local API.
- `requirements.txt`: Python dependencies.

## Setup Instructions

### 1. Prerequisites

Ensure you have Python 3.8+ installed.

### 2. Install Dependencies

Create a virtual environment (optional but recommended) and install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Initialize the Database

Run the seed script to create the SQLite database (`shipping.db`), build the tables, execute the schema views, and insert initial dummy data.

```bash
python seed.py
```

### 4. Run the API Server

Start the FastAPI development server using Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.
You can view the interactive API documentation (Swagger UI) at `http://localhost:8000/docs`.

## Running the Simulator

To see the system in action, you can run the event simulator in a separate terminal window while the API server is running. This script will mimic carriers creating shipments and posting status updates.

```bash
python simulate_events.py
```

Watch the API server logs and the simulator output to see the webhook events being processed and the shipments advancing through their lifecycle.

## API Endpoints Overview

- `POST /orders`: Create a new order.
- `POST /shipments`: Create a shipment for an order.
- `POST /shipments/{shipment_id}/events`: Webhook to receive a tracking event (JSON/XML).
- `GET /shipments/{shipment_id}/track`: Retrieve the current status and full event history of a shipment.
- `GET /shipments/sla-breaches`: Retrieve a list of shipments that missed their delivery SLA.

## Database & Analytics

The project uses a local SQLite database (`shipping.db`). 
For analytics and BI dashboards, the `dashboard_views.sql` file provides the following views which you can query directly:
- `v_shipment_funnel`: Shipment counts by lifecycle stage.
- `v_carrier_sla_compliance`: On-time delivery percentages grouped by carrier.
- `v_avg_transit_time_by_lane`: Average transit times calculated between origin and destination pairs.
