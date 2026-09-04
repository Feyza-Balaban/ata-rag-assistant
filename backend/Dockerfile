# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install "torch==2.13.0" \
    --index-url https://download.pytorch.org/whl/cpu
RUN --mount=type=cache,id=ata-rag-pip-deps-v2,target=/root/.cache/pip,sharing=locked \
    python -m pip install \
    --index-url https://pypi.org/simple \
    --retries 10 \
    --timeout 120 \
    -r /app/backend/requirements.txt
ARG ATA_EMBEDDING_MODEL_ID=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
ENV ATA_EMBEDDING_MODEL_PATH=/opt/models/paraphrase-multilingual-MiniLM-L12-v2
RUN --mount=type=cache,id=ata-rag-hf-model-v1,target=/root/.cache/huggingface,sharing=locked \
    mkdir -p "${ATA_EMBEDDING_MODEL_PATH}" && \
    python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('${ATA_EMBEDDING_MODEL_ID}'); model.save('${ATA_EMBEDDING_MODEL_PATH}')"
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1
COPY backend /app/backend
RUN mkdir -p /app/scraper/output
COPY scraper/output/chunks.jsonl /app/scraper/output/chunks.jsonl
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]