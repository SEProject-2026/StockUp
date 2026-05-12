import uuid
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    # כל משתמש יחכה בין 1 ל-3 שניות בין פעולה לפעולה (כדי לא להיות רובוט מהיר מדי)
    wait_time = between(1, 3)

    def on_start(self):
        """
        פונקציה שרצה פעם אחת עבור כל משתמש וירטואלי כשהוא 'נולד'.
        כאן נכין לו נתונים אישיים.
        """
        self.user_id = str(uuid.uuid4())
        self.email = f"user_{self.user_id[:8]}@test.com"
        self.user_name = "Original Name"

    @task(1)
    def register_user(self):
        """
        משימה 1: הרשמה למערכת.
        """
        payload = {
            "email": self.email,
            "user_id": self.user_id,
            "name": self.user_name
        }
        
        # שליחת בקשת POST לנתיב שכתבת בקוד
        with self.client.post("/auth/register", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                # אם המשתמש כבר קיים (בגלל הרצה חוזרת), זה לא נחשב כשל טכני של השרת
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")

