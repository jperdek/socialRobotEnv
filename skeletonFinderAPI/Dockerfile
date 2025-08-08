FROM python:3.12-slim
COPY ./server /python-flask
WORKDIR /python-flask

RUN apt-get -y update

RUN pip install -r requirements.txt


CMD [ "python", "server.py" ]