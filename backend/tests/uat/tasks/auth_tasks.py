import uuid
import time
import random
from locust import task

@task
def register_user(user):
    """
    Simulate user registration sync flow.
    Generates a unique user ID and email and posts it to the FastAPI local database.
    Since this is a public endpoint used to sync Supabase users to our DB, it is unauthenticated.
    """
    user_id = str(uuid.uuid4())
    # Generate unique email using current millisecond timestamp and a random integer
    email = f"load_test_{int(time.time() * 1000)}_{random.randint(1000, 9999)}@test.com"
    name = f"Load Tester {random.randint(100, 999)}"
    
    payload = {
        "email": email,
        "user_id": user_id,
        "name": name
    }
    
    # Send post request to registration endpoint
    with user.client.post("/auth/register", json=payload, name="/auth/register", catch_response=True) as response:
        if response.status_code in [200, 201]:
            response.success()
        else:
            # Handle common free tier errors gracefully (e.g. 503, 502, 429) without crashing the virtual user
            response.failure(f"Registration failed: {response.status_code} - {response.text}")
