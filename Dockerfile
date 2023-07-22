from python:latest

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

ENV HOSTNAME="0.0.0.0"
ENV PORT="5000"

CMD python main.py server-command --host $HOST --port $PORT
