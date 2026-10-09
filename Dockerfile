# Xnova for Telegram. Railway builds this file automatically.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY xnova_bot ./xnova_bot

# The game database lives on the Railway volume (see README).
CMD ["python", "-m", "xnova_bot.main"]
