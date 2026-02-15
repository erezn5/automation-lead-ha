class ApiError(Exception):
    """Generic API error with structured fields for programmatic assertions."""
    def __init__(self, status_code: int, body: str, url: str = None, original: Exception = None):
        self.status_code = status_code
        self.body = body
        self.url = url
        self.original = original
        super().__init__(f"API Error {status_code} for {url}: {body}")


class NotFoundError(ApiError):
    """Raised when the remote API returns a 404."""
    pass
