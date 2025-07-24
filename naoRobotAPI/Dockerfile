ARG UBUNTU_VERSION=14.04
FROM ubuntu:$UBUNTU_VERSION

ARG PYTHON_VERSION=2.7.5

# Install dependencies
# PIP - openssl version > 1.1 may be an issue (try older ubuntu images)
RUN apt-get update \
  && apt-get install -y wget python-pip python2.7-dev gcc make openssl libffi-dev libgdbm-dev libsqlite3-dev libssl-dev zlib1g-dev \
  && apt-get clean

WORKDIR /tmp/


RUN mkdir pynaoqi
COPY ./pynaoqi /pynaoqi
#COPY ./pynaoqi /usr/local/lib/python2.7/
COPY . /naoRobotAPI
ENV PYTHONPATH=${PYTHONPATH}:/pynaoqi

WORKDIR /naoRobotAPI
RUN ./.bashrc
#RUN apt-get -y update
#RUN apt-get install -y wget
RUN pip install -r requirements.txt
#RUN python initialScript.py
#file:///C:/Program%20Files%20(x86)/Aldebaran%20Robotics/Choregraphe%20Suite%202.1/share/doc/getting_started/helloworld_choregraphe_script.html

CMD [ "python", "a.py" ]