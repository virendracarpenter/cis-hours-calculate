FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV PATH="/usr/lib/chromium/:${PATH}"

# Expose the application port
EXPOSE 8000


CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
