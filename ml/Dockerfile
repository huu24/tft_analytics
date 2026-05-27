FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY etl/config/tft_static_data.py /app/etl/config/tft_static_data.py
COPY etl/__init__.py /app/etl/__init__.py
COPY etl/config/__init__.py /app/etl/config/__init__.py
COPY ml/ ./ml/

RUN mkdir -p /app/ml/checkpoints

CMD ["python", "-m", "ml.train"]
