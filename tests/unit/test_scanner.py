# from src.infrastructure.app_container import AppContainer
from src.infrastructure.scanner.receipt_scanner import ReceiptScanner
from uuid import uuid4


scanner = ReceiptScanner()

# file_path1 = r'tests\unit\8306975.pdf'
file_path1 = r'tests\unit\receipt5_pic1.jpeg'
file_path2 = r'tests\unit\receipt5_pic2.jpeg'

chain_name, products = scanner.parse_receipt(file_path1, file_path2)

print(f"--- RECEIPT: {chain_name} ---")
print(f"{'Barcode':<20} | {'Qty':<5} | {'Unit':<5}")
print("-" * 50)

for barcode in products.keys():
    item = products[barcode]
    print(f"{barcode} | {item[0]} | {item[1]}")

print(f"found {len(products)} unique products.")








#################################################################################################
# stockService = AP.AppContainer.get_stock_service()

# managementService = AP.AppContainer.get_management_service()

# user_id = uuid4()

# home = managementService.create_home(user_id=user_id, home_name="Test Home")


# products = stockService.scan_receipt(user_id=user_id, home_id=home.get_id(), file_path=file_path)