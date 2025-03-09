FROM alpine:latest


RUN apk add --no-cache gcc musl-dev


WORKDIR /app


COPY . /app


CMD ["sh", "-c", "gcc -o \"${folder_path}/${file_name}\" \"${folder_path}/${file_name}.c\" && \"${folder_path}/${file_name}\""]
