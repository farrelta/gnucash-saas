FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    gnucash \
    xpra \
    openbox \
    xterm \
    dbus-x11 \
    && apt-get clean

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 14500

CMD ["/start.sh"]
