FROM --platform=linux/amd64 python:3.9.19-slim as build

WORKDIR /app/

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "main.py"]
