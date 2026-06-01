import os
import random
import time
import json
import threading
from datetime import date, timedelta
from pathlib import Path
import requests
from locust import HttpUser, between, events
from dotenv import load_dotenv

# Load .env file from the backend directory root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Import modular task definitions
from tasks.auth_tasks import register_user
from tasks.inventory_tasks import fetch_inventory, add_product, update_item_quantity, scan_receipt

class SystemLoadTest(HttpUser):
    # Simulated user "think time" between tasks to protect the free tier backend
    wait_time = between(2, 5)
    
    # Load test scenario task mapping with weights
    # scan_receipt and register_user are relatively rare actions.
    tasks = {
        fetch_inventory: 15,
        update_item_quantity: 8,
        add_product: 5,
        register_user: 1,
        scan_receipt: 1
    }
    
    # Class-level caching dictionary to map email -> (token, cached_time)
    _cached_tokens = {}
    _cached_token_expiry = 3000  # Token lifespan is 3600s, cache for 3000s
    _login_lock = threading.Lock()
    
    def on_start(self):
        """
        Executed when a virtual user starts.
        Resolves authentication and secures a home context before starting test tasks.
        """
        self.email = None
        self.password = None
        self.home_id = None
        self.created_home = False
        self.available_items = []
        
        # Resolve path to the example receipt image for scanning tasks
        self.receipt_file_path = Path(__file__).resolve().parent / "example.jpg"
        
        # 1. Select credentials from pool and pin to this session
        self._initialize_credentials()
        
        # 2. Verify token can be resolved (connectivity check)
        if not self.auth_token:
            print("[WARN] Auth token could not be resolved. Authenticated tasks will skip execution.")
            return
            
        # 3. Resolve Home ID
        self.home_id = self._resolve_home_id()
        if not self.home_id:
            print("[WARN] Home ID could not be resolved. Inventory tasks will skip execution.")
            return
            
        # 4. Seed initial products to simulate a heavy read environment
        if self.auth_token != "mock_supabase_jwt_token_placeholder":
            self._seed_products()

    def on_stop(self):
        """
        Executed when a virtual user stops.
        Cleans up dynamically created home and inventory data.
        Introduces random jitter (staggering) and retries to protect the free-tier backend from overload.
        """
        if getattr(self, "created_home", False) and self.home_id and self.auth_token:
            # Stagger requests over a 15-second window to prevent flooding Render
            jitter = random.uniform(0.1, 15.0)
            time.sleep(jitter)
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }
            url = f"/homes/{self.home_id}"
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.delete(
                        f"{self.client.base_url.rstrip('/')}{url}",
                        headers=headers,
                        timeout=15
                    )
                    if response.status_code == 200:
                        print(f"[INFO] Teardown: Successfully deleted dynamic home: {self.home_id}")
                        break
                    elif response.status_code == 404:
                        print(f"[INFO] Teardown: Home {self.home_id} already deleted (404).")
                        break
                    else:
                        print(f"[WARN] Teardown (Attempt {attempt+1}/{max_retries}): Failed to delete home {self.home_id}: {response.status_code}")
                except Exception as e:
                    print(f"[WARN] Teardown (Attempt {attempt+1}/{max_retries}): Connection error for home {self.home_id}: {str(e)}")
                
                # Backoff delay before retrying
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2.0, 5.0))

    def _seed_products(self):
        """
        Query current inventory and seed up to 10 unique products if the count is low.
        This guarantees that subsequent GET /stock/all requests simulate a heavy read query.
        """
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "X-Home-ID": str(self.home_id)
        }
        
        # 1. Check current inventory count
        current_count = 0
        try:
            with self.client.get("/stock/all", headers=headers, name="/stock/all (Seed Check)", catch_response=True) as response:
                if response.status_code == 200:
                    res_data = response.json()
                    current_count = len(res_data.get("data", []))
                    response.success()
                else:
                    response.failure(f"Seed check query failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Exception checking inventory size: {str(e)}")
            return
            
        # 2. Seed if inventory is sparse (less than 10 products)
        if current_count < 10:
            target_to_seed = 10 - current_count
            print(f"[INFO] Seeding home {self.home_id} with {target_to_seed} unique products to guarantee heavy read loads...")
            
            product_names = [
                "Milk", "Eggs", "Whole Wheat Bread", "Cheddar Cheese", "Butter",
                "Apples", "Bananas", "Greek Yogurt", "Spaghetti", "Tomato Sauce",
                "Olive Oil", "Coffee Beans", "Dish Soap", "Paper Towels", "Laundry Detergent"
            ]
            locations = ["FRIDGE", "FREEZER", "PANTRY", "CLEANING", "OTHER"]
            
            for _ in range(target_to_seed):
                # Stagger the seed requests slightly to avoid overwhelming Render free-tier CPU on startup
                time.sleep(random.uniform(0.5, 1.5))
                
                base_name = random.choice(product_names)
                unique_name = f"{base_name} {random.randint(1000, 9999)}"
                quantity = random.randint(1, 5)
                location = random.choice(locations)
                
                exp_date = None
                if random.random() > 0.3:
                    exp_date = (date.today() + timedelta(days=random.randint(5, 30))).isoformat()
                    
                payload = {
                    "name": unique_name,
                    "quantity": quantity,
                    "location": location,
                    "expiration_date": exp_date,
                    "barcode": f"7290{random.randint(100000000, 999999999)}",
                    "nickname": f"Seed {unique_name}"
                }
                
                try:
                    with self.client.post("/stock/add", json=payload, headers=headers, name="/stock/add (Seed)", catch_response=True) as response:
                        if response.status_code in [200, 201]:
                            response.success()
                        else:
                            response.failure(f"Seed addition failed: {response.status_code}")
                except Exception as e:
                    print(f"[ERROR] Exception during product seed addition: {str(e)}")
            
    def _initialize_credentials(self):
        """
        Selects a random credential pair from credentials.json or env variables
        and pins them to this virtual user session.
        """
        emails = []
        passwords = []
        
        credentials_path = Path(__file__).resolve().parent / "credentials.json"
        if credentials_path.exists():
            try:
                with open(credentials_path, "r", encoding="utf-8") as f:
                    creds_data = json.load(f)
                    if isinstance(creds_data, list):
                        for cred in creds_data:
                            email = cred.get("email")
                            password = cred.get("password")
                            if email and password:
                                emails.append(email)
                                passwords.append(password)
            except Exception as e:
                print(f"[ERROR] Failed to read credentials.json: {str(e)}")
                
        # Fall back to env variables if JSON file is missing or empty
        if not emails or not passwords:
            single_email = os.getenv("TEST_USER_EMAIL")
            single_password = os.getenv("TEST_USER_PASSWORD")
            if single_email and single_password:
                emails = [single_email]
                passwords = [single_password]
                
        if emails and passwords:
            user_idx = random.randint(0, len(emails) - 1)
            pass_idx = user_idx if user_idx < len(passwords) else 0
            self.email = emails[user_idx]
            self.password = passwords[pass_idx]
            
    @property
    def auth_token(self):
        """
        Dynamically returns a valid, unexpired token.
        If the cached token is close to expiry, requests a fresh one.
        """
        return self._resolve_token()
        
    def _resolve_token(self):
        """
        Retrieves JWT via environment variable, class-level cache pool, or Supabase login API.
        """
        # Option 1: Static JWT environment variable override
        env_token = os.getenv("SUPABASE_JWT_TOKEN")
        if env_token:
            return env_token
            
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        # If Supabase URL/key is missing, fall back to mock token
        if not supabase_url or not supabase_key:
            return "mock_supabase_jwt_token_placeholder"
            
        # Verify credentials are set for this virtual user session
        if not getattr(self, "email", None) or not getattr(self, "password", None):
            return "mock_supabase_jwt_token_placeholder"
            
        # Check class-level cache pool for this email (Fast Path - read lockless)
        now = time.time()
        cached_info = SystemLoadTest._cached_tokens.get(self.email)
        if cached_info:
            cached_token, cached_time = cached_info
            # Refresh 5 minutes before actual expiry (3600 seconds) to avoid 401 mid-test
            if now - cached_time < (SystemLoadTest._cached_token_expiry - 300):
                return cached_token
                
        # slow path: Acquire lock to authenticate (prevents thundering herd)
        with SystemLoadTest._login_lock:
            # Double-check cache inside lock (in case another user populated it while we waited)
            now = time.time()
            cached_info = SystemLoadTest._cached_tokens.get(self.email)
            if cached_info:
                cached_token, cached_time = cached_info
                if now - cached_time < (SystemLoadTest._cached_token_expiry - 300):
                    return cached_token
                    
            # Authenticate dynamically with Supabase Auth API
            try:
                login_url = f"{supabase_url.rstrip('/')}/auth/v1/token?grant_type=password"
                headers = {
                    "apikey": supabase_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "email": self.email,
                    "password": self.password
                }
                
                response = requests.post(login_url, json=payload, headers=headers, timeout=10)
                if response.status_code in [200, 201]:
                    data = response.json()
                    token = data.get("access_token")
                    if token:
                        SystemLoadTest._cached_tokens[self.email] = (token, now)
                        print(f"[INFO] Successfully refreshed/cached token for user: {self.email}")
                        return token
                print(f"[ERROR] Supabase auth failed for {self.email} (HTTP {response.status_code}): {response.text}")
            except Exception as e:
                print(f"[ERROR] Network error during Supabase auth for {self.email}: {str(e)}")
                
            return "mock_supabase_jwt_token_placeholder"

    def _resolve_home_id(self):
        """
        Secures a home context. If FORCE_NEW_HOME is enabled, creates a fresh home.
        Otherwise, fetches an existing home or creates one if none exists.
        """
        # Option 1: Static Home ID environment variable override
        env_home_id = os.getenv("TEST_HOME_ID")
        if env_home_id:
            self.created_home = False
            return env_home_id
            
        # Check for mock auth mode
        if self.auth_token == "mock_supabase_jwt_token_placeholder":
            self.created_home = False
            return "00000000-0000-0000-0000-000000000000"
            
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        
        # Check if we should force a fresh home for this test run (default: True)
        force_new = os.getenv("FORCE_NEW_HOME", "true").lower() == "true"
        
        if not force_new:
            # Check active homes
            try:
                with self.client.get("/homes/my_homes", headers=headers, name="/homes/my_homes (Setup)", catch_response=True) as response:
                    if response.status_code == 200:
                        res_data = response.json()
                        homes = res_data.get("data", [])
                        if homes:
                            home_id = homes[0].get("id")
                            response.success()
                            self.created_home = False
                            return home_id
                        response.success()
                    else:
                        response.failure(f"Setup lookup failed: {response.status_code}")
            except Exception as e:
                print(f"[ERROR] Error checking user homes: {str(e)}")

        # Option 2: Create a new home
        try:
            create_payload = {
                "name": f"Load Test Home {random.randint(100, 999)}"
            }
            with self.client.post("/homes/create", json=create_payload, headers=headers, name="/homes/create (Setup)", catch_response=True) as response:
                if response.status_code in [200, 201]:
                    res_data = response.json()
                    home_id = res_data.get("data", {}).get("id")
                    response.success()
                    print(f"[INFO] Dynamic home bootstrap successful. Home ID: {home_id}")
                    self.created_home = True
                    return home_id
                else:
                    response.failure(f"Setup creation failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Error bootstrapping home: {str(e)}")
            
        return None

# --- SLA (Service Level Agreement) Thresholds ---
@events.quitting.add_listener
def check_sla(environment):
    """
    Evaluates system performance thresholds after the test finishes.
    """
    total_stats = environment.stats.total
    
    # 1. Error Rate SLA (should be < 1.0%)
    if total_stats.fail_ratio > 0.01:
        print(f"❌ SLA Failure: Error rate of {total_stats.fail_ratio:.2%} exceeded the 1.0% limit.")
        
    # 2. Response Time SLA (P95 should be < 2.0 seconds)
    p95_latency = total_stats.get_response_time_percentile(0.95)
    if p95_latency > 2000:
        print(f"❌ SLA Failure: P95 response time of {p95_latency:.0f}ms exceeded the 2000ms limit.")