FROM ubuntu:24.04

# Install system dependencies (GnuCash, XPRA, nginx as reverse-proxy sidecar)
RUN apt-get update && apt-get install -y \
    gnucash \
    xpra \
    openbox \
    xterm \
    dbus-x11 \
    nginx \
    gettext-base \
    && apt-get clean

COPY start.sh /start.sh
RUN chmod +x /start.sh

# Template nginx config — ${SESSION_TOKEN} is substituted at startup
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

EXPOSE 14500

CMD ["/start.sh"]
