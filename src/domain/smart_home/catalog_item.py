from typing import Optional

class CatalogItem:
    def __init__(self, 
                 barcode: str, 
                 name: str, 
                 chain: Optional[str] = None):
        
        self.barcode = barcode
        self.name = name
        self.chain = chain

    def __repr__(self):
        return f"<CatalogItem: {self.name} ({self.barcode})>"