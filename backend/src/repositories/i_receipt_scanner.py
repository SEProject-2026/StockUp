from abc import ABC, abstractmethod
from typing import List, Tuple, Dict

class IReceiptScanner(ABC):
    @abstractmethod
    def parse_receipt(self, first_path: str, *rest_paths: str) -> Tuple[str, Dict[str, Tuple[float, str]]]:
        """Parses images and returns (chain_name, {barcode: (quantity, unit)})"""
        pass