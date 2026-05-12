import uuid
import time
import random
from locust import HttpUser, task, between, events

class SystemLoadTest(HttpUser):
    wait_time = between(3, 7)
    
    # הגדרה של המשתנים ברמת המחלקה כדי למנוע את ה-AttributeError
    auth_headers = None
    stock_headers = {}

    def on_start(self):
        """
        שלב ה-Setup: כל משתמש נרשם למערכת ומקבל טוקן אמיתי.
        """
        # אתחול המשתנים עבור המשתמש הספציפי
        self.auth_headers = {} 
        self.stock_headers = {}
        
        self.user_id = str(uuid.uuid4())
        self.email = f"load_test_{int(time.time()*1000)}@test.com"
        
        payload = {
            "email": self.email,
            "user_id": self.user_id,
            "name": "Load Tester"
        }
        
        with self.client.post("/auth/register", json=payload, name="[Setup] Register", catch_response=True) as response:
            if response.status_code == 200:
                res_data = response.json()
                # חילוץ הטוקן - אם ה-API מחזיר את הטוקן ב-data.access_token
                token = res_data.get("data", {}).get("access_token")
                
                if token:
                    self.auth_headers = {"Authorization": f"Bearer {token}"}
                    # יצירת הדר בסיסי, ה-Home-ID יתעדכן ב-test_home_management
                    self.stock_headers = {**self.auth_headers}
                    response.success()
                else:
                    response.failure("Token missing in registration response")
            else:
                response.failure(f"Registration failed: {response.status_code}")
    @task(3)
    def test_stock_operations(self):
        if not self.auth_headers: return # מניעת הרצה ללא טוקן

        prod_payload = {
            "name": random.choice(["חלב", "לחם", "קפה", "תפוחים"]),
            "quantity": random.randint(1, 10),
            "location": "FRIDGE",
            "expiration_date": "2026-12-31",
            "barcode": str(uuid.uuid4())[:10]
        }
        self.client.post("/stock/add", json=prod_payload, headers=self.stock_headers, name="[Stock] Add Product")
        self.client.get("/stock/all", headers=self.stock_headers, name="[Stock] View All")

    @task(1)
    def test_home_management(self):
        if not self.auth_headers: return
        
        # יצירת בית אמיתית (כדי שיהיה ID תקין ב-DB)
        home_data = {"name": f"Home_{self.user_id[:4]}"}
        with self.client.post("/homes/create", json=home_data, headers=self.auth_headers, name="[Home] Create Home") as response:
            if response.status_code == 200:
                new_home_id = response.json().get("data", {}).get("id")
                if new_home_id:
                    self.stock_headers["X-Home-ID"] = str(new_home_id)

    @task(2)
    def test_shopping_flow(self):
        if not self.auth_headers or "X-Home-ID" not in self.stock_headers: return
        
        list_data = {"home_id": self.stock_headers["X-Home-ID"], "name": "Shopping List"}
        self.client.post("/shopping-lists/", json=list_data, headers=self.auth_headers, name="[Shopping] Create List")

# --- הגדרת ספי קבלה (SLA) ---
@events.quitting.add_listener
def check_sla(environment):
    if environment.stats.total.fail_ratio > 0.01:
        print("❌ Test Failed: High error rate!")
    if environment.stats.total.get_response_time_percentile(0.95) > 2000:
        print("❌ Test Failed: Response time too slow (P95 > 2s)!")