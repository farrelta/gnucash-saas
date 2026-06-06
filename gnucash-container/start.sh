#!/bin/bash

# Ensure /data directory exists with correct permissions
mkdir -p /data
chown -R 1000:1000 /data 2>/dev/null || true

export XDG_DATA_HOME=/data
export HOME=/data

# ── Generate nginx config with session prefix ───────────────────────
# The nginx sidecar rewrites root-relative asset paths in the XPRA HTML
# so that they include /session/<token>/, matching Traefik's router.
# shellcheck disable=SC2153
export NGINX_SESSION_PREFIX="${SESSION_TOKEN:-}"

envsubst '${NGINX_SESSION_PREFIX}' \
  < /etc/nginx/conf.d/default.conf.template \
  > /etc/nginx/conf.d/default.conf

# If SESSION_TOKEN is non-empty, also rewrite the trailing-slash
# redirect middleware's regex so it redirects correctly.
# (nginx doesn't use this; it's for reference / debugging.)

# ── Start nginx sidecar ─────────────────────────────────────────────
nginx -g "daemon off;" &
NGINX_PID=$!

# Give nginx a moment to start
sleep 1

# ── Clean up Xsession log ───────────────────────────────────────────
# xpra runs /etc/X11/Xsession which creates $HOME/.xsession-errors
# with harmless debug output. Delete it in background after startup.
( sleep 5 && rm -f /data/.xsession-errors ) &

# ── Start XPRA on the INTERNAL port (14501) ─────────────────────────
# nginx listens on 14500 and proxies to 14501.
# Note: openbox is intentionally omitted — xpra's HTML5 client has
# its own window management; openbox would need --start to run in
# the background but fails because the display doesn't exist yet at
# script startup (xpra creates :100 internally).
xpra start :100 \
  --start-child=gnucash \
  --bind-tcp=0.0.0.0:14501 \
  --html=on \
  --sharing=no \
  --daemon=no

# If xpra exits, stop nginx too
kill "$NGINX_PID" 2>/dev/null
exit 0
