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

class ChainType(Enum):
    SHEFA_BIRKAT_HASHEM = 0
    SHUK_HAIR = 1
    SHUFERSAL = 2
    RAMI_LEVI = 3
    KESHET_TEAMIM = 4
    KT = 5
    PAZ = 6
    POLIZTER = 7
    OF_VEHODU_BARKAT = 8
    STOP_MARKET = 9
    CITY_MARKET = 10
    SUPER_PHARM = 11
    SUPER_SAPIR = 12
    SALAH_DABAH_VEBANAV = 13
    NETIV_HAHESED = 14
    MERAV_MAZON = 15
    YOHANANOF = 16
    KOL_BO_HAZI_HINAM = 17
    MAHSANEI_HASHUK = 18
    TIV_TAAM = 19
    VICTORY = 20
    WOLT = 21
    DOR_ALON = 22
    CAREFOUR = 23
    MAAYAN_2000 = 24
    KING_STORE = 25
    OTHER = 99