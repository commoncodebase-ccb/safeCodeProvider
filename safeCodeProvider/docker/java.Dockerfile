
FROM openjdk:17-jdk-slim


WORKDIR /app


COPY . .


CMD ["sh", "-c", "javac Main.java && java Main"]