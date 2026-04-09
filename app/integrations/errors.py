"""Shared domain errors for upstream integration adapters."""

from __future__ import annotations


class UpstreamServiceError(RuntimeError):
    """Base error for failures talking to an upstream dependency."""


class UpstreamTimeoutError(UpstreamServiceError):
    """Raised when an upstream dependency times out."""


class UpstreamBadResponseError(UpstreamServiceError):
    """Raised when an upstream dependency returns an invalid response."""


class UpstreamNotFoundError(UpstreamServiceError):
    """Raised when an upstream dependency cannot find the requested resource."""
