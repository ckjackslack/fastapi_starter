FROM python:3.8
RUN apt update && apt upgrade
RUN mkdir /opt/webapp
WORKDIR /opt/webapp
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
EXPOSE 8000/tcp
COPY . .
WORKDIR /opt/webapp/src