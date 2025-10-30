# CS5270 – HW6: Consumer Program Design  
### Step 1 – Design Overview

## 1️⃣ Goal
Build a **Consumer program** that processes *Widget Requests* from **Bucket 2** and stores results in either **Bucket 3** or a **DynamoDB table**.  
Each request represents one widget creation, update, or deletion.

For **HW6**, you will **implement only Create Requests** — but your design must **anticipate Delete and Update Requests** in later assignments.  
:contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}

---

## 2️⃣ System Flow
1. **Read one Widget Request** from Bucket 2 at a time (in key order – smallest key first).  
   - Do not bulk-list the entire bucket; retrieve a single object each loop.  
   - This makes the program efficient and scalable for future multi-Consumer use.  
   :contentReference[oaicite:2]{index=2}

2. **If a request is found**  
   - Delete the object from Bucket 2.  
   - Process the request according to its type (Create for HW6).  
   - Immediately resume polling for the next request.  
   :contentReference[oaicite:3]{index=3}

3. **If no request is available**  
   - Sleep ~100 milliseconds and try again (polling loop).  
   :contentReference[oaicite:4]{index=4}

4. **Repeat until a stop condition** (e.g., manual interrupt or CLI limit).

---

## 3️⃣ Command-Line Arguments
Allow the user to choose:
- **Storage strategy** (`--target s3 | dynamodb`)  
- **Resource names** (`--bucket2`, `--bucket3`, `--table`)  
- Optional parameters: `--sleep-ms`, `--stop-after`, `--log-file`

Use a third-party CLI library for easier argument parsing.  
:contentReference[oaicite:5]{index=5}

---

## 4️⃣ Architecture & Modules
### A. Poller (Input)
Encapsulate request retrieval from Bucket 2.  
Future assignments will swap this out for a queue, so keep it modular.  
:contentReference[oaicite:6]{index=6}

### B. Parser / Validator
Use a standard JSON library to parse the Widget Request schema. Do not write a custom parser.  
Validate required fields (type, requestId, widgetId, owner pattern [A-Za-z  ]).  
:contentReference[oaicite:7]{index=7}

### C. Router (Request Handler)
- **Create Request:** Store widget in the selected target.  
- **Delete Request:** Log a warning if object does not exist (do not error).  
- **Update Request:** Plan logic for HW7 (e.g., partial field updates, null/empty rules).  
:contentReference[oaicite:8]{index=8}:contentReference[oaicite:9]{index=9}

### D. Storage Targets (Strategy Pattern)
1. **S3 Store:**  
   - Serialize widget as JSON.  
   - Save to `widgets/{owner}/{widgetId}`.  
   - Derive `{owner}` by lower-casing and replacing spaces with dashes.  
   :contentReference[oaicite:10]{index=10}

2. **DynamoDB Store:**  
   - Each widget attribute (including those under `otherAttributes`) becomes a top-level attribute — not a map or list.  
   :contentReference[oaicite:11]{index=11}

### E. Logging
Use an open-source logging library (not manual file I/O).  
Log info, warnings, and errors with timestamps.  
:contentReference[oaicite:12]{index=12}

---

## 5️⃣ Polling Loop Pseudo-Code
```text
Loop until stop condition:
    request = get_next_request()
    if request exists:
        delete_request_from_bucket2()
        if request.type == "create":
            store_widget(request)
        elif request.type in ("delete", "update"):
            log_warning("Not implemented in HW6")
    else:
        sleep(100ms)
End loop
