# CS5270 – HW6: Consumer Program Design  
### Step 1 – Design Overview

## 1️⃣ Goal
Build a **Consumer** that processes *Widget Requests* from **Bucket 2** and persists widgets to **Bucket 3 (S3)** or a **DynamoDB table**.  
Requests encode create/update/delete operations and conform to **`widgetRequest-schema.json`**.

For **HW6**, only **`WidgetCreateRequest`** is implemented. **`WidgetDeleteRequest`** and **`WidgetUpdateRequest`** are designed now and deferred to HW7.

---

## 2️⃣ System Flow
1. **Read exactly one request** from Bucket 2 **in key order (smallest first)**.  
   - Do **not** bulk-list; request the minimal next key each loop for scalability.
2. **If found**  
   - **Delete** the request object from Bucket 2 (delete-after-read for HW6).  
   - Parse/validate JSON → `WidgetRequest`.  
   - Process by `type` (Create only in HW6).  
   - Immediately look for the next request.
3. **If none found**  
   - Sleep ~**100 ms**, then retry.
4. **Stop condition**  
   - Manual interrupt or `--stop-after N`.

---

## 3️⃣ Command-Line Arguments
- **Required:**  
  - `--bucket2` (S3 requests bucket)  
  - `--target {s3|dynamodb}`
- **Conditional:**  
  - `--bucket3` (when `--target s3`)  
  - `--table` (when `--target dynamodb`)
- **Optional:**  
  - `--sleep-ms` (default 100)  
  - `--stop-after` (0 = run forever)  
  - `--log-file` (default `consumer.log`)

Uses `argparse`; logs go to **console + file**. File handler is recreated per run and flushed/closed on exit.

---

## 4️⃣ Architecture & Modules
| Module | Responsibility |
|---|---|
| `poller_s3.py` | **S3RequestPoller** lists minimal keys in Bucket 2, reads smallest key, **deletes** it, returns a **`WidgetRequest`** (or `None` when empty). |
| `models.py` | Stdlib dataclasses for **`WidgetRequest`** and `OtherAttribute`. Validates required fields and **`owner` ~ `[A-Za-z ]+`**. Helpers: `owner_slug`, `to_flat_widget_dict`. |
| `storage_s3.py` | **S3WidgetStore** writes JSON to `widgets/{ownerSlug}/{widgetId}` in Bucket 3. |
| `storage_dynamodb.py` | **DynamoWidgetStore** writes a **flattened** item (each `otherAttributes` entry becomes a **top-level** attribute). |
| `router.py` | Routes by `req.type`. **Create** → store; **Delete/Update** → log “not implemented in HW6”. |
| `consumer.py` | CLI, logging, wiring poller + chosen store, polling loop, graceful shutdown & log flush. |
| `tests/` | Unit/integration tests using **`botocore.stub.Stubber`** (no Moto required). |

---

## 5️⃣ Storage Rules
- **S3**: serialize flattened widget JSON; key = `widgets/{ownerSlug}/{widgetId}` where `ownerSlug = owner.lower().replace(" ", "-")`.
- **DynamoDB**: all widget fields (including `otherAttributes`) are **top-level attributes** (no nested map/list).

---

## 6️⃣ Polling Loop Pseudo-Code
```text
Loop until stop:
    req = poller.get_next_request()      # returns WidgetRequest or None
    if req is None:
        sleep(100ms)
        continue

    if req.type == "WidgetCreateRequest":
        store.put_widget(req)
    elif req.type in ("WidgetDeleteRequest", "WidgetUpdateRequest"):
        log_warning("Not implemented in HW6")
End loop
