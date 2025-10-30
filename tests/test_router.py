# tests/test_router.py
from types import SimpleNamespace
from models import WidgetRequest
from router import handle_request

class FakeStore:
    def __init__(self):
        self.called = False
    def put_widget(self, req):
        self.called = True

class FakeLog:
    def __init__(self):
        self.lines = []
    def info(self, m): self.lines.append(("INFO", m))
    def warning(self, m): self.lines.append(("WARN", m))
    def error(self, m): self.lines.append(("ERR", m))

def test_router_calls_store_for_create():
    store, log = FakeStore(), FakeLog()
    req = WidgetRequest(type="WidgetCreateRequest", requestId="r1", widgetId="w1", owner="Alice Smith")
    handle_request(req, store, log)
    assert store.called is True
