from typing import Optional
from domain.smart_home.enums import ChainType

class CatalogItem:
    def __init__(self, 
                 barcode: str, 
                 name: str, 
                 chain: Optional[ChainType] = None):
        
        self.barcode = barcode
        self.name = name
        self.chain = chain

    def __repr__(self):
        return f"<CatalogItem: {self.name} ({self.barcode})>"