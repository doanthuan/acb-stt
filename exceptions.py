from typing import Any


class APIException(Exception):
    def __init__(self, message: Any, status_code: int = 400, payload: Any = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv
