#!/bin/bash
# docker container entrypoint
#
set -e

ENV_VARS='
$GITLAB_URL
$OAUTH2_CLIENT_ID
$OAUTH2_CLIENT_SECRET
$AUTH_SEVER_NAME
$AUTH_SEVER_NAME_BASE
$AUTH_SEVER_PORT
$AUTH_SEVER_URL
$AUTH_SEVER_COOKIE_SECURE
$AUTH_SEVER_COOKIE_SECRET
'

envsubst "$ENV_VARS" < /app/docker/nginx.conf.template > /etc/nginx/nginx.conf
envsubst "$ENV_VARS" < /app/docker/oauth2_proxy.cfg.template > /etc/oauth2_proxy.cfg

exec /usr/bin/supervisord

