<div align="center">

# Corporate Registry Document Processor

**AI-assisted document classification and human-in-the-loop review for the BVI Financial Services Commission**

[![Live Page](https://img.shields.io/badge/Landing_Page-Live-2563eb?style=flat-square)](https://deze-tingz.github.io/corporate-registry-processor/)
![Python](https://img.shields.io/badge/Python-3.13-3776ab?style=flat-square&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19-61dafb?style=flat-square&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Claude API](https://img.shields.io/badge/Claude_API-Sonnet-d97706?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

[Live Page](https://deze-tingz.github.io/corporate-registry-processor/) · [Features](#features) · [Architecture](#architecture) · [Quick Start](#quick-start) · [API Reference](#api-reference)

</div>

---

## Overview

CRDP is a full-stack document processing system built under the **Caribbean Trusted AI** framework. It uses Claude AI to classify corporate registry filings (articles of incorporation, amendments, annual returns, etc.) and extract structured fields — but every classification requires human approval before becoming final.

The system enforces a strict separation: **AI assists, humans decide**. All actions are recorded in a tamper-evident, hash-chained audit log suitable for regulatory compliance.

## Features

| Feature | Description |
|---------|-------------|
| **AI Classification** | Claude API (Sonnet, temp 0.0) classifies documents into 6 types with confidence scores and reasoning |
| **Field Extraction** | Automatically extracts company name, registration number, filing date, registered agent, signatories, jurisdiction |
| **Human Review** | Split-pane interface: document viewer (left) + classification panel (right) with approve/correct/escalate actions |
| **Hash-Chained Audit** | SHA-256 chained, append-only log with tamper verification. Every action traceable to a user |
| **RBAC + MFA** | 4 hierarchical roles (Intake Clerk → Reviewer → Supervisor → Administrator). TOTP-based MFA |
| **OCR Pipeline** | PyMuPDF for native PDF text, Tesseract fallback for scanned pages and images |
| **Graceful Degradation** | AI unavailable → documents queue for manual classification. System never stops |
| **Filesystem Watcher** | Auto-ingests documents dropped into `storage/intake/` via watchdog |

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (React + TS + Tailwind + Vite)        │
│  8 pages · role-aware nav · TanStack Query      │
├─────────────────────────────────────────────────┤
│  API Gateway (FastAPI)                          │
│  25 endpoints · JWT auth · rate limiting        │
├────────────┬────────────┬───────────────────────┤
│ Auth       │ Classifier │ Audit                 │
│ JWT+RBAC   │ Claude API │ Hash-chain            │
│ MFA (TOTP) │ OCR        │ CSV/JSON export       │
├────────────┴────────────┴───────────────────────┤
│  PostgreSQL (SQLAlchemy Async + Alembic)        │
│  6 tables · async sessions · UUID PKs           │
└─────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.13, FastAPI, SQLAlchemy Async, PostgreSQL, Alembic |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query, Zustand |
| **AI** | Claude API (Sonnet), versioned prompts, temperature 0.0 |
| **OCR** | PyMuPDF, Tesseract (fallback) |
| **Auth** | JWT (python-jose), bcrypt (passlib), TOTP (pyotp) |
| **Audit** | SHA-256 hash chain, append-only, 7-year retention policy |

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 20+
- PostgreSQL 15+
- Anthropic API key

### Backend

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt

# Create .env from template
cp ../.env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET, ANTHROPIC_API_KEY

# Run migrations
alembic upgrade head

# Seed admin user
python -m app.scripts.seed_admin

# Start server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — login with `admin@bvifsc.vg` / `ChangeMe123!`

## API Reference

### Auth
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | Public | Login, returns JWT tokens |
| POST | `/api/auth/refresh` | Public | Refresh access token |
| POST | `/api/auth/logout` | Auth | Logout |
| GET | `/api/auth/me` | Auth | Current user profile |
| POST | `/api/auth/mfa/setup` | Auth | Generate MFA secret + provisioning URI |
| GET | `/api/auth/mfa/qr` | Auth | QR code image for authenticator app |
| POST | `/api/auth/mfa/verify` | Auth | Verify TOTP code, enable MFA |

### Documents
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/documents` | Auth | Upload document (multipart) |
| GET | `/api/documents` | Auth | List documents (filterable by status) |
| GET | `/api/documents/{id}` | Auth | Document detail |
| GET | `/api/documents/{id}/file` | Auth | Stream original file |
| GET | `/api/documents/{id}/text` | Auth | Extracted text |

### Classifications
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/classifications` | Auth | Trigger AI classification |
| GET | `/api/classifications/{doc_id}` | Auth | Get classification result |

### Reviews
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/reviews/queue` | Reviewer+ | Documents awaiting review |
| POST | `/api/reviews` | Reviewer+ | Submit decision (approve/correct/escalate) |
| GET | `/api/reviews/escalated` | Supervisor+ | Escalated documents only |
| POST | `/api/reviews/override` | Supervisor+ | Supervisor override |

### Queue
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/queue` | Reviewer+ | List processing queue |
| PATCH | `/api/queue/{id}` | Reviewer+ | Update queue item status |

### Audit
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/audit` | Supervisor+ | Query audit log (filterable) |
| GET | `/api/audit/verify` | Supervisor+ | Verify hash chain integrity |
| GET | `/api/audit/export/csv` | Admin | Export audit log as CSV |
| GET | `/api/audit/export/json` | Admin | Export audit log as JSON |

### Admin
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/admin/users` | Admin | List all users |
| POST | `/api/admin/users` | Admin | Create user |
| PATCH | `/api/admin/users/{id}` | Admin | Update user (role, status) |
| GET | `/api/admin/status` | Admin | System statistics |

## Document Types

| Type | Description |
|------|-------------|
| `articles_of_incorporation` | Company formation documents |
| `amendment` | Changes to articles or company details |
| `annual_return` | Yearly compliance filings |
| `registered_agent_change` | Change of registered agent |
| `dissolution_notice` | Company dissolution filing |
| `other` | Unclassified or unrecognized |

## Project Structure

```
corporate-registry-processor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── models/              # 6 SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── routers/             # 8 API routers (25 endpoints)
│   │   ├── services/            # Business logic + AI classifier
│   │   ├── middleware/          # Auth + rate limiting
│   │   ├── utils/               # Password hashing, hash chain
│   │   └── scripts/             # Seed admin script
│   ├── alembic/                 # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # 8 pages
│   │   ├── components/          # 9 reusable components
│   │   ├── stores/              # Zustand auth store
│   │   └── lib/                 # Axios client with JWT interceptor
│   └── package.json
├── storage/                     # File storage (intake/originals/processed)
├── docs/                        # GitHub Pages landing page
└── .env.example
```

## Governance

Built under the **Caribbean Trusted AI** framework with these principles:

- **Transparency** — AI reasoning and confidence visible on every classification
- **Accountability** — Hash-chained audit log, every action tied to a user
- **Human Authority** — AI never makes final decisions
- **Resilience** — Graceful degradation when AI is unavailable

---

<div align="center">
  <sub>Built for the BVI Financial Services Commission under the Caribbean Trusted AI framework</sub>
</div>
