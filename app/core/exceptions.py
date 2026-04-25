class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__("not_found", message, 404)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("conflict", message, 409)


class AuthError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__("unauthorized", message, 401)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__("forbidden", message, 403)


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("validation_error", message, 422)
