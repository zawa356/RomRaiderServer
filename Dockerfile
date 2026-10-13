FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY product_v1 ./product_v1
COPY scripts ./scripts
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/srv
USER 10001
