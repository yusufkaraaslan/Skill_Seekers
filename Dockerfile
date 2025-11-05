# Use an official Python runtime as a parent image
FROM python:3.14-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Install test dependencies
RUN pip install pytest

# Run tests
RUN python -m pytest tests/test_mcp_server.py

# Make the entrypoint script executable
RUN chmod +x skill_seeker_mcp/server.py

# Run server.py when the container launches
ENTRYPOINT ["python", "skill_seeker_mcp/server.py"]