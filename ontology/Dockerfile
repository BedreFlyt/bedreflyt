FROM ubuntu:24.04

RUN apt-get update -y
RUN apt-get install -y openjdk-21-jdk-headless

# Set the working directory
WORKDIR /fuseki

COPY . /fuseki
COPY config.ttl /fuseki
COPY bedreflyt.ttl /fuseki/bedreflyt.ttl

RUN mkdir -p /fuseki/databases/Bedreflyt
RUN chmod 755 /fuseki/databases/Bedreflyt

RUN tar -xzf /fuseki/apache-jena-fuseki-6.0.0.tar.gz -C /fuseki \
    && mv /fuseki/apache-jena-fuseki-6.0.0 /fuseki/jena-fuseki \
    && rm /fuseki/apache-jena-fuseki-6.0.0.tar.gz

# Execute the command
CMD ["/fuseki/jena-fuseki/fuseki-server", "--config", "/fuseki/config.ttl"]

# Expose port 3030
EXPOSE 3030