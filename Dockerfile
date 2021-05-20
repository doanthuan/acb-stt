FROM python:3.8-slim-buster

WORKDIR /

COPY . /app

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
