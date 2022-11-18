FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir log

EXPOSE 5001

ENV PONG_DEPLOYMENT_MODE docker

CMD [ "python", "./app.py" ]

