FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
RUN apt-get update && apt-get install -y npm
WORKDIR /app/static
RUN npm init -y && npm install

WORKDIR /app
CMD [ "python3", "app.py" ]