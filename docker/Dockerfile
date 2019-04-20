############################################################
# Dockerfile to build a POSTGIS database for use in concave hull testing
# Based on mdillion/postgres
############################################################

FROM mdillon/postgis:9.6
LABEL author Jeremy Castagno

# Set environment variables
ENV PGADMIN_URL=https://ftp.postgresql.org/pub/pgadmin/pgadmin4/v4.5/pip/pgadmin4-4.5-py2.py3-none-any.whl
ENV PGADMIN=/usr/local/lib/python2.7/dist-packages/pgadmin4

# Copies these files over to the container, the 'z' is just to ensure this file is executed after
ADD initdb-z-postgis-osm.sh /docker-entrypoint-initdb.d/initdb-z-postgis-osm.sh
# ADD ${IMPOSM_URL} /home

# These commands will be run the first time the image is being built, installing needed packages
RUN apt-get update
RUN apt-get install -y nano python-pip libpq-dev python-dev curl

# PGADMIN 4, for viewing database if desired
RUN pip install $PGADMIN_URL
RUN echo "SERVER_MODE = False" >> $PGADMIN/config_local.py
RUN echo "DEFAULT_SERVER = '0.0.0.0'" >> $PGADMIN/config_local.py

# Expose PGAMDIN webserver port
EXPOSE 5050







