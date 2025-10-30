# poller_s3.py
import boto3
import json
import time
import logging
from typing import Optional
from models import WidgetRequest

class S3RequestPoller:
    """
    Polls Bucket 2 for widget requests, one object at a time.
    Reads the smallest key, deletes it, parses JSON into a WidgetRequest.
    Sleeps ~100ms when no requests are available.
    """

    def __init__(self, bucket2_name: str, sleep_ms: int = 100):
        self.s3 = boto3.client("s3")
        self.bucket2 = bucket2_name
        self.sleep = max(1, sleep_ms) / 1000.0
        self.log = logging.getLogger(self.__class__.__name__)

    def get_next_request(self) -> Optional[WidgetRequest]:
        """Return the next WidgetRequest object or None if bucket empty."""
        try:
            resp = self.s3.list_objects_v2(Bucket=self.bucket2, MaxKeys=1)
            contents = resp.get("Contents", [])
            if not contents:
                time.sleep(self.sleep)
                return None

            # Always pick the smallest key lexicographically
            key = sorted([c["Key"] for c in contents])[0]
            obj = self.s3.get_object(Bucket=self.bucket2, Key=key)
            body = obj["Body"].read().decode("utf-8")

            # Delete immediately after reading
            self.s3.delete_object(Bucket=self.bucket2, Key=key)
            self.log.info(f"Consumed request from {key}")

            # Parse JSON into a WidgetRequest
            data = json.loads(body)
            req = WidgetRequest(**data)
            return req

        except self.s3.exceptions.NoSuchBucket:
            self.log.error(f"Bucket {self.bucket2} does not exist.")
            raise
        except Exception as e:
            self.log.error(f"Error retrieving request: {e}")
            return None
