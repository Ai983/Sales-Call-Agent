# Sales Call Analyzer UI

## Setup

```bash
npm install
```

Create `.env.local` and set the API base URL:

```bash
cp .env.local.example .env.local
# edit as needed
```

## Run

```bash
npm run dev
```

App runs at http://localhost:3000

## Backend (required)

In repo root:

```bash
python -m uvicorn web_api.main:app --reload --port 8000
```
