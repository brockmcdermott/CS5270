import io
import json
import boto3
from botocore.stub import Stubber
from storage_s3 import S3WidgetStore
from models import WidgetRequest

def test_put_widget_uploads_correct_json(monkeypatch):
    s3 = boto3.client("s3", region_name="us-east-1")

    # Inject our stubbed client
    def fake_client(service_name, *args, **kwargs):
        assert service_name == "s3"
        return s3
    monkeypatch.setattr("boto3.client", fake_client)

    store = S3WidgetStore("bucket3")

    req = WidgetRequest(
        type="WidgetCreateRequest",
        requestId="r1",
        widgetId="w1",
        owner="Alice Smith",
        label="Widget A",
        description="A red widget",
        otherAttributes=[{"name": "color", "value": "red"}]
    )

    expected_body = json.dumps({
        "widgetId": "w1",
        "owner": "Alice Smith",
        "label": "Widget A",
        "description": "A red widget",
        "color": "red"
    })

    with Stubber(s3) as stub:
        stub.add_response(
            "put_object",
            {},
            {
                "Bucket": "bucket3",
                "Key": "widgets/alice-smith/w1",
                "Body": expected_body,
                "ContentType": "application/json",
            },
        )

        key = store.put_widget(req)
        assert key == "widgets/alice-smith/w1"
