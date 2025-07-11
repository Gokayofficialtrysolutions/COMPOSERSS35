# CHIMera QOS - Common Dataclasses and Enums

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, Dict
import time

@dataclass
class StatusResponse:
    """A generic response format for operations that primarily return a status."""
    success: bool
    message: str
    status_code: Optional[int] = None # e.g., HTTP-like status codes if applicable
    data: Optional[Dict[str, Any]] = None # For any additional relevant data
    error_code: Optional[str] = None # Application-specific error code
    timestamp: float = field(default_factory=time.time)

class OperationStatus(Enum):
    """Generic status for long-running operations or service health."""
    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE = "FAILURE"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    NOT_APPLICABLE = "NOT_APPLICABLE"

# Example of a shared Enum that might be useful across services:
# class PriorityLevel(Enum):
#     LOW = 1
#     MEDIUM = 2
#     HIGH = 3
#     CRITICAL = 4

# More shared types can be added here as common patterns emerge during service implementation.
# For instance, if multiple services deal with 'JobInfo' or 'ResourceDescriptor' in a
# standardized way not specific to one service's detailed model.
