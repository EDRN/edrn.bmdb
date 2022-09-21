# Image for the EDRN RDF Server
# =============================
#
# This is a Docker image definition that sets up the RDF web server providing
# data from the Early Detection Research Network's "Focus Bio Marker Data
# Base".


# Base Image
# ----------
#
# This image is built on Python 3.8.5 running on Alpine Linux 3.12

FROM python:3.10.7-alpine3.16


# Environment
# -----------
#
# These environment variables should be overridden at run time, typically in a
# Docker Composition.

ENV \
    BMDB_HOST=focusbmdb-db \
    BMDB_USER=cbmdb \
    BMDB_PASSWORD=cbmdb \
    BMDB_DB=cbmdb \
    SETUPTOOLS_VERSION=50.3.0


# Context
# -------
#
# This is where the "action" happens, in a directory called ``/app`` in the
# container.

WORKDIR /app


# Supporting Cast
# ---------------
#
# The source of this package; we could ``pip install` this but that would mean
# having to publish this package to PyPI first and what a pain in the butt.

COPY setup.py setup.cfg ./
COPY src/ src/


# Some Assembly Required
# ----------------------
#
# Bootstrap and buildout, as all the cool Plonistas know.

RUN :\
    apk update &&\
    apk add --quiet --virtual build-env gcc musl-dev &&\
    cd /app &&\
    pip install --quiet . &&\
    apk del --quiet build-env &&\
    rm -rf /var/cache/apk/* &&\
    pip uninstall --quiet --yes pip &&\
    :


# Answering Service
# -----------------
#
# That's TCP port 6543, the familiar default for Pyramid users.

EXPOSE 6543


# Are you OK?
# -----------
#
# Make sure we're answering

HEALTHCHECK --interval=1m --timeout=5s --start-period=23s CMD nc -z -w5 127.0.0.1 6543 || exit 1


# What to Run
# -----------
#
# It's the RDF Webserver, buh.

ENTRYPOINT ["/usr/local/bin/rdf-webserver"]


# Image Metadata
# --------------
#
# 
LABEL "org.label-schema.name"="EDRN Focus BMDB RDF Server"
LABEL "org.label-schema.description"="Web-based server of information in the Resource Description Format (RDF) for the Focus Bio Marker Database (BMDB) of the Early Detection Research Network (EDRN)"
LABEL "org.label-schema.version"="1.0.0"
LABEL "org.label-schema.schema-version"="1.0"
LABEL "org.label-schema.docker.cmd"="docker container run --detach --publish 6543:6543 --env BMDB_HOST=host --env BMDB_USER=cbmdb --env BMDB_PASSWORD=cbmdb --env BMDB_DB=cbmdb edrn-bmdb"
