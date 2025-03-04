FROM openjdk:17-jdk-slim


WORKDIR /app


COPY . /app


CMD ["sh", "-c", "javac \"${STUDENT_DIR}/script.java\" && java -cp \"${STUDENT_DIR}\" script"]
