import json
import io
import boto3
from botocore.stub import Stubber
from botocore.response import StreamingBody
from poller_s3 import S3RequestPoller

def _streaming_body(s: str) -> StreamingBody:
    return StreamingBody(io.BytesIO(s.encode("utf-8")), len(s))

def test_poller_reads_and_deletes_object_with_stubber(monkeypatch):
    # Real client, but all network calls are stubbed
    s3 = boto3.client("s3", region_name="us-east-1")

    # Make our poller use *this* client
    def fake_client(service_name, *args, **kwargs):
        assert service_name == "s3"
        return s3
    monkeypatch.setattr("boto3.client", fake_client)

    poller = S3RequestPoller("bucket2", sleep_ms=1)

    request_json = json.dumps({
        "type": "WidgetCreateRequest",
        "requestId": "r1",
        "widgetId": "w1",
        "owner": "Alice Smith"
    })

    with Stubber(s3) as stub:
        # 1) list_objects_v2 returns one key
        stub.add_response(
            "list_objects_v2",
            {"KeyCount": 1, "Contents": [{"Key": "0001.json"}]},
            {"Bucket": "bucket2", "MaxKeys": 1}
        )
        # 2) get_object returns our JSON
        stub.add_response(
            "get_object",
            {"Body": _streaming_body(request_json)},
            {"Bucket": "bucket2", "Key": "0001.json"}
        )
        # 3) delete_object acknowledges delete
        stub.add_response(
            "delete_object",
            {},
            {"Bucket": "bucket2", "Key": "0001.json"}
        )
        # 4) After processing, next call finds nothing → poller will sleep & return None next time.
        #    For this test we only call get_next_request() once, so no stub required.

        req = poller.get_next_request()
        assert req.type == "WidgetCreateRequest"
        assert req.owner == "Alice Smith"
