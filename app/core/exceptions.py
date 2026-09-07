class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


USERNAME_ALREADY_EXISTS = "USERNAME_ALREADY_EXISTS"
EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
UNAUTHENTICATED = "UNAUTHENTICATED"
CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
CATEGORY_ALREADY_EXISTS = "CATEGORY_ALREADY_EXISTS"
CATEGORY_IN_USE = "CATEGORY_IN_USE"
