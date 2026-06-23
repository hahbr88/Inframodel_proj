FROM python:3.12-alpine AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apk add --no-cache --virtual .build-deps build-base linux-headers

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --no-compile -r requirements.txt \
    && find /opt/venv -type d -name "__pycache__" -prune -exec rm -rf {} + \
    && find /opt/venv -type f -name "*.pyc" -delete \
    && rm -rf /opt/venv/lib/python*/site-packages/pip* \
        /opt/venv/lib/python*/site-packages/setuptools* \
        /opt/venv/lib/python*/site-packages/wheel* \
        /opt/venv/share

FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN addgroup -S app && adduser -S -G app app && mkdir -p /app/data

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app main.py .
COPY --chown=app:app app ./app
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
