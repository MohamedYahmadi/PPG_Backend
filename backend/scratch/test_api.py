import urllib.request
import json

BASE_URL = "http://192.168.1.15:8000/api/v1"

def make_post_request(url_path, payload):
    url = f"{BASE_URL}{url_path}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            body = response.read().decode('utf-8')
            return status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            err_data = json.loads(body)
        except:
            err_data = body
        return e.code, err_data
    except Exception as e:
        return 500, str(e)

print("--- TESTING PASSENGER LOGIN ---")
status, response = make_post_request("/auth/login/", {
    "phone_number": "+21699000000",
    "password": "Passenger123!",
    "device_id": "test-device-passenger"
})
print(f"Status: {status}")
print(f"Response: {response}\n")

print("--- TESTING DRIVER LOGIN ---")
status, response = make_post_request("/auth/login/", {
    "phone_number": "+21620000000",
    "password": "Driver123!",
    "device_id": "test-device-driver"
})
print(f"Status: {status}")
print(f"Response: {response}\n")

print("--- TESTING NEW PASSENGER SIGNUP ---")
# Try a unique phone number using timestamp
import time
new_passenger_phone = f"+21698{int(time.time()) % 1000000:06d}"
status, response = make_post_request("/auth/register/", {
    "phone_number": new_passenger_phone,
    "password": "PassengerTest123!",
    "role": "PASSENGER"
})
print(f"Status: {status}")
print(f"Response: {response}\n")

if status == 201:
    print("--- TESTING NEW PASSENGER LOGIN ---")
    status_login, response_login = make_post_request("/auth/login/", {
        "phone_number": new_passenger_phone,
        "password": "PassengerTest123!",
        "device_id": "test-device-new-passenger"
    })
    print(f"Status: {status_login}")
    print(f"Response: {response_login}\n")

print("--- TESTING NEW DRIVER SIGNUP ---")
new_driver_phone = f"+21628{int(time.time()) % 1000000:06d}"
status, response = make_post_request("/auth/register/", {
    "phone_number": new_driver_phone,
    "password": "DriverTest123!",
    "role": "DRIVER"
})
print(f"Status: {status}")
print(f"Response: {response}\n")

if status == 201:
    print("--- TESTING NEW DRIVER LOGIN ---")
    status_login, response_login = make_post_request("/auth/login/", {
        "phone_number": new_driver_phone,
        "password": "DriverTest123!",
        "device_id": "test-device-new-driver"
    })
    print(f"Status: {status_login}")
    print(f"Response: {response_login}\n")
