"""Client address extraction for rate limiting.

Everything arrives through the proxy, so the socket peer is always nginx. The
real client is the last hop of X-Forwarded-For: nginx appends the address it
saw to whatever the client sent, so trusting the *first* entry would let a
caller rotate identities by inventing a header.
"""

from fastapi import Request


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Last entry is the one appended by our own proxy.
        candidate = forwarded.split(",")[-1].strip()
        if candidate:
            return candidate
    if request.client is not None:
        return request.client.host
    return "unknown"
