FROM python:3.11-slim

WORKDIR /app

# Install dependencies directly
RUN pip install "a2a-sdk[http-server]>=0.3.0" uvicorn starlette

# Copy application files
COPY main.py .
COPY negotiator.py .

# Expose port
ENV PORT=8080
EXPOSE 8080

# ENTRYPOINT accepts CLI args from compose; CMD provides defaults
ENTRYPOINT ["python", "main.py"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
