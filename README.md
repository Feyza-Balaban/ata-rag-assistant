# ATA RAG Assistant

Multilingual, source-grounded assistant for ATA University.

## Current project status

- Website scraper, cleaning, heading-based chunking, metadata: ready
- Streamlit chat in English, Turkish, and Polish: ready
- FastAPI `/ask`, `/health`, and `/metrics` endpoints: ready
- Local multilingual retrieval and confidence threshold: ready
- Optional OpenAI grounded answer generation: ready
- Real scraper output integration, persistent vector database, and deployment: next

## Team responsibilities

- **Feyza:** frontend, API integration, integration tests, documentation
- **Ümmü:** scraper, cleaned data, chunk generation, metadata
- **Shared:** backend validation, final integration, deployment, demo video

## Quick setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Generate scraper data before starting the real backend:

```powershell
.\.venv\Scripts\python.exe scraper/scraper.py
.\.venv\Scripts\python.exe scraper/build_chunks.py
```

Start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --port 8000
```

API documentation will be available at `http://127.0.0.1:8000/docs`.

## Frontend

The frontend was developed with Streamlit and includes:

- Multilingual support: English, Turkish, and Polish
- RAG chat interface
- Source link display
- Demo fallback when the backend is unavailable
- Analytics dashboard
- Responsive sidebar design

### Run the Chat Interface

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/chat_app.py
```

### Run the Analytics Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/dashboard.py
```

### Backend Configuration

The frontend reads the backend settings from environment variables:

```powershell
$env:ATA_RAG_API_URL = "BACKEND_ENDPOINT_HERE"
$env:ATA_RAG_API_KEY = "OPTIONAL_API_KEY"
```

If the backend endpoint is unavailable, the application automatically displays a demo response.

### Frontend Files

- `frontend/chat_app.py` – Multilingual chat interface
- `frontend/dashboard.py` – Analytics dashboard
- `frontend/api_client.py` – RAG backend API connection
- `.streamlit/config.toml` – Streamlit theme configuration

## Backend response contract

`POST /ask`

```json
{
  "question": "What are the admission requirements?",
  "language": "English"
}
```

The response includes `answer`, clickable `sources`, `confidence`,
`retrieval_score`, and the active generation `mode`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Docker Compose

After generating `scraper/output/chunks.jsonl`:

```powershell
docker compose up --build
```

The frontend runs on `http://127.0.0.1:8501` and the API runs on
`http://127.0.0.1:8000`.
