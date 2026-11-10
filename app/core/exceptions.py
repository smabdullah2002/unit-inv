from typing import Any, Optional


class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found.", code: str = "NOT_FOUND"):
        super().__init__(message=message, code=code, status_code=404)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict occurred.", code: str = "CONFLICT"):
        super().__init__(message=message, code=code, status_code=409)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access forbidden.", code: str = "FORBIDDEN"):
        super().__init__(message=message, code=code, status_code=403)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required.", code: str = "UNAUTHORIZED"):
        super().__init__(message=message, code=code, status_code=401)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation error.", code: str = "VALIDATION_ERROR", details: Optional[Any] = None):
        super().__init__(message=message, code=code, status_code=422, details=details)

