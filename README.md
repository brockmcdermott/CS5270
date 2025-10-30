# CS5270 – HW6: Consumer Program Design  
### Step 1 – Design Overview

## 1️⃣ Goal
Build a **Consumer program** that processes *Widget Requests* from **Bucket 2** and stores results in either **Bucket 3** (S3) or a **DynamoDB table**.  
Each request represents one widget creation, update, or deletion.

For **HW6**, you will **implement only `WidgetCreateRequest`** — but your design must **anticipate `WidgetDeleteRequest` and `WidgetUpdateRequest`** for later assignments.  
Requests strictly follow the provided `widgetRequest-schema.json`.

---

## 2️⃣ System Flow
1. **Read one Widget Request** from Bucket 2 at a time (in key order – smallest key first).  
   - Do *not* bulk-list the entire bucket; retrieve just the next key each loop.  
   - This ensures scalability for future multi-Consumer designs.

2. **If a request is found**  
   - Delete the object from Bucket 2.  
   - Parse the JSON into a validated `WidgetRequest` model.  
   - Process according to its `type` (only `WidgetCreateRequest` is handled in HW6).  
   - Immediately resume polling for the next request.

3. **If no request is available**  
   - Sleep ≈ 100 milliseconds and retry (polling loop).

4. **Repeat until a stop condition** (manual interrupt or CLI limit).

---

## 3️⃣ Command-Line Arguments
The program accepts configuration options such as:  
- **Storage strategy** (`--target s3 | dynamodb`)  
- **Resource names** (`--bucket2`, `--bucket3`, `--table`)  
- Optional parameters: `--sleep-ms`, `--stop-after`, `--log-file`  

Use a mature 3rd-party CLI library (e.g., `click`, `argparse`) for simplicity and clarity.

---

## 4️⃣ Architecture & Modules
### A. Poller (Input)
Encapsulates request retrieval from Bucket 2.  
It lists one object key (smallest first), reads it, deletes it, and returns the JSON text.  
This module will later be replaceable with a queue-based source (e.g., SQS).

### B. Parser / Validator (`models.py`)
Parse the JSON according to the official schema:  
- `type` must match `WidgetCreateRequest | WidgetDeleteRequest | WidgetUpdateRequest`  
- `requestId`, `widgetId`, and `owner` are required.  
- `owner` must match `[A-Za-z ]+`.  
Use a standard JSON or Pydantic library — never write a custom parser.

### C. Router (Request Handler)
- **WidgetCreateRequest:** Store the new widget in the chosen target.  
- **WidgetDeleteRequest:** Log a warning if the object does not exist (do not throw errors).  
- **WidgetUpdateRequest:** Reserved for HW7 (e.g., partial updates, null/empty rules).

### D. Storage Targets (Strategy Pattern)
1. **S3 Store**  
   - Serialize the widget to JSON.  
   - Save at: `widgets/{ownerSlug}/{widgetId}` where `ownerSlug = owner.lower().replace(" ", "-")`.  
2. **DynamoDB Store**  
   - Each widget attribute (including `otherAttributes`) becomes a top-level attribute — never a map or list.  

### E. Logging
Use a standard logging library (avoid manual file I/O).  
Record info, warnings, and errors with timestamps.  
Write to both console and a log file (e.g., `consumer.log`).

---

## 5️⃣ Polling Loop Pseudo-Code
```text
Loop until stop condition:
    request_json = poller.get_next()
    if request_json exists:
        delete_request_from_bucket2()
        req = parse_and_validate(request_json)
        if req.type == "WidgetCreateRequest":
            store_widget(req)
        elif req.type in ("WidgetDeleteRequest", "WidgetUpdateRequest"):
            log_warning("Not implemented in HW6")
    else:
        sleep(100ms)
End loop
