# FROM pytorch/pytorch:latest
FROM python:3.11-slim

RUN pip install --upgrade pip


WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
COPY models.py .


CMD [ "python3", "app.py" ]