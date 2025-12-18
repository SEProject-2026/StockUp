import unittest
from datetime import date, timedelta
from uuid import uuid4
from src.domain.domain_exception import DomainException
from src.domain.smart_home.enums import ChainType, ExpirationType, LocationType
from src.domain.smart_home.product import Product, ProductBuilder


class TestProduct(unittest.TestCase):

    def setUp(self):
        """Setup common test data."""
        self.home_id = uuid4()
        self.barcode = "123456789"
        self.name = "Milk"
        self.expiration_range = 7
        self.quantity = 1
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.yesterday = self.today - timedelta(days=1)


    def test_builder_creates_minimal_product(self):
        product = (
            Product.builder(self.home_id, self.name, self.quantity, self.expiration_range)
            .build()
        )

        self.assertEqual(product.get_home_id(), self.home_id)
        self.assertEqual(product.get_original_name(), self.name)
        self.assertEqual(product.get_quantity(), self.quantity)
        self.assertIsNone(product.get_nickname())
        self.assertIsNone(product.get_location())



    def test_builder_full_chain(self):
        product = (
            Product.builder(self.home_id, self.name, self.quantity, self.expiration_range)
            .with_nickname("MyMilk")
            .with_location(LocationType.FRIDGE)
            .with_expiration_date(self.tomorrow)
            .build()
        )
        self.assertEqual(product.get_nickname(), "MyMilk")
        self.assertEqual(product.get_location(), LocationType.FRIDGE)
        self.assertEqual(product.get_original_name(), "Milk")
        self.assertEqual(product.get_quantity(), 1)
        self.assertEqual(product.get_expiration_dates(), {self.tomorrow: (1, ExpirationType.GOING_TO_EXPIRE)})


    def test_check_expired_product(self):
        product = (
            Product.builder(self.home_id, self.name, self.quantity, self.expiration_range)
            .with_expiration_date(self.yesterday) 
            .build()
        )
        self.assertEqual(product.get_expiration_dates()[self.yesterday][1], ExpirationType.EXPIRED)


    def test_product_success_on_valid_date(self):
        product = (
            Product.builder(self.home_id, self.name, self.quantity, self.expiration_range)
            .with_expiration_date(self.tomorrow) 
            .build()
        )
        self.assertEqual(product.get_expiration_dates(), {self.tomorrow: (1, ExpirationType.GOING_TO_EXPIRE)})


    def test_product_fails_on_bad_nickname(self):

        pb = Product.builder(self.home_id, self.name, self.quantity, self.expiration_range)
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
        pb = Product.builder(self.home_id, self.name, self.quantity, self.expiration_range)
        for nickname in valid_nicknames:
            product = pb.with_nickname(nickname).build()
            self.assertEqual(product.get_nickname(), nickname)
    

    def test_porduct_fails_on_negative_quantity(self):
        with self.assertRaises(ValueError) as cm:
            Product.builder(self.home_id, self.name, -5, self.expiration_range).build()
        self.assertIn("Quantity cannot be negative.", str(cm.exception))

    def test_product_success_on_valid_quantity(self):
        product = Product.builder(self.home_id, self.name, quantity=10, expiration_range=self.expiration_range).build()
        self.assertEqual(product.get_quantity(), 10)
    
