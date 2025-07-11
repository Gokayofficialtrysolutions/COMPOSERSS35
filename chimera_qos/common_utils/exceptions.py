# CHIMera QOS - Common Custom Exceptions

class QOSBaseError(Exception):
    """Base class for all CHIMera QOS custom exceptions."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details if details is not None else {}

class ServiceError(QOSBaseError):
    """Base class for errors originating from a specific QOS service."""
    def __init__(self, service_name: str, message: str, details: dict = None):
        super().__init__(f"[{service_name}] {message}", details)
        self.service_name = service_name

class ConfigurationError(QOSBaseError):
    """Indicates an error related to system or service configuration."""
    pass

class ResourceError(QOSBaseError):
    """Indicates an error related to resource access, availability, or management."""
    pass

class CommunicationError(QOSBaseError):
    """Indicates an error in inter-service communication."""
    pass

class AuthorizationError(QOSBaseError):
    """Indicates an action was not authorized."""
    pass

class InvalidStateError(QOSBaseError):
    """Indicates an operation was attempted on a component in an invalid state."""
    pass

class OperationTimeoutError(QOSBaseError):
    """Indicates an operation timed out."""
    pass

# Example of service-specific exceptions inheriting from ServiceError:
# These would typically be defined within each service's own exception module,
# but are shown here for structural illustration if common patterns emerge.
#
# class QHALEError(ServiceError):
#     def __init__(self, message: str, details: dict = None):
#         super().__init__("QHALService", message, details)
#
# class RMSError(ServiceError):
#     def __init__(self, message: str, details: dict = None):
#         super().__init__("RMSService", message, details)

# It's generally better for each service to define its more specific exceptions
# inheriting from these common ones or directly from QOSBaseError/ServiceError.
# For example, qhal_service.py might define QHALConnectionError(ServiceError).
# This file provides the most generic, cross-cutting exception types.
