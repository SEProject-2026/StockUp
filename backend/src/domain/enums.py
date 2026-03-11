from enum import Enum

class ExpirationType(str, Enum):
    FRESH = "FRESH"
    GOING_TO_EXPIRE = "GOING_TO_EXPIRE"
    EXPIRED = "EXPIRED"


class LocationType(str, Enum):
    FRIDGE = "FRIDGE"         
    FREEZER = "FREEZER"
    PANTRY = "PANTRY"
    CLEANING = "CLEANING"
    OTHER = "OTHER"

class UnitType(str, Enum):
    UNIT = "UNIT"
    KG = "KG"

class OCRMode(str, Enum):
    DIGITAL_PDF = "DIGITAL_PDF"
    SCANNED_PDF = "SCANNED_PDF"
    IMAGE = "IMAGE"