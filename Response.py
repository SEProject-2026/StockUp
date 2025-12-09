from typing import Optional, TypeVar, Generic

T = TypeVar('T')

class Response(Generic[T]):

    def __init__(self, isOk: bool, data: Optional[T] = None, error_message: Optional[str] = None):
        self.isOk = isOk
        self.data = data 
        self.error_message = error_message
