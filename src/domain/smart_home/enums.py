from enum import Enum

class ExpirationType(Enum):
    FRESH = "תקין"
    GOING_TO_EXPIRE = "בקרוב יפוג"
    EXPIRED = "פג תוקף"


class LocationType(Enum):
    FRIDGE = "מקרר"
    FREEZER = "מקפיא"
    DRY = "יבשים"
    CLEANING_SUPPLIES = "חומרי ניקוי"
    OTHER = "אחר"