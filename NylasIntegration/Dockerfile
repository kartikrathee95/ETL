FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
ARG YOUR_ENV

ENV YOUR_ENV=${YOUR_ENV}
LABEL Name=sentieo Version=1.0

RUN mkdir -p /nylas
WORKDIR /nylas

ENV PYTHONPATH .
COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt
COPY config ./config
COPY slacker ./slacker
COPY utils ./utils
COPY oauth ./oauth
COPY NylasIntegration ./NylasIntegration
COPY helperfiles.py ./helperfiles.py
COPY kafka_logger.py ./kafka_logger.py
COPY setup.py ./setup.py

EXPOSE 8000
EXPOSE 8200
ENTRYPOINT [ "python3", "/nylas/NylasIntegration/app.py"]
# command to run on local=  PYTHONPATH=. YOUR_ENV=integrationservice  python3 NylasIntegration/app.py