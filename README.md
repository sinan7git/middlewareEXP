# Middleware MVP - Container Event Processing

A Django REST API that processes container operational events (Gate/Inspection/Work Order)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Create test users (generates auth tokens)
python manage.py setup_users

# 4. Run server
python manage.py runserver
```

After running `setup_users`, you'll see:
```
=== TEST USERS CREATED ===
Operator Token:      abc123...
Finance Admin Token: xyz789...
==========================
```

**Save these tokens** - you'll need them for API calls.

---

## API Endpoints

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/api/events/` | POST | operator | Submit event |
| `/api/containers/{no}/` | GET | operator | Get container status |
| `/api/audit/{no}/` | GET | operator | Get event history |
| `/api/quarantine/` | GET | operator | List quarantined events |
| `/api/quarantine/{id}/approve/` | POST | finance_admin | Approve quarantine |
| `/api/replay/{no}/` | POST | operator | Rebuild from history |
| `/api/invoices/` | GET | operator | List invoices |
| `/api/invoices/{ref}/send/` | POST | finance_admin | Send to ERP |

---

## Sample API Calls

Replace `YOUR_TOKEN` with actual token from setup.

### 1. Submit GATE_IN Event
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Token YOUR_OPERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "EVT001",
    "event_type": "GATE_IN",
    "container_no": "ABCD1234567",
    "owner_code": "OWNER1"
  }'
```

### 2. Submit INSPECTION Event
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Token YOUR_OPERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "EVT002",
    "event_type": "INSPECTION",
    "container_no": "ABCD1234567"
  }'
```

### 3. Submit WORK_ORDER Event (creates invoice)
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Token YOUR_OPERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "EVT003",
    "event_type": "WORK_ORDER",
    "container_no": "ABCD1234567",
    "payload": {
      "work_order_id": "WO001",
      "amount": "250.00"
    }
  }'
```

### 4. Get Container Status (SSOT)
```bash
curl http://localhost:8000/api/containers/ABCD1234567/ \
  -H "Authorization: Token YOUR_OPERATOR_TOKEN"
```

### 5. Get Audit Trail
```bash
curl http://localhost:8000/api/audit/ABCD1234567/ \
  -H "Authorization: Token YOUR_OPERATOR_TOKEN"
```

### 6. Trigger Quarantine (missing owner)
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Token YOUR_OPERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "EVT010",
    "event_type": "GATE_IN",
    "container_no": "WXYZ9876543"
  }'
```

### 7. Approve Quarantine (finance_admin only)
```bash
curl -X POST http://localhost:8000/api/quarantine/EVT010/approve/ \
  -H "Authorization: Token YOUR_FINANCE_ADMIN_TOKEN"
```

### 8. Send Invoice to ERP (may fail ~30%)
```bash
curl -X POST http://localhost:8000/api/invoices/INV-XXXXXXXX/send/ \
  -H "Authorization: Token YOUR_FINANCE_ADMIN_TOKEN"
```

### 9. Replay Container Events
```bash
curl -X POST http://localhost:8000/api/replay/ABCD1234567/ \
  -H "Authorization: Token YOUR_OPERATOR_TOKEN"
```

---

## Validation Rules

1. **Container Format**: 4 letters + 7 digits (e.g., ABCD1234567)
2. **Status Progression**: Must follow order:
   - PENDING → GATE_IN → INSPECTED → WORK_DONE → GATE_OUT
3. **Duplicate Prevention**: 
   - Same event_id rejected
   - Same work_order cannot be billed twice
4. **Quarantine Triggers**:
   - Missing owner on GATE_IN
   - Owner conflict detected
   - Invalid status progression

---

## Design Decisions

1. **Simple Token Auth**: Used DRF's built-in TokenAuthentication - easy to implement and test.

2. **SQLite**: Default database for MVP - no extra setup needed.

3. **Immutable Events**: Events are write-once. SSOT container status is updated, but event history never changes.

4. **Quarantine Pattern**: Invalid events aren't rejected outright - they're stored for manual review.

5. **ERP Mock**: 30% random failure with 3 retries simulates real-world unreliability.

6. **Replay Function**: Can rebuild container status from event history - useful for debugging/recovery.

---

## What's Implemented

- [x] POST /events with validation
- [x] GET /containers/{no} (SSOT view)
- [x] GET /audit/{no} (event history)
- [x] POST /quarantine/{id}/approve
- [x] POST /replay/{no}
- [x] Container format validation
- [x] Status progression rules
- [x] Duplicate event prevention
- [x] Duplicate work order billing prevention
- [x] Quarantine for missing owner/conflicts
- [x] ERP mock with 30% failure + 3 retries
- [x] RBAC (operator vs finance_admin)
- [x] Token authentication

## What I'd Add Next

- Date range filtering for replay
- Bulk event import
- Webhook notifications
- Rate limiting
- More comprehensive logging
- Docker support
- Test coverage

---

## Time Spent

Approximately 4 hours.

---

## Architecture

See `ARCHITECTURE.md` for diagram.
