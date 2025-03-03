FROM python:3.9-alpine
WORKDIR /app
COPY . .
CMD ["python", "main.py"]

#docker build -f python.Dockerfile -t imagename .
#docker run --name py-app pyimage