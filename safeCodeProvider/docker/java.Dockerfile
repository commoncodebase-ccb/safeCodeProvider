FROM openjdk:17-jdk-slim


WORKDIR /app


COPY safecodeprovider/uploads /app/uploads


CMD ["sh", "-c", "javac \"${STUDENT_DIR}/script.java\" && java -cp \"${STUDENT_DIR}\" script"]
