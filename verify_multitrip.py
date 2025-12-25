import requests
import sys
import uuid
import time

BASE_URL = "http://localhost:8000/api"
ADMIN_TOKEN = "admin123"

def test_multitrip():
    print("Starting Multi-Trip Verification...")
    
    auth_headers = {"X-Admin-Token": ADMIN_TOKEN}
    
    # 1. Create Trip A
    print("Creating Trip A...")
    resp = requests.post(f"{BASE_URL}/trips", json={"name": "Trip A"}, headers=auth_headers)
    assert resp.status_code == 200, f"Failed to create Trip A: {resp.text}"
    trip_a_id = resp.json()['id']
    print(f"Trip A ID: {trip_a_id}")
    
    # 2. Create Trip B
    print("Creating Trip B...")
    resp = requests.post(f"{BASE_URL}/trips", json={"name": "Trip B"}, headers=auth_headers)
    assert resp.status_code == 200, f"Failed to create Trip B: {resp.text}"
    trip_b_id = resp.json()['id']
    print(f"Trip B ID: {trip_b_id}")
    
    assert trip_a_id != trip_b_id, "Trip IDs should be unique"
    
    # Headers for each trip
    headers_a = {"X-Trip-ID": trip_a_id, "X-Admin-Token": ADMIN_TOKEN}
    headers_b = {"X-Trip-ID": trip_b_id, "X-Admin-Token": ADMIN_TOKEN}
    
    # 3. Add Participants
    print("Adding participants...")
    resp = requests.post(f"{BASE_URL}/participants", json={"name": "Alice"}, headers=headers_a)
    assert resp.status_code == 200, f"Failed to add Alice to Trip A: {resp.text}"
    alice_id = resp.json()['id']
    
    resp = requests.post(f"{BASE_URL}/participants", json={"name": "Bob"}, headers=headers_b)
    assert resp.status_code == 200, f"Failed to add Bob to Trip B: {resp.text}"
    bob_id = resp.json()['id']

    # 4. Verify Participant Isolation
    print("Verifying Participant Isolation...")
    parts_a = requests.get(f"{BASE_URL}/participants", headers=headers_a).json()
    names_a = [p['name'] for p in parts_a]
    assert "Alice" in names_a and "Bob" not in names_a
    
    parts_b = requests.get(f"{BASE_URL}/participants", headers=headers_b).json()
    names_b = [p['name'] for p in parts_b]
    assert "Bob" in names_b and "Alice" not in names_b
    
    # 5. Add Expense to Trip A
    print("Adding Expense to Trip A...")
    expense_data = {
        "name": "Dinner",
        "amount": 1000,
        "currency": "JPY",
        "buffer_rate": 0.25,
        "participant_ids": [alice_id]
    }
    resp = requests.post(f"{BASE_URL}/expenses", json=expense_data, headers=headers_a)
    assert resp.status_code == 200, f"Failed to add expense to Trip A: {resp.text}"
    
    # 6. Verify Expense Isolation
    print("Verifying Expense Isolation...")
    exps_a = requests.get(f"{BASE_URL}/expenses", headers=headers_a).json()
    assert len(exps_a) == 1, "Trip A should have 1 expense"
    assert exps_a[0]['name'] == "Dinner"
    
    exps_b = requests.get(f"{BASE_URL}/expenses", headers=headers_b).json()
    assert len(exps_b) == 0, "Trip B should have 0 expenses"
    
    # 7. Modify Settings in Trip A
    print("Modifying Settings in Trip A...")
    settings_data = {"trip_name": "Trip A Updated", "default_buffer_rate": 0.5}
    resp = requests.put(f"{BASE_URL}/settings", json=settings_data, headers=headers_a)
    assert resp.status_code == 200, f"Failed to update settings Trip A: {resp.text}"
    
    # 8. Verify Settings Isolation
    print("Verifying Settings Isolation...")
    settings_a = requests.get(f"{BASE_URL}/settings", headers=headers_a).json()
    assert settings_a['trip_name'] == "Trip A Updated"
    assert settings_a['default_buffer_rate'] == 0.5
    
    settings_b = requests.get(f"{BASE_URL}/settings", headers=headers_b).json()
    assert settings_b['trip_name'] == "Trip B"  # Should remain Trip B
    assert settings_b['default_buffer_rate'] != 0.5 # Should be default (e.g. 0.25) or null, but definitely not confirmed 0.5 unless default
    
    print("SUCCESS: Full Backend Isolation Verified!")

if __name__ == "__main__":
    test_multitrip()
