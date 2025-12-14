class DomainException(Exception):
    """
    Raised when a business rule is violated.
    Example: Inventory is full, Item expired, etc.
    """
    pass

class UserMustBeMemberException(DomainException):
    """
    Raised when a user must be a member of the home to perform an action.
    """
    def __init__(self, message: str = "User must be a member of the home to perform this action."):
        super().__init__(message)

class ProductNotFoundException(DomainException):
    """
    Raised when a product is not found in the inventory.
    """
    def __init__(self, message: str = "Product not found in inventory."):
        super().__init__(message)