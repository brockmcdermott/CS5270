from models import WidgetRequest, owner_slug, to_flat_widget_dict

def test_schema():
    data = {
        "type": "WidgetCreateRequest",
        "requestId": "r1",
        "widgetId": "w1",
        "owner": "Alice Smith",
        "label": "Test Label",
        "description": "A test widget",
        "otherAttributes": [{"name": "color", "value": "red"}]
    }
    req = WidgetRequest(**data)
    assert req.owner == "Alice Smith"
    assert owner_slug(req.owner) == "alice-smith"
    d = to_flat_widget_dict(req)
    assert d["color"] == "red"
    assert "widgetId" in d
