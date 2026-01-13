FROM python:3.11-slim

WORKDIR /app

# Install uv for fast package management
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY negotiator.py .

# Install dependencies
RUN uv pip install --system -e .

# Expose port
ENV PORT=8080
EXPOSE 8080

# Run the agent
CMD ["python", "main.py"]
