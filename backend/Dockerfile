
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y vim curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade -r ./requirements.txt

RUN pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
