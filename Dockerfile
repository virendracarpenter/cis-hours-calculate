# FROM selenium/standalone-chrome:latest
FROM python:3.12

# Install Python and other necessary packages
# USER root
# RUN apt update && \
#     apt install -y python3 python3-pip


RUN apt -y update
RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libpangocairo-1.0-0 \
    libxrandr2 \
    libasound2 \
    libpango-1.0-0 \
    libcups2 \
    libxss1 \
    libgtk-3-0 \
    libgbm-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN pyppeteer-install

# Expose port 80 for the application
EXPOSE $PORT

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the FastAPI application using uvicorn
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT"]
