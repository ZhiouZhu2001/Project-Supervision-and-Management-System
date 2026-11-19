# Deploying to the host

Everything the server needs is in the repository. This page is the order to do
it in, and the checks that prove each step worked.

The application is one compose project on one host: nginx terminates TLS and is
the only published port; `api`, `web`, `db` and `backup` are reachable only on
the compose network.

## 1. Host

Ubuntu 24.04, 2 vCPU / 4 GB, Docker Engine + compose plugin. Then:

```bash
sudo infra/scripts/harden-host.sh
```

It installs UFW (22/80/443 only), fail2ban, unattended upgrades, disables SSH
password logins and caps Docker's log files. `ufw status verbose` is the proof.

## 2. DNS

An `A` record (and `AAAA` if you have IPv6) for `DOMAIN` pointing at the host.
Wait for `dig +short DOMAIN` to answer with the address before continuing —
certbot cannot validate a name that does not resolve yet.

## 3. Configuration

```bash
git clone git@github.com:ZhiouZhu2001/Project-Supervision-and-Management-System.git
cd Project-Supervision-and-Management-System
cp .env.example .env
```

Set at least: `DOMAIN`, `APP_SECRET_KEY` (`openssl rand -hex 32`), `APP_PASSWORD`,
`APP_EMAIL`, the `SMTP_*` block, `RESTIC_REPOSITORY` and `RESTIC_PASSWORD`.
The API refuses to start in production while the development secret or
password is still in place — that failure is the safety net, not a bug.

## 4. First certificate

The HTTPS server block needs a certificate that does not exist yet, so the
first one is obtained with the stack's plain-HTTP path:

```bash
mkdir -p infra/nginx/certs   # empty; the volume is used after this
make certs
```

If the ACME challenge cannot be served yet (nothing is listening on port 80),
use the standalone method for the first certificate only:

```bash
make certs-standalone
```

## 5. Start

```bash
make deploy
curl -fsS https://$DOMAIN/api/healthz
```

## 6. Verify the things ticket 28 asks for

```bash
# HTTP redirects permanently
curl -sI http://$DOMAIN/api/healthz | head -3          # expect 301

# Security headers
curl -sI https://$DOMAIN/ | grep -Ei \
  'strict-transport-security|content-type-options|referrer-policy'

# Only 80 and 443 answer
sudo ufw status verbose
nmap -Pn --top-ports 1000 $DOMAIN                       # from another machine

# Rate limit on login (11 requests in a minute, the 11th+ answers 429)
for i in $(seq 1 12); do
  curl -s -o /dev/null -w '%{http_code} ' -X POST https://$DOMAIN/api/auth/login \
    -H 'content-type: application/json' -d '{"email":"a@b.c","password":"x"}'
done; echo

# Renewal
make certs-renew

# Reboot recovery
sudo reboot
```

After the reboot, `make ps-prod` must show every service `Up` and the
health endpoint must answer — nothing is started by hand.

## Renewal

The `certbot` service loops twice a day and only acts inside the last 30 days
of a certificate's life. `make logs-prod` (the certbot service) is where renewals
appear; the dry run above is the rehearsal.
