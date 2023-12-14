# Start from the official Python 3.9 image
FROM python:3.9

# Set the working directory to /app inside the container
WORKDIR /app

# Copy the requirements file into the container's working directory
COPY requirements.txt .

# Install Python dependencies specified in requirements.txt without storing cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy all other application files into the container's working directory
COPY . .

# Set the default command to run the application using uvicorn
# This command starts the FastAPI application on port 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
