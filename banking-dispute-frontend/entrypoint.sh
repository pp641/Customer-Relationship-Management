#!/usr/bin/env sh

# replacing environment variables in env.js
envsubst < /usr/share/nginx/html/env.js.template > /usr/share/nginx/html/env.js
# Start nginx
nginx -g 'daemon off;'