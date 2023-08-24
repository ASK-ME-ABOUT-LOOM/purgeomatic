FROM python:3.11.4-alpine3.18
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY . /app
