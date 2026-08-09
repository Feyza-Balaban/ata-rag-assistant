# ata-rag-assistant
Multilingual RAG assistant for ATA University
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