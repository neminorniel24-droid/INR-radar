# MoneyTrace India

Dashboard for tracking India's international trade flows and public fund/budget data,
built on free government and international APIs.

## Data Sources
- **World Bank API** — macro economic indicators (GDP, inflation, unemployment, FDI). No key required.
- **UN Comtrade API** — import/export trade flows by country and commodity. Free key required.
- **data.gov.in** — Indian government budget/scheme datasets. Free key required.

## Project Structure
```
moneytrace-india/
├── backend/
│   ├── main.py           # FastAPI app wrapping all three data sources
│   ├── requirements.txt
│   └── .env.example      # copy to .env and add your keys
├── frontend/
│   └── index.html        # single-file dashboard (Chart.js)
└── README.md
```

## Setup

### 1. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your free API keys (Comtrade + data.gov.in)
uvicorn main:app --reload
```
Backend runs at `http://localhost:8000`.

### 2. Frontend
Just open `frontend/index.html` in a browser (or serve it with any static server).
It points to `http://localhost:8000` by default — edit `API_BASE` in the `<script>`
if your backend runs elsewhere.

## Getting free API keys
- **UN Comtrade**: register at https://comtradeplus.un.org, then request a subscription
  key via the Developer Portal. Free tier: up to 500 calls/day, 100K records/call.
- **data.gov.in**: register at https://data.gov.in/apis for a free API key.

## Roadmap
- [ ] Wire up real data.gov.in resource IDs for Indian budget/scheme data
- [ ] Add RBI DBIE data (monetary/banking stats)
- [ ] Add CAG audit report references for fund-misuse tracking
- [ ] Deploy backend (Render/Railway) so frontend can run standalone
