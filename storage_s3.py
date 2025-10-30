# storage_s3.py
import json
import boto3
import logging
from models import WidgetRequest, to_flat_widget_dict, owner_slug

class S3WidgetStore:
    """
    Handles saving widgets to Bucket 3 in S3 as JSON objects.
    File path: widgets/{ownerSlug}/{widgetId}
    """

    def __init__(self, bucket3_name: str):
        self.s3 = boto3.client("s3")
        self.bucket3 = bucket3_name
        self.log = logging.getLogger(self.__class__.__name__)

    def put_widget(self, req: WidgetRequest) -> str:
        """
        Serialize and upload a WidgetRequest to S3.
        Returns the S3 key used for the object.
        """
        key = f"widgets/{owner_slug(req.owner)}/{req.widgetId}"
        body = json.dumps(to_flat_widget_dict(req))

        try:
            self.s3.put_object(
                Bucket=self.bucket3,
                Key=key,
                Body=body,
                ContentType="application/json"
            )
            self.log.info(f"Stored widget {req.widgetId} in {self.bucket3}/{key}")
            return key
        except Exception as e:
            self.log.error(f"Failed to store widget: {e}")
            raise
