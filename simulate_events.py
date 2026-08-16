import time
import requests
import random
import datetime

API_BASE_URL = "http://localhost:8000"

def get_random_carrier():
    return random.choice([1, 2, 3])

def create_shipment():
    order_id = random.choice([1, 2])
    payload = {
        "order_id": order_id,
        "carrier_id": get_random_carrier(),
        "origin": random.choice(["New York", "Chicago", "Los Angeles", "Houston"]),
        "destination": random.choice(["Miami", "Seattle", "Denver", "Boston"]),
        "expected_delivery": (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=random.randint(1, 5))).isoformat()
    }
    try:
        response = requests.post(f"{API_BASE_URL}/shipments", json=payload)
        if response.status_code == 200:
            shipment = response.json()
            print(f"Created Shipment {shipment['shipment_id']} for Order {order_id}")
            return shipment['shipment_id']
        else:
            print(f"Failed to create shipment (Status {response.status_code}):", response.text)
            return None
    except requests.RequestException as e:
        print(f"Connection error when creating shipment: {e}")
        return None

def send_event_json(shipment_id, status, location):
    payload = {
        "status": status,
        "location": location
    }
    try:
        response = requests.post(f"{API_BASE_URL}/shipments/{shipment_id}/events", json=payload)
        if response.status_code == 200:
            print(f"[{shipment_id}] JSON Event '{status}':", response.json())
        else:
            print(f"[{shipment_id}] JSON Event '{status}' Failed (Status {response.status_code}):", response.text)
    except requests.RequestException as e:
        print(f"[{shipment_id}] Connection error for JSON Event: {e}")

def send_event_xml(shipment_id, status, location):
    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<Event>
    <status>{status}</status>
    <location>{location}</location>
</Event>"""
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(f"{API_BASE_URL}/shipments/{shipment_id}/events", data=payload, headers=headers)
        if response.status_code == 200:
            print(f"[{shipment_id}] XML Event '{status}':", response.json())
        else:
            print(f"[{shipment_id}] XML Event '{status}' Failed (Status {response.status_code}):", response.text)
    except requests.RequestException as e:
        print(f"[{shipment_id}] Connection error for XML Event: {e}")

def simulate():
    print("Starting simulator...")
    
    # Keep track of active shipments and their current stage
    active_shipments = {}
    
    stages = ["PICKED_UP", "IN_TRANSIT", "DELIVERED"]

    for _ in range(15): # Run 15 simulation loops
        # 1. Randomly create a new shipment
        if random.random() > 0.5:
            shipment_id = create_shipment()
            if shipment_id:
                active_shipments[shipment_id] = 0 # index in stages array

        # 2. Update existing shipments
        completed = []
        for s_id, stage_idx in active_shipments.items():
            if random.random() > 0.4: # 60% chance to advance
                status = stages[stage_idx]
                location = random.choice(["Warehouse A", "Checkpoint B", "Distribution Center C", "Final Destination"])
                
                # Randomly choose JSON or XML to demonstrate parsing both
                if random.choice(["json", "xml"]) == "json":
                    send_event_json(s_id, status, location)
                else:
                    send_event_xml(s_id, status, location)
                
                active_shipments[s_id] += 1
                
                if active_shipments[s_id] >= len(stages):
                    completed.append(s_id)
        
        # Remove completed shipments
        for s_id in completed:
            del active_shipments[s_id]
            
        time.sleep(2)
        
    print("Simulation finished.")

if __name__ == "__main__":
    simulate()
