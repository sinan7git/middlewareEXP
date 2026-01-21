#!/bin/bash
BASE_URL="http://localhost:8000/api"

echo "MIDDLEWARE MVP - FUNCTIONALITY DEMO"

OP_TOKEN=${1:-"YOUR_OPERATOR_TOKEN"}
ADMIN_TOKEN=${2:-"YOUR_FINANCE_ADMIN_TOKEN"}

echo ""
echo "Using tokens:"
echo "  Operator: $OP_TOKEN"
echo "  Admin: $ADMIN_TOKEN"
echo ""

call_api() {
    local method=$1
    local endpoint=$2
    local token=$3
    local data=$4
    
    echo ">>> $method $endpoint"
    if [ -n "$data" ]; then
        curl -s -X $method "$BASE_URL$endpoint" \
            -H "Authorization: Token $token" \
            -H "Content-Type: application/json" \
            -d "$data" | python -m json.tool
    else
        curl -s -X $method "$BASE_URL$endpoint" \
            -H "Authorization: Token $token" | python -m json.tool
    fi
    echo ""
}

echo "1. NORMAL FLOW - Container ABCD1234567"

echo "Step 1: GATE_IN event"
call_api POST "/events/" $OP_TOKEN '{
    "event_id": "EVT001",
    "event_type": "GATE_IN",
    "container_no": "ABCD1234567",
    "owner_code": "OWNER1"
}'

echo "Step 2: INSPECTION event"
call_api POST "/events/" $OP_TOKEN '{
    "event_id": "EVT002",
    "event_type": "INSPECTION",
    "container_no": "ABCD1234567"
}'

echo "Step 3: WORK_ORDER event (creates invoice)"
call_api POST "/events/" $OP_TOKEN '{
    "event_id": "EVT003",
    "event_type": "WORK_ORDER",
    "container_no": "ABCD1234567",
    "payload": {"work_order_id": "WO001", "amount": "250.00"}
}'

echo "Step 4: Check container status (SSOT)"
call_api GET "/containers/ABCD1234567/" $OP_TOKEN

echo "Step 5: Check audit trail"
call_api GET "/audit/ABCD1234567/" $OP_TOKEN

echo "2. QUARANTINE - Missing Owner"

echo "Submit GATE_IN without owner (will be quarantined)"
call_api POST "/events/" $OP_TOKEN '{
    "event_id": "EVT010",
    "event_type": "GATE_IN",
    "container_no": "WXYZ9876543"
}'

echo "List quarantine"
call_api GET "/quarantine/" $OP_TOKEN

echo "Approve quarantine (finance_admin)"
call_api POST "/quarantine/EVT010/approve/" $ADMIN_TOKEN

echo "3. VALIDATION - Skip Status"

echo "Try WORK_ORDER without INSPECTION (invalid progression)"
call_api POST "/events/" $OP_TOKEN '{
    "event_id": "EVT020",
    "event_type": "WORK_ORDER",
    "container_no": "SKIP1234567",
    "owner_code": "OWNER2",
    "payload": {"work_order_id": "WO002", "amount": "100.00"}
}'

echo "4. DUPLICATE PREVENTION"

echo "Try duplicate event_id"
call_api POST "/events/" $OP_TOKEN '{
    "event_id": "EVT001",
    "event_type": "GATE_IN",
    "container_no": "DUPE1234567",
    "owner_code": "OWNER3"
}'

echo "5. ERP SEND WITH RETRIES"

echo "List invoices"
call_api GET "/invoices/" $OP_TOKEN

echo "Send invoice to ERP (30% failure rate, 3 retries)"
echo "Note: May succeed or fail depending on random result"
INVOICE_REF=$(curl -s "$BASE_URL/invoices/" -H "Authorization: Token $OP_TOKEN" | python -c "import sys,json; d=json.load(sys.stdin); print(d['items'][0]['invoice_ref'] if d['items'] else '')" 2>/dev/null)

if [ -n "$INVOICE_REF" ]; then
    call_api POST "/invoices/$INVOICE_REF/send/" $ADMIN_TOKEN
else
    echo "No invoices found to send"
fi

echo "6. REPLAY CONTAINER"

call_api POST "/replay/ABCD1234567/" $OP_TOKEN

echo "DEMO COMPLETE"
