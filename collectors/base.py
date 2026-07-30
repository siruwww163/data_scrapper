"""Common resilient HTTP behavior for collectors."""
from __future__ import annotations

import time
from typing import Any

import requests

from utils.logging_utils import get_logger


class APIRequestError(RuntimeError):
    """Raised after a recoverable API request exhausts all retries."""


class BaseCollector:
    """Base class with timeout, retry, and exponential backoff."""

    def __init__(self, timeout: int = 30, max_retries: int = 3) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.logger = get_logger(self.__class__.__name__)

    def _get(self, url: str, **kwargs: Any) -> dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    response.raise_for_status()
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                if attempt >= self.max_retries:
                    self.logger.error("Request failed after %s attempts: %s", attempt + 1, type(exc).__name__)
                    raise APIRequestError("API request failed; inspect logs for the error type.") from exc
                delay = 2**attempt
                self.logger.warning("Request failed; retrying in %ss (%s)", delay, type(exc).__name__)
                time.sleep(delay)
        raise APIRequestError("Unreachable retry state")

