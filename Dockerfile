# FROM ubuntu:latest
FROM python:3.10

RUN apt-get update

WORKDIR /app

COPY . .
COPY requirements.txt .

RUN pip3 install --upgrade requests
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7031

CMD ["python3", "main.py"]