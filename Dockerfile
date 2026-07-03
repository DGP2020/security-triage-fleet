FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 8080
EXPOSE 8080

# Command to run the uvicorn server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
