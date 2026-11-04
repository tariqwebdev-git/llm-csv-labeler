"""Exceptions raised by the labeler. Exception classes only."""


class LabelerError(Exception):
    """Base class for all labeler errors."""


class ApiKeyError(LabelerError):
    """API key missing or rejected (401/403). Stops the whole run."""


class ApiConfigError(LabelerError):
    """Request rejected for a reason retrying cannot fix (bad model name,
    unsupported parameter). Stops the whole run."""


class ApiCallError(LabelerError):
    """API call failed after all retries (rate limit, timeout, server error)."""


class CsvReadError(LabelerError):
    """The uploaded file could not be read as a usable CSV."""


class QueryFileError(LabelerError):
    """The query JSON file is invalid."""
