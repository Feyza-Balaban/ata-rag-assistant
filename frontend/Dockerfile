FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY frontend/requirements.txt /app/frontend/requirements.txt
RUN pip install --no-cache-dir -r /app/frontend/requirements.txt

COPY frontend /app/frontend
COPY .streamlit /app/.streamlit

EXPOSE 8501

CMD ["streamlit", "run", "frontend/chat_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

