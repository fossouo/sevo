# Sèvo runtime — the CP-appris brain as a microservice.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[api]"

# Brain state lives on a mounted volume so it survives container restarts.
ENV SEVO_STATE_DIR=/data
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "sevo.api:app", "--host", "0.0.0.0", "--port", "8000"]
