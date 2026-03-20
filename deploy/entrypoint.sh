#!/bin/sh
# Substitute HAIBOT_PORT in supervisord template and start supervisord.
# Default port 8088; override at runtime with -e HAIBOT_PORT=3000.
set -e
export HAIBOT_PORT="${HAIBOT_PORT:-8088}"
envsubst '${HAIBOT_PORT}' \
  < /etc/supervisor/conf.d/supervisord.conf.template \
  > /etc/supervisor/conf.d/supervisord.conf
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
