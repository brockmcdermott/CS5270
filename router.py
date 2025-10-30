# router.py
import logging
from models import WidgetRequest

def handle_request(req: WidgetRequest, store, log: logging.Logger) -> None:
    if req.type == "WidgetCreateRequest":
        store.put_widget(req)
        log.info(f"CREATE processed: widgetId={req.widgetId} owner={req.owner}")
    elif req.type == "WidgetDeleteRequest":
        log.warning("DELETE request received — not implemented in HW6")
    elif req.type == "WidgetUpdateRequest":
        log.warning("UPDATE request received — not implemented in HW6")
    else:
        log.error(f"Unknown request type: {req.type}")
