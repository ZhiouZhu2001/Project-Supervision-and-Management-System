# Backup sidecar. Small, and deliberately not able to write to the database:
# it can only read a dump. If this image is compromised the diary survives.
FROM alpine:3.20

RUN apk add --no-cache postgresql16-client restic tzdata curl \
    && rm -rf /var/cache/apk/*

ENV TZ=Europe/Madrid

COPY backup.sh /usr/local/bin/backup.sh
COPY restore.sh /usr/local/bin/restore.sh
COPY loop.sh /usr/local/bin/loop.sh
RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/restore.sh /usr/local/bin/loop.sh

CMD ["/usr/local/bin/loop.sh"]
