FROM python:3.8-slim-buster

WORKDIR /

COPY app /app

COPY requirements.txt /app/requirements.txt

COPY deploy/gunicorn_conf.py /
COPY deploy/start.sh /

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN chmod +x /start.sh

CMD ["/start.sh"]
