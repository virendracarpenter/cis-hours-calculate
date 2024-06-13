FROM selenium/standalone-chrome:latest

# Install Python and other necessary packages
USER root
RUN apt update && \
    apt install -y python3 python3-pip

RUN apt -y update
RUN pip install --upgrade pip

WORKDIR /app
COPY . /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 80 for the application
EXPOSE $PORT

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the FastAPI application using uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
