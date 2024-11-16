
FROM python:3.10-slim

WORKDIR /app
#ENV PYTHONPATH=/app

COPY . .

RUN apt-get update && apt-get install -y vim curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade -r ./requirements.txt

# if you comment it put torch in requirements
RUN pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
#EXPOSE 8000


# Command to run your FastAPI app (if needed)
#CMD ["python", "-m", "backend.main"]
