class AppException(Exception):
    def __init__(self, code: int, message: str, detail: dict | None = None):
        self.code = code
        self.message = message
        self.detail = detail


class ValidationError(AppException):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(400, message, {"field": field} if field else None)


class AuthError(AppException):
    def __init__(self, message: str = "未授权"):
        super().__init__(401, message)


class ForbiddenError(AppException):
    def __init__(self, message: str = "禁止访问"):
        super().__init__(403, message)


class NotFoundError(AppException):
    def __init__(self, resource: str):
        super().__init__(404, f"{resource}不存在")


class AIServiceError(AppException):
    def __init__(self, message: str = "AI服务暂时不可用"):
        super().__init__(503, message)


class RateLimitError(AppException):
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(429, message)
