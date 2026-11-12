"""SSRF protections for worker HTTP/net jobs and webhook-driven fetches."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class SSRFBlocked(ValueError):
    pass


_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata",
    "instance-data",
}


def _is_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def is_blocked_host(host: str) -> bool:
    host = host.strip().lower().rstrip(".")
    if not host:
        return True
    if host in _BLOCKED_HOSTNAMES or host.endswith(".localhost"):
        return True
    if host.endswith(".internal") or host.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return _is_private_ip(ip)
    except ValueError:
        return False


def resolve_and_check(host: str, *, allow_private: bool = False) -> list[str]:
    if is_blocked_host(host) and not allow_private:
        raise SSRFBlocked(f"blocked host: {host}")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise SSRFBlocked(f"dns failed for {host}: {exc}") from exc
    addrs: list[str] = []
    for info in infos:
        ip_s = info[4][0]
        addrs.append(ip_s)
        ip = ipaddress.ip_address(ip_s)
        if not allow_private and _is_private_ip(ip):
            raise SSRFBlocked(f"resolved to private/reserved address {ip_s} for {host}")
    if not addrs:
        raise SSRFBlocked(f"no addresses for {host}")
    return sorted(set(addrs))


def assert_safe_url(url: str, *, allow_private: bool = False, schemes: set[str] | None = None) -> str:
    schemes = schemes or {"http", "https"}
    parsed = urlparse(url.strip())
    if parsed.scheme not in schemes:
        raise SSRFBlocked(f"scheme not allowed: {parsed.scheme!r}")
    if parsed.username or parsed.password:
        raise SSRFBlocked("userinfo in URL is not allowed")
    host = parsed.hostname
    if not host:
        raise SSRFBlocked("URL missing host")
    if parsed.port in {22, 25, 137, 139, 445, 3306, 5432, 6379, 11211, 27017}:
        raise SSRFBlocked(f"port {parsed.port} blocked")
    resolve_and_check(host, allow_private=allow_private)
    return url
