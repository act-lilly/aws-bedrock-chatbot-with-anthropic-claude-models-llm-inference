FROM python:3.11-slim-buster
WORKDIR /app
COPY bedrock-chat/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bedrock-chat/ .

ENV AWS_BEDROCK_REGION="us-east-1"
ENV LOGGING_LEVEL="INFO"
ENV BOTOCORE_LOGGING_LEVEL="INFO"

EXPOSE 8080
CMD ["python", "-m", "streamlit", "run", "--server.enableCORS", "true", "--server.enableXsrfProtection", "true", "--server.address", "0.0.0.0", "--server.port", "8080", "main.py"]