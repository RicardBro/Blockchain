FROM python:3.11-slim as base
WORKDIR /app

FROM base as builder
COPY requirements.txt /app/
RUN pip install --no-cache-dir --prefix=/install -r /app/requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY miner /app/miner
COPY simulator /app/simulator
CMD ["python", "miner/worker.py"]
