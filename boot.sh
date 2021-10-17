#!/bin/bash

source venv/bin/activate
python -m gunicorn -b :5000 --access-logfile - --error-logfile - wxmeow:app
