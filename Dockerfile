FROM postgres:15.2
COPY ./hstore.sql /docker-entrypoint-initdb.d/
