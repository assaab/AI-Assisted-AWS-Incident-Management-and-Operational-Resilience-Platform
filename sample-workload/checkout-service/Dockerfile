FROM python:3.11-slim

WORKDIR /app
COPY sample-workload/checkout-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY sample-workload/checkout-service/app.py /app/app.py

EXPOSE 8090
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
