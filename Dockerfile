# Use an official lightweight Python image
FROM python:3.9-slim

# Install system dependencies required for CAD libraries (GL/GLU)
RUN apt-get update -y && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglu1-mesa \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
# We use --no-cache-dir to keep the image small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 10000

# Command to run the application
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:10000", "app:app"]

