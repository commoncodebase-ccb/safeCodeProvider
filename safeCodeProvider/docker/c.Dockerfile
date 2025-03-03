FROM alpine:latest


RUN apk add --no-cache gcc musl-dev


WORKDIR /app


COPY . .


CMD ["sh", "-c", "gcc -o main main.c && ./main"]