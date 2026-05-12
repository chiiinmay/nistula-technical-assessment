import httpx
import asyncio
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

async def test_webhook(payload, description, expected_status=200):
    print(f"\n--- Testing: {description} ---")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/webhook/message", json=payload, timeout=35.0)
            print(f"Status Code: {response.status_code}")
            if response.status_code == expected_status:
                print("SUCCESS: Received expected status code.")
                if response.status_code == 200:
                    print(json.dumps(response.json(), indent=2))
                else:
                    print(f"Error Detail: {response.json().get('detail')}")
            else:
                print(f"FAILURE: Expected {expected_status}, but got {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Connection Error: {e}")

async def main():
    # 1. Valid Availability Query
    await test_webhook({
        "source": "whatsapp",
        "guest_name": "Rahul Sharma",
        "message": "Is the villa available from April 20 to 24?",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "property_id": "villa-b1"
    }, "Valid Availability Query")

    # 2. Complaint (Should have lower confidence and trigger escalate)
    await test_webhook({
        "source": "booking_com",
        "guest_name": "John Doe",
        "message": "The AC is not working and I am very unhappy. I want a refund.",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "property_id": "villa-b1"
    }, "Maintenance Complaint")

    # 3. Invalid Source (Should return 422)
    await test_webhook({
        "source": "invalid_channel",
        "guest_name": "Test User",
        "message": "Hello",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "property_id": "villa-b1"
    }, "Invalid Source Channel", expected_status=422)

    # 4. Empty Message (Should return 400)
    await test_webhook({
        "source": "direct",
        "guest_name": "Test User",
        "message": "   ",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "property_id": "villa-b1"
    }, "Empty Message Text", expected_status=400)

if __name__ == "__main__":
    print("Starting tests... Make sure the FastAPI server is running at http://127.0.0.1:8000")
    asyncio.run(main())
