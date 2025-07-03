FROM node:24-slim as builder

WORKDIR /app
COPY . .
WORKDIR /app/static
RUN npm init -y && npm install

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY --from=builder /app /app
CMD [ "python3", "app.py" ]