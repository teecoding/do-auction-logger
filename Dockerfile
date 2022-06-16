FROM python:3.10.5-alpine

RUN apk add --no-cache ffmpeg \
    curl \ 
    git 
    
RUN git clone https://github.com/teecoding/do-auction-logger.git /do-auction-logger

WORKDIR /do-auction-logger

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY .env .

RUN chmod +x *.py

CMD ["python", "-u", "main.py"]