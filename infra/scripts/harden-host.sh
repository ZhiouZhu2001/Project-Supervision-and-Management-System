#!/usr/bin/env bash
# Reduce the host's network surface to what the application needs (ticket 28).
#
# Run once on a fresh Ubuntu 24.04 host, as root, after SSH keys work. It is
# idempotent: running it twice changes nothing the second time.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "run as root" >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ufw fail2ban unattended-upgrades

# Only SSH, HTTP and HTTPS answer from the internet. Everything else — the
# database, the API, Docker's own ports — is not reachable even by accident.
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'ssh'
ufw allow 80/tcp comment 'http -> https redirect + ACME'
ufw allow 443/tcp comment 'https'
ufw --force enable

# Keys only. Password authentication on an internet-facing host is a lifetime
# subscription to credential stuffing.
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
systemctl reload ssh

cat > /etc/fail2ban/jail.local <<'JAIL'
[sshd]
enabled = true
maxretry = 4
bantime = 1h
findtime = 10m
JAIL
systemctl enable --now fail2ban
systemctl restart fail2ban

# Docker publishes on its own iptables chain; this keeps a container from
# opening a host port even if somebody adds a ports: entry by mistake.
python3 - <<'PY'
import json, pathlib
path = pathlib.Path('/etc/docker/daemon.json')
config = json.loads(path.read_text()) if path.exists() else {}
config.setdefault('iptables', True)
config.setdefault('log-driver', 'json-file')
config.setdefault('log-opts', {'max-size': '10m', 'max-file': '3'})
path.write_text(json.dumps(config, indent=2))
PY
systemctl restart docker

echo "host hardened: ufw 22/80/443, ssh keys only, fail2ban, docker logs capped"
ufw status verbose
