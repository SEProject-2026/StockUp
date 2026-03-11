from abc import ABC, abstractmethod

class IAnalyticsRepository(ABC):
    @abstractmethod
    async def save_receipt(self, home_id: str, receipt_data: dict) -> str:
        """Stores raw receipt data for historical analysis."""
        pass

    @abstractmethod
    async def get_receipts_history(self, home_id: str, limit: int = 10) -> list:
        """Retrieves recent receipts to feed into the AnalyticsEngine."""
        pass

    @abstractmethod
    async def save_insights(self, home_id: str, insights: list) -> None:
        """Persists calculated recommendations."""
        pass

    @abstractmethod
    async def get_item_insights(self, home_id: str, item_name: str = None) -> list:
        """
        Fetches recommendations for a home. 
        If item_name is provided, returns insights relevant to that specific product.
        """
        pass