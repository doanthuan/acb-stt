#!/bin/sh

waitress-serve --port=60002 --host=0.0.0.0 --url-scheme='https' app.app:app
# export FLASK_APP=app/app.py
# FLASK_ENV=development flask run --host 0.0.0.0 --port 60002 --cert app/cert.pem --key app/key.pem
# gunicorn --workers=4 --certfile app/cert.pem --keyfile app/key.pem -b 0.0.0.0:60002 app.app:app
