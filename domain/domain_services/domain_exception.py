class DomainException(Exception):
    """
    Raised when a business rule is violated.
    Example: Inventory is full, Item expired, etc.
    """
    pass