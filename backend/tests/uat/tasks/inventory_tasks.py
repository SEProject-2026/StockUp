import os
import random
from datetime import date, timedelta
from locust import task

@task(3)
def fetch_inventory(user):
    """
    Simulate user opening the app and retrieving the full inventory of their home.
    Cache the returned product and item UUIDs in the session to be used by the write tasks.
    """
    if not getattr(user, "home_id", None) or not getattr(user, "auth_token", None):
        return

    headers = {
        "Authorization": f"Bearer {user.auth_token}",
        "X-Home-ID": str(user.home_id)
    }

    with user.client.get("/stock/all", headers=headers, name="/stock/all", catch_response=True) as response:
        if response.status_code == 200:
            try:
                res_data = response.json()
                products = res_data.get("data", [])
                
                # Extract and cache product and item ID pairs
                available = []
                for product in products:
                    p_id = product.get("id")
                    items = product.get("items", [])
                    for item in items:
                        i_id = item.get("id")
                        if p_id and i_id:
                            available.append((p_id, i_id))
                
                user.available_items = available
                response.success()
            except Exception as e:
                response.failure(f"Failed to parse inventory response JSON: {str(e)}")
        else:
            response.failure(f"Fetch inventory failed: {response.status_code} - {response.text}")


@task(1)
def add_product(user):
    """
    Simulate a user adding a new product to their inventory.
    This dynamically populates the database and ensures we have items to update.
    """
    if not getattr(user, "home_id", None) or not getattr(user, "auth_token", None):
        return

    headers = {
        "Authorization": f"Bearer {user.auth_token}",
        "X-Home-ID": str(user.home_id)
    }

    product_names = [
        "Milk", "Eggs", "Whole Wheat Bread", "Cheddar Cheese", "Butter",
        "Apples", "Bananas", "Greek Yogurt", "Spaghetti", "Tomato Sauce",
        "Olive Oil", "Coffee Beans", "Dish Soap", "Paper Towels", "Laundry Detergent"
    ]
    locations = ["FRIDGE", "FREEZER", "PANTRY", "CLEANING", "OTHER"]

    name = f"{random.choice(product_names)} {random.randint(1000, 9999)}"
    quantity = random.randint(1, 5)
    location = random.choice(locations)
    
    # 70% chance of having an expiration date
    exp_date = None
    if random.random() > 0.3:
        exp_date = (date.today() + timedelta(days=random.randint(3, 45))).isoformat()

    payload = {
        "name": name,
        "quantity": quantity,
        "location": location,
        "expiration_date": exp_date,
        "barcode": f"7290{random.randint(100000000, 999999999)}",
        "nickname": f"Test {name}"
    }

    with user.client.post("/stock/add", json=payload, headers=headers, name="/stock/add", catch_response=True) as response:
        if response.status_code in [200, 201]:
            try:
                res_data = response.json()
                product = res_data.get("data", {})
                p_id = product.get("id")
                items = product.get("items", [])
                if p_id and items:
                    # Initialize cache list if it doesn't exist yet
                    if not hasattr(user, "available_items"):
                        user.available_items = []
                    # Append the newly created item batch to the cache
                    user.available_items.append((p_id, items[0].get("id")))
                response.success()
            except Exception as e:
                # Still count as success since HTTP request succeeded, but log parsing failure internally
                response.success()
        else:
            response.failure(f"Add product failed: {response.status_code} - {response.text}")


@task(1)
def update_item_quantity(user):
    """
    Simulate a user adjusting the quantity of an existing item batch.
    Picks a random item from the user's cached inventory.
    """
    # Verify cached inventory items are available
    available_items = getattr(user, "available_items", [])
    if not available_items:
        # Fall back to adding a product to populate cache or return
        return

    p_id, i_id = random.choice(available_items)
    
    headers = {
        "Authorization": f"Bearer {user.auth_token}",
        "X-Home-ID": str(user.home_id)
    }

    # Generate random quantity (e.g. 0 to 10. 0 completely removes the item batch)
    new_qty = random.randint(0, 8)

    payload = {
        "new_quantity": new_qty
    }

    url = f"/stock/{p_id}/items/{i_id}/quantity"
    with user.client.patch(url, json=payload, headers=headers, name="/stock/{product_id}/items/{item_id}/quantity", catch_response=True) as response:
        if response.status_code == 200:
            if new_qty == 0:
                # Remove from cache if the quantity was set to 0 (which deletes it in backend)
                try:
                    user.available_items.remove((p_id, i_id))
                except ValueError:
                    pass
            response.success()
        else:
            response.failure(f"Update quantity failed: {response.status_code} - {response.text}")


@task(1)
def scan_receipt(user):
    """
    Simulate uploading a PDF receipt for scanning and OCR parsing.
    This is a heavy write-operation, so we run it with a lower weight.
    """
    if not getattr(user, "home_id", None) or not getattr(user, "auth_token", None):
        return

    # Check if receipt file path is set on the user session
    receipt_path = getattr(user, "receipt_file_path", None)
    if not receipt_path or not os.path.exists(receipt_path):
        return

    headers = {
        "Authorization": f"Bearer {user.auth_token}",
        "X-Home-ID": str(user.home_id)
    }

    try:
        # Determine filename and media type dynamically
        filename = os.path.basename(receipt_path)
        ext = os.path.splitext(filename)[-1].lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png" if ext == ".png" else "application/pdf"

        # Open receipt file in binary mode
        with open(receipt_path, "rb") as f:
            files_payload = [
                ("files", (filename, f, mime_type))
            ]
            
            # Post file data using multipart form-upload
            # Content-Type header is omitted so requests handles boundary generation
            with user.client.post("/stock/scan", files=files_payload, headers=headers, name="/stock/scan", catch_response=True) as response:
                if response.status_code in [200, 201]:
                    response.success()
                else:
                    response.failure(f"Scan receipt failed: {response.status_code} - {response.text}")
    except Exception as e:
        # Catch local file errors or exceptions to prevent thread crashes
        user.environment.events.request.fire(
            request_type="POST",
            name="/stock/scan",
            response_time=0,
            response_length=0,
            exception=e,
            context={}
        )
