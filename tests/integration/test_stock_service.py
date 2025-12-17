import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.services.stock_service import StockService 
from src.domain.smart_home.product import Product
from src.domain.smart_home.enums import LocationType
from unittest.mock import MagicMock, AsyncMock
from src.response import Response



class TestStockServiceIntegration(unittest.IsolatedAsyncioTestCase):
    

    async def asyncSetUp(self):
        self.mock_home_repo = MagicMock()
        self.mock_product_repo = MagicMock()
        self.mock_catalog_details_provider = MagicMock()

        self.service = StockService(
            home_repository=self.mock_home_repo,
            product_repository=self.mock_product_repo,
            catalog_details_provider=self.mock_catalog_details_provider
        )
        self.user_id = uuid4()
        self.home_id = uuid4()
        self.barcode = "729000000000"
        self.chain = "some_chain"
        self.mock_home = MagicMock()
        self.mock_home.is_member.return_value = True 
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
            

    async def test_add_product_fails_if_home_not_found(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=None)
        response = await self.service.add_product(
            self.barcode, self.chain, self.user_id, self.home_id, 1, None, None, None
        )
        self.assertFalse(response.isOk())
        self.assertEqual(response.get_error_message(), "Home not found")
        self.mock_product_repo.save.assert_not_called()
    

    async def test_add_product_fails_if_user_not_home_member(self):
        self.mock_home.is_member.return_value = False
        response = await self.service.add_product(
            self.barcode, self.chain, self.user_id, self.home_id, 1, None, None, None
        )
        self.assertFalse(response.isOk())
        self.assertIn("User is not a member of the home", response.get_error_message())
        self.mock_product_repo.save.assert_not_called()


    async def test_add_product_success(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_home.is_member.return_value = True
        self.mock_catalog_details_provider.get_product_details = AsyncMock(return_value=None)
        self.mock_product_repo.save = AsyncMock(return_value=None)
        response = await self.service.add_product(
            self.barcode, self.chain, self.user_id, self.home_id, 5, None, None, "My Snack"
        )
        self.assertTrue(response.isOk())
        self.mock_product_repo.save.assert_called_once()
        saved_product = self.mock_product_repo.save.call_args.args[0]
        self.assertEqual(saved_product.get_quantity(), 5)
        self.assertEqual(saved_product.get_nickname(), "My Snack")
        self.assertEqual(saved_product.get_original_name(), "מוצר כללי") 


    async def test_add_product_success_from_catalog(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_home.is_member.return_value = True
        mock_catalog_item = MagicMock()
        mock_catalog_item.name = "Coca Cola"
        self.mock_catalog_details_provider.get_product_details = AsyncMock(return_value=mock_catalog_item)
        self.mock_product_repo.save = AsyncMock(return_value=None)
    
        response = await self.service.add_product(
            self.barcode, self.chain, self.user_id, self.home_id, 2, None, LocationType.DRY, None
        )
        self.assertTrue(response.isOk())
        saved_product = self.mock_product_repo.save.call_args[0][0]
        self.assertEqual(saved_product.get_original_name(), "Coca Cola")
        self.assertEqual(saved_product.get_location(), LocationType.DRY)


    async def test_add_product_fails_on_negative_quantity(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_catalog_details_provider.get_product_details = AsyncMock(return_value=None)
        self.mock_home.is_member.return_value = True
        response = await self.service.add_product(
            self.barcode, self.chain, self.user_id, self.home_id, -1, None, None, None
        )
        self.assertFalse(response.isOk())
        self.assertIn("Quantity cannot be negative", response.get_error_message())
        self.mock_product_repo.save.assert_not_called()


    async def test_remove_product_success(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_home.is_member.return_value = True
        self.mock_catalog_details_provider.get_product_details = AsyncMock(return_value=None)
        mock_product = Product.builder(self.home_id, "123", "Milk", 1).build()
        self.mock_product_repo.get_by_id = AsyncMock(return_value=mock_product)
        self.mock_product_repo.delete = AsyncMock(return_value=None)
        response = await self.service.remove_product(
            self.user_id, self.home_id, mock_product.get_id()
        )
        
        self.assertTrue(response.isOk())
        self.mock_product_repo.delete.assert_called_once_with(mock_product.get_id())


    async def test_update_quantity_success(self):
        mock_product = Product.builder(self.home_id, "123", "Milk", 1).build()
        self.mock_product_repo.get_by_id = AsyncMock(return_value=mock_product)
        self.mock_product_repo.update = AsyncMock(return_value=None)
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_home.is_member.return_value = True
        response = await self.service.update_stock_quantity(
            self.user_id, self.home_id, mock_product.get_id(), 10
        )
        self.assertTrue(response.isOk())
        self.assertEqual(mock_product.get_quantity(), 10) 
        self.mock_product_repo.update.assert_called_once_with(mock_product)


    async def test_update_product_quantity_for_other_home_fail(self):
        other_home_id = uuid4()
        mock_product = Product.builder(other_home_id, "123", "Milk", 1).build()
        self.mock_product_repo.get_by_id = AsyncMock(return_value=mock_product)

        response = await self.service.update_stock_quantity(
            self.user_id, self.home_id, mock_product.get_id(), 5
        )
        self.assertFalse(response.isOk())
        self.assertIn("Product not found", response.get_error_message())
        self.mock_product_repo.update.assert_not_called()


   
