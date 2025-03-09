FROM python:3.9-alpine

WORKDIR /app

COPY . /app

CMD ["sh", "-c", "python \"${folder_path}/${file_name}.py\""]
