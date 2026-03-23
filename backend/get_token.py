import os
from dotenv import load_dotenv
from supabase import create_client

# טעינת המשתנים
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

# פרטי המשתמש שיצרת ב-Supabase Dashboard
email = "test@test.com" 
password = "your_password_here"

print(f"Connecting to: {url}")

try:
    supabase = create_client(url, key)
    res = supabase.auth.sign_in_with_password({
        "email": email, 
        "password": password
    })
    
    print("\n✅ LOGIN SUCCESS!")
    print(f"User UID: {res.user.id}")
    print("\n--- COPY THIS ACCESS TOKEN ---")
    print(res.session.access_token)
    print("------------------------------\n")

except Exception as e:
    print(f"❌ ERROR: {e}")