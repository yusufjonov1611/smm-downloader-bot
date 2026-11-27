FROM python:3.12-slim

# FFmpeg va tizim vositalarini o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render avtomatik PORT muhit o'zgaruvchisini beradi
ENV PORT=10000
EXPOSE 10000

CMD ["python", "main.py"]
