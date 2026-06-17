FROM mariadb:11.8.8

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends socat rsync \
    && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint-galera.sh /usr/local/bin/docker-entrypoint-galera.sh
COPY initdb-create-sst-user.sh /docker-entrypoint-initdb.d/01-create-sst-user.sh

RUN chmod 0755 /usr/local/bin/docker-entrypoint-galera.sh \
    && chmod 0644 /docker-entrypoint-initdb.d/01-create-sst-user.sh

ENTRYPOINT ["docker-entrypoint-galera.sh"]
CMD ["mariadbd"]
