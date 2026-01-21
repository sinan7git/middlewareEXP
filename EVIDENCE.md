# Test Evidence - Middleware MVP

## Test Run: 2026-01-21

### Test Users Created
```
Operator Token:      cb6543252c6c31b9a3dccc294f4a7424e6799bcb
Finance Admin Token: 55f42100564d99ce98047a5520abf10f30d1eda4
```

---

## 1. NORMAL FLOW - Container ABCD1234567

### Step 1: GATE_IN event
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Token cb6543252c6c31b9a3dccc294f4a7424e6799bcb" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "EVT001", "event_type": "GATE_IN", "container_no": "ABCD1234567", "owner_code": "OWNER1"}'
```
**Response:**
```json
{
    "success": true,
    "event_id": "EVT001",
    "new_status": "GATE_IN",
    "invoice": null
}
```

### Step 2: INSPECTION event
```json
{
    "success": true,
    "event_id": "EVT002",
    "new_status": "INSPECTED",
    "invoice": null
}
```

### Step 3: WORK_ORDER event (creates invoice)
```json
{
    "success": true,
    "event_id": "EVT003",
    "new_status": "WORK_DONE",
    "invoice": {
        "invoice_ref": "INV-C0A37C66",
        "status": "PENDING"
    }
}
```

---

## 2. QUARANTINE - Missing Owner (EVIDENCE ITEM)

### Event quarantined due to missing owner:
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Token cb6543252c6c31b9a3dccc294f4a7424e6799bcb" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "EVT010", "event_type": "GATE_IN", "container_no": "WXYZ9876543"}'
```
**Response:**
```json
{
    "success": false,
    "error": "Missing owner_code",
    "quarantined": true
}
```

### Quarantine list shows pending event:
```json
{
    "count": 1,
    "items": [
        {
            "event_id": "EVT010",
            "container_no": "WXYZ9876543",
            "reason": "Missing owner_code",
            "status": "PENDING",
            "event_data": {
                "event_id": "EVT010",
                "event_type": "GATE_IN",
                "container_no": "WXYZ9876543",
                "payload": {}
            },
            "approved_by": null,
            "approved_at": null,
            "created_at": "2026-01-21T11:51:47.839933Z"
        }
    ]
}
```

### Finance admin approves quarantine:
```bash
curl -X POST http://localhost:8000/api/quarantine/EVT010/approve/ \
  -H "Authorization: Token 55f42100564d99ce98047a5520abf10f30d1eda4"
```
**Response:**
```json
{
    "success": true,
    "event_id": "EVT010",
    "new_status": "GATE_IN",
    "approved_by": "finance_admin1"
}
```

### After approval - status changed to APPROVED:
```json
{
    "count": 1,
    "items": [
        {
            "event_id": "EVT010",
            "container_no": "WXYZ9876543",
            "reason": "Missing owner_code",
            "status": "APPROVED",
            "approved_by": "finance_admin1",
            "approved_at": "2026-01-21T11:51:48.018745Z"
        }
    ]
}
```

---

## 3. ERP SEND WITH RETRIES (EVIDENCE ITEM)

### Invoice list before send:
```json
{
    "count": 1,
    "items": [
        {
            "invoice_ref": "INV-C0A37C66",
            "container_no": "ABCD1234567",
            "work_order_id": "WO001",
            "amount": "250.00",
            "currency": "USD",
            "status": "PENDING",
            "reason": null,
            "retry_count": 0,
            "created_at": "2026-01-21T11:51:42.457611Z"
        }
    ]
}
```

### Send to ERP (30% failure rate, up to 3 retries):
```bash
curl -X POST http://localhost:8000/api/invoices/INV-C0A37C66/send/ \
  -H "Authorization: Token 55f42100564d99ce98047a5520abf10f30d1eda4"
```
**Response (success on first attempt):**
```json
{
    "success": true,
    "attempts": 1
}
```

### Invoice status after send:
```json
{
    "invoice_ref": "INV-C0A37C66",
    "container_no": "ABCD1234567",
    "status": "SENT",
    "reason": "Successfully sent to ERP",
    "retry_count": 1
}
```

---

## 4. REPLAY CONTAINER (EVIDENCE ITEM)

### Replay all events for container:
```bash
curl -X POST http://localhost:8000/api/replay/ABCD1234567/ \
  -H "Authorization: Token cb6543252c6c31b9a3dccc294f4a7424e6799bcb"
```
**Response:**
```json
{
    "success": true,
    "container_no": "ABCD1234567",
    "final_status": "WORK_DONE",
    "events_replayed": 3,
    "details": [
        {
            "event_id": "EVT001",
            "event_type": "GATE_IN",
            "status": "GATE_IN"
        },
        {
            "event_id": "EVT002",
            "event_type": "INSPECTION",
            "status": "INSPECTED"
        },
        {
            "event_id": "EVT003",
            "event_type": "WORK_ORDER",
            "status": "WORK_DONE"
        }
    ]
}
```

---

## 5. DUPLICATE PREVENTION

### Duplicate event_id rejected:
```json
{
    "success": false,
    "error": "Duplicate event_id",
    "quarantined": false
}
```

---

## 6. AUDIT TRAIL

### Full event history for container:
```json
{
    "container_no": "ABCD1234567",
    "event_count": 3,
    "events": [
        {
            "event_id": "EVT001",
            "event_type": "GATE_IN",
            "container_no": "ABCD1234567",
            "timestamp": "2026-01-21T11:51:42.255165Z",
            "payload": {},
            "created_by": "operator1"
        },
        {
            "event_id": "EVT002",
            "event_type": "INSPECTION",
            "container_no": "ABCD1234567",
            "timestamp": "2026-01-21T11:51:42.328160Z",
            "payload": {},
            "created_by": "operator1"
        },
        {
            "event_id": "EVT003",
            "event_type": "WORK_ORDER",
            "container_no": "ABCD1234567",
            "timestamp": "2026-01-21T11:51:42.426390Z",
            "payload": {
                "work_order_id": "WO001",
                "amount": "250.00"
            },
            "created_by": "operator1"
        }
    ]
}
```

---

## 7. STATUS PROGRESSION VALIDATION

### Skip status rejected (quarantined):
```json
{
    "success": false,
    "error": "Cannot go from PENDING to WORK_DONE. Allowed: ['GATE_IN']",
    "quarantined": true
}
```

---

## 8. CONTAINER FORMAT VALIDATION

### Invalid format rejected:
```json
{
    "success": false,
    "errors": {
        "container_no": [
            "Container number must be 4 letters + 7 digits (e.g., ABCD1234567)"
        ]
    }
}
```

