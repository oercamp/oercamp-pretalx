# NGINX Config example

Your config could look like this:

```
server {
    listen 80 default_server;
    listen [::]:80 ipv6only=on default_server;
    server_name pretalx.mydomain.com;
}
server {
    listen 443 default_server;
    listen [::]:443 ipv6only=on default_server;
    server_name pretalx.mydomain.com;

    ssl on;
    ssl_certificate /path/to/cert.chain.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8355/;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Host $http_host;
    }
}
```

NOVA Info:

For DEBUG = False (only on live), you will need to serve static and media files
through nginx, they won't be served through pretalx (django).

DEBUG = False wont probably work locally, because there is no nginx :)
Maybe like this: https://stackoverflow.com/questions/72536548/nginx-how-to-specify-a-static-to-point-to-a-docker-volume
