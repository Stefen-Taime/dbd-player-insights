"""
S3 publisher — uploads partitioned NDJSON to AWS S3.

Partition structure: s3://{bucket}/{event_type}/yyyy/mm/dd/hh/batch_XXXXX.json
SNS notifications trigger Snowpipe auto-ingest on each PUT.
"""

from __future__ import annotations

import io
import logging
from collections import defaultdict
from datetime import datetime

import orjson

from generator.publishers.base import BasePublisher

logger = logging.getLogger(__name__)


class S3Publisher(BasePublisher):
    def __init__(
        self,
        bucket: str = "dbd-telemetry-raw",
        prefix: str = "",
        batch_size: int = 10_000,
        region: str = "us-east-1",
    ):
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.batch_size = batch_size
        self._batch_counters: dict[str, int] = defaultdict(int)

        try:
            import boto3
            self.s3 = boto3.client("s3", region_name=region)
        except ImportError:
            logger.warning(
                "boto3 not installed — S3Publisher will raise on publish. "
                "Install with: pip install boto3"
            )
            self.s3 = None

    def publish_batch(self, events: list[dict], partition_date: datetime | str | None = None) -> int:
        if not events:
            return 0
        if self.s3 is None:
            raise RuntimeError("boto3 is required for S3Publisher")

        # Group by event_type + hour
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

        total_uploaded = 0
        for partition_key, partition_events in partitions.items():
            for i in range(0, len(partition_events), self.batch_size):
                batch = partition_events[i : i + self.batch_size]
                self._batch_counters[partition_key] += 1
                batch_num = self._batch_counters[partition_key]

                # Build NDJSON in memory
                buf = io.BytesIO()
                for event in batch:
                    buf.write(orjson.dumps(event))
                    buf.write(b"\n")
                buf.seek(0)

                # S3 key
                key_parts = [self.prefix, partition_key, f"batch_{batch_num:05d}.json"]
                s3_key = "/".join(p for p in key_parts if p)

                self.s3.upload_fileobj(
                    buf, self.bucket, s3_key,
                    ExtraArgs={"ContentType": "application/x-ndjson"},
                )
                total_uploaded += len(batch)
                logger.debug("Uploaded %d events to s3://%s/%s", len(batch), self.bucket, s3_key)

        logger.info("S3 batch: %d events across %d partitions", total_uploaded, len(partitions))
        return total_uploaded
