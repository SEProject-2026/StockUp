from typing import Optional


class Response:


    def __init__(self, isOk: bool, data: Optional[object] = None, error_message: Optional[str] = None):
        self.isOk = isOk
        self.data = data,
        self.error_message = error_message
        
    def isError(self):
        return not self.isOk
    
    def getData(self):
        return self.data
    
    def get_error_message(self):
        return self.error_message
