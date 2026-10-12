# ================================
#   FASTAPI + XGBOOST DOCKERFILE
# ================================

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY api/ ./api/
COPY models/ ./models/
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose API port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]