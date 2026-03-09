# 1. Base Image: Use a lightweight Python version for faster and smaller builds
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Set environment variables
# Prevents Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures that Python output is logged immediately (useful for debugging in the cloud)
ENV PYTHONUNBUFFERED=1

# 4. Copy ONLY the requirements file first (Leverages Docker caching to save build time)
COPY requirements.txt .

# 5. Install dependencies without saving unnecessary cache files
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the actual source code (Tests and other folders are ignored)
COPY src/ ./src/

# 7. Expose the port the server will run on
EXPOSE 8000

# 8. Command to run the server 
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]