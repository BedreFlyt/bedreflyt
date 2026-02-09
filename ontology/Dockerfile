FROM ubuntu:24.04

RUN <<EOF
    apt-get -y update
    apt-get -y install openjdk-17-jdk-headless python3 python3-pip liblapack3 wget curl bash
    rm -rf /var/lib/apt/lists/*
EOF

# Set the working directory
WORKDIR /fuseki

COPY . /fuseki
COPY config.ttl /fuseki
COPY bedreflyt.ttl /fuseki/bedreflyt.ttl

RUN mkdir -p /fuseki/databases/Bedreflyt
RUN chmod 755 /fuseki/databases/Bedreflyt

# Fetch the latest version and download it
RUN set -eux; \
    BASE_URL="https://dlcdn.apache.org/jena/binaries/"; \
    version=$(curl -s $BASE_URL | \
        grep -o 'apache-jena-fuseki-[[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+\.tar\.gz' | \
        sort -V | \
        tail -1); \
    echo "Version: $version"; \
    curl -s $BASE_URL/$version -o /fuseki/$version; \
    mkdir -p /fuseki/jena-fuseki; \
    tar -xvzf /fuseki/$version -C /fuseki/jena-fuseki --strip-components=1; \
    rm /fuseki/$version

# Execute the command
CMD /fuseki/jena-fuseki/fuseki-server --config /fuseki/config.ttl

# Expose port 3030
EXPOSE 3030