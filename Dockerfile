FROM python:3.10.5-alpine

WORKDIR /do-auction-logger

RUN apk add --no-cache git && \
    git clone https://github.com/teecoding/do-auction-logger.git . && \
    git pull && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \ 
    chmod +x *.py

COPY .env .

CMD ["python", "-u", "main.py"]
