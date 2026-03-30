import re

global_dictionary = dict()

# home.py
global_dictionary["Only admin can view join requests."] = "רק מנהל יכול לצפות בבקשות הצטרפות."
global_dictionary["Only current admin can transfer admin rights."] = "רק המנהל הנוכחי יכול להעביר את זכויות הניהול."
global_dictionary["User is not a member of the home."] = "המשתמש אינו חבר בבית."
global_dictionary["User has already requested to join."] = "המשתמש כבר ביקש להצטרף."
global_dictionary["User is already a member of the home."] = "המשתמש כבר חבר בבית."
global_dictionary["Only admin can approve or deny join requests."] = "רק מנהל יכול לאשר או לדחות בקשות הצטרפות."
global_dictionary["No such join request found."] = "לא נמצאה בקשת הצטרפות כזו."
global_dictionary["Only admin can remove members from the home."] = "רק מנהל יכול להסיר חברים מהבית."
global_dictionary["Admin cannot leave the home. Transfer admin rights before leaving."] = "המנהל לא יכול לעזוב את הבית. העבר את זכויות הניהול לפני העזיבה."
global_dictionary["Only admin can view the home join code."] = "רק מנהל יכול לצפות בקוד הצטרפות לבית."
global_dictionary["Only admin can delete the home."] = "רק מנהל יכול למחוק את הבית."
global_dictionary["Only admin can update expiration range."] = "רק מנהל יכול לעדכן את טווח התפוגה."
global_dictionary["Expiration range must be a positive integer."] = "טווח התפוגה חייב להיות מספר שלם חיובי."

# product.py
global_dictionary["Quantity to add must be positive."] = "כמות להוספה חייבת להיות חיובית."
global_dictionary[r"^Item (.*) not found in product (.*)$"] = "הפריט לא נמצא במוצר."
global_dictionary["Quantity cannot be negative."] = "כמות לא יכולה להיות שלילית."
global_dictionary[r"^Item (.*) not found.$"] = "הפריט לא נמצא."

# services

# management_service.py
global_dictionary["Home not found."] = "הבית לא נמצא."

# shopping_list_service.py
global_dictionary[r"^Shopping list not found: (.*)$"] = "רשימת הקניות לא נמצאה."

# stock_service.py
global_dictionary["Product not found."] = "המוצר לא נמצא."
global_dictionary["Product not found in this home."] = "המוצר לא נמצא בבית הזה."

# user_service.py
global_dictionary["User with this email already exists."] = "משתמש עם האימייל הזה כבר קיים."
global_dictionary["Passwords do not match."] = "הסיסמאות לא תואמות."
global_dictionary["Invalid email or password."] = "אימייל או סיסמה לא נכונים."
global_dictionary["User not found."] = "המשתמש לא נמצא."
global_dictionary["Incorrect current password."] = "סיסמה נוכחית שגויה."


def translate_error(error_message: str) -> str:
    # 1. קודם כל, ננקה את השגיאה מרווחים מיותרים
    clean_error = error_message.strip()
    
    # 2. ננסה למצוא התאמה מדויקת (עבור השגיאות הסטטיות) - זה הרבה יותר מהיר ובטוח מ-Regex!
    if clean_error in global_dictionary:
        return global_dictionary[clean_error]
        
    # 3. אם לא מצאנו התאמה מדויקת, אולי זה שגיאה דינמית? נחפש עם Regex
    for pattern, heb_template in global_dictionary.items():
        # נבדוק רק את המפתחות שמוגדרים כ-Regex (יש בהם תווים מיוחדים)
        if "(.*)" in pattern:
            # re.search מחפש את התבנית בכל מקום במחרוזת (לא רק בהתחלה כמו match)
            if re.search(pattern, clean_error):
                return heb_template

    # 4. אם הגענו לפה, לא מצאנו שום תרגום
    return clean_error