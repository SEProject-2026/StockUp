from typing import Optional, TypeVar, Generic

T = TypeVar('T')

class Response(Generic[T]):

    def __init__(self, isOk: bool, data: Optional[T] = None, error_message: Optional[str] = None):
        self._isOk = isOk
        self._data = data 
        self._error_message = error_message

    def isError(self) -> bool:
        return not self._isOk
    
    def get_data(self) -> Optional[T]:
        return self._data
    
    def get_error_message(self) -> Optional[str]:
        return self._error_message