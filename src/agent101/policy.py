from urllib.parse import urlsplit


class PolicyError(ValueError):
    """An operation violates an application rule."""


def validate_url(url: str, allowed_domains: list[str]) -> str:
    """Accept HTTPS URLs on exact approved hosts, without credentials or ports."""

    if "\\" in url or any(char.isspace() or ord(char) < 32 for char in url):
        raise PolicyError("URL contains whitespace or invalid characters.")

    try:
        parts = urlsplit(url)
        hostname = parts.hostname
    except ValueError:
        raise PolicyError("Malformed URL.") from None

    if parts.scheme != "https" or not hostname:
        raise PolicyError("URL must use HTTPS and include a hostname.")

    if parts.netloc.lower() != hostname:
        raise PolicyError("URL credentials and explicit ports are not allowed.")

    approved_hosts = {domain.lower() for domain in allowed_domains}
    if hostname not in approved_hosts:
        raise PolicyError("URL hostname is not approved.")

    return parts._replace(fragment="").geturl()
