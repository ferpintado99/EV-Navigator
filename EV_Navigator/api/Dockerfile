# Use Python 3.9 image as the base image
FROM python:3.9

# Set /app as the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install dependencies from the requirements file without caching to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the api.py file into the container
COPY api.py .

# Set the command to run the API using uvicorn
# Uvicorn runs on host 0.0.0.0 and port 8000 within the container
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]


