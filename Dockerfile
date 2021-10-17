FROM python:slim

RUN useradd wxcat

WORKDIR /home/wxcat

COPY deploy.py setup.py .flaskenv boot.sh ./
COPY wxmeow wxmeow

RUN python -m venv venv
RUN venv/bin/pip install --upgrade pip
RUN venv/bin/pip install -e .
RUN venv/bin/pip install gunicorn
RUN chmod +x boot.sh

ENV FLASK_APP=wxmeow/__init__.py
# RUN python deploy.py

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
