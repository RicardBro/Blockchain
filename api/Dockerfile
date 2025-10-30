FROM python:3.11-slim as base
WORKDIR /app

FROM base as builder
COPY requirements.txt /app/
RUN pip install --no-cache-dir --prefix=/install -r /app/requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app
# Copy only installed packages from builder
COPY --from=builder /install /usr/local
COPY api /app/api
COPY simulator /app/simulator
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
