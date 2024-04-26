FROM python:3.12

WORKDIR /app
COPY .github/workflows/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY app.py app.py
CMD [ "python3", "-u", "app.py"]