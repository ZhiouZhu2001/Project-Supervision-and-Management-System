# 28: Production deploy and hardening

**What to build:** The application running on the real host, on the real domain, over HTTPS, with the network surface reduced to what is actually needed.

**Blocked by:** 26

**Status:** done

- [ ] The site is reachable on the configured domain over HTTPS, and plain HTTP redirects permanently to it.
- [ ] The certificate renews automatically without manual intervention, and renewal has been observed at least once.
- [ ] Security headers are present: transport security, content-type nosniff, and a same-origin referrer policy.
- [ ] The login endpoint is rate-limited and request bodies are capped at the proxy, before they reach the application.
- [ ] From the public internet only 80 and 443 answer; the database and API ports are unreachable, and SSH accepts keys only.
- [ ] Rebooting the host brings every service back without manual steps.
