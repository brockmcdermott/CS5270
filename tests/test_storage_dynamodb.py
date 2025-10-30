# tests/test_storage_dynamodb.py
import json
import boto3
from botocore.stub import Stubber
from boto3.dynamodb.types import TypeSerializer
from storage_dynamodb import DynamoWidgetStore
from models import WidgetRequest

def test_put_widget_flattens_attributes_and_calls_put_item(monkeypatch):
    ddb = boto3.client("dynamodb", region_name="us-east-1")

    # Force our store to use the stubbed client
    def fake_client(service_name, *args, **kwargs):
        assert service_name == "dynamodb"
        return ddb
    monkeypatch.setattr("boto3.client", fake_client)

    store = DynamoWidgetStore("widgets")

    req = WidgetRequest(
        type="WidgetCreateRequest",
        requestId="r1",
        widgetId="w1",
        owner="Alice Smith",
        label="A",
        description="demo",
        otherAttributes=[{"name": "color", "value": "red"}, {"name": "size", "value": "L"}],
    )

    # Build the exact AttributeValue map we expect
    py_item = {
        "widgetId": "w1",
        "owner": "Alice Smith",
        "label": "A",
        "description": "demo",
        "color": "red",
        "size": "L",
    }
    av_item = TypeSerializer().serialize(py_item)["M"]

    with Stubber(ddb) as stub:
        stub.add_response(
            "put_item",
            {},  # empty response body
            {"TableName": "widgets", "Item": av_item},
        )

        pk = store.put_widget(req)
        assert pk == "w1"
