# Use the official Python runtime as a parent image
FROM python:3.12.4-alpine

# Set the working directory to /var/task
WORKDIR /var/task

# Copy function code file, requirements.txt, and key.json to the working directory
COPY bundesliga_update_ecs.py .
COPY requirements.txt .
COPY key.json .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for Google credentials
ENV GOOGLE_APPLICATION_CREDENTIALS=/var/task/key.json

# Set the CMD to run the script directly
CMD ["python", "/var/task/bundesliga_update_ecs.py"]



