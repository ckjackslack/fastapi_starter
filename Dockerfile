FROM python:3.8
RUN apt update && apt upgrade
RUN mkdir /opt/webapp
WORKDIR /opt/webapp
COPY ./requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r ./requirements.txt
COPY ./src ./src
WORKDIR /opt/webapp/src
EXPOSE 8000/tcp
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]