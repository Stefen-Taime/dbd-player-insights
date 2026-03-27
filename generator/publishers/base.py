"""Abstract base publisher."""

from __future__ import annotations

import abc
from datetime import datetime


class BasePublisher(abc.ABC):
    @abc.abstractmethod
    def publish_batch(self, events: list[dict], partition_date: datetime | str | None = None) -> int:
        """Publish a batch of events. Returns count of events published."""
        ...
