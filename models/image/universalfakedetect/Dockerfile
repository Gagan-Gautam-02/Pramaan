FROM python:3.11-slim

WORKDIR /app

COPY sdk /sdk
RUN pip install --no-cache-dir /sdk

COPY models/image/universalfakedetect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models/image/universalfakedetect/ .

EXPOSE 5004
CMD ["python", "server.py"]
