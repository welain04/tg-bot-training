FROM python:3.12-slim

ARG GIT_SHA=unknown
LABEL org.opencontainers.image.revision=$GIT_SHA

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "bot.main"]
