FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
ARG YOUR_ENV

ENV YOUR_ENV=${YOUR_ENV}
LABEL Name=sentieo Version=1.0

RUN mkdir -p /export
WORKDIR /export

ENV PYTHONPATH .
COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

RUN pip install -r requirements.txt
COPY models ./models
COPY constants.py ./constants.py
COPY views.py ./views.py
COPY NylasIntegration ./NylasIntegration
COPY config ./config

EXPOSE 8000
EXPOSE 8300
ENTRYPOINT [ "python3", "/export/views.py"]