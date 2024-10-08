FROM python:3.10-bookworm

RUN apt-get update && \
    apt-get install -y git gettext libmariadb-dev libpq-dev locales libmemcached-dev build-essential \
            supervisor \
            sudo \
            locales \
            --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    dpkg-reconfigure locales && \
    locale-gen C.UTF-8 && \
    /usr/sbin/update-locale LANG=C.UTF-8 && \
    mkdir /etc/pretalx && \
    mkdir /pretalx && \
    mkdir /pretalx/data && \
    mkdir /pretalx/data/media && \
    mkdir /pretalx/public && \
    groupadd -g 1000 pretalxuser && \
    useradd -r -u 1000 -g pretalxuser -d /pretalx -ms /bin/bash pretalxuser && \
    echo 'pretalxuser ALL=(ALL) NOPASSWD: /usr/bin/supervisord' >> /etc/sudoers

RUN usermod -a -G 1000 pretalxuser

ENV LC_ALL=C.UTF-8

COPY .docker/deployment/pretalx.bash /usr/local/bin/pretalx
COPY .docker/deployment/supervisord.conf /etc/supervisord.conf

# We have no volumes yet, so we will copy project files to build all dependencies, because
# dependencies are not installed locally in a vendor-like folder, but globally, so they are gone everytime the container goes down
WORKDIR /pretalx
COPY pyproject.toml /pretalx
COPY ./src /pretalx/src
RUN pip3 install --upgrade-strategy eager -Ue ".[dev]"
RUN pip3 install -e /pretalx/src/pretalx/plugins/pretalx-youtube
RUN pip3 install -e /pretalx/src/pretalx/plugins/pretalx-public-voting
RUN pip3 install -e /pretalx/src/pretalx/plugins/pretalx-pages
RUN rm -f /pretalx/pyproject.toml
RUN rm -rf /pretalx/src

RUN pip3 install -U pip mysqlclient redis setuptools wheel typing pylibmc gunicorn

RUN apt-get update && \
    apt-get install -y nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN chmod +x /usr/local/bin/pretalx
RUN chown -R pretalxuser:pretalxuser /pretalx /pretalx/data /pretalx/public

USER pretalxuser
#VOLUME ["/etc/pretalx", "/pretalx/data", "/pretalx/public"]
EXPOSE 80
ENTRYPOINT ["pretalx"]
CMD ["all"]
