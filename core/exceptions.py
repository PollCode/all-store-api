from typing import Any, Dict, Optional
from fastapi import status


class AppException(Exception):
    """
    Excepción base de la aplicación.

    Atributos:
        status_code: Código HTTP que devolverá la API.
        error_type:  Identificador legible del tipo de error (para el cliente).
        message:     Mensaje descriptivo del error.
        details:     Información adicional opcional (dict).
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type: str = "internal_error"
    default_message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details
        if status_code is not None:
            self.status_code = status_code
        if error_type is not None:
            self.error_type = error_type
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Representación serializable para la respuesta HTTP."""
        payload: Dict[str, Any] = {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "status_code": self.status_code,
            }
        }
        if self.details:
            payload["error"]["details"] = self.details
        return payload


# ------------------------------------------------------------------
# 4xx — Errores del cliente
# ------------------------------------------------------------------

class BadRequestError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_type = "bad_request"
    default_message = "Invalid request"


class UnauthorizedError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_type = "unauthorized"
    default_message = "Authentication required"


class ForbiddenError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_type = "forbidden"
    default_message = "You do not have permission to perform this action"


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_type = "not_found"
    default_message = "Resource not found"


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_type = "conflict"
    default_message = "Resource conflict"


class UnprocessableEntityError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_type = "unprocessable_entity"
    default_message = "The provided data could not be processed"


class TooManyRequestsError(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_type = "too_many_requests"
    default_message = "Too many requests, please slow down"


# ------------------------------------------------------------------
# 5xx — Errores del servidor
# ------------------------------------------------------------------

class InternalServerError(AppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type = "internal_error"
    default_message = "Internal server error"


class ServiceUnavailableError(AppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_type = "service_unavailable"
    default_message = "Service temporarily unavailable"