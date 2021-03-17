 
FROM python:3.8.6

LABEL MAINTAINER="dkeysil dkeysil@protonmail.com"

WORKDIR /contribbot
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY bot bot
COPY core core

CMD python -u __main__.py
