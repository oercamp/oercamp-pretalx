# (nova) pretalx-docker

This repository contains a docker-compose setup for a [pretalx](https://github.com/pretalx/pretalx) installation based on docker.

This repository was inspired by [pretalx-docker](https://github.com/pretalx/pretalx-docker) but is heavily modified and
contains the source-code for pretalx so we can develop on it.

## Installation with docker-compose

### For local developing

* Copy ``src/pretalx.example.cfg`` to ``conf/`` and rename it to ``pretalx.cfg``, so that you have a ``conf/pretalx.cfg`` (Hint: This will later be put to ``/etc/pretalx/pretalx.cfg`` on the server).
* Run ``docker-compose up -d``. After a few minutes the setup should be accessible at http://localhost/orga
* Set up a user and an organizer by running ~~``docker exec -ti pretalx pretalx init``~~ -> ``./bin/pretalx init``. You will need to create a super-user too, see next section for it.

#### How to create a superuser

You can create a super-user interactively inside the docker container:
* connect to your docker container: ``docker exec -it pretalx /bin/bash``
* create one with ``python /pretalx/src/manage.py createsuperuser``

#### Tips

* Exception log: ``(.docker/volumes)/data/logs/pretalx.log``

### For production

* Edit ``conf/pretalx.cfg`` and fill in your own values (→ [configuration
  documentation](https://docs.pretalx.org/en/latest/administrator/configure.html))
* Edit ``docker-compose.yml`` and remove the complete section with ``ports: - "80:80"`` from the file (if you go with
  traefic as reverse proxy) or change the line to ``ports: - "127.0.0.1:8355:80"`` (if you use nginx). **Change the
  database password.**
* If you don't want to use docker volumes, create directories for the persistent data and make them read-writeable for
  the userid 999 and the groupid 999. Change ``pretalx-redis``, ``pretalx-db``, ``pretalx-data`` and ``pretalx-public`` to the corresponding
  directories you've chosen.
* Configure a reverse-proxy for better security and to handle TLS. Pretalx listens on port 80 in the ``pretalxdocker``
  network. I recommend to go with traefik for its ease of setup, docker integration and [LetsEncrypt
  support](https://docs.traefik.io/user-guide/docker-and-lets-encrypt/). An example to copy into the normal compose file
  is located at ``reverse-proxy-examples/docker-compose``. You can also find a few words on an nginx configuration at
  ``reverse-proxy-examples/nginx``
* Make sure you serve all requests for the `/static/` and `/media/` paths (when `debug=false`). See [installation](https://docs.pretalx.org/administrator/installation/#step-7-ssl) for more information
* Optional: Some of the Gunicorn parameters can be adjusted via environment viariables:
  * To adjust the number of [Gunicorn workers](https://docs.gunicorn.org/en/stable/settings.html#workers), provide
  the container with `GUNICORN_WORKERS` environment variable.
  * `GUNICORN_MAX_REQUESTS` and `GUNICORN_MAX_REQUESTS_JITTER` to configure the requests a worker instance will process before restarting.
  * `GUNICORN_FORWARDED_ALLOW_IPS` lets you specify which IPs to trust (i.e. which reverse proxies' `X-Forwarded-*` headers can be used to infer connection security).
  * `GUNICORN_BIND_ADDR` can be used to change the interface and port that Gunicorn will listen on. Default: `0.0.0.0:80`

  Here's how to set an environment variable [in
  `docker-compose.yml`](https://docs.docker.com/compose/environment-variables/set-environment-variables/)
  or when using [`docker run` command](https://docs.docker.com/engine/reference/run/#env-environment-variables).
* Run ``docker-compose up -d ``. After a few minutes the setup should be accessible under http://yourdomain.com/orga
* Set up a user and an organizer by running ``docker exec -ti pretalx pretalx init``.
* Set up a cronjob for periodic tasks like this ``15,45 * * * * docker exec pretalx-app pretalx runperiodic``

