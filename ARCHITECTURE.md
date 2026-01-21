# Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MIDDLEWARE MVP                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   Client     │
                              │  (curl/app)  │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   Token Auth (RBAC)   │
                         │  operator/finance_admin│
                         └───────────┬───────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ POST /events│  │GET /container│  │ GET /audit  │  │POST /replay │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼───────────────┘
          │                │                │                │
          ▼                │                │                │
┌─────────────────────┐    │                │                │
│   VALIDATION        │    │                │                │
│  ┌───────────────┐  │    │                │                │
│  │Container Format│  │    │                │                │
│  │(4 letters+7 dig)│  │    │                │                │
│  └───────────────┘  │    │                │                │
│  ┌───────────────┐  │    │                │                │
│  │Status Progress │  │    │                │                │
│  │(no skip steps) │  │    │                │                │
│  └───────────────┘  │    │                │                │
│  ┌───────────────┐  │    │                │                │
│  │Duplicate Check │  │    │                │                │
│  └───────────────┘  │    │                │                │
│  ┌───────────────┐  │    │                │                │
│  │Owner Check    │  │    │                │                │
│  └───────────────┘  │    │                │                │
└──────────┬──────────┘    │                │                │
           │               │                │                │
     ┌─────┴─────┐         │                │                │
     ▼           ▼         │                │                │
┌─────────┐ ┌─────────┐    │                │                │
│ VALID   │ │ INVALID │    │                │                │
└────┬────┘ └────┬────┘    │                │                │
     │           │         │                │                │
     ▼           ▼         │                │                │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER (SQLite)                                │
│                                                                              │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐         │
│  │  Event (immutable)│   │ Container (SSOT) │   │   Quarantine     │         │
│  │  - event_id (PK)  │   │ - container_no(PK)│   │  - event_id      │         │
│  │  - event_type     │   │ - owner_code     │   │  - reason        │         │
│  │  - container_no   │◄──┤ - status         │   │  - status        │         │
│  │  - timestamp      │   │ - last_event_id  │   │  - approved_by   │         │
│  │  - payload        │   └──────────────────┘   └──────────────────┘         │
│  │  - created_by     │                                                       │
│  └──────────────────┘                                                        │
│                                                                              │
│  ┌──────────────────┐   ┌──────────────────┐                                │
│  │  InvoiceReady    │   │   UserProfile    │                                │
│  │  - invoice_ref(PK)│   │  - user (FK)     │                                │
│  │  - container_no   │   │  - role          │                                │
│  │  - work_order_id  │   │    (operator/    │                                │
│  │  - amount         │   │    finance_admin)│                                │
│  │  - status         │   └──────────────────┘                                │
│  │  - retry_count    │                                                       │
│  └─────────┬─────────┘                                                       │
└────────────┼────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ERP MOCK SERVICE                                   │
│                                                                              │
│   POST /invoices/{ref}/send/                                                │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │  30% random failure simulation                                   │       │
│   │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────────┐  │       │
│   │  │ Attempt │───►│ Attempt │───►│ Attempt │───►│ Mark FAILED  │  │       │
│   │  │    1    │fail│    2    │fail│    3    │fail│ with reason  │  │       │
│   │  └────┬────┘    └────┬────┘    └────┬────┘    └──────────────┘  │       │
│   │       │success       │success       │success                     │       │
│   │       ▼              ▼              ▼                            │       │
│   │  ┌─────────────────────────────────────┐                        │       │
│   │  │        Mark SENT to ERP             │                        │       │
│   │  └─────────────────────────────────────┘                        │       │
│   └─────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘


## Data Flow

1. Client sends event with auth token
2. Token validated → RBAC checked
3. Event validated (format, status, duplicates, owner)
4. If valid → Store in Event table → Update Container SSOT
5. If invalid → Store in Quarantine for review
6. If WORK_ORDER → Create InvoiceReady record
7. Finance admin can send invoice → ERP mock with retries
8. Replay rebuilds Container status from Event history


## Status Progression

PENDING → GATE_IN → INSPECTED → WORK_DONE → GATE_OUT
   │         │          │           │           │
   └─────────┴──────────┴───────────┴───────────┘
         Cannot skip steps (validation enforced)
```
