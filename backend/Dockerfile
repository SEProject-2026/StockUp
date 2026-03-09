# 1. Base Image
FROM python:3.12-slim

# 2. Set the working directory
WORKDIR /app

# 3. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Install system dependencies for OpenCV
# We need libgl1 and libglib2.0-0 for cv2 to work on slim images
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy source code
COPY src/ ./src/

# 7. Expose port
EXPOSE 8000

# 8. Run the app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]