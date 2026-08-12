FROM python:3.12-slim

WORKDIR /app

# System dependencies required by Playwright/Chromium.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the Chromium browser binary + its OS-level dependencies.
# This step makes the image noticeably larger (Chromium alone is
# several hundred MB) - that is expected for a Playwright-based scraper.
RUN playwright install --with-deps chromium

COPY . .

# Runs the full pipeline once: crawl the site, then build chunks/metadata.
# For a recurring (nightly) crawl, schedule this command via Coolify's
# scheduled task feature rather than looping inside the container.
CMD ["sh", "-c", "python scraper.py && python build_chunks.py"]