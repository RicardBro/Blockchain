FROM python:3.11-slim as base
WORKDIR /app

FROM base as builder
COPY requirements.txt /app/
RUN pip install --no-cache-dir --prefix=/install -r /app/requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY ui /app/ui
EXPOSE 8501
# Run streamlit with the local app.py in the ui folder
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
