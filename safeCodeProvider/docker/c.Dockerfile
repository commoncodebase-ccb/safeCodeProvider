FROM alpine:latest


RUN apk add --no-cache gcc musl-dev


WORKDIR /app


COPY safecodeprovider/uploads /app/uploads


CMD ["sh", "-c", "gcc -o \"${STUDENT_DIR}/script\" \"${STUDENT_DIR}/script.c\" && \"${STUDENT_DIR}/script\""]
