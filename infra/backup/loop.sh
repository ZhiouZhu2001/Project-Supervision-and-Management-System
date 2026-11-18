#!/bin/sh
# Nightly at 03:00 local time. A fixed sleep would drift across a restart; this
# recomputes the next 03:00 every time round.
while :; do
    now="$(date +%s)"
    next="$(date -d 'today 03:00' +%s)"
    [ "$next" -le "$now" ] && next="$(date -d 'tomorrow 03:00' +%s)"
    sleep $((next - now))
    /usr/local/bin/backup.sh || echo "backup run failed; status file records it" >&2
done
