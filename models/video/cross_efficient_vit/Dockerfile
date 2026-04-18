FROM python:3.11-slim

WORKDIR /app

COPY sdk /sdk
RUN pip install --no-cache-dir /sdk

COPY models/video/cross_efficient_vit/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models/video/cross_efficient_vit/ .

EXPOSE 7001
CMD ["python", "server.py"]
