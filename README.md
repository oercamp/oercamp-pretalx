# (nova) pretalx-docker

This repository contains our modified version of [pretalx](https://github.com/pretalx/pretalx) and a local and production setup based on docker.

This repository was inspired by [pretalx-docker](https://github.com/pretalx/pretalx-docker), but is heavily modified and
contains the source-code for pretalx so that we can develop on it.

### Tech stack

Pretalx uses following tech-stack:

* Gunicorn - webserver for Python/Django apps
* MySQL
* Python / Django Framework
* JS, Scss and Vue.js for some parts (mainly for Scheduler Feature)
* The VueJs part uses its own stack (vite, pug, stylus)
* Production runs a nginx webserver as a proxy.

# Installation

## Local development environment

* Create ``src/pretalx.cfg``from ``src/pretalx.example.cfg`` and edit it to your needs.


* Create ``.env``from ``.env.example`` and edit it.


* Run ``docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d``.
After a few minutes the setup should be accessible at http://localhost/orga
and a mail catcher at http://localhost:8025


* Run ``sudo ./bin/build`` to build the project and the database.

* Set up a user and an organizer
by running ~~``docker exec -ti pretalx pretalx init``~~ -> ``./bin/pretalx init``.
You will need to create a super-user too, see next section for it.

* Check also https://docs.pretalx.org/developer/ for more infos and troubleshooting

### Creating a superuser

You can create a super-user interactively inside the docker container, which is also
one of the first things to do after installing pretalx:

* connect to your docker container: ``docker exec -it pretalx /bin/bash``
* create one with ``python3 /pretalx/src/manage.py createsuperuser``

### Installing and running Pretalx-Schedule

Pretalx contains a standalone "Pretalx-Schedule" Module.
That's the whole "Scheduler"-Frontend in Pretalx.

It has its own repository at [oercamp-pretalx-schedule](https://github.com/novagmbh/oercamp-pretalx-schedule).

If needed, please clone the repo as a separate Project and follow the installation instructions there.

Pretalx uses a packaged & compressed version of this editor at ``src/pretalx/static/agenda/js/pretalx-schedule.js``.
There is a script file called `update-and-rebuild-pretalx.sh` in the root directory of [oercamp-pretalx-schedule](https://github.com/novagmbh/oercamp-pretalx-schedule).
This will build the code and copy it into your local pretalx project. It expects that both projects are inside the same
parent directory.

So there is no local dev-environment for the pretalx-schedule Module. Just build the code
using that script and the changes will be available in your pretalx project.

If you make changes to [oercamp-pretalx-schedule](https://github.com/novagmbh/oercamp-pretalx-schedule), please do not forget to
push these changes too.

### Running Pretalx-Schedule-Editor (Backend)

There is another module called "predalx-schedule-editor".
It is not the same as the mentioned pretalx-schedule, but the code is very similar.
In Debug Mode (debug=True) it needs a running vite-server in to function.
To use the schedule-editor, you need to
run ``src/pretalx/frontend/schedule-editor$ npm run build`` and then start the server
with ``src/pretalx/frontend/schedule-editor$ npm start``

(!) Update: It should not need a vite-server anymore. But still good to know.

### Plugins

You should activate the Plugins after a fresh installation. Some features depend on it.
Most important are the public-voting, pages and youtube plugins. The venueless Plugins can
stay disabled, it is also not working in the current version. We implemented a venueless
integration, but it does not depend on that plugin for now.

### MailPit

A mailcatcher, Mailpit, is already configured for the local dev-environment.
Access it at http://localhost:8025/


### Tips for developing

* Use ``./bin/pretalx`` to check all cli commands and also to check what environment python is using.
This can help you debugging Problems with the Python environment.


* Use ``./bin/build`` to build the project after changes, and to
re-generate static files, translations, migrations etc.


## Installation for production

* Installation is similar to local development instructions, but with following notable changes:


* Edit ``src/pretalx.cfg`` and ``.env`` for production (see above).


* Include the ``docker-composer.prod.yml`` and exclude the ``docker-composer.dev.yml``
when running docker-compose. Example:
``docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d``


* Configure a reverse-proxy for better security and to handle TLS.
Please check ``reverse-proxy-examples/nginx``,
where you will find a copy/example of a current nginx configuration.


* Make sure you serve all requests for the `/static/` and `/media/` paths when `debug=false`.
Please see [Pretalx Installation - step-7-reverse-proxy](https://docs.pretalx.org/administrator/installation/#step-7-reverse-proxy) for more info.


* Optional: Some of the Gunicorn parameters can be adjusted via environment variables:
  * To adjust the number of [Gunicorn workers](https://docs.gunicorn.org/en/stable/settings.html#workers), provide
  the container with `GUNICORN_WORKERS` environment variable.
  * `GUNICORN_MAX_REQUESTS` and `GUNICORN_MAX_REQUESTS_JITTER` to configure the requests a worker instance will process before restarting.
  * `GUNICORN_FORWARDED_ALLOW_IPS` lets you specify which IPs to trust (i.e. which reverse proxies' `X-Forwarded-*` headers can be used to infer connection security).
  * `GUNICORN_BIND_ADDR` can be used to change the interface and port that Gunicorn will listen on. Default: `0.0.0.0:80`

  Here's how to set an environment variable [in `docker-compose.yml`](https://docs.docker.com/compose/environment-variables/set-environment-variables/)
  or when using [`docker run` command](https://docs.docker.com/engine/reference/run/#env-environment-variables).


* Set up a user and an organizer (see local develop instructions above)


#### Setting up cronjobs on production (important for pretix API):

* We run the cronjobs from the host machine.
It's not the most optimal solution, but ok for now.
Add these instructions to (currently root) crontab:

```
Install cron if needed:
apt-get update
apt-get install -y cron

Add to (currently root user's) crontab:
*/10 * * * * cd /sites/oercamp/oercamp-pretalx && docker compose exec -u pretalxuser -T pretalx python3 /pretalx/src/manage.py runperiodic 2>&1
5 5 5 */1 * cd /sites/oercamp/oercamp-pretalx && docker compose exec -u pretalxuser -T pretalx python3 /pretalx/src/manage.py clearsessions 2>&1
*/5 * * * * cd /sites/oercamp/oercamp-pretalx && docker compose exec -u pretalxuser -T pretalx python3 /pretalx/src/manage.py pretix_import_session_wishes 2>&1
```

## Live deployment procedure

* SSH to the live server, change to workdir ``cd /sites/oercamp/oercamp-pretalx/`` and run ``./bin/deploy-prod``


## Tips & Troubleshooting

* Exception log: ``(.docker/volumes)/data/logs/pretalx.log``


* Python-Dependencies are not installed locally or on a volume (e.g. like the vendor folder in composer).
This means, if you change dependencies, then you need to rebuild the docker image with
``docker compose build --no-cache [--progress=plain]``

* You might also want to add following commands when rebuilding, depending on your problems,
but only if you know what you are doing:
```
sudo rm -rf .docker/volumes/*
sudo docker rmi pretalx-pretalx
sudo docker compose build --progress=plain --no-cache
```

* Simple Debugging: ``import logging``, and then inside code ``logging.info('hallo')``,
then check the ``pretalx.log``. Some parts of the code run in an async task runner (called celery).
This logging solution will not work there.


* Missing CSS (404) or even media files: This is only a Quickfix Approach - the regenerare_css function works weird. It seems that it was removed in a newer version of pretalx, but we still have it.
If the CSS files are missing (agenda and cfp) then you can copy the files from another event,
but the hashes must be the same (You can check them on Browser by the missing files).
Location is usually ``.docker/volumes/public/media/[event-name]``.
You can also rewrite regenerate_css to rebuild the files everytime,
but it will delete all media files too, so approach with high caution.
A deeper understanding of the generation and a better solution must be found.


## Good to know

* When disabling Debug mode (pretix.cfg debug = False), then pretalx (django) will not serve media files.
You will need to use nginx to serve them. This is already configured on live. See more infos at
``reverse-proxy-examples/nginx`` or https://github.com/pretalx/pretalx/issues/1720


### Mentionable changes

* Pretalx has a Plugin system, but it's a relatively simple one. You can define hooks,
but afaik not overwrite files. Because of that, time issues, and the nature of changes,
most changes were made directly inside the code.

