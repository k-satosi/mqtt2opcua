FROM python:3
WORKDIR /work

COPY requirements.txt /work

RUN pip install -r requirements.txt

CMD ["python", "test_mqtt2opcua.py"]
