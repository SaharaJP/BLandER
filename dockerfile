FROM python:3.11

ARG APP_DIR=/app
WORKDIR "$APP_DIR"
ENV PYTHONPATH="$APP_DIR"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y dumb-init

ENTRYPOINT ["dumb-init", "--"]
CMD ["sh", "entrypoint.sh"]