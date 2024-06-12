FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV PATH="/usr/lib/chromium/:${PATH}"

CMD ["python", "app.py"]