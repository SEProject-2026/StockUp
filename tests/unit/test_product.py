import unittest
from datetime import date, timedelta
from uuid import uuid4
from domain.domain_exception import DomainException
from domain.smart_home.enums import ChainType, ExpirationType, LocationType
from domain.smart_home.product import Product, ProductBuilder


class TestProduct(unittest.TestCase):

    def setUp(self):
        """Setup common test data."""
        self.home_id = uuid4()
        self.barcode = "123456789"
        self.name = "Milk"
        self.quantity = 1
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.yesterday = self.today - timedelta(days=1)


    def test_builder_creates_minimal_product(self):
        product = (
            Product.builder(self.home_id, self.barcode, self.name, self.quantity)
            .build()
        )

        self.assertEqual(product.get_home_id(), self.home_id)
        self.assertEqual(product.get_barcode(), self.barcode)
        self.assertEqual(product.get_original_name(), self.name)
        self.assertEqual(product.get_quantity(), self.quantity)
        self.assertIsNone(product.get_nickname())
        self.assertIsNone(product.get_location())
        self.assertIsNone(product.get_expiration_date())


    def test_builder_full_chain(self):
        product = (
            Product.builder(self.home_id, self.barcode, self.name, self.quantity)
            .with_original_name("NewName")
            .with_nickname("MyMilk")
            .with_location(LocationType.FRIDGE)
            .with_chain_origin(ChainType.SHUFERSAL)
            .with_expiration_date(self.tomorrow)
            .build()
        )
        self.assertEqual(product.get_nickname(), "MyMilk")
        self.assertEqual(product.get_location(), LocationType.FRIDGE)
        self.assertEqual(product.get_chain_origin(), ChainType.SHUFERSAL)
        self.assertEqual(product.get_expiration_date(), self.tomorrow)
        self.assertEqual(product.get_original_name(), "NewName")


    def test_product_fails_on_bad_date(self):
        with self.assertRaises(ValueError) as cm:
            (
                Product.builder(self.home_id, self.barcode, self.name, self.quantity)
                .with_expiration_date(self.yesterday) 
                .build()
            )
        self.assertIn("Expiration date cannot be in the past.", str(cm.exception))


    def test_product_success_on_valid_date(self):
        product = (
            Product.builder(self.home_id, self.barcode, self.name, self.quantity)
            .with_expiration_date(self.tomorrow) 
            .build()
        )
        self.assertEqual(product.get_expiration_date(), self.tomorrow)


    def test_product_fails_on_bad_nickname(self):

        pb = Product.builder(self.home_id, self.barcode, self.name, self.quantity)
        with self.assertRaises(ValueError) as cm:
            ( pb.with_nickname("") .build() )
        self.assertIn("Nickname cannot be empty.", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            ( pb.with_nickname("ThisNicknameIsWayTooLongToBeValid") .build() )
        self.assertIn(f"Nickname is too long (max {Product.NICKNAME_MAX_LENGTH} chars).", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            ( pb.with_nickname("Invalid  Nickname") .build() )
        self.assertIn("Nickname cannot contain consecutive spaces.", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            ( pb.with_nickname("wq#$%~") .build() )
        self.assertIn("Nickname must contain only letters or numbers.", str(cm.exception))


    def test_product_success_on_valid_nickname(self):
        valid_nicknames = ["ValidNickname", "Nick123", "Nick Name", "N"*Product.NICKNAME_MAX_LENGTH]
        pb = Product.builder(self.home_id, self.barcode, self.name, self.quantity)
        for nickname in valid_nicknames:
            product = pb.with_nickname(nickname).build()
            self.assertEqual(product.get_nickname(), nickname)
    

    def test_porduct_fails_on_negative_quantity(self):
        with self.assertRaises(DomainException) as cm:
            Product.builder(self.home_id, self.barcode, self.name, -5).build()
        self.assertIn("Quantity cannot be negative.", str(cm.exception))

    def test_product_success_on_valid_quantity(self):
        product = Product.builder(self.home_id, self.barcode, self.name, 10).build()
        self.assertEqual(product.get_quantity(), 10)
    
