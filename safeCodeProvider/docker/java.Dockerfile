FROM openjdk:17-jdk-slim


WORKDIR /app


COPY . /app


CMD sh -c "javac /app/${folder_path}/${file_name}.java && java -cp /app/${folder_path} ${file_name}"