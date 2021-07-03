#!/bin/sh

# For development
waitress-serve --port=60002 --host=0.0.0.0 app.app:app

# For production
# gunicorn --workers 3 --threads 2 -t 0 -b 0.0.0.0:60002 app.app:app
