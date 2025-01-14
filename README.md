# (nova) pretalx-docker

This repository contains a docker-compose setup for a [pretalx](https://github.com/pretalx/pretalx) installation based on docker.

This repository was inspired by [pretalx-docker](https://github.com/pretalx/pretalx-docker) but is heavily modified and
contains the source-code for pretalx so we can develop on it.

## Installation with docker-compose

### For local development

* Create ``src/pretalx.cfg``from ``src/pretalx.cfg.example`` and edit it.
* Create ``.env``from ``.env.example`` and edit it.
* Run ``docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d``. After a few minutes the setup should be accessible at http://localhost/orga
* Run ``sudo ./bin/build`` to build the project and the database.
* Set up a user and an organizer by running ~~``docker exec -ti pretalx pretalx init``~~ -> ``./bin/pretalx init``. You will need to create a super-user too, see next section for it.

### Installing Pretalx-Schedule

Pretalx contains a Pretalx-Schedule Module. You will need it, because that's the whole "Scheduler"-Frontend in Pretalx.
It has its own repository at [oercamp-pretalx-schedule](https://github.com/novagmbh/oercamp-pretalx-schedule).
Please clone the repo and follow the installation instructions.
Basically, pretalx uses a built & compressed version of this editor at ``src/pretalx/static/agenda/js/pretalx-schedule.js`` . So to make changes
you should dit the pretalx-schedule repository, and then there is a command that builds and copies the code over to pretalx.

### Running Pretalx-Schedule-Editor (Backend)

This is only for developing (DEBUG = true):

There is a module called "predalx-schedule-editor" (not same as pretalx-schedule). It needs a running vite-server in develop-mode to function.
To use the schedule-editor, you need to run ``src/pretalx/frontend/schedule-editor$ npm run build`` and then start the server with ``src/pretalx/frontend/schedule-editor$ npm start``


#### How to create a superuser

You can create a super-user interactively inside the docker container:
* connect to your docker container: ``docker exec -it pretalx /bin/bash``
* create one with ``python3 /pretalx/src/manage.py createsuperuser``

#### Start MailPit

Mailpit is configured for local development. Access it at http://localhost:8025/


#### Tips when developing

* Use ``./bin/pretalx`` to check all commands and also to check what environment python is using
* Use ``./bin/pretalx rebuild`` to re-generate static files and translations etc. after changing them.

### For production

#### Same as local development instructions, but with following changes:

* Edit ``src/pretalx.cfg`` and ``.env`` for production (see above).
* Include the ``docker-composer.prod.yml`` when running docker compose.
  Example: ``docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d``


* Configure a reverse-proxy for better security and to handle TLS. Pretalx listens on port 80 in the ``pretalxdocker``
  network. An example to copy into the normal compose file is located at ``reverse-proxy-examples/docker-compose``.
  You can also find a few words on an nginx configuration at ``reverse-proxy-examples/nginx``

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
* Set up a user and an organizer (see local develop instructions above)
* Set up a cronjob for periodic tasks like this ``15,45 * * * * docker exec pretalx-app pretalx runperiodic``

#### Current Live deployment procedure

* SSH to the live server, change to workdir ``cd /sites/oercamp/oercamp-pretalx/`` and run ``./bin/deploy-prod``
* ~~Additionally its good to run ``docker compose exec -u pretalxuser -T pretalx python3 /pretalx/src/manage.py regenerate_css``. This is already inside the the deploy script, but somehow it does not always work.~~


#### Setting up cronjobs on production (important for pretix API):

* We run the cronjobs from the host machine. It's not the most optimal solution, but ok for now. Add these instructions to pretalxuser crontab:

```
Install cron if needed:
apt-get update
apt-get install -y cron

Add to (root user's) crontab:
*/10 * * * * cd /sites/oercamp/oercamp-pretalx && docker compose exec -u pretalxuser -T pretalx python3 /pretalx/src/manage.py runperiodic 2>&1
5 5 5 */1 * cd /sites/oercamp/oercamp-pretalx && docker compose exec -u pretalxuser -T pretalx python3 /pretalx/src/manage.py clearsessions 2>&1
*/5 * * * * cd /sites/oercamp/oercamp-pretalx && docker compose exec -u pretalxuser -T pretalx python3 /pretalx/src/manage.py pretix_import_session_wishes 2>&1
```

#### Tips & Troubleshooting

* Exception log: ``(.docker/volumes)/data/logs/pretalx.log``


* Python-Dependencies are not installed locally or on a volume (i.e. like the vendor folder in composer). This means, if you change dependencies, then you should rebuild the docker image with ``docker compose build --no-cache [--progress=plain]``


* Simple Debugging: ``import logging``, and then in code ``logging.info('hallo')``, then check the ``pretalx.log``


* Missing CSS (404) Tips: This is only a Quickfix Approach - the regenerare_css function works weird. It was removed in a newer version of pretalx. If the css files are missing (agenda and cfp) then you can copy
the files from another event, but the hashes must be the same. Location is usually ``.docker/volumes/public/media/[event-name]``.
You can also rewrite regenerate_css to rebuild the files everytime, but it will delete all media files too,
so approach with high caution. A deeper understanding of the generation and a better solution must be found.


#### Open issues

* When disabling Debug mode (pretix.cfg debug = False), then media files are not found. This is probably due to different
file & folder handling when not in debug mode. Probably also has to do with the docker setup and/or volumes.
