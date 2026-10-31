FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir . || pip install --no-cache-dir "mistralai-workflows>=3.10" "mistralai>=3.0" pydantic httpx

COPY src/ ./src/

CMD ["python", "-m", "src.entrypoints.worker"]
