FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir -U pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

ENV CONFIG_PATH=config_dev.yaml

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
