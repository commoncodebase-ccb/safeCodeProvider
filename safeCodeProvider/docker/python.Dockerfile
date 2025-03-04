FROM python:3.9-alpine

WORKDIR /app

COPY . /app

CMD ["sh", "-c", "python \"${STUDENT_DIR}/script.py\""]


#docker build -f python.Dockerfile -t imagename .
#docker run --name py-app pyimage