from datetime import date, timedelta
import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.services.stock_service import StockService 
from src.domain.smart_home.product import Product
from src.domain.smart_home.enums import ChainType, LocationType
from unittest.mock import MagicMock, AsyncMock
from src.response import Response



class TestStockServiceIntegration(unittest.IsolatedAsyncioTestCase):
    

    async def asyncSetUp(self):
        self.mock_home_repo = MagicMock()
        self.mock_product_repo = MagicMock()
        self.mock_catalog_repo = MagicMock()

        self.service = StockService(
            home_repository=self.mock_home_repo,
            product_repository=self.mock_product_repo,
            catalog_repository=self.mock_catalog_repo
        )
        self.user_id = uuid4()
        self.home_id = uuid4()
        self.barcode = "729000000000"
        self.chain = ChainType.SHUFERSAL
        self.name = "Generic Product"
        self.expiration_range = 7
        self.mock_home = MagicMock()
        self.mock_home.is_member.return_value = True 
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
            

    async def test_add_product_fails_if_home_not_found(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=None)
        with self.assertRaises(ValueError) as cm:
            await self.service.add_product(
                self.name, self.user_id, self.home_id, 1, self.barcode, None, None, None
            )
        self.mock_product_repo.save.assert_not_called()
    

    async def test_add_product_fails_if_user_not_home_member(self):
        self.mock_home.is_member.return_value = False
        with self.assertRaises(ValueError) as cm:
            await self.service.add_product(
                self.name, self.user_id, self.home_id, 1, self.barcode, None, None, None
            )
        self.mock_product_repo.save.assert_not_called()
        self.assertIn("User is not a member of the home", str(cm.exception))
        


    async def test_add_product_success(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_home.is_member.return_value = True
        self.mock_catalog_repo.save = AsyncMock(return_value=None)
        self.mock_product_repo.save = AsyncMock(return_value=None)
        self.mock_product_repo.search_by_name = AsyncMock(return_value=[])
        self.mock_home.get_default_expiration_range = MagicMock(return_value=None)
        await self.service.add_product(
            self.name, self.user_id, self.home_id, 5, self.barcode, None, None, "My Snack"
        )
        self.mock_product_repo.save.assert_called_once()
        saved_product = self.mock_product_repo.save.call_args.args[0]
        self.assertEqual(saved_product.get_quantity(), 5)
        self.assertEqual(saved_product.get_nickname(), "My Snack")
        self.assertEqual(saved_product.get_original_name(), "Generic Product") 


    async def test_add_product_fails_on_negative_quantity(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_catalog_repo.get_product_details = AsyncMock(return_value=None)
        self.mock_catalog_repo.save = AsyncMock(return_value=None)
        self.mock_product_repo.search_by_name = AsyncMock(return_value=[])
        self.mock_home.is_member.return_value = True
        with self.assertRaises(ValueError) as cm:
            await self.service.add_product(
                self.name, self.user_id, self.home_id, -1, self.barcode, None, None, None
            )
        self.mock_product_repo.save.assert_not_called()
        self.assertIn("Quantity cannot be negative", str(cm.exception))


    async def test_remove_product_success(self):
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_home.is_member.return_value = True
        self.mock_home.get_default_expiration_range = MagicMock(return_value=None)
        self.mock_product_repo.save = AsyncMock(return_value=None)
        self.mock_product_repo.delete = AsyncMock(return_value=None)
        self.mock_product_repo.search_by_name = AsyncMock(return_value=[])

        mock_product = (
            Product.builder(self.home_id, "Milk", 1, expiration_range=self.expiration_range)
                .with_expiration_date(date.today()).build()
        )

        await self.service.add_product(mock_product.get_original_name(), self.user_id,
                                        self.home_id, 1, self.barcode, date.today(), None, None)
        self.mock_product_repo.save.assert_called_once()
        self.mock_product_repo.get_by_id = AsyncMock(return_value=mock_product)
        await self.service.remove_product(
            self.user_id, self.home_id, mock_product.get_id(), date.today()
        )
        self.mock_product_repo.delete.assert_called_once_with(mock_product.get_id())


    async def test_update_quantity_success(self):
        mock_product = (
            Product.builder(self.home_id, "Milk", 1, expiration_range=self.expiration_range)
            .with_expiration_date(date.today()).build()
        )
        self.mock_product_repo.get_by_id = AsyncMock(return_value=mock_product)
        self.mock_product_repo.update = AsyncMock(return_value=None)
        self.mock_home_repo.get_by_id = AsyncMock(return_value=self.mock_home)
        self.mock_home.is_member.return_value = True
        await self.service.update_stock_quantity(
            self.user_id, self.home_id, mock_product.get_id(), date.today(), 10
        )
        self.assertEqual(mock_product.get_quantity(), 10) 
        self.mock_product_repo.update.assert_called_once_with(mock_product)


    async def test_update_product_quantity_for_other_home_fail(self):
        with self.assertRaises(ValueError) as cm:
            other_home_id = uuid4()
            mock_product = (
                Product.builder(other_home_id, "Milk", 1, expiration_range=self.expiration_range)
                .with_expiration_date(date.today() + timedelta(days=1)).build()
            )
            self.mock_product_repo.get_by_id = AsyncMock(return_value=mock_product)

            response = await self.service.update_stock_quantity(
                self.user_id, self.home_id, mock_product.get_id(), date.today() + timedelta(days=1), 5
            )
        self.assertIn("Product not found", str(cm.exception))
        self.mock_product_repo.update.assert_not_called()


   
