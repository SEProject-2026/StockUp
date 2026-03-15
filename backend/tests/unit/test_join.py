import requests

# 1. הדבק כאן את הטוקן הארוך שקיבלת מה-login הקודם (בלי המילה Bearer)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2Y2RiNmJlNy03ODJjLTQyMjAtOTE4Zi1mYzk1OWI2MWQzZmEiLCJleHAiOjE3NzM2NjgxMjZ9.NfnW-SBWlDN3sNhr7Gp5WbfmD17eHv1L57HryIUPihg" 

# 2. הדבק כאן את קוד הבית שהעתקת מהאייפון
HOME_CODE = "53728C50" 

# 3. שים כאן את הכתובת המדויקת של ראוט ההצטרפות שלכם
# (תציץ ב-Swagger איך קוראים לראוט, למשל /homes/join או /homes/{home_code}/join)
URL = "http://localhost:8000/homes/join" 

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# אם הראוט שלכם דורש את הקוד בגוף הבקשה (JSON):
payload = {"home_code": HOME_CODE} 
response = requests.post(URL, json=payload, headers=headers)

# (אם הראוט דורש את זה ב-URL Params, תשנה ל: requests.post(URL, params=payload, headers=headers))

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")