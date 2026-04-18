FROM python:3.11-slim

WORKDIR /app

# SDK is mounted by docker compose via build context
COPY sdk /sdk
RUN pip install --no-cache-dir /sdk

COPY models/image/npr_deepfakedetection/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models/image/npr_deepfakedetection/ .

EXPOSE 5001
CMD ["python", "server.py"]
