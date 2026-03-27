"""
Local file publisher — writes partitioned JSON files to disk.

Partitioning: event_type/yyyy/mm/dd/hh/batch_XXXXX.json
This mirrors the S3 partition structure exactly, so the same
dbt models work against both local and cloud data.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import orjson

from generator.publishers.base import BasePublisher

logger = logging.getLogger(__name__)


class LocalPublisher(BasePublisher):
    def __init__(self, output_dir: str = "./data/raw", batch_size: int = 5000):
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        self._batch_counters: dict[str, int] = defaultdict(int)

    def publish_batch(self, events: list[dict], partition_date: datetime | str | None = None) -> int:
        if not events:
            return 0

        # Group events by event_type and hour for partitioning
        partitions: dict[str, list[dict]] = defaultdict(list)

        for event in events:
            event_type = event.get("event_type", "unknown")
            ts_str = event.get("timestamp", "")

            try:
                ts = datetime.fromisoformat(ts_str.rstrip("Z"))
                partition_key = f"{event_type}/{ts.strftime('%Y/%m/%d/%H')}"
            except (ValueError, AttributeError):
                if isinstance(partition_date, datetime):
                    partition_key = f"{event_type}/{partition_date.strftime('%Y/%m/%d/00')}"
                else:
                    partition_key = f"{event_type}/unknown"

            partitions[partition_key].append(event)

        total_written = 0
        for partition_key, partition_events in partitions.items():
            # Write in batches
            for i in range(0, len(partition_events), self.batch_size):
                batch = partition_events[i : i + self.batch_size]
                self._batch_counters[partition_key] += 1
                batch_num = self._batch_counters[partition_key]

                output_path = self.output_dir / partition_key / f"batch_{batch_num:05d}.json"
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Write as newline-delimited JSON (NDJSON) — Snowflake-friendly
                with open(output_path, "wb") as f:
                    for event in batch:
                        f.write(orjson.dumps(event))
                        f.write(b"\n")

                total_written += len(batch)

        return total_written
