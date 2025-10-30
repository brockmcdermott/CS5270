# tests/test_consumer.py
import types
from pathlib import Path
from models import WidgetRequest

# We'll import consumer and then monkeypatch the classes it instantiates:
# - consumer.S3RequestPoller
# - consumer.S3WidgetStore / consumer.DynamoWidgetStore
import consumer


class FakePoller:
    """Returns exactly one request, then None forever (like empty bucket)."""
    def __init__(self, bucket2_name: str, sleep_ms: int = 100):
        self.called = 0
        self.bucket2_name = bucket2_name
        self.sleep_ms = sleep_ms

    def get_next_request(self):
        if self.called == 0:
            self.called += 1
            return WidgetRequest(
                type="WidgetCreateRequest",
                requestId="r1",
                widgetId="w1",
                owner="Alice Smith",
                otherAttributes=[{"name": "color", "value": "red"}],
            )
        self.called += 1
        return None


class FakeS3Store:
    def __init__(self, bucket3_name: str):
        self.bucket3_name = bucket3_name
        self.calls = []

    def put_widget(self, req: WidgetRequest):
        self.calls.append(("put", req.widgetId))


class FakeDdbStore:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.calls = []

    def put_widget(self, req: WidgetRequest):
        self.calls.append(("put", req.widgetId))


def test_consumer_s3_path(monkeypatch, tmp_path: Path):
    # Patch the classes consumer.main() will construct
    monkeypatch.setattr(consumer, "S3RequestPoller", FakePoller)
    monkeypatch.setattr(consumer, "S3WidgetStore", FakeS3Store)

    log_file = tmp_path / "log_s3.txt"
    # Run with --stop-after=1 so the loop exits after processing one request
    rc = consumer.main([
        "--bucket2", "bucket2",
        "--target", "s3",
        "--bucket3", "bucket3",
        "--sleep-ms", "1",
        "--stop-after", "1",
        "--log-file", str(log_file),
    ])
    assert rc == 0
    # Basic sanity: log file created and contains our startup line
    assert log_file.exists()
    assert "Consumer starting" in log_file.read_text()


def test_consumer_dynamodb_path(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(consumer, "S3RequestPoller", FakePoller)
    monkeypatch.setattr(consumer, "DynamoWidgetStore", FakeDdbStore)

    log_file = tmp_path / "log_ddb.txt"
    rc = consumer.main([
        "--bucket2", "bucket2",
        "--target", "dynamodb",
        "--table", "widgets",
        "--sleep-ms", "1",
        "--stop-after", "1",
        "--log-file", str(log_file),
    ])
    assert rc == 0
    assert log_file.exists()
    assert "Consumer starting" in log_file.read_text()
