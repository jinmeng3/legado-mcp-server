from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import httpx

MAX_RESPONSE_BYTES = 10 * 1024 * 1024
MAX_REDIRECTS = 5
MAX_TIMEOUT_SECONDS = 60.0


def _validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("url must be an absolute http(s) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are not allowed")

    host = parsed.hostname.rstrip(".")
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(
                    host,
                    parsed.port or (443 if parsed.scheme == "https" else 80),
                    type=socket.SOCK_STREAM,
                )
            ]
        except OSError as exc:
            raise ValueError(f"Could not resolve URL host: {host}") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("URL host must resolve exclusively to public IP addresses")


def fetch_public_url(
    url: str,
    *,
    method: str = "GET",
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = 20.0,
) -> tuple[bytes, str, int, dict[str, str]]:
    timeout = max(0.1, min(float(timeout_seconds), MAX_TIMEOUT_SECONDS))
    current_url = url
    request_headers = dict(headers or {})
    original = urlsplit(current_url)

    with httpx.Client(
        follow_redirects=False, timeout=timeout, trust_env=False
    ) as client:
        for redirect_count in range(MAX_REDIRECTS + 1):
            _validate_public_url(current_url)
            with client.stream(
                method,
                current_url,
                content=content,
                headers=request_headers,
            ) as response:
                network_stream = response.extensions.get("network_stream")
                get_extra_info = getattr(network_stream, "get_extra_info", None)
                peer_address = get_extra_info("server_addr") if get_extra_info else None
                if not peer_address:
                    raise ValueError("Could not verify connected URL address")
                try:
                    peer_ip = ipaddress.ip_address(peer_address[0])
                except ValueError as exc:
                    raise ValueError("Could not verify connected URL address") from exc
                if not peer_ip.is_global:
                    raise ValueError("Connected URL address must be public")
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Redirect response has no Location header")
                    if redirect_count == MAX_REDIRECTS:
                        raise ValueError("Too many redirects")
                    next_url = urljoin(str(response.url), location)
                    next_origin = urlsplit(next_url)
                    if (next_origin.scheme, next_origin.hostname, next_origin.port) != (
                        original.scheme,
                        original.hostname,
                        original.port,
                    ):
                        request_headers = {
                            key: value
                            for key, value in request_headers.items()
                            if key.lower() not in {
                                "authorization",
                                "cookie",
                                "proxy-authorization",
                            }
                        }
                    if response.status_code == 303 or (
                        response.status_code in {301, 302} and method.upper() == "POST"
                    ):
                        method, content = "GET", None
                    current_url = next_url
                    continue

                data = bytearray()
                for chunk in response.iter_bytes():
                    if len(data) + len(chunk) > MAX_RESPONSE_BYTES:
                        raise ValueError(
                            f"Response exceeds {MAX_RESPONSE_BYTES} byte limit"
                        )
                    data.extend(chunk)
                return (
                    bytes(data),
                    str(response.url),
                    response.status_code,
                    dict(response.headers),
                )

    raise ValueError("Too many redirects")
